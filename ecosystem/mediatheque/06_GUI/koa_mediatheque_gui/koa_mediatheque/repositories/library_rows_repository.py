# 06_GUI/koa_mediatheque_gui/koa_mediatheque/repositories/library_rows_repository.py
"""Repository functions for the canonical `library_rows` SQLite table.

This module is intentionally thin:
- it receives an already-open sqlite3.Connection;
- it never closes the connection;
- it explicitly closes every cursor it creates;
- it performs direct SQL operations only;
- it does not calculate file facts;
- it does not validate business rules or controlled values;
- it does not write audit rows directly.

Business validation belongs in services/validation.
Audit writing belongs in audit_service.py or audit_log_repository.py.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from typing import Any

from koa_mediatheque.errors import (
    ERR_DB_SCHEMA,
    ERR_REQUIRED_FIELD,
    ERR_VERSION_UUID_DUPLICATE,
    ERR_VERSION_UUID_MISSING,
)
from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.schema import utc_now_iso


TABLE_NAME = "library_rows"
ERR_PROTECTED_FIELD_UPDATE = "ERR_PROTECTED_FIELD_UPDATE"

_ALLOWED_FILTER_COLUMNS: frozenset[str] = frozenset(
    {
        "id",
        "media_uuid",
        "version_uuid",
        "sha256",
        "status",
        "visibility",
        "public_state",
        "access_level",
        "library_scope",
        "uckk_relevance",
        "target_system",
        "target_export_allowed",
        "media_type",
        "language",
        "ownership_scope",
        "source_type",
        "source_ownership",
        "rights_status",
        "restriction_state",
        "redaction_required",
        "ai_validation_state",
        "canonical_validation_state",
        "human_review_required",
        "review_queue",
        "audience_suitability",
        "export_to_uckk",
        "export_to_public",
        "import_batch",
        "filearea",
    }
)

_SEARCH_COLUMNS: tuple[str, ...] = (
    "title",
    "subtitle",
    "description",
    "summary",
    "filename",
    "notes",
    "rights_note",
    "restriction_reason",
    "review_reason",
    "export_policy_note",
)

_SORT_COLUMNS: frozenset[str] = frozenset(
    {
        "id",
        "title",
        "filename",
        "media_uuid",
        "version_uuid",
        "sha256",
        "status",
        "visibility",
        "public_state",
        "uckk_relevance",
        "target_system",
        "media_type",
        "human_review_required",
        "created_at",
        "updated_at",
    }
)

_REQUIRED_INSERT_FIELDS: tuple[str, ...] = (
    "media_uuid",
    "version_uuid",
    "title",
    "original_path",
    "filename",
)

_IDENTITY_PROTECTED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "media_uuid",
        "version_uuid",
        "created_at",
    }
)


def list_library_rows(
    connection: sqlite3.Connection,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return `library_rows` records as dictionaries.

    Supported filter keys:
    - exact-match filters for keys in _ALLOWED_FILTER_COLUMNS;
    - list/tuple/set values for SQL IN filtering;
    - "search" for LIKE search across common text fields;
    - "limit" and "offset";
    - "order_by" and "order_dir".

    Unknown filter keys are ignored, never interpolated.
    """
    filters = filters or {}
    where_sql, params = _build_where_clause(filters)

    order_by = _safe_order_by(filters.get("order_by"))
    order_dir = _safe_order_dir(filters.get("order_dir"))
    limit = _safe_int(filters.get("limit"), default=500, minimum=1, maximum=10_000)
    offset = _safe_int(filters.get("offset"), default=0, minimum=0, maximum=10_000_000)

    return _execute_fetch_all_dicts(
        connection,
        f"""
        SELECT *
        FROM {TABLE_NAME}
        {where_sql}
        ORDER BY {order_by} {order_dir}
        LIMIT ?
        OFFSET ?
        """,
        (*params, limit, offset),
    )


def get_library_row_by_id(
    connection: sqlite3.Connection,
    row_id: int,
) -> dict[str, Any] | None:
    """Return one `library_rows` row by local SQLite id."""
    return _execute_fetch_one_dict(
        connection,
        f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE id = ?
        LIMIT 1
        """,
        (row_id,),
    )


def get_library_row_by_version_uuid(
    connection: sqlite3.Connection,
    version_uuid: str,
) -> dict[str, Any] | None:
    """Return one `library_rows` row by stable version UUID."""
    if _is_blank(version_uuid):
        return None

    return _execute_fetch_one_dict(
        connection,
        f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE version_uuid = ?
        LIMIT 1
        """,
        (str(version_uuid).strip(),),
    )


def get_library_rows_by_media_uuid(
    connection: sqlite3.Connection,
    media_uuid: str,
) -> list[dict[str, Any]]:
    """Return all versions that share a media UUID."""
    if _is_blank(media_uuid):
        return []

    return _execute_fetch_all_dicts(
        connection,
        f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE media_uuid = ?
        ORDER BY created_at ASC, id ASC
        """,
        (str(media_uuid).strip(),),
    )


def get_library_rows_by_sha256(
    connection: sqlite3.Connection,
    sha256: str,
) -> list[dict[str, Any]]:
    """Return all rows with the same content hash."""
    if _is_blank(sha256):
        return []

    return _execute_fetch_all_dicts(
        connection,
        f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE sha256 = ?
        ORDER BY created_at ASC, id ASC
        """,
        (str(sha256).strip().lower(),),
    )


def insert_library_row(
    connection: sqlite3.Connection,
    row_data: dict[str, Any],
) -> OperationResult:
    """Insert a new canonical library row.

    Repository-level checks only:
    - required insert fields are present;
    - version_uuid is present;
    - version_uuid is unique;
    - provided columns exist in the table.
    """
    operation = "insert_library_row"

    if not isinstance(row_data, Mapping):
        return _failure(
            operation=operation,
            result="invalid_row_data",
            code=ERR_REQUIRED_FIELD,
            message="row_data must be a dictionary.",
        )

    missing_fields = [
        field_name
        for field_name in _REQUIRED_INSERT_FIELDS
        if _is_blank(row_data.get(field_name))
    ]

    if missing_fields:
        return _failure(
            operation=operation,
            result="missing_required_fields",
            code=ERR_REQUIRED_FIELD,
            message="Required library row fields are missing.",
            data={"missing_fields": missing_fields},
        )

    version_uuid = str(row_data["version_uuid"]).strip()
    media_uuid = _string_or_none(row_data.get("media_uuid"))

    if get_library_row_by_version_uuid(connection, version_uuid) is not None:
        return _failure(
            operation=operation,
            result="duplicate_version_uuid",
            code=ERR_VERSION_UUID_DUPLICATE,
            message="A library row already exists for this version_uuid.",
            version_uuid=version_uuid,
            media_uuid=media_uuid,
        )

    try:
        allowed_columns = _get_table_columns(connection)
        insert_data, ignored_columns = _filter_insert_columns(row_data, allowed_columns)

        now = utc_now_iso()
        insert_data.setdefault("created_at", now)
        insert_data.setdefault("updated_at", now)

        if not insert_data:
            return _failure(
                operation=operation,
                result="no_insertable_fields",
                code=ERR_DB_SCHEMA,
                message="No insertable library_rows columns were provided.",
                version_uuid=version_uuid,
                media_uuid=media_uuid,
            )

        columns = tuple(insert_data)
        column_sql = ", ".join(columns)
        placeholders = ", ".join("?" for _ in columns)

        row_id = _execute_insert(
            connection,
            f"""
            INSERT INTO {TABLE_NAME} ({column_sql})
            VALUES ({placeholders})
            """,
            tuple(insert_data[column] for column in columns),
        )
        connection.commit()

        inserted_row = get_library_row_by_id(connection, row_id)
        warnings = _ignored_columns_warnings(
            ignored_columns,
            "Some fields were ignored because they are not columns in library_rows.",
        )

        return OperationResult(
            success=True,
            operation=operation,
            result="inserted",
            entity_type="library_row",
            entity_uuid=version_uuid,
            media_uuid=media_uuid,
            version_uuid=version_uuid,
            data={
                "id": row_id,
                "row": inserted_row,
                "ignored_columns": ignored_columns,
            },
            warnings=warnings,
            errors=[],
        )

    except sqlite3.IntegrityError as exc:
        connection.rollback()
        return _failure(
            operation=operation,
            result="integrity_error",
            code=ERR_VERSION_UUID_DUPLICATE
            if "version_uuid" in str(exc).lower()
            else ERR_DB_SCHEMA,
            message="SQLite integrity error while inserting a library row.",
            version_uuid=version_uuid,
            media_uuid=media_uuid,
            data={"exception": str(exc)},
        )

    except sqlite3.Error as exc:
        connection.rollback()
        return _failure(
            operation=operation,
            result="sqlite_error",
            code=ERR_DB_SCHEMA,
            message="SQLite error while inserting a library row.",
            version_uuid=version_uuid,
            media_uuid=media_uuid,
            data={"exception": str(exc)},
        )


def update_library_row_by_version_uuid(
    connection: sqlite3.Connection,
    version_uuid: str,
    updates: dict[str, Any],
    *,
    actor: str = "local_user",
) -> OperationResult:
    """Update an existing `library_rows` row by version UUID.

    This repository rejects identity/provenance mutations:
    - id
    - media_uuid
    - version_uuid
    - created_at

    Technical protected facts are handled by repair_service or import rules.
    """
    operation = "update_library_row_by_version_uuid"

    if _is_blank(version_uuid):
        return _failure(
            operation=operation,
            result="missing_version_uuid",
            code=ERR_VERSION_UUID_MISSING,
            message="version_uuid is required for library row updates.",
        )

    version_uuid = str(version_uuid).strip()

    if not isinstance(updates, Mapping):
        return _failure(
            operation=operation,
            result="invalid_updates",
            code=ERR_REQUIRED_FIELD,
            message="updates must be a dictionary.",
            version_uuid=version_uuid,
        )

    existing_row = get_library_row_by_version_uuid(connection, version_uuid)
    if existing_row is None:
        return _failure(
            operation=operation,
            result="not_found",
            code=ERR_VERSION_UUID_MISSING,
            message="No library row exists for this version_uuid.",
            version_uuid=version_uuid,
        )

    protected_updates = sorted(
        key for key in updates if key in _IDENTITY_PROTECTED_FIELDS
    )

    if protected_updates:
        return _failure(
            operation=operation,
            result="protected_field_update",
            code=ERR_PROTECTED_FIELD_UPDATE,
            message="Identity or provenance fields cannot be updated by this repository.",
            version_uuid=version_uuid,
            media_uuid=_string_or_none(existing_row.get("media_uuid")),
            data={
                "protected_fields": protected_updates,
                "actor": actor,
            },
        )

    try:
        allowed_columns = _get_table_columns(connection)
        update_data, ignored_columns = _filter_update_columns(updates, allowed_columns)

        if not update_data:
            return OperationResult(
                success=True,
                operation=operation,
                result="no_changes",
                entity_type="library_row",
                entity_uuid=version_uuid,
                media_uuid=_string_or_none(existing_row.get("media_uuid")),
                version_uuid=version_uuid,
                data={
                    "row": existing_row,
                    "ignored_columns": ignored_columns,
                    "actor": actor,
                },
                warnings=_ignored_columns_warnings(
                    ignored_columns,
                    "Some fields were ignored because they are not columns in library_rows.",
                ),
                errors=[],
            )

        update_data["updated_at"] = utc_now_iso()

        set_sql = ", ".join(f"{column} = ?" for column in update_data)
        params = tuple(update_data[column] for column in update_data) + (version_uuid,)

        _execute_non_query(
            connection,
            f"""
            UPDATE {TABLE_NAME}
            SET {set_sql}
            WHERE version_uuid = ?
            """,
            params,
        )
        connection.commit()

        updated_row = get_library_row_by_version_uuid(connection, version_uuid)

        return OperationResult(
            success=True,
            operation=operation,
            result="updated",
            entity_type="library_row",
            entity_uuid=version_uuid,
            media_uuid=_string_or_none(
                updated_row.get("media_uuid")
                if updated_row
                else existing_row.get("media_uuid")
            ),
            version_uuid=version_uuid,
            data={
                "before": existing_row,
                "after": updated_row,
                "ignored_columns": ignored_columns,
                "actor": actor,
            },
            warnings=_ignored_columns_warnings(
                ignored_columns,
                "Some fields were ignored because they are not columns in library_rows.",
            ),
            errors=[],
        )

    except sqlite3.Error as exc:
        connection.rollback()
        return _failure(
            operation=operation,
            result="sqlite_error",
            code=ERR_DB_SCHEMA,
            message="SQLite error while updating a library row.",
            version_uuid=version_uuid,
            media_uuid=_string_or_none(existing_row.get("media_uuid")),
            data={"exception": str(exc), "actor": actor},
        )


def soft_delete_library_row(
    connection: sqlite3.Connection,
    version_uuid: str,
    *,
    actor: str = "local_user",
) -> OperationResult:
    """Soft-delete a library row by setting status = 'deleted_soft'."""
    operation = "soft_delete_library_row"

    if _is_blank(version_uuid):
        return _failure(
            operation=operation,
            result="missing_version_uuid",
            code=ERR_VERSION_UUID_MISSING,
            message="version_uuid is required for soft delete.",
        )

    version_uuid = str(version_uuid).strip()
    existing_row = get_library_row_by_version_uuid(connection, version_uuid)

    if existing_row is None:
        return _failure(
            operation=operation,
            result="not_found",
            code=ERR_VERSION_UUID_MISSING,
            message="No library row exists for this version_uuid.",
            version_uuid=version_uuid,
        )

    try:
        _execute_non_query(
            connection,
            f"""
            UPDATE {TABLE_NAME}
            SET status = ?, updated_at = ?
            WHERE version_uuid = ?
            """,
            ("deleted_soft", utc_now_iso(), version_uuid),
        )
        connection.commit()

        updated_row = get_library_row_by_version_uuid(connection, version_uuid)

        return OperationResult(
            success=True,
            operation=operation,
            result="deleted_soft",
            entity_type="library_row",
            entity_uuid=version_uuid,
            media_uuid=_string_or_none(existing_row.get("media_uuid")),
            version_uuid=version_uuid,
            data={
                "before": existing_row,
                "after": updated_row,
                "actor": actor,
            },
            warnings=[],
            errors=[],
        )

    except sqlite3.Error as exc:
        connection.rollback()
        return _failure(
            operation=operation,
            result="sqlite_error",
            code=ERR_DB_SCHEMA,
            message="SQLite error while soft-deleting a library row.",
            version_uuid=version_uuid,
            media_uuid=_string_or_none(existing_row.get("media_uuid")),
            data={"exception": str(exc), "actor": actor},
        )


def _build_where_clause(filters: dict[str, Any]) -> tuple[str, tuple[Any, ...]]:
    clauses: list[str] = []
    params: list[Any] = []

    for key, value in filters.items():
        if key not in _ALLOWED_FILTER_COLUMNS:
            continue

        if _is_blank(value):
            continue

        if isinstance(value, (list, tuple, set, frozenset)):
            values = [item for item in value if not _is_blank(item)]
            if not values:
                continue

            placeholders = ", ".join("?" for _ in values)
            clauses.append(f"{key} IN ({placeholders})")
            params.extend(values)
            continue

        clauses.append(f"{key} = ?")
        params.append(value)

    search_value = str(filters.get("search") or "").strip()
    if search_value:
        like_value = f"%{search_value}%"
        search_clauses = [f"{column} LIKE ?" for column in _SEARCH_COLUMNS]
        clauses.append(f"({' OR '.join(search_clauses)})")
        params.extend(like_value for _ in _SEARCH_COLUMNS)

    if not clauses:
        return "", ()

    return "WHERE " + " AND ".join(clauses), tuple(params)


def _filter_insert_columns(
    row_data: Mapping[str, Any],
    allowed_columns: set[str],
) -> tuple[dict[str, Any], list[str]]:
    insert_data: dict[str, Any] = {}
    ignored_columns: list[str] = []

    for key, value in row_data.items():
        if key == "id" or key not in allowed_columns:
            ignored_columns.append(key)
            continue

        insert_data[key] = value

    return insert_data, sorted(set(ignored_columns))


def _filter_update_columns(
    updates: Mapping[str, Any],
    allowed_columns: set[str],
) -> tuple[dict[str, Any], list[str]]:
    update_data: dict[str, Any] = {}
    ignored_columns: list[str] = []

    for key, value in updates.items():
        if key not in allowed_columns:
            ignored_columns.append(key)
            continue

        update_data[key] = value

    return update_data, sorted(set(ignored_columns))


def _get_table_columns(connection: sqlite3.Connection) -> set[str]:
    cursor = connection.execute(f"PRAGMA table_info({TABLE_NAME})")
    try:
        rows = cursor.fetchall()
    finally:
        cursor.close()

    columns: set[str] = set()
    for row in rows:
        if isinstance(row, sqlite3.Row):
            columns.add(str(row["name"]))
        else:
            columns.add(str(row[1]))

    if not columns:
        raise sqlite3.OperationalError(f"Table not found or has no columns: {TABLE_NAME}")

    return columns


def _execute_fetch_one_dict(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...],
) -> dict[str, Any] | None:
    cursor = connection.execute(sql, params)
    try:
        return _fetch_one_dict(cursor)
    finally:
        cursor.close()


def _execute_fetch_all_dicts(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...],
) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, params)
    try:
        return _fetch_all_dicts(cursor)
    finally:
        cursor.close()


def _execute_insert(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...],
) -> int:
    cursor = connection.execute(sql, params)
    try:
        return int(cursor.lastrowid)
    finally:
        cursor.close()


def _execute_non_query(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...],
) -> None:
    cursor = connection.execute(sql, params)
    try:
        return None
    finally:
        cursor.close()


def _fetch_one_dict(cursor: sqlite3.Cursor) -> dict[str, Any] | None:
    row = cursor.fetchone()
    if row is None:
        return None

    return _row_to_dict(cursor, row)


def _fetch_all_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [_row_to_dict(cursor, row) for row in cursor.fetchall()]


def _row_to_dict(cursor: sqlite3.Cursor, row: Any) -> dict[str, Any]:
    if isinstance(row, sqlite3.Row):
        return dict(row)

    column_names = [description[0] for description in cursor.description or []]
    return dict(zip(column_names, row, strict=False))


def _safe_order_by(value: Any) -> str:
    order_by = str(value or "updated_at")
    if order_by not in _SORT_COLUMNS:
        return "updated_at"
    return order_by


def _safe_order_dir(value: Any) -> str:
    order_dir = str(value or "desc").lower()
    if order_dir not in {"asc", "desc"}:
        return "DESC"
    return order_dir.upper()


def _safe_int(
    value: Any,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        return default

    return max(minimum, min(maximum, int_value))


def _is_blank(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, dict)):
        return len(list(value)) == 0

    return False


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _ignored_columns_warnings(
    ignored_columns: list[str],
    message: str,
) -> list[KoaMessage]:
    if not ignored_columns:
        return []

    return [
        KoaMessage(
            code=ERR_DB_SCHEMA,
            severity="warning",
            message=message,
            details={"ignored_columns": ignored_columns},
        )
    ]


def _failure(
    *,
    operation: str,
    result: str,
    code: str,
    message: str,
    version_uuid: str | None = None,
    media_uuid: str | None = None,
    data: dict[str, Any] | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        entity_type="library_row",
        entity_uuid=version_uuid,
        media_uuid=media_uuid,
        version_uuid=version_uuid,
        data=data or {},
        warnings=[],
        errors=[
            KoaMessage(
                code=code,
                severity="error",
                message=message,
                details=data or {},
            )
        ],
    )