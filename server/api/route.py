from __future__ import annotations

import sys

from importlib import import_module

from flask import (
    Blueprint,
    request
)

from server import __version__ as SERVER_VER

from server.api.handlers.registry import handle
from server.api.requests.factory import RequestFactory
from server.api.responses.base import ErrorResp


class ApiRoute(Blueprint):
    def __init__(self, route, path="server.api", origin="gameserver",
                 version=SERVER_VER):
        super().__init__(route, __name__, url_prefix=f"/{route}")
        try:
            import_module(f"{path}.requests.{route}")
            import_module(f"{path}.handlers.{route}")
            import_module(f"{path}.responses.{route}")
        except ModuleNotFoundError as e:
            print(f"FATAL: Could not import {path}.(requests|handlers|responses).{route}: {e}")
            sys.exit(1)
        self.add_url_rule("/", view_func=self._post, methods=["POST"])
        self.route = route
        self.path = path
        self.origin = origin
        self.version = version

    def _post(self):
        factory = RequestFactory(request, route=self.route, path=self.path)

        req = factory.build()
        response: ApiResp = None

        if req is None:
            response = ErrorResp(error=factory.error, errType="badreq")
        else:
            response = handle(req)

        response.origin = self.origin
        response.version = self.version

        return response.to_flask()

