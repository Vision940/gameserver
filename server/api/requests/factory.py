from dataclasses import MISSING, fields
from importlib import import_module

from flask import request


class RequestFactory:
    def __init__(self, req: request, route=None, path="server.api"):
        self.data = req.get_json(silent=True) or {}
        self.route = route or req.path.rstrip("/").split("/")[-1]
        self.msg_type = self.data.get("msgType")
        self.error = None
        self.path = path


    def build(self):
        """
        Parse the JSON request into the appropriate ApiReq object.
        Returns None on failure and populates self.error.
        """

        cls = self._resolve_class()
        if cls is None: return None
        field_defs = fields(cls)

        # Filter out extra fields
        field_names = {f.name for f in field_defs}
        req_kwargs = {k: v for k, v in self.data.items() if k in field_names}

        # Check for missing fields
        missing = [
            f.name
            for f in field_defs
            if (
                f.init
                and f.default is MISSING
                and f.default_factory is MISSING
                and f.name not in req_kwargs
            )
        ]
        if missing:
            self.error = f"Malformed request: missing fields: {', '.join(missing)}"
            return None

        # Instantiate and check for null fields
        req = cls(**req_kwargs)
        if req.null_fields:
            self.error = f"Malformed request: null fields: {', '.join(req.null_fields)}"
            return None

        return req


    def _resolve_class(self):
        """
        Resolve class using naming convention RouteTypeReq
        """

        # Ensure type given for request
        if self.msg_type is None:
            self.error = "No msgType provided to request"
            return None

        # Check for class name in route's requests module
        module = import_module(f"{self.path}.requests.{self.route}")
        class_name = "".join(
            part[0].upper() + part[1:] if len(part) > 1 else part.upper()
            for part in [self.route, self.msg_type, "Req"]
        )
        cls = getattr(module, class_name, None)

        # Ensure class found
        if cls is None:
            self.error = f"Unknown message type '{self.msg_type}' for request route '/{self.route}'"
            return None

        return cls

