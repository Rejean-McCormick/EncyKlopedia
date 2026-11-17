# 06_GUI/koa_mediatheque_gui/koa_mediatheque/repositories/chatgpt_intake_log_repository.py
"""Repository functions for the `chatgpt_intake_log` SQLite support table.

This module is intentionally thin:
- it receives an already-open sqlite3.Connection;
- it never closes the connection;
- it performs direct SQL operations only;
- it does not validate ChatGPT JSON;
- it does not calculate file facts;
- it does not integrate rows into `library_rows`.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from koa_mediatheque.errors import ERR_DB_SCHEMA, ERR_REQUIRED_FIELD
from koa_mediatheque.models import KoaMessage, OperationResult


TABLE_NAME = "chatgpt_intake_log"

_ALLOWED_COLUMNS: frozenset[str] = frozenset(
    {
        "id",
        "version_uuid",
        "file_path",
        "prompt_template",
        "raw_response",
        "parsed_json",
        "validation_status",
        "validation_errors",
        "created_at",
    }
)

_INSERT_COLUMNS: tuple[str, ...] = (
    "version_uuid",
    "file_path",
    "prompt_template",
    "raw_response",
    "parsed_json",
    "validation_status",
    "validation_errors",
    "created_at",
)

_LIST_FILTER_COLUMNS: frozenset[str] = frozenset(
    {
        "version_uuid",
        "file_path",
        "validation_status",
    }
)


def insert_chatgpt_intake_log(
    connection: sqlite3.Connection,
    log_data: dict[str, Any],
) -> OperationResult:
    """Insert one ChatGPT intake log row.

    Expected keys may include:
    - version_uuid
    - file_path
    - prompt_template
    - raw_response
    - parsed_json
    - validation_status
    - validation_errors
    - created_at

    `version_uuid` may be null when validation failed before a library row was
    built. At least one of `file_path`, `raw_response`, or `validation_status`
    must be present so the log is not empty.
    """
    operation = "insert_chatgpt_intake_log"

    if not isinstance(log_data, dict):
        return _failure(
            operation=operation,
            result="invalid_log_data",
            code=ERR_REQUIRED_FIELD,
            message="chatgpt_intake_log data must be a dictionary.",
            data={"received_type": type(log_data).__name__},
        )

    if (
        _is_blank(log_data.get("file_path"))
        and _is_blank(log_data.get("raw_response"))
        and _is_blank(log_data.get("validation_status"))
    ):
        return _failure(
            operation=operation,
            result="missing_log_content",
            code=ERR_REQUIRED_FIELD,
            message="At least one of file_path, raw_response, or validation_status is required.",
            data={"required_any": ["file_path", "raw_response", "validation_status"]},
        )

    insert_data = {
        key: _normalize_text_value(key, log_data.get(key))
        for key in _INSERT_COLUMNS
        if key in log_data and key in _ALLOWED_COLUMNS
    }

    ignored_columns = sorted(
        key
        for key in log_data
        if key not in _ALLOWED_COLUMNS or key == "id"
    )

    try:
        if insert_data:
            columns = list(insert_data.keys())
            column_sql = ", ".join(columns)
            placeholders = ", ".join("?" for _ in columns)

            cursor = connection.execute(
                f"""
                INSERT INTO {TABLE_NAME} ({column_sql})
                VALUES ({placeholders})
                """,
                tuple(insert_data[column] for column in columns),
            )
        else:
            cursor = connection.execute(
                f"""
                INSERT INTO {TABLE_NAME} DEFAULT VALUES
                """
            )

        connection.commit()

        row_id = int(cursor.lastrowid)
        inserted_row = _get_chatgpt_intake_log_by_id(connection, row_id)

        warnings = []
        if ignored_columns:
            warnings.append(
                KoaMessage(
                    code=ERR_DB_SCHEMA,
                    severity="warning",
                    message="Some fields were ignored because they are not columns in chatgpt_intake_log.",
                    details={"ignored_columns": ignored_columns},
                )
            )

        version_uuid = _string_or_none(insert_data.get("version_uuid"))

        return OperationResult(
            success=True,
            operation=operation,
            result="inserted",
            entity_type="chatgpt_intake",
            entity_uuid=version_uuid or str(row_id),
            version_uuid=version_uuid,
            data={
                "id": row_id,
                "row": inserted_row,
                "ignored_columns": ignored_columns,
            },
            warnings=warnings,
            errors=[],
        )

    except sqlite3.Error as exc:
        connection.rollback()
        return _failure(
            operation=operation,
            result="sqlite_error",
            code=ERR_DB_SCHEMA,
            message="SQLite error while inserting a ChatGPT intake log row.",
            data={
                "exception": str(exc),
                "version_uuid": _string_or_none(log_data.get("version_uuid")),
                "file_path": _string_or_none(log_data.get("file_path")),
            },
        )


def list_chatgpt_intake_log(
    connection: sqlite3.Connection,
    limit: int = 200,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return ChatGPT intake log rows ordered newest first.

    Supported filters:
    - version_uuid
    - file_path
    - validation_status

    Unknown filters are ignored.
    """
    filters = filters or {}
    where_sql, params = _build_where_clause(filters)
    safe_limit = _safe_int(limit, default=200, minimum=1, maximum=10000)

    cursor = connection.execute(
        f"""
        SELECT *
        FROM {TABLE_NAME}
        {where_sql}
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (*params, safe_limit),
    )
    return _fetch_all_dicts(cursor)


def _get_chatgpt_intake_log_by_id(
    connection: sqlite3.Connection,
    row_id: int,
) -> dict[str, Any] | None:
    cursor = connection.execute(
        f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE id = ?
        LIMIT 1
        """,
        (row_id,),
    )
    return _fetch_one_dict(cursor)


def _build_where_clause(filters: dict[str, Any]) -> tuple[str, tuple[Any, ...]]:
    clauses: list[str] = []
    params: list[Any] = []

    for key, value in filters.items():
        if key not in _LIST_FILTER_COLUMNS:
            continue

        if value is None or value == "":
            continue

        if isinstance(value, (list, tuple, set, frozenset)):
            values = [item for item in value if item is not None and item != ""]
            if not values:
                continue

            placeholders = ", ".join("?" for _ in values)
            clauses.append(f"{key} IN ({placeholders})")
            params.extend(values)
            continue

        clauses.append(f"{key} = ?")
        params.append(value)

    if not clauses:
        return "", ()

    return "WHERE " + " AND ".join(clauses), tuple(params)


def _normalize_text_value(key: str, value: Any) -> Any:
    if value is None:
        return None

    if key in {"parsed_json", "validation_errors"} and not isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    return value


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
    return value is None or str(value).strip() == ""


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


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
        entity_type="chatgpt_intake",
        entity_uuid=_string_or_none(data.get("version_uuid")) if data else None,
        version_uuid=_string_or_none(data.get("version_uuid")) if data else None,
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