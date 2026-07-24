from server.api.auth import validate_api_req # api validation
from server.games.base import Game


class GameHandler:
    """
    Handler object to assist games with server operations
    Provides:
        Variables:
        game_name: game's name
        game: Game object with game config loaded
        version: game config version

        Functions:
        validate_api_req(request, admin_check=False):
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


    def validate_api_req(self, request, admin_check=False):
        return validate_api_req(request, key_check=True, admin_check=admin_check)

