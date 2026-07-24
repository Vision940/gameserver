from flask import (
    Blueprint,
    request
)

from server.api.route import ApiRoute


class Api(Blueprint):
    def __init__(self, *routes, name="api", path="server.api"):
        super().__init__(name, __name__, url_prefix=f"/{name}")

        self.app = None
        self.registered_routes = {}
        self.name = name
        self.path = path

        for route in routes:
            self.add_route(route)


    def add_route(self, route):
        """
        Add an API route to the instance
        """

        if route in self.registered_routes:
            raise ValueError(f"Route '{route}' already registered")

        # Register blueprint to Api
        bp = ApiRoute(route, self.path)
        self.register_blueprint(bp)
        self.registered_routes[route] = bp


    def register_api(self, app):
        """
        Register api to app
        Equivalent to calling app.register_blueprint(<Api object>)
        """

        self.app = app
        app.register_blueprint(self)


