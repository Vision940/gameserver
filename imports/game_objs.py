from imports import json

## Classes ##
#TODO: support grid option to json
class Game:
    def __init__(self, json_config):
        cfg = json.load_json(json_config)
        self.version = cfg.get("version", "")
        self.min_bash = cfg.get("min_bash", None)
        self.cmd_name = cfg.get("cmd_name", "")
        self.full_name = cfg.get("full_name", "")
        self.imports = cfg.get("imports", [])
        self.mouse = cfg.get("mouse", False)

