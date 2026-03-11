import secrets
import time

import bcrypt

from flask import jsonify

from imports import __version__ as SERVER_API_VER
from imports import json # cfg helper functions

API_KEY_LIFETIME = 3600 * 24 * 90 # 90 days

def validate_api_req(request):
    data = request.get_json()
    resp = None

    if data.get("ver") != SERVER_API_VER:
        resp = jsonify(valid=False, error="Old server api version", oldver=True), 464
    return data, resp

def hash_password(raw):
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()

def verify_password(raw, hashed):
    return bcrypt.checkpw(raw.encode(), hashed.encode())

def generate_api_key():
    key = secrets.token_hex(32)
    expires = int(time.time()) + API_KEY_LIFETIME
    return key, expires

def validate_key(api_key):
    users = json.load_users()
    now = int(time.time())

    for username, u in users.items():
        if u.get("api_key") == api_key:
            if u.get("api_key_expires", 0) < now:
                return False, None  # Expired
            return True, username
    return False, None

