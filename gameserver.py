#!/usr/bin/env python3

import signal

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    Response
)

from imports import admin # admin cmd handling
from imports import auth # api key / login handling
from imports import config # server config loader
from imports import db # db connection handling
from imports import games # game module handling
from imports import man # man index and html/terminal pages
from imports import users # public user functions

# Initialize app
app = Flask(__name__)

# Register import blueprints
app.register_blueprint(admin.bp)
app.register_blueprint(games.bp)
app.register_blueprint(man.bp)

# Initialize game blueprints
games.import_game_bps(app)

# Initialize database
db.init_pool()

# Save SERVER_CONFIG as CONFIG for readability
CONFIG = config.SERVER_CONFIG

# Set up exit handler
def handle_exit(*args):
    db.close_pool()
    raise KeyboardInterrupt()
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


@app.route('/')
def index():
    script = render_template(
        "client/init",
        url=request.host_url.rstrip("/"),
        admins=CONFIG.admins,
        server_ver=auth.SERVER_API_VER
    )

    return Response(script, mimetype="text/plain")


##############
# Completion #
##############

@app.route('/templates/<name>-completion')
def completion(name):
    script = render_template(
        "client/completion",
        game=name,
        game_list=games.GAME_CMDS
    )

    return Response(script, mimetype="text/plain")


@app.route('/templates/<name>-alias-completion')
def alias_completion(name):
    script = render_template(
        "client/alias-completion",
        alias=name
    )

    return Response(script, mimetype="text/plain")


#TODO: Log user events to user log for server
################
# Login Routes #
################

@app.route('/user', methods=['POST'])
def user():
    """
    Client curls this during init

    If the user exists and gives invalid key, returns no key
    If the user exists and gives valid key, returns the key
    If the user does not exist and create is true, the user is created w/o password
    """

    data, resp = auth.validate_api_req(request, key_check=False)
    if resp: return resp

    username = data.get('user')
    cur_user = data.get('curuser')
    host = data.get('host')
    api_key = data.get('key')
    create = data.get('create', False)

    # Initial username filter
    if not username or any(char.isspace() for char in username):
        return jsonify(valid=False, action="Username invalid", user=None), 403

    # Retrieve user info
    user_info = auth.get_user_auth(username)

    # Create user if not in db and create flag provided
    if create and not user_info:
        auth.create_user(username, cur_user, host)
        if users.user_is_admin(username):
            return jsonify(action="Set password", user=username), 200
        return jsonify(action="User requested", user=username), 200

    # User exists but create requested
    if create and user_info and users.user_approved(user_info):
        return jsonify(action="User exists", user=username), 409

    # User needs to be created
    if not user_info:
        return jsonify(action="User not created", user=username), 404

    # No banned or rejected users
    if users.user_banned_or_rejected(user_info):
        return jsonify(action="User disavowed", user=username), 403

    # Users must be approved
    if not users.user_approved(user_info):
        return jsonify(action="User pending", user=username), 403

    # Return set password
    if not user_info.get('password_hash'):
        return jsonify(action="Set password", user=username), 401

    # Validate provided key
    active = auth.validate_key(username, api_key)
    if active and api_key:
        return jsonify(key=api_key, user=username), 200

    # Return login required
    return jsonify(user=username, action="Login"), 401


@app.route('/cancel', methods=['POST'])
def cancel():
    """
    Client curls this to cancel their user request
    Cancelling request logs to running server and deletes user from db
    """

    data, resp = auth.validate_api_req(request, key_check=False)
    if resp: return resp

    username = data.get('user')
    cur_user = data.get('curuser')
    host = data.get('host')

    with db.db_cursor() as cursor:
        user_req = db.fetch_row(
            """
            SELECT *
            FROM users
            WHERE username = %(username)s
                AND status = 'requested'
            """,
            {
                "username": username
            },
            cursor=cursor
        )

        # Was there a request for this user
        if not user_req:
            return jsonify(valid=False, action="Request not found"), 404

        # Cancellation needs to come from request user/host
        if user_req.get("created_by") != cur_user or user_req.get("created_on_host") != host:
            return jsonify(valid=False, action="Cancel where requested"), 403

        cancelled = db.fetch_row(
            """
            DELETE FROM users
            WHERE username = %(username)s
                AND status = 'requested'
            RETURNING id, username
            """,
            {
                "username": username
            },
            cursor=cursor
        )
    app.logger.info(f"User {cur_user} cancelled request for creation of {username} from {host}")

    return jsonify(valid=True, user=cancelled.get("username"), user_id=cancelled.get("id")), 200


@app.route('/passwd', methods=['POST'])
def passwd():
    """
    Method to set/reset passwords
    Password can only be set for user if never set
    Password can only be reset for user if api key is valid
    """

    data, resp = auth.validate_api_req(request)
    if resp: return resp

    password = data.get('password')
    username = data.get('user')
    api_key  = data.get('key')

    if not username or not password:
        return jsonify(valid=False, user=username), 400

    # Retrieve user info
    user_info = auth.get_user_auth(username)
    if not user_info:
        return jsonify(valid=False, user=username), 404

    # Check if user banned or rejected
    if users.user_banned_or_rejected(user_info):
        return jsonify(valid=False, user=username), 403

    # Validate api key - True if password unset
    active = auth.validate_key(username, api_key)

    # Change password only if unset or api key active
    if active:
        # Delete all keys for user
        auth.cleanup_api_keys(unused_days=0, username=username)
        # Set password
        auth.set_password(username, password)
        # Get key
        key = auth.create_api_key(username)

        return jsonify(valid=True, key=key, user=username), 200

    return jsonify(valid=False, user=username), 401


@app.route('/login', methods=['POST'])
def login():
    data, resp = auth.validate_api_req(request, key_check=False)
    if resp: return resp

    password = data.get('password')
    username = data.get('user')

    # Check user existence
    user_info = auth.get_user_auth(username)
    if not user_info:
        return jsonify(valid=False, action="Invalid user", user=username), 401

    # Check if user banned or rejected
    if users.user_banned_or_rejected(user_info):
        return jsonify(valid=False, action="User disavowed", user=username), 403

    # Check that user is approved
    if not users.user_approved(user_info):
        return jsonify(valid=False, action="User pending", user=username), 403

    # Check password is correct
    if not auth.verify_password(password, user_info['password_hash']):
        return jsonify(valid=False, action="Retry password", user=username), 401

    # Get and return new api key
    key = auth.create_api_key(username)
    return jsonify(valid=True, key=key, user=username), 200


@app.route('/list_users', methods=['POST'])
def list_users():
    """
    Route to send user profile data to clients on `game users` command
    This makes usernames and statuses available to all users

    If requesting user is an admin, id and more detailed status information is shown
    """

    data, resp = auth.validate_api_req(request)
    if resp: return resp

    username = data.get('user')
    is_admin = users.user_is_admin(username)

    rows = []
    table = "detailed_user_profiles" if is_admin else "user_profiles"
    rows = db.fetch_rows(
       f"""
        SELECT *
        FROM {table}
        """
    )

    return jsonify(valid=True, users=rows, admin=is_admin), 200


@app.route('/whoami', methods=['POST'])
def whoami():
    """
    Route to send simple user profile data back to user
    """

    data, resp = auth.validate_api_req(request)
    if resp: return resp

    username = data.get('user')

    row = db.fetch_row(
        """
        SELECT username, status, last_seen_at
        FROM user_profiles
        WHERE username = %(username)s
        """,
        {
            "username": username
        }
    )

    return jsonify(valid=True, user_profile=row), 200


########
# Main #
########

if __name__ == '__main__':
    app.run(host=CONFIG.host, port=CONFIG.port, debug=True, threaded=True)

