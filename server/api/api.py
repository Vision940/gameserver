from flask import Blueprint

from server import __version__ as SERVER_VER

from server.api.route import ApiRoute


class Api(Blueprint):
    def __init__(self, *routes, name=None, route="/api", path="server.api",
                 origin="gameserver", version=SERVER_VER):
        if name is None:
            raise ValueError("Argument name to class Api cannot be None")

        super().__init__(name, __name__, url_prefix=route)

        self.app = None
        self.registered_subroutes = {}
        self.name = name
        self.route = route
        self.path = path
        self.origin = origin
        self.version = version

        for subroute in routes:
            self.add_route(subroute)


    def add_route(self, route):
        """
        Add an API route to the instance
        """

        if route in self.registered_subroutes:
            raise ValueError(f"Route '{route}' already registered")

        # Register blueprint to Api
        bp = ApiRoute(route, path=self.path, origin=self.origin,
                      version=self.version)
        self.register_blueprint(bp)
        self.registered_subroutes[route] = bp


    def register_api(self, app):
        """
        Register api to app
        Equivalent to calling app.register_blueprint(<Api object>)
        """

        self.app = app
        app.register_blueprint(self)


