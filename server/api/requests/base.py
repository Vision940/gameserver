from dataclasses import dataclass, fields
from typing import get_args

from server.funcs import user


## Classes ##
@dataclass
class ApiReq:
    """
    Basic request message class
    """

    apiKey: str
    caller: str
    curUser: str
    host: str
    msgType: str
    user: str
    version: str

    @property
    def userId(self) -> int:
        return user.user_id_from_username(self.user)


    @property
    def userProfile(self) -> dict:
        return user.get_user(self.user)


    @property
    def userIsAdmin(self) -> bool:
        return user.user_is_admin(self.user)


    @property
    def null_fields(self) -> list[str]:
        def allows_none(field_type):
            return type(None) in get_args(field_type)

        return [
            f.name for f in fields(self)
            if getattr(self, f.name) is None and not allows_none(f.type)
        ]

