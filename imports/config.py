import json
import os
import sys

from collections import namedtuple

from imports import json

Config = namedtuple('Config', ['host', 'port', 'admins'])


def load_config():
    try:
        filename = os.environ.get("SERVER_CONFIG", "data/config.json")
        print(f"INFO: Loading server config {filename}")
        cfg = json.load_json(filename)

        for value in ["host", "port", "admins"]:
            if not cfg.get(value, None):
                print(f"ERROR: json config incorrect - missing \"{value}\"")
                sys.exit(2)
        return Config(cfg.get("host"), cfg.get("port"), cfg.get("admins"))
    except FileNotFoundError:
        print(f"ERROR: Could not find config file {filename}")
        sys.exit(2)


SERVER_CONFIG = load_config()

