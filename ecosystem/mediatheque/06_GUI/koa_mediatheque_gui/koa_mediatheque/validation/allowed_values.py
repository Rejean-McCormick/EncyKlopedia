"""
Controlled values for Médiathèque kOA.

This module exposes the canonical allowed values used by validation, UI widgets,
XLSX lists, and import/export services.

The source values are imported from constants.py. Do not redefine enums in
services or pages.
"""

from __future__ import annotations

from typing import Any
from typing import Final

from koa_mediatheque.constants import (
    ACCESS_LEVEL_VALUES,
    AUDIENCE_SUITABILITY_VALUES,
    AUDIT_ACTION_VALUES,
    AUDIT_ENTITY_TYPE_VALUES,
    CANONICAL_VALIDATION_VALUES,
    CONTENT_FLAG_VALUES,
    COPY_MODE_VALUES,
    EXPORT_DECISION_VALUES,
    EXPORT_TYPE_VALUES,
    LANGUAGE_VALUES,
    LIBRARY_SCOPE_VALUES,
    LOCAL_AI_VALIDATION_VALUES,
    MEDIA_STATUS_VALUES,
    MEDIA_TYPE_VALUES,
    MESSAGE_SEVERITY_VALUES,
    OWNERSHIP_SCOPE_VALUES,
    PROVENANCE_VALUES,
    PUBLIC_STATE_VALUES,
    RELATION_TYPE_VALUES,
    RESTRICTION_STATE_VALUES,
    RIGHTS_STATUS_VALUES,
    SOURCE_OWNERSHIP_VALUES,
    SOURCE_TYPE_VALUES,
    STORAGE_FILEAREAS,
    TARGET_EXPORT_ALLOWED_VALUES,
    TARGET_SYSTEM_VALUES,
    UCKK_RELEVANCE_VALUES,
    VALIDATION_STATUS_VALUES,
    VISIBILITY_NORMALIZATION_ALIASES,
    VISIBILITY_VALUES,
    XLSX_ACTION_VALUES,
    XLSX_IMPORT_MODES,
)


ALLOWED_VALUES_BY_FIELD: Final[dict[str, tuple[Any, ...]]] = {
    "access_level": ACCESS_LEVEL_VALUES,
    "ai_validation_state": LOCAL_AI_VALIDATION_VALUES,
    "audience_suitability": AUDIENCE_SUITABILITY_VALUES,
    "canonical_validation_state": CANONICAL_VALIDATION_VALUES,
    "content_flags": CONTENT_FLAG_VALUES,
    "copy_mode": COPY_MODE_VALUES,
    "export_to_public": EXPORT_DECISION_VALUES,
    "export_to_uckk": EXPORT_DECISION_VALUES,
    "export_type": EXPORT_TYPE_VALUES,
    "filearea": STORAGE_FILEAREAS,
    "language": LANGUAGE_VALUES,
    "library_scope": LIBRARY_SCOPE_VALUES,
    "media_type": MEDIA_TYPE_VALUES,
    "message_severity": MESSAGE_SEVERITY_VALUES,
    "ownership_scope": OWNERSHIP_SCOPE_VALUES,
    "provenance": PROVENANCE_VALUES,
    "public_state": PUBLIC_STATE_VALUES,
    "relation_type": RELATION_TYPE_VALUES,
    "restriction_state": RESTRICTION_STATE_VALUES,
    "rights_status": RIGHTS_STATUS_VALUES,
    "source_ownership": SOURCE_OWNERSHIP_VALUES,
    "source_type": SOURCE_TYPE_VALUES,
    "status": MEDIA_STATUS_VALUES,
    "target_export_allowed": TARGET_EXPORT_ALLOWED_VALUES,
    "target_system": TARGET_SYSTEM_VALUES,
    "uckk_relevance": UCKK_RELEVANCE_VALUES,
    "validation_status": VALIDATION_STATUS_VALUES,
    "visibility": VISIBILITY_VALUES,
    "xlsx_action": XLSX_ACTION_VALUES,
    "xlsx_import_mode": XLSX_IMPORT_MODES,
}

CONTROLLED_FIELD_NAMES: Final[tuple[str, ...]] = tuple(ALLOWED_VALUES_BY_FIELD.keys())

HUMAN_REVIEW_REQUIRED_VALUES: Final[tuple[int, ...]] = (0, 1)
BOOLEAN_INT_VALUES: Final[tuple[int, ...]] = (0, 1)

NORMALIZED_VALUE_ALIASES: Final[dict[str, dict[str, Any]]] = {
    "visibility": dict(VISIBILITY_NORMALIZATION_ALIASES),
    "target_export_allowed": {
        "false": 0,
        "no": 0,
        "non": 0,
        "0": 0,
        "true": 1,
        "yes": 1,
        "oui": 1,
        "1": 1,
    },
    "redaction_required": {
        "false": 0,
        "no": 0,
        "non": 0,
        "0": 0,
        "true": 1,
        "yes": 1,
        "oui": 1,
        "1": 1,
    },
    "human_review_required": {
        "false": 0,
        "no": 0,
        "non": 0,
        "0": 0,
        "true": 1,
        "yes": 1,
        "oui": 1,
        "1": 1,
    },
}


def get_allowed_values(field_name: str) -> tuple[Any, ...]:
    """Return allowed values for a controlled field, or an empty tuple."""
    return ALLOWED_VALUES_BY_FIELD.get(field_name, ())


def is_controlled_field(field_name: str) -> bool:
    """Return True if the field has a canonical allowed-value list."""
    return field_name in ALLOWED_VALUES_BY_FIELD


def is_allowed_value(field_name: str, value: Any) -> bool:
    """Return True when value is valid for the controlled field."""
    normalized = normalize_allowed_value(field_name, value)
    allowed = get_allowed_values(field_name)

    if not allowed:
        return True

    return normalized in allowed


def normalize_allowed_value(field_name: str, value: Any) -> Any:
    """
    Normalize a value for a controlled field.

    Normalization is intentionally conservative. It trims strings, applies known
    aliases, and preserves canonical values without guessing new vocabulary.
    """
    if value is None:
        return value

    if isinstance(value, str):
        normalized: Any = value.strip()
        alias_key = normalized.lower()
    else:
        normalized = value
        alias_key = str(value).strip().lower()

    field_aliases = NORMALIZED_VALUE_ALIASES.get(field_name, {})
    if alias_key in field_aliases:
        return field_aliases[alias_key]

    if field_name in {"target_export_allowed", "redaction_required", "human_review_required"}:
        return _normalize_int_boolean(normalized)

    return normalized


def require_allowed_value(field_name: str, value: Any) -> Any:
    """
    Return normalized value if valid, otherwise raise ValueError.

    This helper is for settings, UI controls, and low-level validation rules
    that need a simple exception instead of a structured ValidationResult.
    """
    normalized = normalize_allowed_value(field_name, value)
    allowed = get_allowed_values(field_name)

    if allowed and normalized not in allowed:
        allowed_text = ", ".join(map(str, allowed))
        raise ValueError(
            f"Invalid value for {field_name}: {value!r}. Allowed: {allowed_text}"
        )

    return normalized


def normalize_controlled_values(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with controlled values normalized where known."""
    normalized = dict(data)

    for field_name in CONTROLLED_FIELD_NAMES:
        if field_name in normalized:
            normalized[field_name] = normalize_allowed_value(
                field_name,
                normalized[field_name],
            )

    return normalized


def validate_controlled_values(data: dict[str, Any]) -> dict[str, str]:
    """
    Validate all controlled fields in a data dictionary.

    Returns a mapping of field_name -> error message. An empty mapping means all
    controlled values are valid.
    """
    errors: dict[str, str] = {}

    for field_name in CONTROLLED_FIELD_NAMES:
        if field_name not in data:
            continue

        value = normalize_allowed_value(field_name, data[field_name])
        allowed = get_allowed_values(field_name)

        if allowed and value not in allowed:
            allowed_text = ", ".join(map(str, allowed))
            errors[field_name] = (
                f"Invalid value {data[field_name]!r}. Allowed values: {allowed_text}"
            )

    return errors


def validate_array_values(
    field_name: str,
    values: list[Any] | tuple[Any, ...],
) -> dict[int, str]:
    """
    Validate controlled values inside an array field.

    Used mainly for content_flags. Unknown relation compact strings are validated
    elsewhere because relation entries may be structured objects.
    """
    errors: dict[int, str] = {}
    allowed = get_allowed_values(field_name)

    if not allowed:
        return errors

    for index, value in enumerate(values):
        normalized = normalize_allowed_value(field_name, value)
        if normalized not in allowed:
            allowed_text = ", ".join(map(str, allowed))
            errors[index] = (
                f"Invalid value {value!r}. Allowed values: {allowed_text}"
            )

    return errors


def allowed_values_as_dict() -> dict[str, tuple[Any, ...]]:
    """Return a copy of all allowed-value mappings."""
    return dict(ALLOWED_VALUES_BY_FIELD)


def allowed_values_for_xlsx_lists() -> dict[str, list[Any]]:
    """Return values formatted for the XLSX Lists sheet."""
    return {
        field_name: list(values)
        for field_name, values in ALLOWED_VALUES_BY_FIELD.items()
        if values
    }


def _normalize_int_boolean(value: Any) -> int | Any:
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int) and value in BOOLEAN_INT_VALUES:
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        aliases = NORMALIZED_VALUE_ALIASES["target_export_allowed"]
        if lowered in aliases:
            return aliases[lowered]

    return value


__all__ = [
    "ALLOWED_VALUES_BY_FIELD",
    "BOOLEAN_INT_VALUES",
    "CONTROLLED_FIELD_NAMES",
    "HUMAN_REVIEW_REQUIRED_VALUES",
    "NORMALIZED_VALUE_ALIASES",
    "allowed_values_as_dict",
    "allowed_values_for_xlsx_lists",
    "get_allowed_values",
    "is_allowed_value",
    "is_controlled_field",
    "normalize_allowed_value",
    "normalize_controlled_values",
    "require_allowed_value",
    "validate_array_values",
    "validate_controlled_values",
]