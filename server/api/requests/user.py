from dataclasses import dataclass

from server.api.requests.base import ApiReq


@dataclass
class UserUserReq(ApiReq):
    register: bool = False


@dataclass
class UserLoginReq(ApiReq):
    password: str


@dataclass
class UserPasswdReq(ApiReq):
    password: str


class UserCancelReq(ApiReq): ...
class UserListReq(ApiReq): ...
class UserWhoamiReq(ApiReq): ...

