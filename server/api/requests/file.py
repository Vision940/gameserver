from dataclasses import dataclass

from server.api.requests.base import ApiReq


@dataclass
class FileUploadReq(ApiReq):
    checksum: str
    replaceExisting: bool = True
    uuidName: bool = False

