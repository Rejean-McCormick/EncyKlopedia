"""
Safe default values for Médiathèque kOA.

These defaults are intentionally conservative:

- private by default
- non-exportable by default
- canonical validation unverified by default
- AI validation uncertain by default
- unknown source/rights trigger human review
- multi-value fields default to empty arrays

This module does not validate JSON structure. It provides safe values used by
JSON intake, XLSX import normalization, row mapping, UI forms, and tests.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any
from typing import Final

from koa_mediatheque.constants import (
    DEFAULT_ACCESS_LEVEL,
    DEFAULT_AI_VALIDATION_STATE,
    DEFAULT_AUDIENCE_SUITABILITY,
    DEFAULT_CANONICAL_VALIDATION_STATE,
    DEFAULT_EXPORT_TO_PUBLIC,
    DEFAULT_EXPORT_TO_UCKK,
    DEFAULT_FILEAREA,
    DEFAULT_HUMAN_REVIEW_REQUIRED,
    DEFAULT_JSON_ARRAY_TEXT,
    DEFAULT_LANGUAGE,
    DEFAULT_LIBRARY_SCOPE,
    DEFAULT_MEDIA_TYPE,
    DEFAULT_OWNERSHIP_SCOPE,
    DEFAULT_PROVENANCE,
    DEFAULT_PUBLIC_STATE,
    DEFAULT_REDACTION_REQUIRED,
    DEFAULT_RESTRICTION_STATE,
    DEFAULT_RIGHTS_STATUS,
    DEFAULT_SOURCE_OWNERSHIP,
    DEFAULT_SOURCE_TYPE,
    DEFAULT_STATUS,
    DEFAULT_TARGET_EXPORT_ALLOWED,
    DEFAULT_TARGET_SYSTEM,
    DEFAULT_UCKK_RELEVANCE,
    DEFAULT_VISIBILITY,
    JSON_ARRAY_FIELDS,
    SQLITE_JSON_TEXT_FIELDS,
)


# ---------------------------------------------------------------------------
# Safe scalar defaults for user/AI-provided metadata
# ---------------------------------------------------------------------------

SAFE_METADATA_DEFAULTS: Final[dict[str, Any]] = {
    "title": "",
    "subtitle": "",
    "description": "",
    "summary": "",
    "media_type": DEFAULT_MEDIA_TYPE,
    "language": DEFAULT_LANGUAGE,
    "library_scope": DEFAULT_LIBRARY_SCOPE,
    "uckk_relevance": DEFAULT_UCKK_RELEVANCE,
    "target_system": DEFAULT_TARGET_SYSTEM,
    "target_export_allowed": DEFAULT_TARGET_EXPORT_ALLOWED,
    "public_state": DEFAULT_PUBLIC_STATE,
    "visibility": DEFAULT_VISIBILITY,
    "access_level": DEFAULT_ACCESS_LEVEL,
    "ownership_scope": DEFAULT_OWNERSHIP_SCOPE,
    "source_type": DEFAULT_SOURCE_TYPE,
    "source_ownership": DEFAULT_SOURCE_OWNERSHIP,
    "rights_status": DEFAULT_RIGHTS_STATUS,
    "rights_note": "",
    "restriction_state": DEFAULT_RESTRICTION_STATE,
    "restriction_reason": "",
    "redaction_required": DEFAULT_REDACTION_REQUIRED,
    "status": DEFAULT_STATUS,
    "provenance": DEFAULT_PROVENANCE,
    "ai_validation_state": DEFAULT_AI_VALIDATION_STATE,
    "ai_confidence": None,
    "canonical_validation_state": DEFAULT_CANONICAL_VALIDATION_STATE,
    "human_review_required": DEFAULT_HUMAN_REVIEW_REQUIRED,
    "review_queue": "",
    "review_reason": "",
    "audience_suitability": DEFAULT_AUDIENCE_SUITABILITY,
    "export_to_uckk": DEFAULT_EXPORT_TO_UCKK,
    "export_to_public": DEFAULT_EXPORT_TO_PUBLIC,
    "export_policy_note": "",
    "notes": "",
}

SAFE_ARRAY_DEFAULTS: Final[dict[str, list[Any]]] = {
    "collections": [],
    "tags": [],
    "relations": [],
    "content_flags": [],
}

SAFE_SQLITE_JSON_TEXT_DEFAULTS: Final[dict[str, str]] = {
    "collections_json": DEFAULT_JSON_ARRAY_TEXT,
    "tags_json": DEFAULT_JSON_ARRAY_TEXT,
    "relations_json": DEFAULT_JSON_ARRAY_TEXT,
    "content_flags_json": DEFAULT_JSON_ARRAY_TEXT,
}


# ---------------------------------------------------------------------------
# Safe defaults for app-enriched library_rows fields
# ---------------------------------------------------------------------------

SAFE_FILE_FACT_DEFAULTS: Final[dict[str, Any]] = {
    "original_path": "",
    "storage_path": "",
    "filename": "",
    "extension": "",
    "mimetype": None,
    "filesize": None,
    "sha256": None,
    "filearea": DEFAULT_FILEAREA,
}

SAFE_IDENTIFIER_DEFAULTS: Final[dict[str, Any]] = {
    "media_uuid": "",
    "version_uuid": "",
    "import_batch": "",
}

SAFE_AUDIT_FIELD_DEFAULTS: Final[dict[str, Any]] = {
    "created_at": "",
    "updated_at": "",
}


SAFE_LIBRARY_ROW_DEFAULTS: Final[dict[str, Any]] = {
    **SAFE_IDENTIFIER_DEFAULTS,
    **SAFE_METADATA_DEFAULTS,
    **SAFE_FILE_FACT_DEFAULTS,
    **SAFE_SQLITE_JSON_TEXT_DEFAULTS,
    **SAFE_AUDIT_FIELD_DEFAULTS,
}


# ---------------------------------------------------------------------------
# Review defaults
# ---------------------------------------------------------------------------

UNKNOWN_SOURCE_RIGHTS_FIELDS: Final[tuple[str, ...]] = (
    "source_type",
    "source_ownership",
    "rights_status",
    "ownership_scope",
)

REVIEW_REQUIRED_DEFAULT_REASONS: Final[dict[str, str]] = {
    "source_type": "source_type is unknown or requires review",
    "source_ownership": "source_ownership is unknown or requires review",
    "rights_status": "rights_status is unknown or requires review",
    "ownership_scope": "ownership_scope is unknown or requires review",
    "restriction_state": "restriction_state requires review",
    "visibility": "visibility requires review",
    "public_state": "public_state requires review",
    "redaction_required": "redaction_required is enabled",
    "content_flags": "content_flags require review",
}

SOURCE_RIGHTS_REVIEW_VALUES: Final[dict[str, tuple[Any, ...]]] = {
    "source_type": (
        "unknown",
        "external_reference_only",
        "fair_use_reference",
        "restricted_reference",
    ),
    "source_ownership": (
        "unknown_source",
        "external_reference",
        "third_party_copyright",
    ),
    "rights_status": (
        "unknown",
        "fair_use_reference",
        "third_party",
    ),
    "ownership_scope": (
        "unknown",
        "personal",
        "third_party",
    ),
}

RESTRICTION_REVIEW_VALUES: Final[dict[str, tuple[Any, ...]]] = {
    "restriction_state": (
        "possible",
        "restricted",
        "confidential",
        "cultural",
        "integrity",
        "privacy",
        "copyright",
        "unknown",
    ),
    "visibility": (
        "restricted",
        "restricted_integrity",
        "restricted_cultural",
    ),
    "public_state": (
        "restricted",
        "confidential",
        "unknown",
    ),
}

CONTENT_FLAGS_REQUIRING_REVIEW: Final[tuple[str, ...]] = (
    "sexual_violence",
    "violence",
    "racism",
    "colonial_violence",
    "death",
    "self_harm",
    "substance_use",
    "nudity",
    "explicit_language",
    "culturally_sensitive",
    "sacred_content",
    "ceremonial_content",
    "restricted_knowledge",
    "grief_or_mourning",
    "requires_context",
    "not_for_children",
    "privacy_sensitive",
    "copyright_uncertain",
    "non_public",
    "confidential",
)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_safe_default(field_name: str, fallback: Any = None) -> Any:
    """Return a defensive copy of the safe default for a field."""
    if field_name in SAFE_METADATA_DEFAULTS:
        return deepcopy(SAFE_METADATA_DEFAULTS[field_name])

    if field_name in SAFE_ARRAY_DEFAULTS:
        return deepcopy(SAFE_ARRAY_DEFAULTS[field_name])

    if field_name in SAFE_SQLITE_JSON_TEXT_DEFAULTS:
        return deepcopy(SAFE_SQLITE_JSON_TEXT_DEFAULTS[field_name])

    if field_name in SAFE_FILE_FACT_DEFAULTS:
        return deepcopy(SAFE_FILE_FACT_DEFAULTS[field_name])

    if field_name in SAFE_IDENTIFIER_DEFAULTS:
        return deepcopy(SAFE_IDENTIFIER_DEFAULTS[field_name])

    if field_name in SAFE_AUDIT_FIELD_DEFAULTS:
        return deepcopy(SAFE_AUDIT_FIELD_DEFAULTS[field_name])

    return deepcopy(fallback)


def build_safe_metadata_defaults() -> dict[str, Any]:
    """Return safe defaults for ChatGPT-style metadata fields."""
    return {
        **deepcopy(SAFE_METADATA_DEFAULTS),
        **deepcopy(SAFE_ARRAY_DEFAULTS),
    }


def build_safe_library_row_defaults() -> dict[str, Any]:
    """Return safe defaults for a full library_rows-like dictionary."""
    return deepcopy(SAFE_LIBRARY_ROW_DEFAULTS)


def build_safe_sqlite_json_defaults() -> dict[str, str]:
    """Return default JSON text values for SQLite multi-value fields."""
    return deepcopy(SAFE_SQLITE_JSON_TEXT_DEFAULTS)


def apply_safe_defaults(
    data: dict[str, Any] | None,
    *,
    include_arrays: bool = True,
    include_sqlite_json_text: bool = False,
    include_file_facts: bool = False,
    include_identifiers: bool = False,
    include_audit_fields: bool = False,
    force_human_review_when_needed: bool = True,
) -> dict[str, Any]:
    """
    Apply conservative defaults to a metadata or row dictionary.

    Existing non-None values are preserved. Missing keys and None values receive
    safe defaults.

    By default, this function targets ChatGPT-style metadata:
    scalar metadata + array fields.
    """
    result: dict[str, Any] = {}

    if include_identifiers:
        result.update(deepcopy(SAFE_IDENTIFIER_DEFAULTS))

    result.update(deepcopy(SAFE_METADATA_DEFAULTS))

    if include_arrays:
        result.update(deepcopy(SAFE_ARRAY_DEFAULTS))

    if include_sqlite_json_text:
        result.update(deepcopy(SAFE_SQLITE_JSON_TEXT_DEFAULTS))

    if include_file_facts:
        result.update(deepcopy(SAFE_FILE_FACT_DEFAULTS))

    if include_audit_fields:
        result.update(deepcopy(SAFE_AUDIT_FIELD_DEFAULTS))

    for key, value in (data or {}).items():
        if value is not None:
            result[key] = value

    normalize_missing_array_fields(result)
    normalize_missing_sqlite_json_text_fields(result)

    if force_human_review_when_needed:
        result = apply_human_review_safety(result)

    return result


def apply_library_row_safe_defaults(data: dict[str, Any] | None) -> dict[str, Any]:
    """Apply defaults for a full library_rows-like dictionary."""
    return apply_safe_defaults(
        data,
        include_arrays=False,
        include_sqlite_json_text=True,
        include_file_facts=True,
        include_identifiers=True,
        include_audit_fields=True,
        force_human_review_when_needed=True,
    )


def apply_chatgpt_metadata_safe_defaults(data: dict[str, Any] | None) -> dict[str, Any]:
    """Apply defaults for ChatGPT JSON metadata."""
    return apply_safe_defaults(
        data,
        include_arrays=True,
        include_sqlite_json_text=False,
        include_file_facts=False,
        include_identifiers=False,
        include_audit_fields=False,
        force_human_review_when_needed=True,
    )


def apply_xlsx_row_safe_defaults(data: dict[str, Any] | None) -> dict[str, Any]:
    """
    Apply defaults for an XLSX row dictionary.

    XLSX rows use semicolon text for multi-value fields, so JSON array fields are
    present as arrays only after import parsing. This helper keeps safe scalar
    values and allows the import parser to decide how to split multi-value text.
    """
    return apply_safe_defaults(
        data,
        include_arrays=True,
        include_sqlite_json_text=False,
        include_file_facts=False,
        include_identifiers=False,
        include_audit_fields=False,
        force_human_review_when_needed=True,
    )


def apply_human_review_safety(data: dict[str, Any]) -> dict[str, Any]:
    """
    Force human_review_required=1 when conservative rules require it.

    This is a safe-default helper, not a substitute for full blocking validation.
    """
    result = dict(data)
    reasons = get_human_review_reasons(result)

    if reasons:
        result["human_review_required"] = 1
        existing_reason = str(result.get("review_reason") or "").strip()
        generated_reason = "; ".join(reasons)

        if existing_reason:
            result["review_reason"] = existing_reason
        else:
            result["review_reason"] = generated_reason

        if not str(result.get("review_queue") or "").strip():
            result["review_queue"] = "human_review"

    return result


def get_human_review_reasons(data: dict[str, Any]) -> list[str]:
    """Return human-review reasons implied by conservative defaults."""
    reasons: list[str] = []

    for field_name, review_values in SOURCE_RIGHTS_REVIEW_VALUES.items():
        if data.get(field_name) in review_values:
            reasons.append(REVIEW_REQUIRED_DEFAULT_REASONS[field_name])

    for field_name, review_values in RESTRICTION_REVIEW_VALUES.items():
        if data.get(field_name) in review_values:
            reasons.append(REVIEW_REQUIRED_DEFAULT_REASONS[field_name])

    if _as_int(data.get("redaction_required", 0)) == 1:
        reasons.append(REVIEW_REQUIRED_DEFAULT_REASONS["redaction_required"])

    content_flags = normalize_array_value(data.get("content_flags", []))
    if set(content_flags) & set(CONTENT_FLAGS_REQUIRING_REVIEW):
        reasons.append(REVIEW_REQUIRED_DEFAULT_REASONS["content_flags"])

    return _dedupe_preserve_order(reasons)


def force_non_exportable_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy forced to non-exportable safe defaults.

    Used when metadata is uncertain, invalid, blocked, or not yet reviewed.
    """
    result = dict(data)
    result["target_system"] = DEFAULT_TARGET_SYSTEM
    result["target_export_allowed"] = DEFAULT_TARGET_EXPORT_ALLOWED
    result["export_to_uckk"] = DEFAULT_EXPORT_TO_UCKK
    result["export_to_public"] = DEFAULT_EXPORT_TO_PUBLIC
    return result


def force_private_access_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy forced to private/local access defaults."""
    result = dict(data)
    result["public_state"] = DEFAULT_PUBLIC_STATE
    result["visibility"] = DEFAULT_VISIBILITY
    result["access_level"] = DEFAULT_ACCESS_LEVEL
    return result


def force_unverified_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy forced to unverified canonical validation defaults."""
    result = dict(data)
    result["canonical_validation_state"] = DEFAULT_CANONICAL_VALIDATION_STATE
    return result


def make_safe_empty_metadata() -> dict[str, Any]:
    """Return an empty-but-safe ChatGPT metadata structure."""
    return apply_chatgpt_metadata_safe_defaults({})


def make_safe_empty_library_row() -> dict[str, Any]:
    """Return an empty-but-safe library row structure."""
    return apply_library_row_safe_defaults({})


def normalize_missing_array_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure JSON array fields exist and are lists when present."""
    for field_name in JSON_ARRAY_FIELDS:
        if field_name not in data or data[field_name] is None:
            data[field_name] = []

        data[field_name] = normalize_array_value(data[field_name])

    return data


def normalize_missing_sqlite_json_text_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure SQLite JSON text fields exist and contain JSON arrays."""
    for field_name in SQLITE_JSON_TEXT_FIELDS:
        if field_name not in data or data[field_name] is None:
            data[field_name] = DEFAULT_JSON_ARRAY_TEXT

        data[field_name] = normalize_sqlite_json_array_text(data[field_name])

    return data


def normalize_array_value(value: Any) -> list[Any]:
    """
    Normalize a multi-value field to a list.

    Accepts list, tuple, JSON array text, semicolon-separated text, or a single
    scalar value.
    """
    if value is None:
        return []

    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]

    if isinstance(value, tuple):
        return [item for item in value if item not in (None, "")]

    if isinstance(value, str):
        text = value.strip()

        if not text or text == "[]":
            return []

        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None

            if isinstance(parsed, list):
                return [item for item in parsed if item not in (None, "")]

        return [part.strip() for part in text.split(";") if part.strip()]

    return [value]


def normalize_sqlite_json_array_text(value: Any) -> str:
    """Normalize a value to SQLite JSON text containing an array."""
    array_value = normalize_array_value(value)
    return json.dumps(array_value, ensure_ascii=False, sort_keys=True)


def sqlite_json_text_to_array(value: Any) -> list[Any]:
    """Convert SQLite JSON text to a list, safely falling back to []."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if not isinstance(value, str):
        return [value]

    text = value.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return normalize_array_value(text)

    if isinstance(parsed, list):
        return parsed

    return [parsed]


def array_to_xlsx_text(value: Any) -> str:
    """Convert a multi-value field to semicolon-separated XLSX text."""
    return "; ".join(str(item) for item in normalize_array_value(value))


def xlsx_text_to_array(value: Any) -> list[str]:
    """Convert semicolon-separated XLSX text to an array of strings."""
    return [str(item) for item in normalize_array_value(value)]


def _as_int(value: Any) -> int | Any:
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "oui"}:
            return 1
        if lowered in {"0", "false", "no", "non", ""}:
            return 0

    return value


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


__all__ = [
    "CONTENT_FLAGS_REQUIRING_REVIEW",
    "RESTRICTION_REVIEW_VALUES",
    "REVIEW_REQUIRED_DEFAULT_REASONS",
    "SAFE_ARRAY_DEFAULTS",
    "SAFE_AUDIT_FIELD_DEFAULTS",
    "SAFE_FILE_FACT_DEFAULTS",
    "SAFE_IDENTIFIER_DEFAULTS",
    "SAFE_LIBRARY_ROW_DEFAULTS",
    "SAFE_METADATA_DEFAULTS",
    "SAFE_SQLITE_JSON_TEXT_DEFAULTS",
    "SOURCE_RIGHTS_REVIEW_VALUES",
    "UNKNOWN_SOURCE_RIGHTS_FIELDS",
    "apply_chatgpt_metadata_safe_defaults",
    "apply_human_review_safety",
    "apply_library_row_safe_defaults",
    "apply_safe_defaults",
    "apply_xlsx_row_safe_defaults",
    "array_to_xlsx_text",
    "build_safe_library_row_defaults",
    "build_safe_metadata_defaults",
    "build_safe_sqlite_json_defaults",
    "force_non_exportable_defaults",
    "force_private_access_defaults",
    "force_unverified_defaults",
    "get_human_review_reasons",
    "get_safe_default",
    "make_safe_empty_library_row",
    "make_safe_empty_metadata",
    "normalize_array_value",
    "normalize_missing_array_fields",
    "normalize_missing_sqlite_json_text_fields",
    "normalize_sqlite_json_array_text",
    "sqlite_json_text_to_array",
    "xlsx_text_to_array",
]