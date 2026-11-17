# 06_GUI/koa_mediatheque_gui/koa_mediatheque/db.py
# Médiathèque kOA — SQLite database helpers

from __future__ import annotations

import re
import shutil
import sqlite3
from pathlib import Path

from .errors import (
    ERR_DB_NOT_FOUND,
    ERR_DB_SCHEMA,
    ERR_FILE_NOT_FOUND,
)
from .models import KoaMessage, OperationResult
from .schema import (
    REQUIRED_TABLES,
    SCHEMA_FILES,
    SCHEMA_VERSION,
    utc_now_iso,
)


DEFAULT_BUSY_TIMEOUT_MS = 5000


def get_db_connection(db_path: str | Path) -> sqlite3.Connection:
    """
    Open a SQLite connection configured for Médiathèque kOA.

    Rules:
    - sqlite3.Row row_factory for dict-like reads.
    - foreign_keys ON.
    - busy_timeout set.
    - WAL mode attempted when possible.
    """
    resolved_path = _resolve_path(db_path)

    connection = sqlite3.connect(str(resolved_path))
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute(f"PRAGMA busy_timeout = {DEFAULT_BUSY_TIMEOUT_MS};")

    try:
        connection.execute("PRAGMA journal_mode = WAL;")
    except sqlite3.DatabaseError:
        pass

    return connection


def database_exists(db_path: str | Path) -> bool:
    """
    Return True only when the SQLite database file exists.
    """
    return _resolve_path(db_path).is_file()


def initialize_database(
    db_path: str | Path,
    schema_dir: str | Path,
    *,
    overwrite: bool = False,
) -> OperationResult:
    """
    Initialize the Médiathèque kOA SQLite database.

    Applies schema files in the canonical order defined by schema.SCHEMA_FILES.
    Refuses to overwrite an existing DB unless overwrite=True.
    """
    operation = "initialize_database"
    resolved_db_path = _resolve_path(db_path)
    resolved_schema_dir = _resolve_path(schema_dir)

    warnings: list[KoaMessage] = []

    schema_validation = _validate_schema_dir(resolved_schema_dir)
    if schema_validation is not None:
        return OperationResult(
            success=False,
            operation=operation,
            result=schema_validation["result"],
            entity_type="database",
            path=str(resolved_db_path),
            data={"schema_dir": str(resolved_schema_dir)},
            warnings=warnings,
            errors=schema_validation["errors"],
        )

    if resolved_db_path.exists() and not overwrite:
        return OperationResult(
            success=False,
            operation=operation,
            result="db_already_exists",
            entity_type="database",
            path=str(resolved_db_path),
            data={
                "db_path": str(resolved_db_path),
                "schema_dir": str(resolved_schema_dir),
                "overwrite": overwrite,
            },
            warnings=warnings,
            errors=[
                KoaMessage(
                    code=ERR_DB_SCHEMA,
                    severity="blocking",
                    message="SQLite database already exists. Pass overwrite=True to recreate it.",
                    field="db_path",
                    details={"db_path": str(resolved_db_path)},
                )
            ],
        )

    created_new_db = not resolved_db_path.exists()

    if overwrite:
        _remove_sqlite_database_files(resolved_db_path)

    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    applied_files: list[str] = []
    connection: sqlite3.Connection | None = None

    try:
        connection = get_db_connection(resolved_db_path)

        for filename in SCHEMA_FILES:
            schema_path = resolved_schema_dir / filename
            result = apply_schema_file(connection, schema_path)
            warnings.extend(result.warnings)

            if not result.success:
                if created_new_db or overwrite:
                    _safe_close(connection)
                    connection = None
                    _remove_sqlite_database_files(resolved_db_path)

                return OperationResult(
                    success=False,
                    operation=operation,
                    result="schema_apply_failed",
                    entity_type="database",
                    path=str(resolved_db_path),
                    data={
                        "failed_file": filename,
                        "applied_files": applied_files,
                        "schema_dir": str(resolved_schema_dir),
                    },
                    warnings=warnings,
                    errors=result.errors,
                )

            applied_files.append(filename)

        missing_tables = _get_missing_required_tables(connection)
        if missing_tables:
            return OperationResult(
                success=False,
                operation=operation,
                result="required_tables_missing",
                entity_type="database",
                path=str(resolved_db_path),
                data={
                    "applied_files": applied_files,
                    "missing_tables": missing_tables,
                    "schema_dir": str(resolved_schema_dir),
                },
                warnings=warnings,
                errors=[
                    KoaMessage(
                        code=ERR_DB_SCHEMA,
                        severity="blocking",
                        message="Database initialization completed, but required tables are missing.",
                        field="required_tables",
                        details={"missing_tables": missing_tables},
                    )
                ],
            )

        set_schema_meta(connection, "schema_version", str(SCHEMA_VERSION))
        set_schema_meta(connection, "schema_initialized_at", utc_now_iso())

        return OperationResult(
            success=True,
            operation=operation,
            result="initialized",
            entity_type="database",
            path=str(resolved_db_path),
            data={
                "db_path": str(resolved_db_path),
                "schema_dir": str(resolved_schema_dir),
                "schema_version": str(SCHEMA_VERSION),
                "applied_files": applied_files,
                "required_tables": list(REQUIRED_TABLES),
                "overwrite": overwrite,
            },
            warnings=warnings,
            errors=[],
        )

    except sqlite3.DatabaseError as exc:
        if created_new_db or overwrite:
            _safe_close(connection)
            connection = None
            _remove_sqlite_database_files(resolved_db_path)

        return OperationResult(
            success=False,
            operation=operation,
            result="failed",
            entity_type="database",
            path=str(resolved_db_path),
            data={
                "applied_files": applied_files,
                "schema_dir": str(resolved_schema_dir),
            },
            warnings=warnings,
            errors=[
                KoaMessage(
                    code=ERR_DB_SCHEMA,
                    severity="error",
                    message="SQLite schema initialization failed.",
                    field="db_path",
                    details={
                        "db_path": str(resolved_db_path),
                        "error": str(exc),
                    },
                )
            ],
        )

    finally:
        _safe_close(connection)


def apply_schema_file(
    connection: sqlite3.Connection,
    schema_path: str | Path,
) -> OperationResult:
    """
    Apply a single SQL schema file with sqlite3.executescript().
    """
    operation = "apply_schema_file"
    resolved_schema_path = _resolve_path(schema_path)

    if not resolved_schema_path.is_file():
        return OperationResult(
            success=False,
            operation=operation,
            result="schema_file_missing",
            entity_type="schema_file",
            path=str(resolved_schema_path),
            errors=[
                KoaMessage(
                    code=ERR_FILE_NOT_FOUND,
                    severity="error",
                    message="Schema file does not exist.",
                    field="schema_path",
                    details={"schema_path": str(resolved_schema_path)},
                )
            ],
        )

    try:
        sql = resolved_schema_path.read_text(encoding="utf-8-sig")
        connection.executescript(sql)
        connection.commit()

        return OperationResult(
            success=True,
            operation=operation,
            result="applied",
            entity_type="schema_file",
            path=str(resolved_schema_path),
            data={"schema_file": resolved_schema_path.name},
            warnings=[],
            errors=[],
        )

    except sqlite3.DatabaseError as exc:
        connection.rollback()

        return OperationResult(
            success=False,
            operation=operation,
            result="failed",
            entity_type="schema_file",
            path=str(resolved_schema_path),
            errors=[
                KoaMessage(
                    code=ERR_DB_SCHEMA,
                    severity="error",
                    message="Could not apply schema file.",
                    field="schema_path",
                    details={
                        "schema_path": str(resolved_schema_path),
                        "error": str(exc),
                    },
                )
            ],
        )


def get_schema_version(connection: sqlite3.Connection) -> str | None:
    """
    Return schema_meta['schema_version'] when available.
    """
    try:
        row = connection.execute(
            "SELECT value FROM schema_meta WHERE key = ?;",
            ("schema_version",),
        ).fetchone()
    except sqlite3.DatabaseError:
        return None

    if row is None:
        return None

    try:
        return str(row["value"])
    except (KeyError, IndexError, TypeError):
        return str(row[0])


def set_schema_meta(
    connection: sqlite3.Connection,
    key: str,
    value: str,
) -> None:
    """
    Upsert a schema_meta value.
    """
    if not str(key).strip():
        raise ValueError("schema_meta key cannot be empty.")

    connection.execute(
        """
        INSERT INTO schema_meta (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at;
        """,
        (str(key), str(value), utc_now_iso()),
    )
    connection.commit()


def backup_sqlite_database(
    db_path: str | Path,
    backup_dir: str | Path,
    reason: str,
) -> OperationResult:
    """
    Create a backup copy of the SQLite database.

    Preferred path uses sqlite3.Connection.backup().
    Falls back to shutil.copy2() only if SQLite backup fails.
    """
    operation = "backup_sqlite_database"
    resolved_db_path = _resolve_path(db_path)
    resolved_backup_dir = _resolve_path(backup_dir)

    if not resolved_db_path.is_file():
        return OperationResult(
            success=False,
            operation=operation,
            result="db_not_found",
            entity_type="backup",
            path=str(resolved_db_path),
            errors=[
                KoaMessage(
                    code=ERR_DB_NOT_FOUND,
                    severity="error",
                    message="SQLite database file does not exist.",
                    field="db_path",
                    details={"db_path": str(resolved_db_path)},
                )
            ],
        )

    resolved_backup_dir.mkdir(parents=True, exist_ok=True)

    safe_reason = _sanitize_backup_reason(reason)
    timestamp = _backup_timestamp()
    backup_path = resolved_backup_dir / f"koa_mediatheque_{timestamp}_{safe_reason}.sqlite"

    warnings: list[KoaMessage] = []

    try:
        source = sqlite3.connect(str(resolved_db_path))
        destination = sqlite3.connect(str(backup_path))

        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        return OperationResult(
            success=True,
            operation=operation,
            result="created",
            entity_type="backup",
            path=str(backup_path),
            data={
                "source_db_path": str(resolved_db_path),
                "backup_path": str(backup_path),
                "reason": reason,
            },
            warnings=warnings,
            errors=[],
        )

    except sqlite3.DatabaseError as exc:
        warnings.append(
            KoaMessage(
                code=ERR_DB_SCHEMA,
                severity="warning",
                message="SQLite backup API failed; falling back to file copy.",
                field="db_path",
                details={
                    "db_path": str(resolved_db_path),
                    "error": str(exc),
                },
            )
        )

        try:
            shutil.copy2(resolved_db_path, backup_path)

            return OperationResult(
                success=True,
                operation=operation,
                result="created_by_copy",
                entity_type="backup",
                path=str(backup_path),
                data={
                    "source_db_path": str(resolved_db_path),
                    "backup_path": str(backup_path),
                    "reason": reason,
                },
                warnings=warnings,
                errors=[],
            )

        except OSError as copy_exc:
            return OperationResult(
                success=False,
                operation=operation,
                result="failed",
                entity_type="backup",
                path=str(backup_path),
                warnings=warnings,
                errors=[
                    KoaMessage(
                        code=ERR_DB_SCHEMA,
                        severity="error",
                        message="Could not create SQLite database backup.",
                        field="backup_dir",
                        details={
                            "source_db_path": str(resolved_db_path),
                            "backup_path": str(backup_path),
                            "error": str(copy_exc),
                        },
                    )
                ],
            )


def _validate_schema_dir(schema_dir: Path) -> dict[str, object] | None:
    if not schema_dir.is_dir():
        return {
            "result": "schema_dir_missing",
            "errors": [
                KoaMessage(
                    code=ERR_FILE_NOT_FOUND,
                    severity="error",
                    message="Schema directory does not exist.",
                    field="schema_dir",
                    details={"schema_dir": str(schema_dir)},
                )
            ],
        }

    missing_schema_files = [
        filename
        for filename in SCHEMA_FILES
        if not (schema_dir / filename).is_file()
    ]

    if missing_schema_files:
        return {
            "result": "schema_files_missing",
            "errors": [
                KoaMessage(
                    code=ERR_FILE_NOT_FOUND,
                    severity="error",
                    message="One or more schema files are missing.",
                    field="schema_dir",
                    details={
                        "schema_dir": str(schema_dir),
                        "missing_files": missing_schema_files,
                    },
                )
            ],
        }

    return None


def _get_missing_required_tables(connection: sqlite3.Connection) -> list[str]:
    existing_tables = {
        str(row["name"])
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table';
            """
        ).fetchall()
    }

    return [
        table_name
        for table_name in REQUIRED_TABLES
        if table_name not in existing_tables
    ]


def _remove_sqlite_database_files(db_path: Path) -> None:
    for path in _sqlite_database_file_set(db_path):
        if path.exists():
            path.unlink()


def _sqlite_database_file_set(db_path: Path) -> tuple[Path, Path, Path]:
    return (
        db_path,
        db_path.with_name(f"{db_path.name}-wal"),
        db_path.with_name(f"{db_path.name}-shm"),
    )


def _safe_close(connection: sqlite3.Connection | None) -> None:
    if connection is None:
        return

    try:
        connection.close()
    except sqlite3.Error:
        pass


def _backup_timestamp() -> str:
    return (
        utc_now_iso()
        .replace("-", "")
        .replace(":", "")
        .replace("T", "_")
        .replace("Z", "")
    )


def _sanitize_backup_reason(reason: str) -> str:
    cleaned = str(reason or "").strip().lower()

    if not cleaned:
        return "manual"

    cleaned = re.sub(r"[^a-z0-9_-]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")

    return cleaned[:64] or "manual"


def _resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)