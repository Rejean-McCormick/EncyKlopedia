# 06_GUI/koa_mediatheque_gui/koa_mediatheque/repositories/schema_meta_repository.py
"""Repository functions for the `schema_meta` SQLite support table.

This module is intentionally thin:
- it receives an already-open sqlite3.Connection;
- it never closes the connection;
- it performs direct SQL operations only;
- it does not apply migrations;
- it does not inspect schema files;
- it does not own database initialization.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from koa_mediatheque.errors import ERR_DB_SCHEMA, ERR_REQUIRED_FIELD
from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.schema import utc_now_iso


TABLE_NAME = "schema_meta"


def get_schema_meta(
    connection: sqlite3.Connection,
    key: str,
) -> str | None:
    """Return a schema metadata value by key.

    Returns None when the key is absent.
    """
    if _is_blank(key):
        return None

    cursor = connection.execute(
        f"""
        SELECT value
        FROM {TABLE_NAME}
        WHERE key = ?
        LIMIT 1
        """,
        (key,),
    )
    row = cursor.fetchone()

    if row is None:
        return None

    if isinstance(row, sqlite3.Row):
        return str(row["value"])

    return str(row[0])


def set_schema_meta(
    connection: sqlite3.Connection,
    key: str,
    value: str,
) -> OperationResult:
    """Insert or update one schema metadata key/value pair."""
    operation = "set_schema_meta"

    if _is_blank(key):
        return _failure(
            operation=operation,
            result="missing_key",
            code=ERR_REQUIRED_FIELD,
            message="schema_meta key is required.",
            data={"field": "key"},
        )

    if value is None:
        return _failure(
            operation=operation,
            result="missing_value",
            code=ERR_REQUIRED_FIELD,
            message="schema_meta value is required.",
            data={"field": "value", "key": key},
        )

    normalized_key = str(key).strip()
    normalized_value = str(value)
    now = utc_now_iso()

    try:
        before = _get_schema_meta_row(connection, normalized_key)

        if before is None:
            connection.execute(
                f"""
                INSERT INTO {TABLE_NAME} (key, value, updated_at)
                VALUES (?, ?, ?)
                """,
                (normalized_key, normalized_value, now),
            )
            result = "inserted"
        else:
            connection.execute(
                f"""
                UPDATE {TABLE_NAME}
                SET value = ?,
                    updated_at = ?
                WHERE key = ?
                """,
                (normalized_value, now, normalized_key),
            )
            result = "updated"

        connection.commit()

        after = _get_schema_meta_row(connection, normalized_key)

        return OperationResult(
            success=True,
            operation=operation,
            result=result,
            entity_type="schema_meta",
            entity_uuid=normalized_key,
            data={
                "key": normalized_key,
                "before": before,
                "after": after,
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
            message="SQLite error while writing schema metadata.",
            data={
                "key": normalized_key,
                "exception": str(exc),
            },
        )


def list_schema_meta(
    connection: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Return all schema metadata rows as dictionaries."""
    cursor = connection.execute(
        f"""
        SELECT key, value, updated_at
        FROM {TABLE_NAME}
        ORDER BY key ASC
        """
    )
    return _fetch_all_dicts(cursor)


def _get_schema_meta_row(
    connection: sqlite3.Connection,
    key: str,
) -> dict[str, Any] | None:
    cursor = connection.execute(
        f"""
        SELECT key, value, updated_at
        FROM {TABLE_NAME}
        WHERE key = ?
        LIMIT 1
        """,
        (key,),
    )
    return _fetch_one_dict(cursor)


def _fetch_one_dict(cursor: sqlite3.Cursor) -> dict[str, Any] | None:
    row = cursor.fetchone()
    if row is None:
        return None

    return _row_to_dict(cursor, row)


def _fetch_all_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    return [_row_to_dict(cursor, row) for row in rows]


def _row_to_dict(cursor: sqlite3.Cursor, row: Any) -> dict[str, Any]:
    if isinstance(row, sqlite3.Row):
        return dict(row)

    column_names = [description[0] for description in cursor.description or []]
    return dict(zip(column_names, row, strict=False))


def _is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _failure(
    *,
    operation: str,
    result: str,
    code: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        entity_type="schema_meta",
        entity_uuid=str(data.get("key")) if data and data.get("key") else None,
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