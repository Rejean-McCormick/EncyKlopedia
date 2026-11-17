"""
Repair service for Médiathèque kOA.

Repair operations are explicit maintenance actions. They may update protected
technical fields, but only through these repair handles and with audit logging.
"""

from __future__ import annotations

import re
from pathlib import Path
from koa_mediatheque.workspace import resolve_content_path
from typing import Any

from koa_mediatheque.errors import (
    ERR_FILE_NOT_FOUND,
    ERR_PROTECTED_FIELD_UPDATE,
    ERR_VERSION_UUID_MISSING,
)
from koa_mediatheque.models import FileFacts, KoaMessage, OperationResult
from koa_mediatheque.repositories.library_rows_repository import (
    get_library_row_by_version_uuid,
    update_library_row_by_version_uuid,
)
from koa_mediatheque.services.audit_service import write_audit_log
from koa_mediatheque.services.file_facts import get_file_facts, is_external_reference_path


_REPAIRABLE_PROTECTED_FIELDS = {
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
    "original_path",
    "storage_path",
}

_NON_REPAIRABLE_FIELDS = {
    "id",
    "media_uuid",
    "version_uuid",
    "created_at",
}

_FILE_FACT_FIELDS = {
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def recalculate_file_facts_for_row(
    connection,
    version_uuid: str,
    *,
    actor: str = "local_user",
) -> OperationResult:
    """
    Recalculate local file facts for one library row.

    Path priority:
    1. storage_path, if present and it points to an existing local file.
    2. original_path.

    This function repairs only computed file facts:
    filename, extension, mimetype, filesize, sha256.

    It does not rewrite original_path or storage_path.
    """
    operation = "recalculate_file_facts_for_row"
    normalized_version_uuid = _normalize_required_uuid(version_uuid)

    if not normalized_version_uuid:
        return _failure(
            operation=operation,
            result="missing_version_uuid",
            code=ERR_VERSION_UUID_MISSING,
            message="version_uuid cannot be empty.",
            field="version_uuid",
        )

    before = _get_row(connection, normalized_version_uuid)

    if before is None:
        return _failure(
            operation=operation,
            result="row_not_found",
            code=ERR_VERSION_UUID_MISSING,
            message=f"No library row found for version_uuid: {normalized_version_uuid}",
            field="version_uuid",
            version_uuid=normalized_version_uuid,
        )

    fact_source_path = _select_fact_source_path(before)

    if not fact_source_path:
        return _failure(
            operation=operation,
            result="missing_file_path",
            code=ERR_FILE_NOT_FOUND,
            message="Row has no usable storage_path or original_path.",
            field="original_path",
            version_uuid=normalized_version_uuid,
            details={
                "storage_path": before.get("storage_path"),
                "original_path": before.get("original_path"),
            },
        )

    try:
        facts = get_file_facts(fact_source_path)
    except Exception as exc:
        return _failure(
            operation=operation,
            result="file_not_found",
            code=ERR_FILE_NOT_FOUND,
            message=f"Could not recalculate file facts: {exc}",
            field="original_path",
            version_uuid=normalized_version_uuid,
            path=str(fact_source_path),
            details={
                "exception_type": type(exc).__name__,
                "fact_source_path": str(fact_source_path),
            },
        )

    updates = _file_facts_to_updates(facts)
    changes = _changed_values(before, updates)

    if not changes:
        return OperationResult(
            success=True,
            operation=operation,
            result="no_changes",
            entity_type="version_uuid",
            entity_uuid=normalized_version_uuid,
            version_uuid=normalized_version_uuid,
            media_uuid=_string_or_none(before.get("media_uuid")),
            path=str(fact_source_path),
            data={
                "updates": {},
                "changes": {},
                "file_facts": _file_facts_to_dict(facts),
            },
            warnings=[],
            errors=[],
        )

    update_result = update_library_row_by_version_uuid(
        connection,
        normalized_version_uuid,
        updates,
        actor=actor,
    )

    if not update_result.success:
        update_result.operation = operation
        return update_result

    after = _get_row(connection, normalized_version_uuid)

    _append_audit_result(
        connection,
        result=update_result,
        before=before,
        after=after,
        version_uuid=normalized_version_uuid,
        actor=actor,
        note="Recalculated protected technical file facts.",
    )

    return OperationResult(
        success=True,
        operation=operation,
        result="recalculated",
        entity_type="version_uuid",
        entity_uuid=normalized_version_uuid,
        version_uuid=normalized_version_uuid,
        media_uuid=_string_or_none(before.get("media_uuid")),
        path=str(fact_source_path),
        data={
            "updates": updates,
            "changes": changes,
            "file_facts": _file_facts_to_dict(facts),
        },
        warnings=update_result.warnings,
        errors=update_result.errors,
    )


def repair_protected_fields(
    connection,
    version_uuid: str,
    updates: dict[str, Any],
    *,
    actor: str = "local_user",
) -> OperationResult:
    """
    Repair protected fields for one library row.

    Only fields in _REPAIRABLE_PROTECTED_FIELDS may be updated here. Identity
    fields such as media_uuid and version_uuid are intentionally not repairable
    through this function.
    """
    operation = "repair_protected_fields"
    normalized_version_uuid = _normalize_required_uuid(version_uuid)

    if not normalized_version_uuid:
        return _failure(
            operation=operation,
            result="missing_version_uuid",
            code=ERR_VERSION_UUID_MISSING,
            message="version_uuid cannot be empty.",
            field="version_uuid",
        )

    if not isinstance(updates, dict) or not updates:
        return _failure(
            operation=operation,
            result="missing_updates",
            code=ERR_PROTECTED_FIELD_UPDATE,
            message="updates must be a non-empty dictionary.",
            field="updates",
            version_uuid=normalized_version_uuid,
        )

    invalid_fields = _invalid_repair_fields(updates)

    if invalid_fields:
        return _failure(
            operation=operation,
            result="invalid_repair_fields",
            code=ERR_PROTECTED_FIELD_UPDATE,
            message="One or more fields are not repairable through repair_protected_fields.",
            field="updates",
            version_uuid=normalized_version_uuid,
            details={
                "invalid_fields": invalid_fields,
                "repairable_fields": sorted(_REPAIRABLE_PROTECTED_FIELDS),
                "non_repairable_fields": sorted(_NON_REPAIRABLE_FIELDS),
            },
        )

    normalized_updates, validation_errors = _normalize_repair_updates(updates)

    if validation_errors:
        return OperationResult(
            success=False,
            operation=operation,
            result="invalid_repair_values",
            entity_type="version_uuid",
            entity_uuid=normalized_version_uuid,
            version_uuid=normalized_version_uuid,
            warnings=[],
            errors=validation_errors,
        )

    before = _get_row(connection, normalized_version_uuid)

    if before is None:
        return _failure(
            operation=operation,
            result="row_not_found",
            code=ERR_VERSION_UUID_MISSING,
            message=f"No library row found for version_uuid: {normalized_version_uuid}",
            field="version_uuid",
            version_uuid=normalized_version_uuid,
        )

    changes = _changed_values(before, normalized_updates)

    if not changes:
        return OperationResult(
            success=True,
            operation=operation,
            result="no_changes",
            entity_type="version_uuid",
            entity_uuid=normalized_version_uuid,
            version_uuid=normalized_version_uuid,
            media_uuid=_string_or_none(before.get("media_uuid")),
            data={
                "updates": {},
                "changes": {},
                "repaired_fields": sorted(normalized_updates.keys()),
            },
            warnings=[],
            errors=[],
        )

    update_result = update_library_row_by_version_uuid(
        connection,
        normalized_version_uuid,
        normalized_updates,
        actor=actor,
    )

    if not update_result.success:
        update_result.operation = operation
        return update_result

    after = _get_row(connection, normalized_version_uuid)

    _append_audit_result(
        connection,
        result=update_result,
        before=before,
        after=after,
        version_uuid=normalized_version_uuid,
        actor=actor,
        note="Repaired protected technical fields.",
    )

    return OperationResult(
        success=True,
        operation=operation,
        result="repaired",
        entity_type="version_uuid",
        entity_uuid=normalized_version_uuid,
        version_uuid=normalized_version_uuid,
        media_uuid=_string_or_none(before.get("media_uuid")),
        data={
            "updates": normalized_updates,
            "changes": changes,
            "repaired_fields": sorted(normalized_updates.keys()),
        },
        warnings=update_result.warnings,
        errors=update_result.errors,
    )


def _normalize_required_uuid(value: Any) -> str:
    return str(value or "").strip()


def _get_row(connection, version_uuid: str) -> dict[str, Any] | None:
    row = get_library_row_by_version_uuid(connection, version_uuid)
    if row is None:
        return None
    return _row_to_dict(row)


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)

    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}

    return {
        key: value
        for key, value in vars(row).items()
        if not key.startswith("_")
    }


def _select_fact_source_path(row: dict[str, Any]) -> str | None:
    storage_path = _normalize_optional_text(row.get("storage_path"))
    original_path = _normalize_optional_text(row.get("original_path"))

    if storage_path and not is_external_reference_path(storage_path):
        storage = resolve_content_path(storage_path)
        if storage.exists() and storage.is_file():
            return str(storage)

    if original_path:
        return original_path

    if storage_path:
        return storage_path

    return None


def _file_facts_to_updates(facts: FileFacts) -> dict[str, Any]:
    return {
        "filename": facts.filename,
        "extension": _normalize_extension(facts.extension),
        "mimetype": facts.mimetype,
        "filesize": facts.filesize,
        "sha256": facts.sha256,
    }


def _file_facts_to_dict(facts: FileFacts) -> dict[str, Any]:
    return {
        "original_path": facts.original_path,
        "filename": facts.filename,
        "extension": _normalize_extension(facts.extension),
        "mimetype": facts.mimetype,
        "filesize": facts.filesize,
        "sha256": facts.sha256,
    }


def _invalid_repair_fields(updates: dict[str, Any]) -> list[str]:
    return sorted(
        field_name
        for field_name in updates
        if field_name not in _REPAIRABLE_PROTECTED_FIELDS
    )


def _normalize_repair_updates(
    updates: dict[str, Any],
) -> tuple[dict[str, Any], list[KoaMessage]]:
    normalized: dict[str, Any] = {}
    errors: list[KoaMessage] = []

    for key, value in updates.items():
        if key == "filesize":
            parsed_value, error = _normalize_optional_filesize(value)
            if error is not None:
                errors.append(error)
            else:
                normalized[key] = parsed_value

        elif key == "sha256":
            parsed_value, error = _normalize_optional_sha256(value)
            if error is not None:
                errors.append(error)
            else:
                normalized[key] = parsed_value

        elif key == "extension":
            normalized[key] = _normalize_extension(value)

        elif key in {"filename", "mimetype", "original_path", "storage_path"}:
            normalized[key] = _normalize_optional_text(value)

        else:
            errors.append(
                KoaMessage(
                    code=ERR_PROTECTED_FIELD_UPDATE,
                    severity="blocking",
                    message=f"Unsupported repair field: {key}",
                    field=key,
                )
            )

    return normalized, errors


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _normalize_extension(value: Any) -> str:
    text = _normalize_optional_text(value)

    if text is None:
        return ""

    text = text.lower()

    if not text:
        return ""

    if not text.startswith("."):
        return f".{text}"

    return text


def _normalize_optional_filesize(value: Any) -> tuple[int | None, KoaMessage | None]:
    if value is None or value == "":
        return None, None

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, KoaMessage(
            code=ERR_PROTECTED_FIELD_UPDATE,
            severity="blocking",
            message="filesize must be an integer or null.",
            field="filesize",
            details={"value": value},
        )

    if parsed < 0:
        return None, KoaMessage(
            code=ERR_PROTECTED_FIELD_UPDATE,
            severity="blocking",
            message="filesize cannot be negative.",
            field="filesize",
            details={"value": value},
        )

    return parsed, None


def _normalize_optional_sha256(value: Any) -> tuple[str | None, KoaMessage | None]:
    text = _normalize_optional_text(value)

    if text is None:
        return None, None

    text = text.lower()

    if not _SHA256_RE.fullmatch(text):
        return None, KoaMessage(
            code=ERR_PROTECTED_FIELD_UPDATE,
            severity="blocking",
            message="sha256 must be a lowercase 64-character hexadecimal digest.",
            field="sha256",
            details={"value": value},
        )

    return text, None


def _changed_values(
    before: dict[str, Any],
    updates: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}

    for key, after_value in updates.items():
        before_value = before.get(key)

        if _values_differ(before_value, after_value):
            changes[key] = {
                "before": before_value,
                "after": after_value,
            }

    return changes


def _values_differ(before: Any, after: Any) -> bool:
    if before is None and after is None:
        return False

    if isinstance(before, int) or isinstance(after, int):
        try:
            return int(before) != int(after)
        except (TypeError, ValueError):
            return before != after

    return str(before) != str(after)


def _failure(
    *,
    operation: str,
    result: str,
    code: str,
    message: str,
    field: str | None,
    version_uuid: str | None = None,
    path: str | None = None,
    details: dict[str, Any] | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        entity_type="version_uuid" if version_uuid else None,
        entity_uuid=version_uuid,
        version_uuid=version_uuid,
        path=path,
        warnings=[],
        errors=[
            KoaMessage(
                code=code,
                severity="blocking",
                message=message,
                field=field,
                details=details or {},
            )
        ],
    )


def _append_audit_result(
    connection,
    *,
    result: OperationResult,
    before: dict[str, Any],
    after: dict[str, Any] | None,
    version_uuid: str,
    actor: str,
    note: str,
) -> None:
    audit_result = write_audit_log(
        connection,
        action="repair_applied",
        entity_type="version_uuid",
        entity_uuid=version_uuid,
        before=before,
        after=after,
        actor=actor,
        note=note,
    )

    if not audit_result.success:
        result.warnings.extend(audit_result.errors)


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None