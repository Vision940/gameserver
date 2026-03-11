import json
import sys

from collections import namedtuple

Config = namedtuple('Config', ['host', 'port'])

SERVER_CONFIG = "config.json"

def load_config(filename):
    try:
        with open(filename, 'r') as cfg_file:
            cfg = json.load(cfg_file)

        for value in ["host", "port"]:
            if not cfg.get(value, None):
                print(f"Error: json config incorrect - missing \"{value}\"")
                sys.exit(2)
        return Config(cfg.get("host"), cfg.get("port"))
    except FileNotFoundError:
        print(f"Error: could not find config file {filename}")
        sys.exit(2)
    except json.JSONDecodeError:
        print(f"Error: could not read config file {filename}")
        sys.exit(2)
