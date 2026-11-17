"""
XLSX validation rules for Médiathèque kOA.

This module defines the controlled XLSX round-trip contract:

SQLite -> XLSX -> human edits -> import preview -> validated update -> SQLite

SQLite remains the source of truth. Deleting an XLSX row must not delete a
SQLite row. Protected technical fields cannot be overwritten from XLSX unless
explicit repair mode is used.
"""

from __future__ import annotations

from typing import Any
from typing import Final

from koa_mediatheque.constants import (
    JSON_TO_SQLITE_JSON_TEXT_FIELD_MAP,
    SQLITE_JSON_TEXT_TO_JSON_FIELD_MAP,
    TECHNICAL_PROTECTED_FIELDS,
    XLSX_ACTION_COLUMN,
    XLSX_ACTION_VALUES,
    XLSX_DEFAULT_ACTION,
    XLSX_IMPORT_MODES,
    XLSX_LIBRARY_COLUMNS,
    XLSX_PROTECTED_COLUMNS,
    XLSX_REQUIRED_SHEETS,
    XLSX_SHEET_IMPORT_REPORT,
    XLSX_SHEET_LIBRARY,
    XLSX_SHEET_LISTS,
)
from koa_mediatheque.validation.allowed_values import (
    normalize_allowed_value,
    validate_controlled_values,
)
from koa_mediatheque.validation.safety_defaults import (
    array_to_xlsx_text,
    normalize_array_value,
    xlsx_text_to_array,
)


SEVERITY_BLOCKING: Final[str] = "blocking"
SEVERITY_ERROR: Final[str] = "error"
SEVERITY_WARNING: Final[str] = "warning"
SEVERITY_INFO: Final[str] = "info"


# ---------------------------------------------------------------------------
# Rule codes
# ---------------------------------------------------------------------------

ERR_XLSX_MISSING_SHEET: Final[str] = "ERR_XLSX_MISSING_SHEET"
ERR_XLSX_MISSING_COLUMN: Final[str] = "ERR_XLSX_MISSING_COLUMN"
ERR_XLSX_UNKNOWN_COLUMN: Final[str] = "ERR_XLSX_UNKNOWN_COLUMN"
ERR_XLSX_INVALID_ACTION: Final[str] = "ERR_XLSX_INVALID_ACTION"
ERR_VERSION_UUID_MISSING: Final[str] = "ERR_VERSION_UUID_MISSING"
ERR_PROTECTED_FIELD_UPDATE: Final[str] = "ERR_PROTECTED_FIELD_UPDATE"
ERR_INVALID_ENUM: Final[str] = "ERR_INVALID_ENUM"
ERR_INVALID_TYPE: Final[str] = "ERR_INVALID_TYPE"
ERR_XLSX_INVALID_MODE: Final[str] = "ERR_XLSX_INVALID_MODE"

WARN_FIELD_NORMALIZED: Final[str] = "WARN_FIELD_NORMALIZED"
WARN_XLSX_EMPTY_ROW: Final[str] = "WARN_XLSX_EMPTY_ROW"
WARN_XLSX_IGNORED_COLUMN: Final[str] = "WARN_XLSX_IGNORED_COLUMN"


# ---------------------------------------------------------------------------
# XLSX import/export column groups
# ---------------------------------------------------------------------------

XLSX_IMPORT_REQUIRED_SHEETS: Final[tuple[str, ...]] = (
    XLSX_SHEET_LIBRARY,
)

XLSX_EXPORT_REQUIRED_SHEETS: Final[tuple[str, ...]] = XLSX_REQUIRED_SHEETS

XLSX_REQUIRED_LIBRARY_COLUMNS: Final[tuple[str, ...]] = (
    XLSX_ACTION_COLUMN,
    "version_uuid",
    "title",
)

XLSX_RECOMMENDED_LIBRARY_COLUMNS: Final[tuple[str, ...]] = XLSX_LIBRARY_COLUMNS

XLSX_ALLOWED_LIBRARY_COLUMNS: Final[tuple[str, ...]] = XLSX_LIBRARY_COLUMNS

XLSX_EDITABLE_COLUMNS: Final[tuple[str, ...]] = tuple(
    column
    for column in XLSX_LIBRARY_COLUMNS
    if column not in XLSX_PROTECTED_COLUMNS and column != XLSX_ACTION_COLUMN
)

XLSX_METADATA_MULTI_VALUE_COLUMNS: Final[tuple[str, ...]] = (
    "collections",
    "tags",
    "relations",
    "content_flags",
)

XLSX_ACTIONS_REQUIRING_VERSION_UUID: Final[tuple[str, ...]] = (
    "update",
    "archive",
)

XLSX_ACTIONS_ALLOWING_EMPTY_VERSION_UUID: Final[tuple[str, ...]] = (
    "ignore",
    "new",
)

XLSX_MODES_ALLOWING_PROTECTED_FIELD_UPDATES: Final[tuple[str, ...]] = (
    "repair",
)

XLSX_CHANGE_IGNORED_COLUMNS: Final[tuple[str, ...]] = (
    XLSX_ACTION_COLUMN,
)

XLSX_IMPORT_REPORT_COLUMNS: Final[tuple[str, ...]] = (
    "row_number",
    "version_uuid",
    "action",
    "result",
    "message",
    "changed_fields",
)

XLSX_LISTS_COLUMNS: Final[tuple[str, ...]] = (
    "field",
    "allowed_value",
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_xlsx_library_columns() -> tuple[str, ...]:
    """Return the canonical Library sheet columns."""
    return XLSX_LIBRARY_COLUMNS


def get_xlsx_required_sheets(*, for_import: bool = True) -> tuple[str, ...]:
    """Return required sheet names for import or full export workbooks."""
    if for_import:
        return XLSX_IMPORT_REQUIRED_SHEETS

    return XLSX_EXPORT_REQUIRED_SHEETS


def get_xlsx_required_library_columns() -> tuple[str, ...]:
    """Return columns that must exist in the Library sheet."""
    return XLSX_REQUIRED_LIBRARY_COLUMNS


def get_xlsx_editable_columns() -> tuple[str, ...]:
    """Return XLSX columns editable in normal mode."""
    return XLSX_EDITABLE_COLUMNS


def get_xlsx_protected_columns() -> tuple[str, ...]:
    """Return columns protected in normal XLSX import mode."""
    return XLSX_PROTECTED_COLUMNS


def get_xlsx_import_report_columns() -> tuple[str, ...]:
    """Return canonical Import_Report columns."""
    return XLSX_IMPORT_REPORT_COLUMNS


def get_xlsx_lists_columns() -> tuple[str, ...]:
    """Return canonical Lists sheet columns."""
    return XLSX_LISTS_COLUMNS


def normalize_xlsx_action(value: Any) -> str:
    """Normalize an XLSX row action."""
    if value is None:
        return XLSX_DEFAULT_ACTION

    normalized = str(value).strip().lower()

    if not normalized:
        return XLSX_DEFAULT_ACTION

    return normalized


def require_xlsx_action(value: Any) -> str:
    """Return a normalized valid XLSX action or raise ValueError."""
    action = normalize_xlsx_action(value)

    if action not in XLSX_ACTION_VALUES:
        allowed = ", ".join(XLSX_ACTION_VALUES)
        raise ValueError(f"Invalid XLSX action: {value!r}. Allowed: {allowed}")

    return action


def normalize_xlsx_import_mode(value: Any) -> str:
    """Normalize an XLSX import mode."""
    if value is None:
        return "normal"

    normalized = str(value).strip().lower()

    if not normalized:
        return "normal"

    return normalized


def require_xlsx_import_mode(value: Any) -> str:
    """Return a normalized valid XLSX import mode or raise ValueError."""
    mode = normalize_xlsx_import_mode(value)

    if mode not in XLSX_IMPORT_MODES:
        allowed = ", ".join(XLSX_IMPORT_MODES)
        raise ValueError(f"Invalid XLSX import mode: {value!r}. Allowed: {allowed}")

    return mode


def is_xlsx_protected_column(column_name: str) -> bool:
    """Return True if a column is protected in normal XLSX import mode."""
    return column_name in XLSX_PROTECTED_COLUMNS


def is_xlsx_editable_column(column_name: str) -> bool:
    """Return True if a column may be edited in normal XLSX import mode."""
    return column_name in XLSX_EDITABLE_COLUMNS


def is_xlsx_known_column(column_name: str) -> bool:
    """Return True if a column belongs to the canonical Library sheet."""
    return column_name in XLSX_ALLOWED_LIBRARY_COLUMNS


def validate_xlsx_workbook_shape(
    sheet_names: list[str] | tuple[str, ...],
    *,
    for_import: bool = True,
) -> dict[str, Any]:
    """
    Validate workbook-level sheet presence.

    This function accepts sheet names only, so it remains independent of
    openpyxl/pandas.
    """
    required_sheets = get_xlsx_required_sheets(for_import=for_import)
    messages: list[dict[str, Any]] = []

    for sheet_name in required_sheets:
        if sheet_name not in sheet_names:
            messages.append(
                make_xlsx_message(
                    code=ERR_XLSX_MISSING_SHEET,
                    severity=SEVERITY_BLOCKING,
                    message=f"Missing required XLSX sheet: {sheet_name}",
                    details={
                        "sheet": sheet_name,
                        "required_sheets": list(required_sheets),
                    },
                )
            )

    return {
        "is_valid": not has_blocking_messages(messages),
        "is_blocked": has_blocking_messages(messages),
        "messages": messages,
    }


def validate_xlsx_library_columns(
    columns: list[str] | tuple[str, ...],
    *,
    strict_unknown_columns: bool = False,
) -> dict[str, Any]:
    """
    Validate Library sheet columns.

    Missing required columns are blocking. Unknown columns are warnings by
    default, or blocking when strict_unknown_columns=True.
    """
    normalized_columns = tuple(str(column).strip() for column in columns)
    messages: list[dict[str, Any]] = []

    for column_name in XLSX_REQUIRED_LIBRARY_COLUMNS:
        if column_name not in normalized_columns:
            messages.append(
                make_xlsx_message(
                    code=ERR_XLSX_MISSING_COLUMN,
                    severity=SEVERITY_BLOCKING,
                    field=column_name,
                    message=f"Missing required Library column: {column_name}",
                    details={
                        "column": column_name,
                        "required_columns": list(XLSX_REQUIRED_LIBRARY_COLUMNS),
                    },
                )
            )

    for column_name in normalized_columns:
        if column_name and column_name not in XLSX_ALLOWED_LIBRARY_COLUMNS:
            messages.append(
                make_xlsx_message(
                    code=ERR_XLSX_UNKNOWN_COLUMN,
                    severity=(
                        SEVERITY_BLOCKING
                        if strict_unknown_columns
                        else SEVERITY_WARNING
                    ),
                    field=column_name,
                    message=f"Unknown Library column: {column_name}",
                    details={
                        "column": column_name,
                        "known_columns": list(XLSX_ALLOWED_LIBRARY_COLUMNS),
                    },
                )
            )

    return {
        "is_valid": not any(
            message["severity"] in {SEVERITY_BLOCKING, SEVERITY_ERROR}
            for message in messages
        ),
        "is_blocked": has_blocking_messages(messages),
        "messages": messages,
        "normalized_columns": normalized_columns,
    }


def normalize_xlsx_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a raw XLSX row dictionary.

    - trims column names
    - normalizes action
    - normalizes controlled values
    - converts semicolon multi-value text to arrays for metadata processing
    """
    normalized: dict[str, Any] = {}

    for key, value in row.items():
        column_name = str(key).strip()
        if not column_name:
            continue

        normalized[column_name] = _normalize_cell_value(value)

    normalized[XLSX_ACTION_COLUMN] = normalize_xlsx_action(
        normalized.get(XLSX_ACTION_COLUMN)
    )

    for column_name in XLSX_METADATA_MULTI_VALUE_COLUMNS:
        if column_name in normalized:
            normalized[column_name] = xlsx_text_to_array(normalized[column_name])

    for field_name in tuple(normalized.keys()):
        normalized[field_name] = normalize_allowed_value(
            field_name,
            normalized[field_name],
        )

    return normalized


def validate_xlsx_row(
    row: dict[str, Any],
    *,
    row_number: int | None = None,
    mode: str = "normal",
) -> dict[str, Any]:
    """
    Validate one normalized or raw XLSX Library row without database comparison.

    This validates shape, action, version_uuid requirements, controlled values,
    and basic type rules. Protected-field comparison requires the original row
    and is handled by detect_protected_field_changes().
    """
    normalized_mode = normalize_xlsx_import_mode(mode)
    normalized_row = normalize_xlsx_row(row)
    messages: list[dict[str, Any]] = []

    if normalized_mode not in XLSX_IMPORT_MODES:
        messages.append(
            make_xlsx_message(
                code=ERR_XLSX_INVALID_MODE,
                severity=SEVERITY_BLOCKING,
                row_number=row_number,
                message=f"Invalid XLSX import mode: {mode!r}",
                details={
                    "mode": mode,
                    "allowed": list(XLSX_IMPORT_MODES),
                },
            )
        )

    if is_empty_xlsx_row(normalized_row):
        messages.append(
            make_xlsx_message(
                code=WARN_XLSX_EMPTY_ROW,
                severity=SEVERITY_WARNING,
                row_number=row_number,
                message="XLSX row is empty and will be ignored.",
            )
        )
        return {
            "is_valid": True,
            "is_blocked": False,
            "messages": messages,
            "normalized_row": normalized_row,
        }

    action = normalized_row.get(XLSX_ACTION_COLUMN, XLSX_DEFAULT_ACTION)
    if action not in XLSX_ACTION_VALUES:
        messages.append(
            make_xlsx_message(
                code=ERR_XLSX_INVALID_ACTION,
                severity=SEVERITY_BLOCKING,
                field=XLSX_ACTION_COLUMN,
                row_number=row_number,
                message=f"Invalid XLSX action: {action!r}",
                details={
                    "value": action,
                    "allowed": list(XLSX_ACTION_VALUES),
                },
            )
        )

    if action in XLSX_ACTIONS_REQUIRING_VERSION_UUID and not str(
        normalized_row.get("version_uuid") or ""
    ).strip():
        messages.append(
            make_xlsx_message(
                code=ERR_VERSION_UUID_MISSING,
                severity=SEVERITY_BLOCKING,
                field="version_uuid",
                row_number=row_number,
                message=f"version_uuid is required for action {action!r}.",
                details={"action": action},
            )
        )

    messages.extend(
        _controlled_value_messages(
            normalized_row,
            row_number=row_number,
        )
    )

    messages.extend(
        _type_messages(
            normalized_row,
            row_number=row_number,
        )
    )

    return {
        "is_valid": not any(
            message["severity"] in {SEVERITY_BLOCKING, SEVERITY_ERROR}
            for message in messages
        ),
        "is_blocked": has_blocking_messages(messages),
        "messages": messages,
        "normalized_row": normalized_row,
    }


def validate_xlsx_rows(
    rows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    mode: str = "normal",
    first_data_row_number: int = 2,
) -> dict[str, Any]:
    """Validate multiple XLSX Library rows."""
    row_results: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []

    for index, row in enumerate(rows):
        row_number = first_data_row_number + index
        result = validate_xlsx_row(row, row_number=row_number, mode=mode)
        row_results.append(result)
        messages.extend(result["messages"])

    return {
        "is_valid": not any(
            message["severity"] in {SEVERITY_BLOCKING, SEVERITY_ERROR}
            for message in messages
        ),
        "is_blocked": has_blocking_messages(messages),
        "messages": messages,
        "row_results": row_results,
    }


def detect_protected_field_changes(
    original_row: dict[str, Any],
    imported_row: dict[str, Any],
    *,
    mode: str = "normal",
    row_number: int | None = None,
) -> dict[str, Any]:
    """
    Detect protected-field updates from XLSX.

    In normal and dry_run modes, protected-field changes are blocking.
    In repair mode, protected-field changes are allowed but still reported.
    """
    normalized_mode = normalize_xlsx_import_mode(mode)
    original = normalize_xlsx_row(original_row)
    imported = normalize_xlsx_row(imported_row)

    changed_fields: list[str] = []
    messages: list[dict[str, Any]] = []

    for column_name in XLSX_PROTECTED_COLUMNS:
        if column_name not in imported:
            continue

        original_value = _normalize_compare_value(original.get(column_name))
        imported_value = _normalize_compare_value(imported.get(column_name))

        if original_value != imported_value:
            changed_fields.append(column_name)

    if changed_fields:
        severity = (
            SEVERITY_WARNING
            if normalized_mode in XLSX_MODES_ALLOWING_PROTECTED_FIELD_UPDATES
            else SEVERITY_BLOCKING
        )

        messages.append(
            make_xlsx_message(
                code=ERR_PROTECTED_FIELD_UPDATE,
                severity=severity,
                row_number=row_number,
                message=(
                    "XLSX row attempts to modify protected technical fields."
                    if severity == SEVERITY_BLOCKING
                    else "Repair mode allows protected technical field updates."
                ),
                details={
                    "changed_fields": changed_fields,
                    "mode": normalized_mode,
                    "protected_columns": list(XLSX_PROTECTED_COLUMNS),
                },
            )
        )

    return {
        "is_allowed": not has_blocking_messages(messages),
        "changed_fields": changed_fields,
        "messages": messages,
    }


def build_xlsx_update_dict(
    imported_row: dict[str, Any],
    *,
    mode: str = "normal",
) -> dict[str, Any]:
    """
    Build an update dictionary from an imported XLSX row.

    In normal and dry_run mode, protected columns and action are removed.
    In repair mode, protected columns are kept.
    """
    normalized_mode = normalize_xlsx_import_mode(mode)
    normalized = normalize_xlsx_row(imported_row)

    excluded_columns = set(XLSX_CHANGE_IGNORED_COLUMNS)

    if normalized_mode not in XLSX_MODES_ALLOWING_PROTECTED_FIELD_UPDATES:
        excluded_columns.update(XLSX_PROTECTED_COLUMNS)
        excluded_columns.update(TECHNICAL_PROTECTED_FIELDS)

    update_dict = {
        column_name: value
        for column_name, value in normalized.items()
        if column_name not in excluded_columns
        and column_name in XLSX_ALLOWED_LIBRARY_COLUMNS
    }

    return convert_xlsx_multivalue_columns_to_sqlite_json_fields(update_dict)


def convert_xlsx_multivalue_columns_to_sqlite_json_fields(
    row: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert XLSX multi-value fields to SQLite JSON text field names.

    collections -> collections_json
    tags -> tags_json
    relations -> relations_json
    content_flags -> content_flags_json
    """
    converted = dict(row)

    for xlsx_field, sqlite_field in JSON_TO_SQLITE_JSON_TEXT_FIELD_MAP.items():
        if xlsx_field not in converted:
            continue

        converted[sqlite_field] = _json_array_text_from_xlsx_value(
            converted.pop(xlsx_field)
        )

    return converted


def convert_sqlite_json_fields_to_xlsx_multivalue_columns(
    row: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert SQLite JSON text multi-value fields to XLSX semicolon text columns.
    """
    converted = dict(row)

    for sqlite_field, xlsx_field in SQLITE_JSON_TEXT_TO_JSON_FIELD_MAP.items():
        if sqlite_field not in converted:
            continue

        converted[xlsx_field] = array_to_xlsx_text(converted.pop(sqlite_field))

    return converted


def is_empty_xlsx_row(row: dict[str, Any]) -> bool:
    """Return True when a row has no meaningful data."""
    for key, value in row.items():
        if key == XLSX_ACTION_COLUMN and normalize_xlsx_action(value) == XLSX_DEFAULT_ACTION:
            continue

        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        if isinstance(value, list | tuple | set) and not value:
            continue

        return False

    return True


def is_ignore_row(row: dict[str, Any]) -> bool:
    """Return True when row action is ignore."""
    return normalize_xlsx_action(row.get(XLSX_ACTION_COLUMN)) == "ignore"


def is_new_row(row: dict[str, Any]) -> bool:
    """Return True when row action is new."""
    return normalize_xlsx_action(row.get(XLSX_ACTION_COLUMN)) == "new"


def is_archive_row(row: dict[str, Any]) -> bool:
    """Return True when row action is archive."""
    return normalize_xlsx_action(row.get(XLSX_ACTION_COLUMN)) == "archive"


def is_update_row(row: dict[str, Any]) -> bool:
    """Return True when row action is update."""
    return normalize_xlsx_action(row.get(XLSX_ACTION_COLUMN)) == "update"


def summarize_xlsx_actions(
    rows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> dict[str, int]:
    """Return counts by XLSX action."""
    summary = {action: 0 for action in XLSX_ACTION_VALUES}

    for row in rows:
        action = normalize_xlsx_action(row.get(XLSX_ACTION_COLUMN))
        if action in summary:
            summary[action] += 1

    return summary


def make_xlsx_message(
    *,
    code: str,
    severity: str,
    message: str,
    field: str | None = None,
    row_number: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standard XLSX validation message dictionary."""
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "field": field,
        "row_number": row_number,
        "details": details or {},
    }


def has_blocking_messages(messages: list[dict[str, Any]]) -> bool:
    """Return True if any message is blocking."""
    return any(message.get("severity") == SEVERITY_BLOCKING for message in messages)


def has_error_messages(messages: list[dict[str, Any]]) -> bool:
    """Return True if any message is error or blocking."""
    return any(
        message.get("severity") in {SEVERITY_ERROR, SEVERITY_BLOCKING}
        for message in messages
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _controlled_value_messages(
    row: dict[str, Any],
    *,
    row_number: int | None = None,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    errors = validate_controlled_values(row)

    for field_name, error_message in errors.items():
        messages.append(
            make_xlsx_message(
                code=ERR_INVALID_ENUM,
                severity=SEVERITY_BLOCKING,
                field=field_name,
                row_number=row_number,
                message=error_message,
                details={
                    "field": field_name,
                    "value": row.get(field_name),
                },
            )
        )

    return messages


def _type_messages(
    row: dict[str, Any],
    *,
    row_number: int | None = None,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []

    integer_fields = (
        "target_export_allowed",
        "redaction_required",
        "human_review_required",
        "filesize",
    )

    for field_name in integer_fields:
        if field_name not in row or row[field_name] in (None, ""):
            continue

        if not _can_parse_int(row[field_name]):
            messages.append(
                make_xlsx_message(
                    code=ERR_INVALID_TYPE,
                    severity=SEVERITY_BLOCKING,
                    field=field_name,
                    row_number=row_number,
                    message=f"{field_name} must be an integer-compatible value.",
                    details={
                        "field": field_name,
                        "value": row[field_name],
                    },
                )
            )

    if "ai_confidence" in row and row["ai_confidence"] not in (None, ""):
        if not _can_parse_float(row["ai_confidence"]):
            messages.append(
                make_xlsx_message(
                    code=ERR_INVALID_TYPE,
                    severity=SEVERITY_BLOCKING,
                    field="ai_confidence",
                    row_number=row_number,
                    message="ai_confidence must be a number between 0 and 1.",
                    details={"value": row["ai_confidence"]},
                )
            )
        else:
            value = float(row["ai_confidence"])
            if value < 0 or value > 1:
                messages.append(
                    make_xlsx_message(
                        code=ERR_INVALID_TYPE,
                        severity=SEVERITY_BLOCKING,
                        field="ai_confidence",
                        row_number=row_number,
                        message="ai_confidence must be between 0 and 1.",
                        details={"value": row["ai_confidence"]},
                    )
                )

    return messages


def _normalize_cell_value(value: Any) -> Any:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return value


def _normalize_compare_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, list | tuple):
        return "; ".join(str(item).strip() for item in value if str(item).strip())

    return str(value).strip()


def _json_array_text_from_xlsx_value(value: Any) -> str:
    import json

    normalized_array = normalize_array_value(value)
    return json.dumps(normalized_array, ensure_ascii=False, sort_keys=True)


def _can_parse_int(value: Any) -> bool:
    try:
        int(value)
    except (TypeError, ValueError):
        return False

    return True


def _can_parse_float(value: Any) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False

    return True


__all__ = [
    "ERR_INVALID_ENUM",
    "ERR_INVALID_TYPE",
    "ERR_PROTECTED_FIELD_UPDATE",
    "ERR_VERSION_UUID_MISSING",
    "ERR_XLSX_INVALID_ACTION",
    "ERR_XLSX_INVALID_MODE",
    "ERR_XLSX_MISSING_COLUMN",
    "ERR_XLSX_MISSING_SHEET",
    "ERR_XLSX_UNKNOWN_COLUMN",
    "SEVERITY_BLOCKING",
    "SEVERITY_ERROR",
    "SEVERITY_INFO",
    "SEVERITY_WARNING",
    "WARN_FIELD_NORMALIZED",
    "WARN_XLSX_EMPTY_ROW",
    "WARN_XLSX_IGNORED_COLUMN",
    "XLSX_ACTIONS_ALLOWING_EMPTY_VERSION_UUID",
    "XLSX_ACTIONS_REQUIRING_VERSION_UUID",
    "XLSX_ALLOWED_LIBRARY_COLUMNS",
    "XLSX_CHANGE_IGNORED_COLUMNS",
    "XLSX_EDITABLE_COLUMNS",
    "XLSX_EXPORT_REQUIRED_SHEETS",
    "XLSX_IMPORT_REPORT_COLUMNS",
    "XLSX_IMPORT_REQUIRED_SHEETS",
    "XLSX_LISTS_COLUMNS",
    "XLSX_METADATA_MULTI_VALUE_COLUMNS",
    "XLSX_MODES_ALLOWING_PROTECTED_FIELD_UPDATES",
    "XLSX_RECOMMENDED_LIBRARY_COLUMNS",
    "XLSX_REQUIRED_LIBRARY_COLUMNS",
    "build_xlsx_update_dict",
    "convert_sqlite_json_fields_to_xlsx_multivalue_columns",
    "convert_xlsx_multivalue_columns_to_sqlite_json_fields",
    "detect_protected_field_changes",
    "get_xlsx_editable_columns",
    "get_xlsx_import_report_columns",
    "get_xlsx_library_columns",
    "get_xlsx_lists_columns",
    "get_xlsx_protected_columns",
    "get_xlsx_required_library_columns",
    "get_xlsx_required_sheets",
    "has_blocking_messages",
    "has_error_messages",
    "is_archive_row",
    "is_empty_xlsx_row",
    "is_ignore_row",
    "is_new_row",
    "is_update_row",
    "is_xlsx_editable_column",
    "is_xlsx_known_column",
    "is_xlsx_protected_column",
    "make_xlsx_message",
    "normalize_xlsx_action",
    "normalize_xlsx_import_mode",
    "normalize_xlsx_row",
    "require_xlsx_action",
    "require_xlsx_import_mode",
    "summarize_xlsx_actions",
    "validate_xlsx_library_columns",
    "validate_xlsx_row",
    "validate_xlsx_rows",
    "validate_xlsx_workbook_shape",
]

