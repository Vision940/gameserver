import json
import os
import sys

from collections import namedtuple

from server.funcs import json

Config = namedtuple('Config', ['host', 'port', 'admins'])


def load_config():
    try:
        filename = os.environ.get("SERVER_CONFIG", "data/config.json")
        print(f"INFO: Loading server config {filename}")
        cfg = json.load_json(filename)

        # Check each key in Config namedtuple is in json
        for key in Config._fields:
            if not cfg.get(key, None):
                print(f"ERROR: json config incorrect - missing key \"{key}\"")
                sys.exit(2)

        # Check each key in json is in Config namedtuple
        for key in cfg.keys():
            if key not in Config._fields:
                print(f"ERROR: json config incorrect - extra key \"{key}\" present")
                sys.exit(2)

        # Initialize namedtuple
        return Config(**cfg)
    except FileNotFoundError:
        print(f"ERROR: Could not find config file {filename}")
        sys.exit(2)


SERVER_CONFIG = load_config()

