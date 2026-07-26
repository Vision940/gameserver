from __future__ import annotations

from flask import request

from server.api.auth import validate_api_req
from server.api.handlers.registry import handles
from server.api.responses.base import ErrorResp
from server.api.requests.file import (
    FileUploadReq
)
from server.api.responses.file import (
    FileResp
)

from server.funcs import file as file_funcs


@handles(FileUploadReq)
def upload(req: FileUploadReq) -> ApiResp:
    """
    Upload a file to the server
    Files get stored to data/uploads in server runtime env
    """

    resp = validate_api_req(req)
    if resp: return resp

    file = request.files.get("file")
    result = file_funcs.save_upload(file, req.checksum, replace=req.replaceExisting, uuid_name=req.uuidName)

    if isinstance(result, ErrorResp): return result
    return FileResp(filename=result.name)

