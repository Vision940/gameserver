import json
import sys

from collections import namedtuple

from imports import json

Config = namedtuple('Config', ['host', 'port'])

SERVER_CONFIG = "config.json"

def load_config(filename):
    try:
        cfg = json.load_json(filename)

        for value in ["host", "port"]:
            if not cfg.get(value, None):
                print(f"Error: json config incorrect - missing \"{value}\"")
                sys.exit(2)
        return Config(cfg.get("host"), cfg.get("port"))
    except FileNotFoundError:
        print(f"Error: could not find config file {filename}")
        sys.exit(2)
