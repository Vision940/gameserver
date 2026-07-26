from server.api.auth import validate_api_req # api validation
from server.games.base import Game


_GAME_CONTEXT={}


class GameContext:
    """
    Context object to assist games with server operations
    Provides:
        Variables:
        game_name: game's name
        config: Game object with game config loaded
        module: game's main imported module

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
        self.config = Game(game_name)
        self.module = module_name
        _GAME_CONTEXT[game_name] = self


    def validate_api_req(self, request, admin_check=False):
        return validate_api_req(request, key_check=True, admin_check=admin_check)


class GameContextProxy:
    """
    Proxy class to GameContext that allows modules of a game to access the
        game's context without initializing it themselves
    """

    def __init__(self, module_name):
        self._module_name = module_name

    @property
    def _context(self):
        return get_game_context(self._module_name)

    def __getattr__(self, name):
        return getattr(self._context, name)


def get_game_context(module_name):
    parts = module_name.split(".")

    try:
        idx = parts.index("games")
        game_name = parts[idx + 1]
    except (ValueError, IndexError) as e:
        raise RuntimeError(f"Could not get game context from module: {module_name}") from e

    return _GAME_CONTEXT[game_name] if game_name in _GAME_CONTEXT else None

