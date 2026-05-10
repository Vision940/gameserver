import hashlib
import hmac
import os
import secrets

from datetime import datetime, timezone

import bcrypt

from flask import jsonify

from imports import __version__ as SERVER_API_VER
from imports import db # db interactions
from imports import users # public user functions
from imports import config # server config

# Ensure secret key set up for server
SERVER_SECRET = os.environ.get('SECRET_KEY', '').encode("utf-8")
if not SERVER_SECRET:
    raise RuntimeError("SECRET_KEY is not set in server env")

API_KEY_LIFETIME_DAYS = 90


def validate_api_req(request, key_check=True):
    data = request.get_json(silent=True) or {}
    resp = None

    # Check latest server ver
    if data.get("ver") != SERVER_API_VER:
        resp = jsonify(valid=False, error="Old server API version", oldver=True), 464

    # Key check should happen for every request except /login and /user
    if key_check:
        # Check valid api key
        valid = validate_key(data.get('user'), data.get('key'))
        if not valid:
            resp = jsonify(valid=False, error="Invalid API key", oldkey=True), 403

    return data, resp


def hash_password(raw):
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def verify_password(raw, hashed):
    if not raw or not hashed:
        return False
    return bcrypt.checkpw(raw.encode(), hashed.encode())


def generate_api_key():
    return secrets.token_hex(32)


def hash_api_key(username, api_key):
    """
    Hash username:key for storage in database
    This one-way hash allows checking key against user all
      without storing raw keys in the database
    """

    msg = f"{username}:{api_key}".encode("utf-8")
    return hmac.new(SERVER_SECRET, msg, hashlib.sha256).hexdigest()


def get_user_auth(username):
    return db.fetch_row(
        """
        SELECT
          id,
          username,
          password_hash,
          status
        FROM users
        WHERE username = %(username)s
        """,
        {"username": username}
    )


def validate_key(username, api_key):
    """
    Validate raw api key for user against db hash
    returned bool valid is True if API key is valid
    """

    if not username:
        return False

    user_info = get_user_auth(username)
    if not user_info['password_hash']:
        return True

    if not api_key or api_key.lower() == "null" or users.user_banned_or_rejected(user_info):
        return False

    row = db.fetch_row(
        """
        SELECT
          u.id AS user_id,
          u.username,
          u.status,
          k.id AS key_id,
          k.expires_at
        FROM users u
        JOIN user_api_keys k ON k.user_id = u.id
        WHERE u.username = %(username)s
          AND k.key_hash = %(key_hash)s
        """,
        {
            "username": username,
            "key_hash": hash_api_key(username, api_key)
        }
    )

    # Did we get a row and is it expired
    if not row or row["expires_at"] <= datetime.now(timezone.utc):
        return False

    db.execute(
        """
        UPDATE user_api_keys
        SET last_used_at = now()
        WHERE id = %(key_id)s
        """,
        {"key_id": row["key_id"]}
    )

    db.execute(
        """
        UPDATE users
        SET last_seen_at = now()
        WHERE id = %(user_id)s
        """,
        {"user_id": row["user_id"]}
    )

    return True


def create_api_key(username):
    user_id = users.user_id_from_username(username)
    raw_key = generate_api_key()
    key_hash = hash_api_key(username, raw_key)

    db.execute(
        """
        INSERT INTO user_api_keys (
          user_id,
          key_hash,
          expires_at
        )
        VALUES (
          %(user_id)s,
          %(key_hash)s,
          now() + (%(lifetime_days)s * interval '1 day')
        )
        """,
        {
            "user_id": user_id,
            "key_hash": key_hash,
            "lifetime_days": API_KEY_LIFETIME_DAYS
        }
    )

    return raw_key


def cleanup_api_keys(unused_days=7, username=None):
    """
    Function to delete API keys

    Goal is to have this run routinely to clean up keys that have gone unused for a while or expired
    This is also used to delete all keys for a user for things like password reset
    """

    count = db.fetch_col(
        """
        WITH deleted AS (
          DELETE FROM user_api_keys k
          USING users u
          WHERE k.user_id = u.id
            AND (
              %(username)s::text IS NULL
              OR u.username = %(username)s::text
            )
            AND (
              k.expires_at <= now()
              OR COALESCE(k.last_used_at, k.created_at) < now() - (%(unused_days)s * interval '1 day')
            )
          RETURNING 1
        )
        SELECT count(*) AS count
        FROM deleted
        """,
        {
            "unused_days": unused_days,
            "username": username
        }
    )

    # Return number of keys cleaned up
    return 0 if count is None else count


def create_user(username, cur_user, hostname):
    """
    Function to create users
    Here and not in users module because interacts directly with users table
    Games are intended to only import public-facing users module
    """

    status = "requested"
    if username in config.SERVER_CONFIG.admins:
        status = "approved"

    return db.fetch_row(
        """
        INSERT INTO users (
          username,
          created_by,
          created_on_host,
          status,
          password_hash
        )
        VALUES (
          %(username)s,
          %(cur_user)s,
          %(hostname)s,
          %(status)s,
          NULL
        )
        RETURNING id, username
        """,
        {
            "username": username,
            "cur_user": cur_user,
            "hostname": hostname,
            "status": status
        }
    )


def set_password(username, new_password):
    db.execute(
        """
        UPDATE users
        SET password_hash = %(password_hash)s,
            updated_at = now()
        WHERE username = %(username)s
        """,
        {
            "username": username,
            "password_hash": hash_password(new_password)
        }
    )

