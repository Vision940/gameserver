from server.api.responses.base import ApiResp, respdataclass


@respdataclass
class FileResp(ApiResp):
    filename: str

