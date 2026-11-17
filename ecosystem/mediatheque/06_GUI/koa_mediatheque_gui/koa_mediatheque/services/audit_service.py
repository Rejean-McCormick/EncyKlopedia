"""
Audit service for Médiathèque kOA.

The audit log records meaningful local operations without becoming a separate
source of truth. SQLite remains authoritative for current state; audit entries
preserve operation traces.
"""

from __future__ import annotations

import json
from typing import Any

from koa_mediatheque.errors import ERR_INVALID_ENUM
from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.repositories.audit_log_repository import insert_audit_log
from koa_mediatheque.schema import utc_now_iso

_ALLOWED_AUDIT_ACTIONS = {
    "database_initialized",
    "library_row_inserted",
    "library_row_updated",
    "library_row_archived",
    "chatgpt_intake_validated",
    "chatgpt_intake_integrated",
    "xlsx_exported",
    "xlsx_import_previewed",
    "xlsx_import_applied",
    "manifest_exported",
    "file_scanned",
    "file_copied_to_storage",
    "duplicate_detected",
    "backup_created",
    "repair_applied",
    "settings_updated",
}

_ALLOWED_ENTITY_TYPES = {
    "database",
    "library_row",
    "media_uuid",
    "version_uuid",
    "chatgpt_intake",
    "xlsx_import",
    "manifest_export",
    "file",
    "backup",
    "settings",
}


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
    """
    Write one audit entry.

    Args:
        connection: Open sqlite3 connection.
        action: Controlled audit action.
        entity_type: Controlled audited entity type.
        entity_uuid: Optional UUID or stable identifier for the entity.
        before: Optional state snapshot before the operation.
        after: Optional state snapshot after the operation.
        actor: Local actor name.
        note: Human-readable note.

    Returns:
        OperationResult: success=False when action/entity_type is invalid or
        when repository insertion fails.
    """
    operation = "write_audit_log"
    normalized_action = str(action or "").strip()
    normalized_entity_type = str(entity_type or "").strip()
    normalized_actor = str(actor or "local_user").strip() or "local_user"

    validation_errors = _validate_audit_input(
        action=normalized_action,
        entity_type=normalized_entity_type,
    )

    if validation_errors:
        return OperationResult(
            success=False,
            operation=operation,
            result="invalid_audit_log",
            entity_type=normalized_entity_type or None,
            entity_uuid=entity_uuid,
            errors=validation_errors,
        )

    log_data = {
        "action": normalized_action,
        "entity_type": normalized_entity_type,
        "entity_uuid": entity_uuid,
        "before_json": _json_or_none(before),
        "after_json": _json_or_none(after),
        "actor": normalized_actor,
        "note": str(note or ""),
        "created_at": utc_now_iso(),
    }

    try:
        repo_result = insert_audit_log(connection, log_data)
    except Exception as exc:
        return OperationResult(
            success=False,
            operation=operation,
            result="audit_log_failed",
            entity_type=normalized_entity_type,
            entity_uuid=entity_uuid,
            errors=[
                KoaMessage(
                    code="ERR_AUDIT_LOG_FAILED",
                    severity="error",
                    message=f"Failed to write audit log: {exc}",
                    details={"exception_type": type(exc).__name__},
                )
            ],
        )

    if isinstance(repo_result, OperationResult):
        if not repo_result.operation:
            repo_result.operation = operation
        return repo_result

    return OperationResult(
        success=True,
        operation=operation,
        result="audit_log_inserted",
        entity_type=normalized_entity_type,
        entity_uuid=entity_uuid,
        data={"audit_log": log_data},
    )


def _validate_audit_input(
    *,
    action: str,
    entity_type: str,
) -> list[KoaMessage]:
    errors: list[KoaMessage] = []

    if action not in _ALLOWED_AUDIT_ACTIONS:
        errors.append(
            KoaMessage(
                code=ERR_INVALID_ENUM,
                severity="error",
                message=f"Invalid audit action: {action}",
                field="action",
                details={"allowed_values": sorted(_ALLOWED_AUDIT_ACTIONS)},
            )
        )

    if entity_type not in _ALLOWED_ENTITY_TYPES:
        errors.append(
            KoaMessage(
                code=ERR_INVALID_ENUM,
                severity="error",
                message=f"Invalid audit entity_type: {entity_type}",
                field="entity_type",
                details={"allowed_values": sorted(_ALLOWED_ENTITY_TYPES)},
            )
        )

    return errors


def _json_or_none(value: dict[str, Any] | None) -> str | None:
    if value is None:
        return None

    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)