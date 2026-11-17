# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/file_facts.py

"""
Local file fact utilities for Médiathèque kOA.

Rules:
- The app recalculates technical facts locally.
- ChatGPT and XLSX must never be trusted for sha256, filesize, mimetype,
  filename, extension, original_path, storage_path, or any filesystem fact.
"""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlparse

from koa_mediatheque.models import FileFacts


_HASH_CHUNK_SIZE = 1024 * 1024

_EXTERNAL_REFERENCE_SCHEMES = {
    "http",
    "https",
    "ftp",
    "ftps",
    "s3",
    "gs",
    "doi",
    "urn",
    "external",
}


def calculate_sha256(file_path: str | Path) -> str:
    """
    Calculate the lowercase hexadecimal SHA-256 hash for a local file.

    Raises:
        ValueError: if file_path is empty.
        FileNotFoundError: if the path does not exist.
        IsADirectoryError: if the path is a directory.
    """
    path = _require_local_file(file_path)

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_HASH_CHUNK_SIZE), b""):
            digest.update(chunk)

    return digest.hexdigest()


def detect_mimetype(file_path: str | Path) -> str | None:
    """
    Detect MIME type from a filename, local path, or external-reference path.

    This is extension-based and deterministic. It does not inspect binary
    content.
    """
    path_text = str(file_path).strip()

    if not path_text:
        return None

    mimetype, _encoding = mimetypes.guess_type(path_text)
    return mimetype


def get_file_facts(file_path: str | Path) -> FileFacts:
    """
    Return file facts computed locally.

    Local files:
        filename, extension, mimetype, filesize, sha256.

    External references:
        best-effort filename, extension, mimetype.
        filesize and sha256 remain None.
    """
    path_text = str(file_path).strip()

    if not path_text:
        raise ValueError("file_path cannot be empty")

    if is_external_reference_path(path_text):
        filename = _external_reference_filename(path_text)

        return FileFacts(
            original_path=path_text,
            filename=filename,
            extension=_extension_from_filename(filename),
            mimetype=detect_mimetype(path_text),
            filesize=None,
            sha256=None,
        )

    path = _require_local_file(path_text)
    stat = path.stat()

    return FileFacts(
        original_path=str(path),
        filename=path.name,
        extension=_extension_from_filename(path.name),
        mimetype=detect_mimetype(path),
        filesize=stat.st_size,
        sha256=calculate_sha256(path),
    )


def is_external_reference_path(path_value: str) -> bool:
    """
    Return True when path_value is an external reference, not a local path.

    Windows drive paths such as C:\\folder\\file.pdf are treated as local paths.
    """
    value = str(path_value).strip()

    if not value:
        return False

    if _looks_like_windows_drive_path(value):
        return False

    parsed = urlparse(value)

    if not parsed.scheme:
        return False

    return parsed.scheme.lower() in _EXTERNAL_REFERENCE_SCHEMES


def _require_local_file(file_path: str | Path) -> Path:
    path_text = str(file_path).strip()

    if not path_text:
        raise ValueError("file_path cannot be empty")

    path = Path(path_text).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.is_dir():
        raise IsADirectoryError(f"Expected a file, got directory: {path}")

    return path


def _looks_like_windows_drive_path(value: str) -> bool:
    return (
        len(value) >= 3
        and value[1] == ":"
        and value[0].isalpha()
        and value[2] in {"\\", "/"}
    )


def _extension_from_filename(filename: str) -> str:
    """
    Return lowercase extension with leading dot.

    Examples:
        sample.txt -> .txt
        Document.PDF -> .pdf
        README -> ""
    """
    return Path(filename).suffix.lower()


def _external_reference_filename(path_value: str) -> str:
    parsed = urlparse(path_value)

    if parsed.path:
        candidate = Path(unquote(parsed.path)).name
        if candidate:
            return candidate

    if parsed.netloc:
        return parsed.netloc

    if parsed.scheme:
        return f"{parsed.scheme}_external_reference"

    candidate = Path(path_value.strip()).name
    return candidate or "external_reference"