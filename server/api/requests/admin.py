from dataclasses import dataclass

from server.api.requests.base import ApiReq


@dataclass
class AdminApproveReq(ApiReq):
    id: int


@dataclass
class AdminRejectReq(ApiReq):
    id: int
    reason: str


@dataclass
class AdminBanReq(ApiReq):
    id: int
    reason: str


class AdminQueryReq(ApiReq): ...
class AdminRequestsReq(ApiReq): ...
class AdminInfoReq(ApiReq): ...

