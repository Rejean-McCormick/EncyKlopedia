# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/row_mapping_service.py

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from koa_mediatheque.models import FileFacts

try:
    from koa_mediatheque.constants import (
        LIBRARY_ROW_COLUMNS,
        JSON_ARRAY_FIELDS,
        SQLITE_JSON_TEXT_FIELDS,
        XLSX_PROTECTED_COLUMNS,
        TECHNICAL_PROTECTED_FIELDS,
    )
except ImportError:
    LIBRARY_ROW_COLUMNS: list[str] = [
        "id",
        "media_uuid",
        "version_uuid",
        "title",
        "subtitle",
        "description",
        "summary",
        "original_path",
        "storage_path",
        "filename",
        "extension",
        "mimetype",
        "filesize",
        "sha256",
        "filearea",
        "media_type",
        "language",
        "library_scope",
        "uckk_relevance",
        "target_system",
        "target_export_allowed",
        "public_state",
        "visibility",
        "access_level",
        "ownership_scope",
        "source_type",
        "source_ownership",
        "rights_status",
        "rights_note",
        "restriction_state",
        "restriction_reason",
        "redaction_required",
        "status",
        "provenance",
        "ai_validation_state",
        "ai_confidence",
        "canonical_validation_state",
        "human_review_required",
        "review_queue",
        "review_reason",
        "collections_json",
        "tags_json",
        "relations_json",
        "content_flags_json",
        "audience_suitability",
        "export_to_uckk",
        "export_to_public",
        "export_policy_note",
        "import_batch",
        "notes",
        "created_at",
        "updated_at",
    ]
    JSON_ARRAY_FIELDS: list[str] = [
        "collections",
        "tags",
        "relations",
        "content_flags",
    ]
    SQLITE_JSON_TEXT_FIELDS: list[str] = [
        "collections_json",
        "tags_json",
        "relations_json",
        "content_flags_json",
    ]
    XLSX_PROTECTED_COLUMNS: list[str] = [
        "media_uuid",
        "version_uuid",
        "filename",
        "original_path",
        "storage_path",
        "sha256",
        "filesize",
        "mimetype",
        "updated_at",
    ]
    TECHNICAL_PROTECTED_FIELDS: list[str] = [
        "sha256",
        "filesize",
        "mimetype",
        "filename",
        "extension",
        "original_path",
        "storage_path",
    ]

try:
    from koa_mediatheque.schema import utc_now_iso
except ImportError:

    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


_JSON_ARRAY_TO_SQLITE_FIELD = {
    "collections": "collections_json",
    "tags": "tags_json",
    "relations": "relations_json",
    "content_flags": "content_flags_json",
}

_SQLITE_FIELD_TO_JSON_ARRAY = {
    "collections_json": "collections",
    "tags_json": "tags",
    "relations_json": "relations",
    "content_flags_json": "content_flags",
}

_DEFAULT_LIBRARY_ROW_VALUES: dict[str, Any] = {
    "title": "Sans titre",
    "subtitle": None,
    "description": None,
    "summary": None,
    "filearea": "media_original",
    "media_type": "document",
    "language": "fr",
    "library_scope": "koa",
    "uckk_relevance": "unknown",
    "target_system": "none",
    "target_export_allowed": 0,
    "public_state": "unknown",
    "visibility": "private",
    "access_level": "private",
    "ownership_scope": "unknown",
    "source_type": "unknown",
    "source_ownership": "unknown_source",
    "rights_status": "unknown",
    "rights_note": None,
    "restriction_state": "none",
    "restriction_reason": None,
    "redaction_required": 0,
    "status": "active",
    "provenance": "ai_assisted",
    "ai_validation_state": "ai_uncertain",
    "ai_confidence": None,
    "canonical_validation_state": "unverified",
    "human_review_required": 0,
    "review_queue": None,
    "review_reason": None,
    "collections_json": "[]",
    "tags_json": "[]",
    "relations_json": "[]",
    "content_flags_json": "[]",
    "audience_suitability": "unknown",
    "export_to_uckk": "no",
    "export_to_public": "no",
    "export_policy_note": None,
    "import_batch": None,
    "notes": None,
}

_INTEGER_BOOL_FIELDS = {
    "target_export_allowed",
    "redaction_required",
    "human_review_required",
}

_INTEGER_FIELDS = {
    "filesize",
}

_FLOAT_FIELDS = {
    "ai_confidence",
}

_SYSTEM_COLUMNS = {
    "id",
    "created_at",
    "updated_at",
}

_XLSX_META_COLUMNS = {
    "action",
    "import_action",
    "_action",
    "_status",
    "_errors",
    "_warnings",
}


def metadata_to_library_row(
    metadata: dict[str, Any],
    file_facts: FileFacts,
    *,
    media_uuid: str | None = None,
    version_uuid: str | None = None,
    storage_path: str | None = None,
    filearea: str = "media_original",
    import_batch: str | None = None,
) -> dict[str, Any]:
    """
    Map validated ChatGPT metadata and local FileFacts into one library_rows dict.

    Technical facts always come from FileFacts and function arguments, never
    from ChatGPT metadata.
    """
    now = utc_now_iso()
    row: dict[str, Any] = {}

    for column in LIBRARY_ROW_COLUMNS:
        if column == "id":
            continue
        row[column] = _DEFAULT_LIBRARY_ROW_VALUES.get(column)

    row["media_uuid"] = _clean_string(media_uuid) or _clean_string(metadata.get("media_uuid")) or _new_uuid()
    row["version_uuid"] = _clean_string(version_uuid) or _new_uuid()

    row["original_path"] = str(file_facts.original_path)
    row["storage_path"] = _clean_string(storage_path)
    row["filename"] = file_facts.filename
    row["extension"] = file_facts.extension
    row["mimetype"] = file_facts.mimetype
    row["filesize"] = file_facts.filesize
    row["sha256"] = file_facts.sha256
    row["filearea"] = _clean_string(filearea) or "media_original"

    for key, value in metadata.items():
        if key in TECHNICAL_PROTECTED_FIELDS:
            continue
        if key in {"id", "created_at", "updated_at"}:
            continue
        if key in {"media_uuid", "version_uuid"}:
            continue
        if key in JSON_ARRAY_FIELDS:
            sqlite_field = _JSON_ARRAY_TO_SQLITE_FIELD.get(key)
            if sqlite_field:
                row[sqlite_field] = _json_dumps_array(value)
            continue
        if key in _JSON_ARRAY_TO_SQLITE_FIELD.values():
            row[key] = _json_dumps_array(value)
            continue
        if key in row:
            row[key] = _normalize_scalar_for_sqlite(key, value)

    row["import_batch"] = _clean_string(import_batch) or _clean_string(metadata.get("import_batch"))
    row["created_at"] = now
    row["updated_at"] = now

    _ensure_required_row_defaults(row)

    return _ordered_library_row(row)


def library_row_to_display_dict(row: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a SQLite library_rows dict into GUI-friendly display values.
    """
    display = dict(row)

    for sqlite_field, display_field in _SQLITE_FIELD_TO_JSON_ARRAY.items():
        display[display_field] = _json_text_to_list(row.get(sqlite_field))
        display[f"{display_field}_text"] = _json_text_to_semicolon_text(row.get(sqlite_field))

    for field_name in _INTEGER_BOOL_FIELDS:
        if field_name in display:
            display[field_name] = _normalize_int_bool(display[field_name])

    return display


def library_row_to_xlsx_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a SQLite library_rows dict into one XLSX Library sheet row.
    """
    xlsx_row: dict[str, Any] = {}

    for column in LIBRARY_ROW_COLUMNS:
        if column in SQLITE_JSON_TEXT_FIELDS:
            xlsx_row[column] = _json_text_to_semicolon_text(row.get(column))
            continue

        value = row.get(column)
        xlsx_row[column] = _normalize_value_for_xlsx(value)

    xlsx_row["action"] = "ignore"

    return xlsx_row


def xlsx_row_to_update_dict(row: dict[str, Any]) -> dict[str, Any]:
    """
    Convert one XLSX row into safe updates for library_rows.

    Protected technical columns and import-control columns are excluded.
    version_uuid remains the import key and is not updated here.
    """
    updates: dict[str, Any] = {}
    protected = set(XLSX_PROTECTED_COLUMNS) | set(TECHNICAL_PROTECTED_FIELDS) | _SYSTEM_COLUMNS

    for key, value in row.items():
        field_name = str(key).strip() if key is not None else ""
        if not field_name:
            continue
        if field_name in protected:
            continue
        if field_name in _XLSX_META_COLUMNS:
            continue
        if field_name not in LIBRARY_ROW_COLUMNS and field_name not in _SQLITE_FIELD_TO_JSON_ARRAY:
            continue

        if _is_missing_value(value):
            updates[field_name] = None
            continue

        if field_name in SQLITE_JSON_TEXT_FIELDS:
            updates[field_name] = _semicolon_text_to_json_array_text(value)
            continue

        if field_name in _JSON_ARRAY_TO_SQLITE_FIELD:
            sqlite_field = _JSON_ARRAY_TO_SQLITE_FIELD[field_name]
            updates[sqlite_field] = _semicolon_text_to_json_array_text(value)
            continue

        updates[field_name] = _normalize_scalar_for_sqlite(field_name, value)

    updates["updated_at"] = utc_now_iso()

    return updates


def _ordered_library_row(row: dict[str, Any]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}

    for column in LIBRARY_ROW_COLUMNS:
        if column == "id":
            continue
        if column in row:
            ordered[column] = row[column]

    for key, value in row.items():
        if key not in ordered and key != "id":
            ordered[key] = value

    return ordered


def _ensure_required_row_defaults(row: dict[str, Any]) -> None:
    if not _clean_string(row.get("title")):
        row["title"] = "Sans titre"

    if not _clean_string(row.get("media_uuid")):
        row["media_uuid"] = _new_uuid()

    if not _clean_string(row.get("version_uuid")):
        row["version_uuid"] = _new_uuid()

    for sqlite_field in SQLITE_JSON_TEXT_FIELDS:
        row[sqlite_field] = _json_dumps_array(row.get(sqlite_field))

    for field_name in _INTEGER_BOOL_FIELDS:
        row[field_name] = _normalize_int_bool(row.get(field_name))

    for field_name in _INTEGER_FIELDS:
        row[field_name] = _normalize_int_or_none(row.get(field_name))

    for field_name in _FLOAT_FIELDS:
        row[field_name] = _normalize_float_or_none(row.get(field_name))


def _normalize_scalar_for_sqlite(field_name: str, value: Any) -> Any:
    if field_name in _INTEGER_BOOL_FIELDS:
        return _normalize_int_bool(value)

    if field_name in _INTEGER_FIELDS:
        return _normalize_int_or_none(value)

    if field_name in _FLOAT_FIELDS:
        return _normalize_float_or_none(value)

    if isinstance(value, str):
        return _clean_string(value)

    if _is_missing_value(value):
        return None

    return value


def _normalize_value_for_xlsx(value: Any) -> Any:
    if _is_missing_value(value):
        return ""

    if isinstance(value, (list, tuple, set)):
        return _list_to_semicolon_text(value)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    return value


def _json_dumps_array(value: Any) -> str:
    if _is_missing_value(value):
        return "[]"

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return "[]"

        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        except json.JSONDecodeError:
            pass

        return json.dumps(_semicolon_text_to_list(stripped), ensure_ascii=False, sort_keys=True)

    if isinstance(value, list):
        return json.dumps(_clean_array(value), ensure_ascii=False, sort_keys=True)

    if isinstance(value, tuple | set):
        return json.dumps(_clean_array(list(value)), ensure_ascii=False, sort_keys=True)

    return json.dumps([value], ensure_ascii=False, sort_keys=True)


def _json_text_to_list(value: Any) -> list[Any]:
    if _is_missing_value(value):
        return []

    if isinstance(value, list):
        return _clean_array(value)

    if not isinstance(value, str):
        return [value]

    stripped = value.strip()
    if not stripped:
        return []

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return _semicolon_text_to_list(stripped)

    if isinstance(parsed, list):
        return _clean_array(parsed)

    return [parsed]


def _json_text_to_semicolon_text(value: Any) -> str:
    return _list_to_semicolon_text(_json_text_to_list(value))


def _semicolon_text_to_json_array_text(value: Any) -> str:
    return json.dumps(_semicolon_text_to_list(value), ensure_ascii=False, sort_keys=True)


def _semicolon_text_to_list(value: Any) -> list[Any]:
    if _is_missing_value(value):
        return []

    if isinstance(value, list):
        return _clean_array(value)

    if isinstance(value, tuple | set):
        return _clean_array(list(value))

    if not isinstance(value, str):
        return [value]

    stripped = value.strip()
    if not stripped:
        return []

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return _clean_array(parsed)
    except json.JSONDecodeError:
        pass

    return [
        item.strip()
        for item in stripped.split(";")
        if item.strip()
    ]


def _list_to_semicolon_text(value: list[Any] | tuple[Any, ...] | set[Any]) -> str:
    items: list[str] = []

    for item in value:
        if _is_missing_value(item):
            continue
        if isinstance(item, dict):
            items.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
        else:
            item_text = str(item).strip()
            if item_text:
                items.append(item_text)

    return "; ".join(items)


def _clean_array(value: list[Any]) -> list[Any]:
    cleaned: list[Any] = []

    for item in value:
        if _is_missing_value(item):
            continue
        if isinstance(item, str):
            stripped = item.strip()
            if stripped:
                cleaned.append(stripped)
            continue
        cleaned.append(item)

    return cleaned


def _normalize_int_bool(value: Any) -> int:
    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, int) and value in (0, 1):
        return value

    if isinstance(value, float) and value in (0.0, 1.0):
        return int(value)

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "oui", "y", "o"}:
            return 1
        if normalized in {"0", "false", "no", "non", "n"}:
            return 0

    return 0


def _normalize_int_or_none(value: Any) -> int | None:
    if _is_missing_value(value):
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if math.isnan(value):
            return None
        return int(value)

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(float(stripped.replace(",", ".")))
        except ValueError:
            return None

    return None


def _normalize_float_or_none(value: Any) -> float | None:
    if _is_missing_value(value):
        return None

    if isinstance(value, bool):
        return float(int(value))

    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped.replace(",", "."))
        except ValueError:
            return None

    return None


def _clean_string(value: Any) -> str | None:
    if _is_missing_value(value):
        return None

    text = str(value).strip()
    return text or None


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, float):
        return math.isnan(value)

    return False


def _new_uuid() -> str:
    return str(uuid4())