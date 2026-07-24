from __future__ import annotations

from flask import current_app

from server import db

from server.api import auth
from server.api.handlers.registry import handles
from server.api.requests.user import (
    UserUserReq,
    UserLoginReq,
    UserPasswdReq,
    UserCancelReq,
    UserListReq,
    UserWhoamiReq
)
from server.api.responses.user import (
    UserResp,
    UserCancelResp,
    UserListResp,
    UserWhoamiResp
)

from server.funcs import users


#TODO: Log user events to user log for server
@handles(UserUserReq)
def user(req: UserUserReq) -> ApiResp:
    """
    Client curls this during init

    If the user exists and gives invalid key, returns no key
    If the user exists and gives valid key, returns the key
    If the user does not exist and create is true, the user is created w/o password
    """

    resp = auth.validate_api_req(req, key_check=False)
    if resp: return resp

    # Initial username filter
    if not req.user or any(char.isspace() for char in req.user):
        return UserResp(valid=False, action="Username invalid", code=403)

    # Retrieve user info
    user_info = auth.get_user_auth(req.user)

    # Create user if not in db and create flag provided
    if req.register and not user_info:
        auth.create_user(req.user, req.curUser, req.host)
        if users.user_is_admin(req.user):
            return UserResp(action="Set password", user=req.user)
        return UserResp(action="User requested", user=req.user)

    # User exists but create requested
    if req.register and user_info and users.user_approved(user_info):
        return UserResp(action="User exists", user=req.user, code=409)

    # User needs to be created
    if not user_info:
        return UserResp(action="User not created", user=req.user, code=404)

    # No banned or rejected users
    if users.user_banned_or_rejected(user_info):
        return UserResp(action="User disavowed", user=req.user, code=403)

    # Users must be approved
    if not users.user_approved(user_info):
        return UserResp(action="User pending", user=req.user, code=403)

    # Return set password
    if not user_info.get('password_hash'):
        return UserResp(action="Set password", user=req.user, code=401)

    # Validate provided key
    active = auth.validate_key(req.user, req.apiKey)
    if active and req.apiKey:
        return UserResp(apiKey=req.apiKey, user=req.user)

    # Return login required
    return UserResp(action="Login", user=req.user, code=401)


@handles(UserLoginReq)
def login(req: UserLoginReq) -> ApiResp:
    resp = auth.validate_api_req(req, key_check=False)
    if resp: return resp

    # Check user existence
    user_info = auth.get_user_auth(req.user)
    if not user_info:
        return UserResp(valid=False, action="Invalid user", user=req.user, code=401)

    # Check if user banned or rejected
    if users.user_banned_or_rejected(user_info):
        return UserResp(valid=False, action="User disavowed", user=req.user, code=403)

    # Check that user is approved
    if not users.user_approved(user_info):
        return UserResp(valid=False, action="User pending", user=req.user, code=403)

    # Check password is correct
    if not auth.verify_password(req.password, user_info['password_hash']):
        return UserResp(valid=False, action="Retry password", user=req.user, code=401)

    # Get and return new api key
    key = auth.create_api_key(req.user)
    return UserResp(apiKey=key, user=req.user)


@handles(UserPasswdReq)
def passwd(req: UserPasswdReq) -> ApiResp:
    """
    Method to set/reset passwords
    Password can only be set for user if never set
    Password can only be reset for user if api key is valid
    """

    resp = auth.validate_api_req(req)
    if resp: return resp

    if not req.user or not req.password:
        return UserResp(valid=False, user=req.user, code=400)

    # Retrieve user info
    user_info = auth.get_user_auth(req.user)
    if not user_info:
        return UserResp(valid=False, user=req.user, code=404)

    # Check if user banned or rejected
    if users.user_banned_or_rejected(user_info):
        return UserResp(valid=False, user=req.user, code=403)

    # Validate api key - True if password unset or key valid
    active = auth.validate_key(req.user, req.apiKey)

    # Change password only if unset or api key active
    if active:
        # Delete all keys for user
        auth.cleanup_api_keys(unused_days=0, username=req.user)
        # Set password
        auth.set_password(req.user, req.password)
        # Get key
        key = auth.create_api_key(req.user)

        return UserResp(apiKey=key, user=req.user)

    return UserResp(valid=False, user=req.user, code=401)


@handles(UserCancelReq)
def cancel(req: UserCancelReq) -> ApiResp:
    """
    Client curls this to cancel their user request
    Cancelling request logs to running server and deletes user from db
    """

    resp = auth.validate_api_req(req, key_check=False)
    if resp: return resp

    with db.db_cursor() as cursor:
        user_req = db.fetch_row(
            """
            SELECT *
            FROM users
            WHERE username = %(username)s
                AND status = 'requested'
            """,
            {
                "username": req.user
            },
            cursor=cursor
        )

        # Was there a request for this user
        if not user_req:
            return UserCancelResp(valid=False, action="Request not found", code=404)

        # Cancellation needs to come from request user/host
        if user_req.get("created_by") != req.curUser or user_req.get("created_on_host") != req.host:
            return UserCancelResp(valid=False, action="Cancel where requested", code=403)

        cancelled = db.fetch_row(
            """
            DELETE FROM users
            WHERE username = %(username)s
                AND status = 'requested'
            RETURNING id, username
            """,
            {
                "username": req.user
            },
            cursor=cursor
        )
    current_app.logger.info(f"User {req.curUser} cancelled request for creation of {req.user} from {req.host}")

    return UserCancelResp(user=cancelled.get("username"), userId=cancelled.get("id"))


@handles(UserListReq)
def list_users(req: UserListReq) -> ApiResp:
    """
    Route to send user profile data to clients on `game users` command
    This makes usernames and statuses available to all users

    If requesting user is an admin, id and more detailed status information is shown
    """

    resp = auth.validate_api_req(req)
    if resp: return resp

    rows = []
    table = "detailed_user_profiles" if req.userIsAdmin else "user_profiles"
    rows = db.fetch_rows(
       f"""
        SELECT *
        FROM {table}
        """
    )

    return UserListResp(users=rows, admin=req.userIsAdmin)


@handles(UserWhoamiReq)
def whoami(req: UserWhoamiReq) -> ApiResp:
    """
    Route to send simple user profile data back to user
    """

    resp = auth.validate_api_req(req)
    if resp: return resp

    row = db.fetch_row(
        """
        SELECT username, status, last_seen_at
        FROM user_profiles
        WHERE username = %(username)s
        """,
        {
            "username": req.user
        }
    )

    return UserWhoamiResp(userProfile=row)

