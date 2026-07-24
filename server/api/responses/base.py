from dataclasses import asdict, dataclass, field
from typing import dataclass_transform

from flask import jsonify, Response

from server import __version__ as SERVER_VER


## Functions ##
@dataclass_transform(kw_only_default=True)
def respdataclass(cls, **kwargs):
    options = {
        "kw_only": True,
        **kwargs
    }

    return dataclass(**options)(cls)


## Classes ##
@respdataclass
class ApiResp:
    """
    Basic response message class
    """

    origin: str = "gameserver"
    version: str = SERVER_VER
    valid: bool = True
    code: int = 200

    def to_flask(self):
        return jsonify(asdict(self)), self.code


@respdataclass
class ApiTextResp(ApiResp):
    """
    Basic message class for returning flask Response with mimetype="text/plain"
    """

    text: str

    def to_flask(self):
        return Response(self.text, mimetype="text/plain")


@respdataclass
class ErrorResp(ApiResp):
    """
    Basic error response message class
    """

    errType: str
    error: str
    valid: bool = field(init=False, default=False)
    code: int = 400

