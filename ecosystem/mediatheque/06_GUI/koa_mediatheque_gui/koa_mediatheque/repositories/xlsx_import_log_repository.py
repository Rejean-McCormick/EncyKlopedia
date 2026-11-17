# 06_GUI/koa_mediatheque_gui/koa_mediatheque/repositories/xlsx_import_log_repository.py
"""Repository functions for the `xlsx_import_log` SQLite support table.

This module is intentionally thin:
- it receives an already-open sqlite3.Connection;
- it never closes the connection;
- it performs direct SQL operations only;
- it does not parse XLSX files;
- it does not validate import actions;
- it does not update `library_rows`.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from koa_mediatheque.errors import ERR_DB_SCHEMA, ERR_REQUIRED_FIELD
from koa_mediatheque.models import KoaMessage, OperationResult


TABLE_NAME = "xlsx_import_log"

_ALLOWED_COLUMNS: frozenset[str] = frozenset(
    {
        "id",
        "import_uuid",
        "xlsx_path",
        "mode",
        "row_number",
        "version_uuid",
        "result",
        "message",
        "changed_fields",
        "created_at",
    }
)

_INSERT_COLUMNS: tuple[str, ...] = (
    "import_uuid",
    "xlsx_path",
    "mode",
    "row_number",
    "version_uuid",
    "result",
    "message",
    "changed_fields",
    "created_at",
)

_REQUIRED_INSERT_FIELDS: tuple[str, ...] = (
    "import_uuid",
    "xlsx_path",
    "mode",
)


def insert_xlsx_import_log(
    connection: sqlite3.Connection,
    log_data: dict[str, Any],
) -> OperationResult:
    """Insert one XLSX import log row.

    Expected keys may include:
    - import_uuid
    - xlsx_path
    - mode
    - row_number
    - version_uuid
    - result
    - message
    - changed_fields
    - created_at

    `changed_fields` may be supplied as a string, list, tuple, set, or dict.
    Non-string values are serialized to JSON text.
    """
    operation = "insert_xlsx_import_log"

    if not isinstance(log_data, dict):
        return _failure(
            operation=operation,
            result="invalid_log_data",
            code=ERR_REQUIRED_FIELD,
            message="xlsx_import_log data must be a dictionary.",
            data={"received_type": type(log_data).__name__},
        )

    missing_fields = [
        field_name
        for field_name in _REQUIRED_INSERT_FIELDS
        if _is_blank(log_data.get(field_name))
    ]

    if missing_fields:
        return _failure(
            operation=operation,
            result="missing_required_fields",
            code=ERR_REQUIRED_FIELD,
            message="Required XLSX import log fields are missing.",
            data={"missing_fields": missing_fields},
        )

    insert_data = {
        key: _normalize_value(key, log_data.get(key))
        for key in _INSERT_COLUMNS
        if key in log_data and key in _ALLOWED_COLUMNS
    }

    ignored_columns = sorted(
        key
        for key in log_data
        if key not in _ALLOWED_COLUMNS or key == "id"
    )

    try:
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
        connection.commit()

        row_id = int(cursor.lastrowid)
        inserted_row = _get_xlsx_import_log_by_id(connection, row_id)

        warnings = []
        if ignored_columns:
            warnings.append(
                KoaMessage(
                    code=ERR_DB_SCHEMA,
                    severity="warning",
                    message="Some fields were ignored because they are not columns in xlsx_import_log.",
                    details={"ignored_columns": ignored_columns},
                )
            )

        import_uuid = _string_or_none(insert_data.get("import_uuid"))
        version_uuid = _string_or_none(insert_data.get("version_uuid"))

        return OperationResult(
            success=True,
            operation=operation,
            result="inserted",
            entity_type="xlsx_import",
            entity_uuid=import_uuid or str(row_id),
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
            message="SQLite error while inserting an XLSX import log row.",
            data={
                "exception": str(exc),
                "import_uuid": _string_or_none(log_data.get("import_uuid")),
                "xlsx_path": _string_or_none(log_data.get("xlsx_path")),
                "version_uuid": _string_or_none(log_data.get("version_uuid")),
            },
        )


def list_xlsx_import_log(
    connection: sqlite3.Connection,
    import_uuid: str | None = None,
) -> list[dict[str, Any]]:
    """Return XLSX import log rows.

    When `import_uuid` is supplied, rows are returned in import order.
    Otherwise, rows are returned newest first.
    """
    if _is_blank(import_uuid):
        cursor = connection.execute(
            f"""
            SELECT *
            FROM {TABLE_NAME}
            ORDER BY created_at DESC, id DESC
            """
        )
        return _fetch_all_dicts(cursor)

    cursor = connection.execute(
        f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE import_uuid = ?
        ORDER BY
            CASE WHEN row_number IS NULL THEN 1 ELSE 0 END ASC,
            row_number ASC,
            id ASC
        """,
        (str(import_uuid).strip(),),
    )
    return _fetch_all_dicts(cursor)


def _get_xlsx_import_log_by_id(
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


def _normalize_value(key: str, value: Any) -> Any:
    if value is None:
        return None

    if key == "changed_fields" and not isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    if key == "row_number":
        return _int_or_none(value)

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


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
        entity_type="xlsx_import",
        entity_uuid=_string_or_none(data.get("import_uuid")) if data else None,
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