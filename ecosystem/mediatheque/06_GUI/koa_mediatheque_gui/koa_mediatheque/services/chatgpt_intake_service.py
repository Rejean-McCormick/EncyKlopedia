# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/chatgpt_intake_service.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from koa_mediatheque.errors import ERR_FILE_NOT_FOUND
from koa_mediatheque.models import FileFacts, KoaMessage, OperationResult, ValidationResult
from koa_mediatheque.services.file_facts import get_file_facts
from koa_mediatheque.services.json_validation_service import validate_chatgpt_json
from koa_mediatheque.services.row_mapping_service import metadata_to_library_row
from koa_mediatheque.services.storage_service import copy_into_storage

try:
    from koa_mediatheque.services.duplicate_service import build_duplicate_warnings
except ImportError:

    def build_duplicate_warnings(connection, file_facts: FileFacts) -> list[KoaMessage]:
        return []


try:
    from koa_mediatheque.repositories.library_rows_repository import insert_library_row
except ImportError:

    def insert_library_row(connection, row_data: dict[str, Any]) -> OperationResult:
        raise NotImplementedError("insert_library_row() is not available.")


try:
    from koa_mediatheque.repositories.chatgpt_intake_log_repository import (
        insert_chatgpt_intake_log,
    )
except ImportError:

    def insert_chatgpt_intake_log(connection, log_data: dict[str, Any]) -> OperationResult:
        return OperationResult(
            success=True,
            operation="insert_chatgpt_intake_log",
            result="skipped_repository_unavailable",
            data={"log_data": log_data},
            warnings=[],
            errors=[],
        )


try:
    from koa_mediatheque.services.audit_service import write_audit_log
except ImportError:

    def write_audit_log(
        connection,
        *,
        action: str,
        entity_type: str,
        entity_uuid: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        actor: str = "local_user",
        note: str = "",
    ) -> OperationResult:
        return OperationResult(
            success=True,
            operation="write_audit_log",
            result="skipped_service_unavailable",
            entity_type=entity_type,
            entity_uuid=entity_uuid,
            data={
                "action": action,
                "before": before,
                "after": after,
                "actor": actor,
                "note": note,
            },
            warnings=[],
            errors=[],
        )


TECHNICAL_FIELDS_FROM_AI = {
    "sha256",
    "filesize",
    "mimetype",
    "filename",
    "extension",
    "original_path",
    "storage_path",
    "path",
    "file_path",
    "absolute_path",
    "local_path",
}

DEFAULT_FILEAREA = "media_original"


def preview_chatgpt_intake(
    connection,
    *,
    file_path: str | Path,
    raw_response: str,
    storage_root: str | Path,
    import_batch: str,
    copy_mode: str = "copy_to_storage",
    allow_human_verified_override: bool = False,
) -> OperationResult:
    """
    Validate one ChatGPT JSON response and build a preview library_rows payload.

    Contract:
    - no SQLite insert
    - no chatgpt_intake_log insert
    - no audit_log insert
    - no file copy
    - all file facts are calculated locally
    - technical fields proposed by ChatGPT are ignored
    """
    operation = "preview_chatgpt_intake"
    source_path = _normalize_path(file_path)

    if not source_path.is_file():
        return _file_not_found_result(operation, source_path)

    validation = _validate_response(
        raw_response,
        allow_human_verified_override=allow_human_verified_override,
    )

    if not validation.is_valid:
        return OperationResult(
            success=False,
            operation=operation,
            result="validation_failed",
            entity_type="chatgpt_intake",
            path=str(source_path),
            data={"validation": _validation_to_dict(validation)},
            warnings=validation.warnings,
            errors=validation.errors,
        )

    file_facts_result = _get_local_file_facts(operation, source_path, validation)
    if file_facts_result.errors:
        return file_facts_result.result

    file_facts = file_facts_result.file_facts
    metadata = _clean_metadata(validation.normalized_data)

    media_uuid = _coerce_uuid(metadata.get("media_uuid"))
    version_uuid = str(uuid4())
    filearea = _coerce_filearea(metadata.get("filearea"))

    storage_path_preview = _build_storage_path_preview(
        storage_root=storage_root,
        filearea=filearea,
        version_uuid=version_uuid,
        filename=file_facts.filename,
        copy_mode=copy_mode,
        source_path=source_path,
    )

    row_data = metadata_to_library_row(
        metadata,
        file_facts,
        media_uuid=media_uuid,
        version_uuid=version_uuid,
        storage_path=storage_path_preview,
        filearea=filearea,
        import_batch=import_batch,
    )

    row_data = _enforce_local_file_facts(
        row_data=row_data,
        file_facts=file_facts,
        source_path=source_path,
        storage_path=storage_path_preview,
        filearea=filearea,
    )

    duplicate_warnings = _safe_duplicate_warnings(connection, file_facts)

    return OperationResult(
        success=True,
        operation=operation,
        result="preview",
        entity_type="library_row",
        entity_uuid=version_uuid,
        media_uuid=row_data.get("media_uuid"),
        version_uuid=row_data.get("version_uuid"),
        path=str(source_path),
        data={
            "row": row_data,
            "preview_row": row_data,
            "library_row": row_data,
            "file_facts": _file_facts_to_dict(file_facts),
            "validation": _validation_to_dict(validation),
            "copy_mode": copy_mode,
            "storage_root": str(Path(storage_root).expanduser()),
            "import_batch": import_batch,
        },
        warnings=[*validation.warnings, *duplicate_warnings],
        errors=[],
    )


def integrate_chatgpt_intake(
    connection,
    *,
    file_path: str | Path,
    raw_response: str,
    storage_root: str | Path,
    import_batch: str,
    copy_mode: str = "copy_to_storage",
    actor: str = "local_user",
    allow_human_verified_override: bool = False,
) -> OperationResult:
    """
    Validate one ChatGPT JSON response, calculate local facts, copy/reference
    the file, insert one library_rows record, and write intake/audit logs.
    """
    operation = "integrate_chatgpt_intake"
    source_path = _normalize_path(file_path)

    if not source_path.is_file():
        return _file_not_found_result(operation, source_path)

    validation = _validate_response(
        raw_response,
        allow_human_verified_override=allow_human_verified_override,
    )

    if not validation.is_valid:
        _safe_insert_chatgpt_log(
            connection,
            _build_chatgpt_log_data(
                file_path=source_path,
                raw_response=raw_response,
                validation=validation,
                version_uuid=None,
                validation_status=_validation_status(validation),
            ),
        )

        return OperationResult(
            success=False,
            operation=operation,
            result="validation_failed",
            entity_type="chatgpt_intake",
            path=str(source_path),
            data={"validation": _validation_to_dict(validation)},
            warnings=validation.warnings,
            errors=validation.errors,
        )

    file_facts_result = _get_local_file_facts(operation, source_path, validation)
    if file_facts_result.errors:
        _safe_insert_chatgpt_log(
            connection,
            _build_chatgpt_log_data(
                file_path=source_path,
                raw_response=raw_response,
                validation=validation,
                version_uuid=None,
                validation_status="file_facts_failed",
            ),
        )
        return file_facts_result.result

    file_facts = file_facts_result.file_facts
    metadata = _clean_metadata(validation.normalized_data)

    media_uuid = _coerce_uuid(metadata.get("media_uuid"))
    version_uuid = str(uuid4())
    filearea = _coerce_filearea(metadata.get("filearea"))

    storage_result = copy_into_storage(
        source_path,
        storage_root,
        filearea=filearea,
        version_uuid=version_uuid,
        mode=copy_mode,
    )

    if not storage_result.success:
        _safe_insert_chatgpt_log(
            connection,
            _build_chatgpt_log_data(
                file_path=source_path,
                raw_response=raw_response,
                validation=validation,
                version_uuid=version_uuid,
                validation_status="storage_failed",
            ),
        )

        return OperationResult(
            success=False,
            operation=operation,
            result="storage_failed",
            entity_type="file",
            entity_uuid=version_uuid,
            media_uuid=media_uuid,
            version_uuid=version_uuid,
            path=str(source_path),
            data={
                "validation": _validation_to_dict(validation),
                "storage_result": _operation_to_dict(storage_result),
            },
            warnings=[*validation.warnings, *storage_result.warnings],
            errors=storage_result.errors,
        )

    storage_path = _extract_storage_path(storage_result)

    row_data = metadata_to_library_row(
        metadata,
        file_facts,
        media_uuid=media_uuid,
        version_uuid=version_uuid,
        storage_path=storage_path,
        filearea=filearea,
        import_batch=import_batch,
    )

    row_data = _enforce_local_file_facts(
        row_data=row_data,
        file_facts=file_facts,
        source_path=source_path,
        storage_path=storage_path,
        filearea=filearea,
    )

    duplicate_warnings = _safe_duplicate_warnings(connection, file_facts)
    insert_result = insert_library_row(connection, row_data)

    _safe_insert_chatgpt_log(
        connection,
        _build_chatgpt_log_data(
            file_path=source_path,
            raw_response=raw_response,
            validation=validation,
            version_uuid=version_uuid,
            validation_status="integrated" if insert_result.success else "insert_failed",
        ),
    )

    if not insert_result.success:
        return OperationResult(
            success=False,
            operation=operation,
            result="insert_failed",
            entity_type="library_row",
            entity_uuid=version_uuid,
            media_uuid=row_data.get("media_uuid"),
            version_uuid=row_data.get("version_uuid"),
            path=str(source_path),
            data={
                "row": row_data,
                "library_row": row_data,
                "validation": _validation_to_dict(validation),
                "storage_result": _operation_to_dict(storage_result),
                "insert_result": _operation_to_dict(insert_result),
            },
            warnings=[
                *validation.warnings,
                *storage_result.warnings,
                *duplicate_warnings,
                *insert_result.warnings,
            ],
            errors=insert_result.errors,
        )

    _safe_write_audit_log(
        connection,
        action="chatgpt_intake_integrated",
        entity_type="library_row",
        entity_uuid=version_uuid,
        after=row_data,
        actor=actor,
        note="ChatGPT metadata integrated into library_rows.",
    )

    return OperationResult(
        success=True,
        operation=operation,
        result="inserted",
        entity_type="library_row",
        entity_uuid=version_uuid,
        media_uuid=row_data.get("media_uuid"),
        version_uuid=row_data.get("version_uuid"),
        path=str(source_path),
        data={
            "row": row_data,
            "library_row": row_data,
            "file_facts": _file_facts_to_dict(file_facts),
            "validation": _validation_to_dict(validation),
            "storage_result": _operation_to_dict(storage_result),
            "insert_result": _operation_to_dict(insert_result),
            "copy_mode": copy_mode,
            "storage_root": str(Path(storage_root).expanduser()),
            "import_batch": import_batch,
        },
        warnings=[
            *validation.warnings,
            *storage_result.warnings,
            *duplicate_warnings,
            *insert_result.warnings,
        ],
        errors=[],
    )


class _FileFactsResult:
    def __init__(
        self,
        *,
        file_facts: FileFacts | None = None,
        result: OperationResult | None = None,
    ) -> None:
        self.file_facts = file_facts
        self.result = result

    @property
    def errors(self) -> bool:
        return self.result is not None


def _normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _validate_response(
    raw_response: str,
    *,
    allow_human_verified_override: bool,
) -> ValidationResult:
    validation = validate_chatgpt_json(
        raw_response,
        allow_human_verified_override=allow_human_verified_override,
    )

    validation.normalized_data = _clean_metadata(validation.normalized_data)

    return validation


def _clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(metadata or {})

    for field_name in TECHNICAL_FIELDS_FROM_AI:
        cleaned.pop(field_name, None)

    return cleaned


def _get_local_file_facts(
    operation: str,
    source_path: Path,
    validation: ValidationResult,
) -> _FileFactsResult:
    try:
        return _FileFactsResult(file_facts=get_file_facts(source_path))
    except FileNotFoundError:
        return _FileFactsResult(result=_file_not_found_result(operation, source_path))
    except Exception as exc:
        return _FileFactsResult(
            result=OperationResult(
                success=False,
                operation=operation,
                result="file_facts_failed",
                entity_type="file",
                path=str(source_path),
                warnings=validation.warnings,
                errors=[
                    KoaMessage(
                        code="ERR_FILE_FACTS",
                        severity="blocking",
                        field="file_path",
                        message=(
                            "Impossible de calculer les faits techniques "
                            f"du fichier : {exc}"
                        ),
                    )
                ],
            )
        )


def _file_not_found_result(operation: str, path: Path) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result="file_not_found",
        entity_type="file",
        path=str(path),
        data={"file_path": str(path)},
        warnings=[],
        errors=[
            KoaMessage(
                code=ERR_FILE_NOT_FOUND,
                severity="blocking",
                field="file_path",
                message=f"Fichier introuvable : {path}",
            )
        ],
    )


def _coerce_uuid(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return str(uuid4())


def _coerce_filearea(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return DEFAULT_FILEAREA


def _build_storage_path_preview(
    *,
    storage_root: str | Path,
    filearea: str,
    version_uuid: str,
    filename: str,
    copy_mode: str,
    source_path: Path,
) -> str | None:
    if copy_mode == "reference_only":
        return None

    root = Path(storage_root).expanduser()
    suffix = Path(filename).suffix
    safe_name = f"{version_uuid}{suffix.lower()}" if suffix else version_uuid

    return str(root / filearea / safe_name)


def _extract_storage_path(storage_result: OperationResult) -> str | None:
    if storage_result.path:
        return storage_result.path

    if not isinstance(storage_result.data, dict):
        return None

    for key in (
        "storage_path",
        "stored_path",
        "copied_path",
        "destination_path",
        "path",
    ):
        value = storage_result.data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _enforce_local_file_facts(
    *,
    row_data: dict[str, Any],
    file_facts: FileFacts,
    source_path: Path,
    storage_path: str | None,
    filearea: str,
) -> dict[str, Any]:
    row = dict(row_data)

    row["original_path"] = str(source_path)
    row["filename"] = file_facts.filename
    row["extension"] = file_facts.extension
    row["mimetype"] = file_facts.mimetype
    row["filesize"] = file_facts.filesize
    row["sha256"] = file_facts.sha256
    row["filearea"] = filearea

    if storage_path is None:
        row["storage_path"] = ""
    else:
        row["storage_path"] = storage_path

    return row


def _safe_duplicate_warnings(connection, file_facts: FileFacts) -> list[KoaMessage]:
    try:
        return list(build_duplicate_warnings(connection, file_facts))
    except Exception:
        return []


def _build_chatgpt_log_data(
    *,
    file_path: Path,
    raw_response: str,
    validation: ValidationResult,
    version_uuid: str | None,
    validation_status: str,
) -> dict[str, Any]:
    return {
        "version_uuid": version_uuid,
        "file_path": str(file_path),
        "prompt_template": "",
        "raw_response": raw_response,
        "parsed_json": _json_dumps(validation.normalized_data),
        "validation_status": validation_status,
        "validation_errors": _json_dumps(
            [_message_to_dict(message) for message in validation.errors]
        ),
    }


def _validation_status(validation: ValidationResult) -> str:
    if validation.is_valid:
        return "valid"

    if validation.is_blocked:
        return "blocked"

    return "invalid"


def _safe_insert_chatgpt_log(connection, log_data: dict[str, Any]) -> None:
    try:
        insert_chatgpt_intake_log(connection, log_data)
    except Exception:
        return


def _safe_write_audit_log(
    connection,
    *,
    action: str,
    entity_type: str,
    entity_uuid: str | None,
    after: dict[str, Any],
    actor: str,
    note: str,
) -> None:
    try:
        write_audit_log(
            connection,
            action=action,
            entity_type=entity_type,
            entity_uuid=entity_uuid,
            before=None,
            after=after,
            actor=actor,
            note=note,
        )
    except Exception:
        return


def _file_facts_to_dict(file_facts: FileFacts) -> dict[str, Any]:
    return {
        "original_path": file_facts.original_path,
        "filename": file_facts.filename,
        "extension": file_facts.extension,
        "mimetype": file_facts.mimetype,
        "filesize": file_facts.filesize,
        "sha256": file_facts.sha256,
    }


def _validation_to_dict(validation: ValidationResult) -> dict[str, Any]:
    return {
        "is_valid": validation.is_valid,
        "is_blocked": validation.is_blocked,
        "normalized_data": validation.normalized_data,
        "warnings": [_message_to_dict(message) for message in validation.warnings],
        "errors": [_message_to_dict(message) for message in validation.errors],
    }


def _operation_to_dict(result: OperationResult) -> dict[str, Any]:
    return {
        "success": result.success,
        "operation": result.operation,
        "result": result.result,
        "entity_type": result.entity_type,
        "entity_uuid": result.entity_uuid,
        "media_uuid": result.media_uuid,
        "version_uuid": result.version_uuid,
        "path": result.path,
        "data": result.data,
        "warnings": [_message_to_dict(message) for message in result.warnings],
        "errors": [_message_to_dict(message) for message in result.errors],
    }


def _message_to_dict(message: KoaMessage) -> dict[str, Any]:
    return {
        "code": message.code,
        "severity": message.severity,
        "message": message.message,
        "field": message.field,
        "row_number": message.row_number,
        "details": message.details,
    }


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)