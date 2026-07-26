from __future__ import annotations

import os

from uuid import uuid4
from pathlib import Path

import xxhash

from werkzeug.utils import secure_filename

from server.api.responses.base import ErrorResp


## Functions ##
def save_upload(file: FileStorage, checksum, replace=True, uuid_name=False) -> Path | ErrorResp:
    """
    Save uploaded file to server at data/uploads
    Returns ErrorResp or Path object of saved file
    """

    if not file or file.filename == "":
        return ErrorResp(error="No file uploaded", errType="noupload")

    filename = secure_filename(file.filename)
    if not filename:
        return ErrorResp(error="Invalid filename to upload", errType="invalidfilename", code=422)

    if not file.stream.read(1):
        return ErrorResp(error="Uploaded file is empty", errType="emptyupload", code=422)
    file.stream.seek(0)

    if uuid_name:
        filename = f"{uuid4().hex}.upload"

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / f".{filename}.{uuid4().hex}.tmp"
    upload_path = upload_dir / filename

    try:
        file.save(temp_path)

        if not check_hash(temp_path, checksum):
            return ErrorResp(error=f"File upload checksum mismatch {checksum} {hash_file(temp_path)}", errType="checksummismatch")

        if replace:
            os.replace(temp_path, upload_path)
        else:
            try:
                os.link(temp_path, upload_path)
            except FileExistsError:
                return ErrorResp(error=f"File {filename} exists on server", errType="fileexists")

        return upload_path
    finally:
        temp_path.unlink(missing_ok=True)


def check_hash(filepath, checksum):
    """
    Insecure hash checker for validating file uploads
    Compares provided checksum to provided file using hash_file
    """

    try:
        filehash = hash_file(filepath)
        return filehash == checksum.lower()
    except FileNotFoundError:
        return False


def hash_file(filepath):
    """
    Hash file with emphasis on speed
    Uses 32 bit to not limit potential 32 bit clients
    """

    hasher = xxhash.xxh32()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def remove_file(filepath: str | Path):
    Path(filepath).unlink(missing_ok=True)

