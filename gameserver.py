import signal

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    Response
)
from jinja2 import (
    ChoiceLoader,
    FileSystemLoader
)

from imports import __version__ as SERVER_API_VER
from imports import api # api key handling
from imports import config # server config handling
from imports import json # json data file handling
from imports.games import (
    bp as games_bp,
    GAME_LIST
)
from imports.man import (
    bp as man_bp,
    MAN_DIR
) # man index and html/terminal pages

app = Flask(__name__)
app.register_blueprint(games_bp)
app.register_blueprint(man_bp)

# Add man pages to jinja template paths
app.jinja_loader = ChoiceLoader([
    app.jinja_loader,
    FileSystemLoader(MAN_DIR),
])


def handle_exit(*args):
    raise KeyboardInterrupt()

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

CONFIG = config.load_config(config.SERVER_CONFIG)

@app.route('/')
def index():
    script = render_template(
        "client/init",
        host=CONFIG.host,
        port=CONFIG.port,
        server_ver=api.SERVER_API_VER
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
        game_list=GAME_LIST
    )

    return Response(script, mimetype="text/plain")

################
# Login Routes #
################

@app.route('/user', methods=['POST'])
def user():
    """
    The user method is curled in the init script

    If the user exists and has an inactive key, it erases the key
    If the user exists and has an active key, it returns the key
    If the user does not exist, the user is added to users.json
    """

    data, resp = api.validate_api_req(request)
    if resp:
        return resp

    username = data.get("user")

    users = json.load_users()

    if username in users:
        # No need to create user if exists
        user_info = users[username]

        # If password not set up, don't generate key
        if not user_info.get("password_hash"):
            return jsonify(valid=True, key=None, expires=0, user=username), 200

        api_key = user_info["api_key"]
        expr = user_info["api_key_expires"]

        valid, _ = api.validate_key(api_key)
        if not valid:
            user_info["api_key"] = api_key = None
            user_info["api_key_expires"] = expr = 0
            json.save_users(users)

        return jsonify(valid=True, key=api_key, expires=expr, user=username), 200

    if username and " " not in username and username != "null":
        users[username] = {
            "password_hash": None,
            "api_key": None,
            "api_key_expires": 0
        }
    else:
        return jsonify(valid=False, key=None, expires=0, user=None), 403

    json.save_users(users)

    return jsonify(valid=True, key=None, expires=0, user=username), 200

@app.route('/passwd', methods=['POST'])
def passwd():
    """
    Method to set/reset passwords
    Password can only be set for user if never set
    Password can only be reset for user if api key is valid
    """

    data, resp = api.validate_api_req(request)
    if resp:
        return resp

    password  = data.get('password')
    username  = data.get('user')
    api_key   = data.get('key')

    users = json.load_users()

    if username in users:
        user_info = users[username]
        active, usern = api.validate_key(api_key)

        if not user_info["password_hash"] or (active and username == usern):
            user_info["password_hash"] = api.hash_password(password)
            key, expr = api.generate_api_key()
            user_info["api_key"] = key
            user_info["api_key_expires"] = expr
            json.save_users(users)

            return jsonify(valid=True, key=api_key, expires=expr, user=username), 200

    return jsonify(valid=False, user=username), 400

@app.route('/login', methods=['POST'])
def login():
    data, resp = api.validate_api_req(request)
    if resp:
        return resp

    password = data.get('password')
    username = data.get('user')

    users = json.load_users()

    if username in users:
        user_info = users[username]
        if not user_info["password_hash"]:
            return jsonify(valid=False, action="Set password", user=username), 403

        if not api.verify_password(password, user_info["password_hash"]):
            return jsonify(valid=False, action="Retry password", user=username), 401

        # Only regenerate key if inactive
        key = user_info["api_key"]
        expr = user_info["api_key_expires"]

        active, _ = api.validate_key(user_info["api_key"])
        if not active:
            key, expr = api.generate_api_key()
            user_info["api_key"] = key
            user_info["api_key_expires"] = expr
            json.save_users(users)

        return jsonify(valid=True, key=key, expires=expr, user=username), 200

    return jsonify(valid=False, action="Invalid user", user=username), 401

########
# Main #
########

if __name__ == '__main__':
    app.run(host=CONFIG.host, port=CONFIG.port, debug=True, threaded=True)

