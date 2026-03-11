import json
import os
import shutil
import sys

from threading import Lock

USERS_JSON = "data/users.json"

def check_json_exists(filename):
    """
    Check that json data file exists at filename and copies template json if it doesn't
    """

    if not os.path.exists(filename):
        if not os.path.exists(f"{filename}-template"):
            return False

        try:
            shutil.copyfile(f"{filename}-template", filename)
            os.chmod(filename, 0o600)
        except:
            return False

    return True

file_lock = Lock()

def load_json(path):
    try:
        with file_lock:
            if not os.path.exists(path):
                return {}
            with open(path, "r") as f:
                return json.load(f)
    except json.decoder.JSONDecodeError:
        return {}

def save_json(path, data):
    with file_lock:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

def load_users():
    return load_json(USERS_JSON)

def save_users(users):
    save_json(USERS_JSON, users)

# Init users.json on startup
if not check_json_exists(USERS_JSON):
    print("FATAL ERROR: Could not init users.json")
    sys.exit(1)

