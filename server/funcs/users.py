from server import db # db interactions
from server import config # server config loader


## Functions ##
def user_banned_or_rejected(user_profile):
    """
    Input row of user profile and return True if status is banned/rejected
    """

    return user_profile and user_profile.get('status') in ["banned", "rejected"]


def user_approved(user_profile):
    """
    Input row of user profile and return True if status is approved
    """

    return user_profile and user_profile.get('status') == "approved"


def user_is_admin(username):
    """
    Input username and return True if user is an admin
    """

    return username in config.SERVER_CONFIG.admins


def user_id_from_username(username):
    """
    Return user id from their username
    """

    return db.fetch_col(
        """
        SELECT id
        FROM user_profiles
        WHERE username = %(username)s
        """,
        {
            "username": username
        }
    )


def get_user(username):
    """
    Retrieve user_profile for username
    This method is what games should use to get single user data
    """

    return db.fetch_row(
        """
        SELECT *
        FROM user_profiles
        WHERE username = %(username)s
        """,
        {
            "username": username
        }
    )


def get_users():
    """
    Retrieve all user_profiles
    This method is what games should use to get all user data
    """

    return db.fetch_row(
        """
        SELECT *
        FROM user_profiles
        """
    )

