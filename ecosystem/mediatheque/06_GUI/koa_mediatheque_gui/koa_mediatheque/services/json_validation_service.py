# 06_GUI/koa_mediatheque_gui/koa_mediatheque/services/json_validation_service.py

from __future__ import annotations

import json
from typing import Any

from koa_mediatheque.errors import (
    ERR_BLOCKED_PUBLIC_EXPORT,
    ERR_BLOCKED_UCKK_EXPORT,
    ERR_BLOCKED_VERIFIED,
    ERR_INVALID_ENUM,
    ERR_INVALID_TYPE,
    ERR_JSON_PARSE,
    ERR_REQUIRED_FIELD,
    ERR_REVIEW_REQUIRED,
    WARN_FIELD_NORMALIZED,
    WARN_UNKNOWN_RIGHTS,
    WARN_UNKNOWN_SOURCE,
)
from koa_mediatheque.models import KoaMessage, ValidationResult

try:
    from koa_mediatheque.constants import (
        APP_ENRICHED_FIELDS,
        CHATGPT_JSON_REQUIRED_FIELDS,
        JSON_ARRAY_FIELDS,
        TECHNICAL_PROTECTED_FIELDS,
    )
except ImportError:  # pragma: no cover
    APP_ENRICHED_FIELDS = (
        "media_uuid",
        "version_uuid",
        "original_path",
        "storage_path",
        "filename",
        "extension",
        "mimetype",
        "filesize",
        "sha256",
        "filearea",
        "created_at",
        "updated_at",
        "import_batch",
    )
    CHATGPT_JSON_REQUIRED_FIELDS = (
        "title",
        "description",
        "summary",
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
        "restriction_state",
        "redaction_required",
        "status",
        "provenance",
        "ai_validation_state",
        "ai_confidence",
        "canonical_validation_state",
        "human_review_required",
        "review_queue",
        "collections",
        "tags",
        "relations",
        "content_flags",
        "audience_suitability",
        "export_to_uckk",
        "export_to_public",
        "notes",
    )
    JSON_ARRAY_FIELDS = ("collections", "tags", "relations", "content_flags")
    TECHNICAL_PROTECTED_FIELDS = (
        "filename",
        "extension",
        "mimetype",
        "filesize",
        "sha256",
        "storage_path",
        "created_at",
        "updated_at",
    )

try:
    from koa_mediatheque.validation.allowed_values import ALLOWED_VALUES_BY_FIELD
except ImportError:  # pragma: no cover
    ALLOWED_VALUES_BY_FIELD: dict[str, tuple[Any, ...]] = {}


DEFAULT_CANONICAL_VALIDATION_STATE = "unverified"
DEFAULT_AI_VALIDATION_STATE = "ai_uncertain"

_BOOLEAN_INT_FIELDS = {
    "target_export_allowed",
    "human_review_required",
    "redaction_required",
}

_FLOAT_FIELDS = {
    "ai_confidence",
}

_STRING_FIELDS = {
    "title",
    "subtitle",
    "description",
    "summary",
    "media_type",
    "language",
    "library_scope",
    "uckk_relevance",
    "target_system",
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
    "status",
    "provenance",
    "ai_validation_state",
    "canonical_validation_state",
    "review_queue",
    "review_reason",
    "audience_suitability",
    "export_to_uckk",
    "export_to_public",
    "export_policy_note",
    "import_batch",
    "notes",
}

_DEFAULTS: dict[str, Any] = {
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
    "restriction_state": "none",
    "redaction_required": 0,
    "status": "active",
    "provenance": "ai_assisted",
    "ai_validation_state": DEFAULT_AI_VALIDATION_STATE,
    "canonical_validation_state": DEFAULT_CANONICAL_VALIDATION_STATE,
    "human_review_required": 0,
    "review_queue": "",
    "collections": [],
    "tags": [],
    "relations": [],
    "content_flags": [],
    "audience_suitability": "unknown",
    "export_to_uckk": "no",
    "export_to_public": "no",
    "notes": "",
}

_PROTECTED_AI_FIELDS = set(APP_ENRICHED_FIELDS) | set(TECHNICAL_PROTECTED_FIELDS) | {
    "media_uuid",
    "version_uuid",
    "original_path",
    "storage_path",
    "filename",
    "extension",
    "mimetype",
    "filesize",
    "sha256",
    "filearea",
    "created_at",
    "updated_at",
}

_REVIEW_REQUIRED_RIGHTS_STATUSES = {
    "unknown",
    "third_party",
    "unclear",
}

_REVIEW_REQUIRED_SOURCE_TYPES = {
    "unknown",
}

_REVIEW_REQUIRED_SOURCE_OWNERSHIPS = {
    "unknown_source",
}

_REVIEW_REQUIRED_OWNERSHIP_SCOPES = {
    "unknown",
}

_REVIEW_REQUIRED_RESTRICTIONS = {
    "restricted",
    "cultural",
    "confidential",
    "privacy",
    "copyright",
}

_REVIEW_REQUIRED_VISIBILITIES = {
    "restricted",
    "restricted_cultural",
    "restricted_integrity",
}

_REVIEW_REQUIRED_CONTENT_FLAGS = {
    "copyright_uncertain",
    "privacy_sensitive",
    "culturally_sensitive",
    "sacred_content",
    "ceremonial_content",
    "restricted_knowledge",
    "non_public",
    "confidential",
}

_PUBLIC_EXPORT_BLOCKING_PUBLIC_STATES = {
    "non_public",
    "private",
    "restricted",
    "confidential",
    "unknown",
}

_PUBLIC_EXPORT_BLOCKING_VISIBILITIES = {
    "private",
    "restricted",
    "restricted_cultural",
    "restricted_integrity",
}

_PUBLIC_EXPORT_BLOCKING_ACCESS_LEVELS = {
    "private",
    "restricted",
    "confidential",
}

_PUBLIC_EXPORT_BLOCKING_RESTRICTIONS = {
    "restricted",
    "cultural",
    "confidential",
    "privacy",
    "copyright",
}

_PUBLIC_EXPORT_BLOCKING_RIGHTS_STATUSES = {
    "unknown",
    "third_party",
    "unclear",
}

_UCKK_EXPORT_BLOCKING_RELEVANCE = {
    "not_uckk",
}

_UCKK_EXPORT_REQUIRED_TARGET_SYSTEM = "uckkarchive"

_YES_VALUES = {
    "1",
    "true",
    "yes",
    "y",
    "oui",
    "o",
}


def parse_json_text(raw_text: str) -> ValidationResult:
    """Parse a raw ChatGPT response as one JSON object and normalize safe fields."""
    if not isinstance(raw_text, str):
        return _invalid_result(
            code=ERR_INVALID_TYPE,
            message="La réponse ChatGPT doit être une chaîne de caractères.",
            field=None,
        )

    cleaned = _strip_markdown_json_fence(raw_text.strip())

    if not cleaned:
        return _invalid_result(
            code=ERR_JSON_PARSE,
            message="La réponse ChatGPT est vide.",
            field=None,
        )

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return _invalid_result(
            code=ERR_JSON_PARSE,
            message=f"JSON invalide : {exc.msg}.",
            field=None,
            details={
                "line": exc.lineno,
                "column": exc.colno,
                "position": exc.pos,
            },
        )

    if not isinstance(parsed, dict):
        return _invalid_result(
            code=ERR_INVALID_TYPE,
            message="La réponse ChatGPT doit être un objet JSON.",
            field=None,
        )

    return ValidationResult(
        is_valid=True,
        is_blocked=False,
        normalized_data=normalize_metadata_dict(parsed),
        warnings=[],
        errors=[],
    )


def validate_chatgpt_json(
    raw_text: str,
    *,
    allow_human_verified_override: bool = False,
) -> ValidationResult:
    """Validate a raw ChatGPT JSON response against the kOA intake contract."""
    parsed = parse_json_text(raw_text)

    if not parsed.is_valid:
        return parsed

    return validate_metadata_dict(
        parsed.normalized_data,
        allow_human_verified_override=allow_human_verified_override,
    )


def validate_metadata_dict(
    metadata: dict[str, Any],
    *,
    allow_human_verified_override: bool = False,
) -> ValidationResult:
    """Validate metadata produced by ChatGPT before app-side enrichment."""
    if not isinstance(metadata, dict):
        return _invalid_result(
            code=ERR_INVALID_TYPE,
            message="Les métadonnées doivent être un objet dictionnaire.",
            field=None,
        )

    original = dict(metadata)
    normalized = normalize_metadata_dict(metadata)

    warnings: list[KoaMessage] = []
    errors: list[KoaMessage] = []

    stripped_fields = sorted(set(original) & _PROTECTED_AI_FIELDS)
    for field_name in stripped_fields:
        warnings.append(
            _warning_message(
                code=WARN_FIELD_NORMALIZED,
                field=field_name,
                message=(
                    "Champ technique ignoré; il sera recalculé localement : "
                    f"{field_name}."
                ),
                details={"ignored_value": original.get(field_name)},
            )
        )

    errors.extend(_validate_required_fields(normalized, original))
    errors.extend(_validate_field_types(normalized))
    errors.extend(_validate_controlled_values(normalized))
    errors.extend(_validate_array_controlled_values(normalized))

    verified_by_ai = normalized.get("canonical_validation_state") == "verified"

    if verified_by_ai and not allow_human_verified_override:
        errors.append(
            _blocking_message(
                code=ERR_BLOCKED_VERIFIED,
                field="canonical_validation_state",
                message=(
                    "ChatGPT ne peut pas définir "
                    "canonical_validation_state = verified sans override humain explicite."
                ),
            )
        )

    if _is_public_export_blocked(normalized):
        errors.append(
            _blocking_message(
                code=ERR_BLOCKED_PUBLIC_EXPORT,
                field="export_to_public",
                message=(
                    "Export public bloqué pour un enregistrement non public, "
                    "restreint ou incertain."
                ),
            )
        )

    if _is_uckk_export_blocked(normalized):
        errors.append(
            _blocking_message(
                code=ERR_BLOCKED_UCKK_EXPORT,
                field="export_to_uckk",
                message=(
                    "Export UCKK bloqué pour un enregistrement non UCKK "
                    "ou sans cible uckkarchive."
                ),
            )
        )

    # An explicit human override means the human has reviewed this exact intake.
    # It bypasses both AI-verified blocking and review-required checks.
    if not (verified_by_ai and allow_human_verified_override):
        review_reasons = _review_required_reasons(normalized)

        if review_reasons and not _has_review_marker(normalized):
            errors.append(
                _blocking_message(
                    code=ERR_REVIEW_REQUIRED,
                    field="human_review_required",
                    message=(
                        "Une revue humaine est requise pour source, droits, "
                        "restriction ou visibilité incertains."
                    ),
                    details={"reasons": review_reasons},
                )
            )
        elif review_reasons:
            warnings.extend(_review_warnings(review_reasons))

    return ValidationResult(
        is_valid=not errors,
        is_blocked=bool(errors),
        normalized_data=normalized,
        warnings=warnings,
        errors=errors,
    )


def normalize_metadata_dict(metadata: dict[str, Any]) -> dict[str, Any]:
    """Normalize user-editable ChatGPT metadata and drop app-enriched facts."""
    if not isinstance(metadata, dict):
        return {}

    normalized: dict[str, Any] = {}

    for key, value in metadata.items():
        if key in _PROTECTED_AI_FIELDS:
            continue

        normalized[key] = _normalize_field_value(key, value)

    for key, value in _DEFAULTS.items():
        if key not in normalized or normalized[key] is None:
            normalized[key] = list(value) if isinstance(value, list) else value

    for key in JSON_ARRAY_FIELDS:
        if key not in normalized or normalized[key] is None:
            normalized[key] = []
        elif isinstance(normalized[key], tuple):
            normalized[key] = list(normalized[key])

    if not normalized.get("canonical_validation_state"):
        normalized["canonical_validation_state"] = DEFAULT_CANONICAL_VALIDATION_STATE

    if not normalized.get("ai_validation_state"):
        normalized["ai_validation_state"] = DEFAULT_AI_VALIDATION_STATE

    return normalized


def _validate_required_fields(
    normalized: dict[str, Any],
    original: dict[str, Any],
) -> list[KoaMessage]:
    errors: list[KoaMessage] = []

    for field_name in CHATGPT_JSON_REQUIRED_FIELDS:
        if field_name in _PROTECTED_AI_FIELDS:
            continue

        if field_name not in original and field_name not in _DEFAULTS:
            errors.append(
                _blocking_message(
                    code=ERR_REQUIRED_FIELD,
                    field=field_name,
                    message=f"Champ requis manquant : {field_name}.",
                )
            )
            continue

        value = normalized.get(field_name)

        if field_name in JSON_ARRAY_FIELDS:
            if value is None:
                errors.append(
                    _blocking_message(
                        code=ERR_REQUIRED_FIELD,
                        field=field_name,
                        message=f"Champ requis manquant : {field_name}.",
                    )
                )
        elif value is None or (isinstance(value, str) and value.strip() == ""):
            errors.append(
                _blocking_message(
                    code=ERR_REQUIRED_FIELD,
                    field=field_name,
                    message=f"Champ requis vide : {field_name}.",
                )
            )

    return errors


def _validate_field_types(normalized: dict[str, Any]) -> list[KoaMessage]:
    errors: list[KoaMessage] = []

    for field_name in _BOOLEAN_INT_FIELDS:
        if field_name not in normalized:
            continue

        value = normalized[field_name]

        if not (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value in (0, 1)
        ):
            errors.append(
                _blocking_message(
                    code=ERR_INVALID_TYPE,
                    field=field_name,
                    message=f"{field_name} doit être un entier 0 ou 1.",
                    details={
                        "actual_type": type(value).__name__,
                        "actual_value": value,
                    },
                )
            )

    for field_name in _FLOAT_FIELDS:
        if field_name not in normalized or normalized[field_name] is None:
            continue

        value = normalized[field_name]

        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(
                _blocking_message(
                    code=ERR_INVALID_TYPE,
                    field=field_name,
                    message=f"{field_name} doit être un nombre.",
                    details={
                        "actual_type": type(value).__name__,
                        "actual_value": value,
                    },
                )
            )

    for field_name in _STRING_FIELDS:
        if field_name not in normalized or normalized[field_name] is None:
            continue

        value = normalized[field_name]

        if not isinstance(value, str):
            errors.append(
                _blocking_message(
                    code=ERR_INVALID_TYPE,
                    field=field_name,
                    message=f"{field_name} doit être une chaîne de caractères.",
                    details={
                        "actual_type": type(value).__name__,
                        "actual_value": value,
                    },
                )
            )

    for field_name in JSON_ARRAY_FIELDS:
        if field_name not in normalized:
            continue

        value = normalized[field_name]

        if not isinstance(value, list):
            errors.append(
                _blocking_message(
                    code=ERR_INVALID_TYPE,
                    field=field_name,
                    message=f"{field_name} doit être une liste JSON.",
                    details={
                        "actual_type": type(value).__name__,
                        "actual_value": value,
                    },
                )
            )

    return errors


def _validate_controlled_values(normalized: dict[str, Any]) -> list[KoaMessage]:
    errors: list[KoaMessage] = []

    for field_name, allowed_values in ALLOWED_VALUES_BY_FIELD.items():
        if field_name not in normalized or field_name in JSON_ARRAY_FIELDS:
            continue

        value = normalized[field_name]

        if value is None or value == "":
            continue

        # ChatGPT intake is strict: it must emit canonical enum values, not UI
        # aliases. This keeps prompt/template drift visible.
        allowed = set(allowed_values)

        if allowed and value not in allowed:
            errors.append(_invalid_enum_message(field_name, value, allowed))

    return errors


def _validate_array_controlled_values(
    normalized: dict[str, Any],
) -> list[KoaMessage]:
    errors: list[KoaMessage] = []

    content_flags = normalized.get("content_flags")
    allowed_content_flags = set(ALLOWED_VALUES_BY_FIELD.get("content_flags", ()))

    if isinstance(content_flags, list) and allowed_content_flags:
        for index, value in enumerate(content_flags):
            if value not in allowed_content_flags:
                errors.append(
                    _blocking_message(
                        code=ERR_INVALID_ENUM,
                        field="content_flags",
                        message=(
                            f"Valeur non autorisée pour content_flags[{index}] : "
                            f"{value}."
                        ),
                        details={
                            "actual_value": value,
                            "allowed_values": sorted(
                                str(item) for item in allowed_content_flags
                            ),
                        },
                    )
                )

    return errors


def _normalize_field_value(field_name: str, value: Any) -> Any:
    if field_name in JSON_ARRAY_FIELDS:
        return _normalize_array(value)

    if field_name in _BOOLEAN_INT_FIELDS:
        # ChatGPT JSON must use canonical numeric booleans. Do not coerce strings
        # such as "yes" because that hides prompt/template errors.
        if isinstance(value, bool):
            return 1 if value else 0

        return value

    if field_name in _FLOAT_FIELDS:
        if value is None or value == "":
            return None

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)

        return value

    if isinstance(value, str):
        return value.strip()

    return value


def _normalize_array(value: Any) -> list[Any] | Any:
    if value is None:
        return []

    if isinstance(value, list):
        return [
            _normalize_array_item(item)
            for item in value
            if _normalize_array_item(item) not in {"", None}
        ]

    if isinstance(value, tuple):
        return [
            _normalize_array_item(item)
            for item in value
            if _normalize_array_item(item) not in {"", None}
        ]

    return value


def _normalize_array_item(item: Any) -> Any:
    if isinstance(item, str):
        return item.strip()

    return item


def _review_required_reasons(data: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    if data.get("rights_status") in _REVIEW_REQUIRED_RIGHTS_STATUSES:
        reasons.append("rights_status")

    if data.get("source_type") in _REVIEW_REQUIRED_SOURCE_TYPES:
        reasons.append("source_type")

    if data.get("source_ownership") in _REVIEW_REQUIRED_SOURCE_OWNERSHIPS:
        reasons.append("source_ownership")

    if data.get("ownership_scope") in _REVIEW_REQUIRED_OWNERSHIP_SCOPES:
        reasons.append("ownership_scope")

    if data.get("restriction_state") in _REVIEW_REQUIRED_RESTRICTIONS:
        reasons.append("restriction_state")

    if data.get("visibility") in _REVIEW_REQUIRED_VISIBILITIES:
        reasons.append("visibility")

    flags = data.get("content_flags") or []

    if isinstance(flags, list) and set(flags) & _REVIEW_REQUIRED_CONTENT_FLAGS:
        reasons.append("content_flags")

    return reasons


def _has_review_marker(data: dict[str, Any]) -> bool:
    return _is_yes(data.get("human_review_required")) and bool(
        str(data.get("review_reason") or "").strip()
    )


def _review_warnings(reasons: list[str]) -> list[KoaMessage]:
    warnings: list[KoaMessage] = []

    if "rights_status" in reasons:
        warnings.append(
            _warning_message(
                code=WARN_UNKNOWN_RIGHTS,
                field="rights_status",
                message="Droits inconnus ou incertains; revue humaine requise.",
            )
        )

    if "source_type" in reasons or "source_ownership" in reasons:
        warnings.append(
            _warning_message(
                code=WARN_UNKNOWN_SOURCE,
                field="source_type",
                message="Source inconnue ou incertaine; revue humaine requise.",
            )
        )

    return warnings


def _is_public_export_blocked(data: dict[str, Any]) -> bool:
    if not _is_yes(data.get("export_to_public")):
        return False

    if data.get("public_state") in _PUBLIC_EXPORT_BLOCKING_PUBLIC_STATES:
        return True

    if data.get("visibility") in _PUBLIC_EXPORT_BLOCKING_VISIBILITIES:
        return True

    if data.get("access_level") in _PUBLIC_EXPORT_BLOCKING_ACCESS_LEVELS:
        return True

    if data.get("restriction_state") in _PUBLIC_EXPORT_BLOCKING_RESTRICTIONS:
        return True

    if data.get("rights_status") in _PUBLIC_EXPORT_BLOCKING_RIGHTS_STATUSES:
        return True

    flags = data.get("content_flags") or []

    return isinstance(flags, list) and bool(
        set(flags) & _REVIEW_REQUIRED_CONTENT_FLAGS
    )


def _is_uckk_export_blocked(data: dict[str, Any]) -> bool:
    wants_uckk_export = _is_yes(data.get("export_to_uckk")) or _is_yes(
        data.get("target_export_allowed")
    )

    if not wants_uckk_export:
        return False

    if data.get("uckk_relevance") in _UCKK_EXPORT_BLOCKING_RELEVANCE:
        return True

    return data.get("target_system") != _UCKK_EXPORT_REQUIRED_TARGET_SYSTEM


def _strip_markdown_json_fence(raw_text: str) -> str:
    text = raw_text.strip()

    if not text.startswith("```"):
        return text

    lines = text.splitlines()

    if len(lines) < 3:
        return text

    first_line = lines[0].strip().lower()
    last_line = lines[-1].strip()

    if (
        first_line in {"```", "```json", "```javascript", "```js"}
        and last_line == "```"
    ):
        return "\n".join(lines[1:-1]).strip()

    return text


def _is_yes(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in _YES_VALUES

    return False


def _blocking_message(
    *,
    code: str,
    field: str | None,
    message: str,
    details: dict[str, Any] | None = None,
) -> KoaMessage:
    return KoaMessage(
        code=code,
        severity="blocking",
        message=message,
        field=field,
        details=details or {},
    )


def _warning_message(
    *,
    code: str,
    field: str | None,
    message: str,
    details: dict[str, Any] | None = None,
) -> KoaMessage:
    return KoaMessage(
        code=code,
        severity="warning",
        message=message,
        field=field,
        details=details or {},
    )


def _invalid_enum_message(
    field_name: str,
    value: Any,
    allowed_set: set[Any],
) -> KoaMessage:
    return _blocking_message(
        code=ERR_INVALID_ENUM,
        field=field_name,
        message=f"Valeur non autorisée pour {field_name} : {value}.",
        details={
            "actual_value": value,
            "allowed_values": sorted(str(item) for item in allowed_set),
        },
    )


def _invalid_result(
    *,
    code: str,
    message: str,
    field: str | None,
    details: dict[str, Any] | None = None,
) -> ValidationResult:
    return ValidationResult(
        is_valid=False,
        is_blocked=True,
        normalized_data={},
        warnings=[],
        errors=[
            _blocking_message(
                code=code,
                field=field,
                message=message,
                details=details,
            )
        ],
    )