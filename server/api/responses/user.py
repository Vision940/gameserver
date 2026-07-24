from server.api.responses.base import ApiResp, respdataclass


@respdataclass
class UserResp(ApiResp):
    action: str = None
    user: str = None
    apiKey: str = None


@respdataclass
class UserCancelResp(UserResp):
    userId: int = None


@respdataclass
class UserListResp(UserResp):
    users: list
    admin: bool

@respdataclass
class UserWhoamiResp(UserResp):
    userProfile: dict

