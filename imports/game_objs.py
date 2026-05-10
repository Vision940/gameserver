import os

from imports.auth import validate_api_req # api validation
from imports import json # json file handling


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
        self.min_bash = cfg.get("min_bash", "4.2")
        self.cmd_name = cfg.get("cmd_name", name)
        self.full_name = cfg.get("full_name", "")
        self.imports = [imp.replace("GAME", name) for imp in cfg.get("imports", [])]
        self.source_name = name
        self.has_migrations = cfg.get("db_migrations", False)

        # Support unconventional games
        self.has_main = cfg.get("has_main", True)
        self.default_cmd = cfg.get("default_cmd", "game")

        # Capability options
        self.mouse = cfg.get("mouse", False)

        # Size config options
        size = cfg.get("size", {})
        self.size_y_min = size.get("y_min", 30) # default min is 30 lines 81 columns
        self.size_xy_ratio = size.get("xy_ratio", 3)


class GameHandler:
    """
    Handler object to assist games with server operations
    Provides:
        Variables:
        game_name: game's name
        game: Game object with game config loaded
        version: game config version

        Functions:
        validate_api_req():
            Validates against game version
            returns (data, resp) where resp is None unless error
    """

    def __init__(self, module_name):
        """
        Gets game name from module_name and initializes Game obj with name
        This way games can interact with their configs / the server without worrying about server handling
        """

        parts = module_name.split(".")
        try:
            idx = parts.index("games")
            game_name = parts[idx + 1]
        except (ValueError, IndexError) as e:
            raise RuntimeError(f"Could not get game name from module: {module_name}") from e

        self.game_name = game_name
        self.game = Game(game_name)

    @property
    def version(self):
        return self.game.version

    def validate_api_req(self, request, admin_check=False):
        return validate_api_req(request, cur_ver=self.version, key_check=True, admin_check=admin_check)

