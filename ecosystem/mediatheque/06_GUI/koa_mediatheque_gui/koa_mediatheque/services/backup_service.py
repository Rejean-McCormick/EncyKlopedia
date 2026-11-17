# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/backup_service.py

"""
Backup service for Médiathèque kOA.

Every import or risky repair operation must create a SQLite backup before
modifying the source-of-truth database.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from pathlib import Path

from koa_mediatheque.errors import ERR_DB_NOT_FOUND
from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.schema import utc_now_iso
from koa_mediatheque.services.audit_service import write_audit_log


ERR_BACKUP_FAILED = "ERR_BACKUP_FAILED"
WARN_BACKUP_AUDIT_FAILED = "WARN_BACKUP_AUDIT_FAILED"


def backup_database(
    db_path: str | Path,
    backup_dir: str | Path,
    *,
    reason: str,
    actor: str = "local_user",
) -> OperationResult:
    """
    Create a SQLite backup in the backup directory.

    Contract filename:
        koa_mediatheque_YYYYMMDD_HHMMSS_<reason>.sqlite

    Collision behavior:
        If that filename already exists, append _2, _3, etc.
    """
    operation = "backup_database"
    source = Path(db_path).expanduser()
    target_dir = Path(backup_dir).expanduser()
    normalized_reason = _safe_reason(reason)
    normalized_actor = _clean_actor(actor)

    invalid_source_result = _validate_source_database(
        source=source,
        operation=operation,
    )
    if invalid_source_result is not None:
        return invalid_source_result

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return _failure_result(
            operation=operation,
            result="backup_dir_failed",
            path=target_dir,
            code=ERR_BACKUP_FAILED,
            message=f"Could not create backup directory: {target_dir}. {exc}",
            field="backup_dir",
            details={"exception_type": type(exc).__name__},
        )

    timestamp = utc_now_iso()
    backup_path = _build_unique_backup_path(
        target_dir=target_dir,
        timestamp=timestamp,
        reason=normalized_reason,
    )

    try:
        _copy_sqlite_database(source, backup_path)
    except Exception as exc:
        return _failure_result(
            operation=operation,
            result="backup_failed",
            path=backup_path,
            code=ERR_BACKUP_FAILED,
            message=f"SQLite backup failed: {exc}",
            field="backup_path",
            details={
                "db_path": str(source),
                "backup_path": str(backup_path),
                "exception_type": type(exc).__name__,
            },
        )

    result = OperationResult(
        success=True,
        operation=operation,
        result="backup_created",
        entity_type="backup",
        entity_uuid=None,
        version_uuid=None,
        media_uuid=None,
        path=str(backup_path),
        data={
            "db_path": str(source),
            "backup_path": str(backup_path),
            "reason": normalized_reason,
            "actor": normalized_actor,
            "created_at": timestamp,
        },
        warnings=[],
        errors=[],
    )

    _try_write_backup_audit(
        db_path=source,
        backup_path=backup_path,
        actor=normalized_actor,
        reason=normalized_reason,
        result=result,
    )

    return result


def _validate_source_database(
    *,
    source: Path,
    operation: str,
) -> OperationResult | None:
    if not source.exists():
        return _failure_result(
            operation=operation,
            result="db_not_found",
            path=source,
            code=ERR_DB_NOT_FOUND,
            message=f"SQLite database not found: {source}",
            field="db_path",
        )

    if source.is_dir():
        return _failure_result(
            operation=operation,
            result="db_path_is_directory",
            path=source,
            code=ERR_DB_NOT_FOUND,
            message=f"Expected SQLite database file, got directory: {source}",
            field="db_path",
        )

    return None


def _copy_sqlite_database(source: Path, backup_path: Path) -> None:
    """
    Copy SQLite using the online backup API.

    This is safer than shutil.copy2 for a live SQLite database and ensures both
    SQLite connections are closed explicitly.
    """
    source_connection: sqlite3.Connection | None = None
    target_connection: sqlite3.Connection | None = None

    try:
        source_connection = sqlite3.connect(str(source))
        target_connection = sqlite3.connect(str(backup_path))
        source_connection.backup(target_connection)
        target_connection.commit()
    finally:
        if target_connection is not None:
            target_connection.close()
        if source_connection is not None:
            source_connection.close()


def _build_unique_backup_path(
    *,
    target_dir: Path,
    timestamp: str,
    reason: str,
) -> Path:
    filename_timestamp = _timestamp_for_filename(timestamp)
    stem = f"koa_mediatheque_{filename_timestamp}_{reason}"

    candidate = target_dir / f"{stem}.sqlite"

    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = target_dir / f"{stem}_{counter}.sqlite"
        if not candidate.exists():
            return candidate
        counter += 1


def _timestamp_for_filename(timestamp: str) -> str:
    """
    Convert ISO UTC timestamp to YYYYMMDD_HHMMSS.

    Fractional seconds are intentionally dropped to preserve the public backup
    filename contract.
    """
    clean = str(timestamp).strip()

    if "." in clean:
        clean = clean.split(".", 1)[0] + "Z"

    return (
        clean.replace("-", "")
        .replace(":", "")
        .replace("T", "_")
        .replace("Z", "")
    )


def _safe_reason(reason: str) -> str:
    value = str(reason or "").strip().lower()

    if not value:
        value = "manual"

    value = re.sub(r"[^a-z0-9._-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._-")

    return value or "manual"


def _clean_actor(actor: str) -> str:
    return str(actor or "local_user").strip() or "local_user"


def _failure_result(
    *,
    operation: str,
    result: str,
    path: Path,
    code: str,
    message: str,
    field: str,
    details: dict | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        entity_type="backup",
        entity_uuid=None,
        version_uuid=None,
        media_uuid=None,
        path=str(path),
        data={"path": str(path)},
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


def _try_write_backup_audit(
    *,
    db_path: Path,
    backup_path: Path,
    actor: str,
    reason: str,
    result: OperationResult,
) -> None:
    """
    Best-effort audit logging.

    A successful backup must not become failed only because audit logging failed.
    Audit errors are appended as warnings.
    """
    try:
        with closing(sqlite3.connect(str(db_path))) as connection:
            connection.row_factory = sqlite3.Row

            audit_result = write_audit_log(
                connection,
                action="backup_created",
                entity_type="backup",
                entity_uuid=None,
                before=None,
                after={
                    "backup_path": str(backup_path),
                    "reason": reason,
                },
                actor=actor,
                note=f"SQLite backup created: {backup_path}",
            )

            connection.commit()

            if not audit_result.success:
                result.warnings.extend(audit_result.errors)

    except Exception as exc:
        result.warnings.append(
            KoaMessage(
                code=WARN_BACKUP_AUDIT_FAILED,
                severity="warning",
                message=f"Backup was created, but audit logging failed: {exc}",
                field="audit_log",
                details={
                    "exception_type": type(exc).__name__,
                    "backup_path": str(backup_path),
                },
            )
        )