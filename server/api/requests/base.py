from dataclasses import dataclass, fields

from server.funcs import users


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
        return users.user_id_from_username(self.user)


    @property
    def userProfile(self) -> dict:
        return users.get_user(self.user)


    @property
    def userIsAdmin(self) -> bool:
        return users.user_is_admin(self.user)


    @property
    def null_fields(self) -> list[str]:
        return [
            f.name for f in fields(self)
            if getattr(self, f.name) is None
        ]

