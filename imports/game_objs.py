import os

from imports import json

## Classes ##
#TODO: support grid option to json
class Game:
    def __init__(self, name = "demo"):
        cfg_file = name if name != "demo" else "default"
        game_cfg = f"static/games/{cfg_file}/{cfg_file}.json"
        if not os.path.isfile(game_cfg):
            game_cfg = "static/games/default/default.json"
        cfg = json.load_json(game_cfg)

        # Basic game info
        self.version = cfg.get("version", "")
        self.min_bash = cfg.get("min_bash", None)
        self.cmd_name = cfg.get("cmd_name", name)
        self.full_name = cfg.get("full_name", "")
        self.imports = [imp.replace("GAME", name) for imp in cfg.get("imports", [])]
        self.source_name = name

        # Support unconventional games
        self.has_main = cfg.get("has_main", True)
        self.default_cmd = cfg.get("default_cmd", "game")

        # Capability options
        self.mouse = cfg.get("mouse", False)

        # Size config options
        size = cfg.get("size", {})
        self.size_y_min = size.get("y_min", 30) # default min is 30 lines 81 columns
        self.size_xy_ratio = size.get("xy_ratio", 3)

