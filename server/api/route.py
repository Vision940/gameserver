from __future__ import annotations

import sys

from importlib import import_module

from flask import (
    Blueprint,
    request
)

from server.api.handlers.registry import handle
from server.api.requests.factory import RequestFactory
from server.api.responses.base import ErrorResp


class ApiRoute(Blueprint):
    def __init__(self, route, path="server.api"):
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

    def _post(self):
        factory = RequestFactory(request, self.route)

        req = factory.build()
        response: ApiResp = None
        if req is None:
            response = ErrorResp(error=factory.error, errType="badreq")
        else:
            response = handle(req)

        return response.to_flask()

