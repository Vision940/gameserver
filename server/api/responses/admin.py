from server.api.responses.base import (
    ApiResp,
    ApiTextResp,
    respdataclass
)


@respdataclass
class AdminUpdateResp(ApiResp):
    updated: dict = None


@respdataclass
class AdminRequestsResp(ApiResp):
    requests: list = None


@respdataclass
class AdminInfoResp(ApiResp):
    admins: list


class AdminQueryResp(ApiTextResp): ...

