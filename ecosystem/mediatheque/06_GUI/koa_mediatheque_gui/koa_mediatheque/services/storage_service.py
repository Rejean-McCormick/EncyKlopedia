# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/storage_service.py

"""
Local storage service for Médiathèque kOA.

Supported modes:
- reference_only: keep the original path, do not copy the file.
- copy_to_storage: copy the file into a canonical storage filearea.
- copy_and_rename: copy the file using <version_uuid><extension>.

The app must preserve version_uuid and locally calculated file facts.
ChatGPT or XLSX must never be trusted for technical file facts.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from koa_mediatheque.errors import (
    ERR_FILE_NOT_FOUND,
    WARN_STORAGE_COPY_SKIPPED,
)
from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.services.file_facts import (
    get_file_facts,
    is_external_reference_path,
)

try:
    from koa_mediatheque.constants import STORAGE_FILEAREAS
except Exception:  # pragma: no cover - defensive fallback for partial builds
    STORAGE_FILEAREAS = [
        "media_original",
        "media_preview",
        "media_thumbnail",
        "media_derivative",
        "media_caption",
        "media_transcript",
        "media_attachment",
        "content_review_files",
        "external_work_reference_files",
        "cultural_protocol_files",
    ]


_ALLOWED_COPY_MODES = {
    "reference_only",
    "copy_to_storage",
    "copy_and_rename",
}

_CANONICAL_FILEAREAS = set(STORAGE_FILEAREAS)

_RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def resolve_storage_dir(
    storage_root: str | Path,
    filearea: str = "media_original",
) -> Path:
    """
    Resolve and create a canonical storage filearea directory.

    Raises:
        ValueError: if storage_root is empty, or filearea is not canonical/safe.
    """
    root_text = str(storage_root).strip()

    if not root_text:
        raise ValueError("storage_root cannot be empty")

    safe_filearea = _validate_filearea(filearea)
    storage_dir = Path(root_text).expanduser() / safe_filearea
    storage_dir.mkdir(parents=True, exist_ok=True)

    return storage_dir


def build_canonical_storage_filename(
    version_uuid: str,
    original_filename: str,
) -> str:
    """
    Build the canonical stored filename.

    Format:
        <version_uuid><lowercase_original_extension>

    Examples:
        2222...2222.txt
        2222...2222.pdf
        2222...2222
    """
    version = str(version_uuid).strip()

    if not version:
        raise ValueError("version_uuid cannot be empty")

    suffix = Path(str(original_filename).strip()).suffix.lower()
    return f"{version}{suffix}"


def copy_into_storage(
    source_path: str | Path,
    storage_root: str | Path,
    *,
    filearea: str = "media_original",
    version_uuid: str | None = None,
    mode: str = "copy_to_storage",
) -> OperationResult:
    """
    Copy a local file into controlled storage, or keep it by reference.

    Returns:
        OperationResult.path:
            - original path for reference_only or external reference
            - copied storage path for copy_to_storage/copy_and_rename
    """
    operation = "copy_into_storage"
    source_text = str(source_path).strip()
    selected_mode = str(mode).strip()

    if selected_mode not in _ALLOWED_COPY_MODES:
        return _error_result(
            result="invalid_mode",
            path=source_text,
            code="ERR_INVALID_COPY_MODE",
            message=f"Invalid copy mode: {selected_mode}",
            field="mode",
            details={"allowed_modes": sorted(_ALLOWED_COPY_MODES)},
        )

    if not source_text:
        return _error_result(
            result="missing_source_path",
            path="",
            code=ERR_FILE_NOT_FOUND,
            message="source_path cannot be empty",
            field="source_path",
        )

    if selected_mode == "reference_only":
        return _reference_result(
            result="reference_only",
            path=source_text,
            message="Storage copy skipped because mode is reference_only.",
            data={
                "source_path": source_text,
                "storage_path": source_text,
                "filearea": filearea,
                "mode": selected_mode,
            },
        )

    if is_external_reference_path(source_text):
        return _reference_result(
            result="external_reference_only",
            path=source_text,
            message="Storage copy skipped because source_path is an external reference.",
            data={
                "source_path": source_text,
                "storage_path": source_text,
                "filearea": filearea,
                "mode": selected_mode,
            },
        )

    source = Path(source_text).expanduser()

    if not source.exists():
        return _error_result(
            result="file_not_found",
            path=str(source),
            code=ERR_FILE_NOT_FOUND,
            message=f"File not found: {source}",
            field="source_path",
        )

    if not source.is_file():
        return _error_result(
            result="source_is_directory",
            path=str(source),
            code=ERR_FILE_NOT_FOUND,
            message=f"Expected a file, got directory: {source}",
            field="source_path",
        )

    try:
        target_dir = resolve_storage_dir(storage_root, filearea=filearea)
    except ValueError as exc:
        return _error_result(
            result="invalid_filearea",
            path=str(source),
            code="ERR_INVALID_FILEAREA",
            message=str(exc),
            field="filearea",
            details={"allowed_fileareas": sorted(_CANONICAL_FILEAREAS)},
        )

    effective_version_uuid = str(version_uuid or uuid.uuid4()).strip()

    if not effective_version_uuid:
        effective_version_uuid = str(uuid.uuid4())

    target_name = build_canonical_storage_filename(
        effective_version_uuid,
        source.name,
    )

    target_path = target_dir / target_name

    if selected_mode == "copy_to_storage":
        target_path = _resolve_non_colliding_path(target_path)

    try:
        shutil.copy2(source, target_path)
        facts = _file_facts_to_dict(get_file_facts(source))
    except Exception as exc:
        return _error_result(
            result="copy_failed",
            path=str(source),
            code="ERR_STORAGE_COPY_FAILED",
            message=str(exc),
            field="source_path",
        )

    data = {
        "source_path": str(source),
        "storage_path": str(target_path),
        "filearea": filearea,
        "mode": selected_mode,
        "filename": facts.get("filename", source.name),
        "extension": facts.get("extension", source.suffix.lower()),
        "mimetype": facts.get("mimetype"),
        "filesize": facts.get("filesize"),
        "sha256": facts.get("sha256"),
    }

    return OperationResult(
        success=True,
        operation=operation,
        result="copied",
        entity_type="file",
        entity_uuid=None,
        media_uuid=None,
        version_uuid=effective_version_uuid,
        path=str(target_path),
        data=data,
        warnings=[],
        errors=[],
    )


def _validate_filearea(filearea: str) -> str:
    value = str(filearea).strip()

    if not value:
        raise ValueError("filearea cannot be empty")

    candidate = Path(value)

    if candidate.is_absolute():
        raise ValueError(f"filearea must be relative: {filearea}")

    if ".." in candidate.parts:
        raise ValueError(f"filearea cannot contain '..': {filearea}")

    if len(candidate.parts) != 1:
        raise ValueError(f"filearea must be a single directory name: {filearea}")

    if value not in _CANONICAL_FILEAREAS:
        raise ValueError(f"unknown canonical filearea: {filearea}")

    return value


def _safe_filename(filename: str) -> str:
    """
    Safe helper kept for future non-canonical display use.

    Storage filenames are canonicalized by build_canonical_storage_filename().
    """
    name = Path(str(filename).strip()).name

    if not name:
        return "file"

    stem = Path(name).stem
    suffix = Path(name).suffix.lower()

    safe_stem = "".join(
        character if character.isalnum() or character in "._-" else "_"
        for character in stem
    ).strip("._-")

    while "__" in safe_stem:
        safe_stem = safe_stem.replace("__", "_")

    if not safe_stem:
        safe_stem = "file"

    if safe_stem.upper() in _RESERVED_WINDOWS_NAMES:
        safe_stem = f"{safe_stem}_file"

    safe_suffix = "".join(
        character
        for character in suffix
        if character.isalnum() or character == "."
    )

    return f"{safe_stem}{safe_suffix}"


def _resolve_non_colliding_path(target_path: Path) -> Path:
    if not target_path.exists():
        return target_path

    parent = target_path.parent
    stem = target_path.stem
    suffix = target_path.suffix
    counter = 2

    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"

        if not candidate.exists():
            return candidate

        counter += 1


def _file_facts_to_dict(file_facts: Any) -> dict[str, Any]:
    if isinstance(file_facts, dict):
        return file_facts

    return {
        "original_path": getattr(file_facts, "original_path", None),
        "filename": getattr(file_facts, "filename", None),
        "extension": getattr(file_facts, "extension", None),
        "mimetype": getattr(file_facts, "mimetype", None),
        "filesize": getattr(file_facts, "filesize", None),
        "sha256": getattr(file_facts, "sha256", None),
    }


def _reference_result(
    *,
    result: str,
    path: str,
    message: str,
    data: dict[str, Any],
) -> OperationResult:
    return OperationResult(
        success=True,
        operation="copy_into_storage",
        result=result,
        entity_type="file",
        entity_uuid=None,
        media_uuid=None,
        version_uuid=None,
        path=path,
        data=data,
        warnings=[
            KoaMessage(
                code=WARN_STORAGE_COPY_SKIPPED,
                severity="warning",
                message=message,
                field="mode",
            )
        ],
        errors=[],
    )


def _error_result(
    *,
    result: str,
    path: str,
    code: str,
    message: str,
    field: str,
    details: dict[str, Any] | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation="copy_into_storage",
        result=result,
        entity_type="file",
        entity_uuid=None,
        media_uuid=None,
        version_uuid=None,
        path=path,
        data={},
        warnings=[],
        errors=[
            KoaMessage(
                code=code,
                severity="error",
                message=message,
                field=field,
                details=details or {},
            )
        ],
    )