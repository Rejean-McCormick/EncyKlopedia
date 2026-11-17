"""
Blocking validation rules for Médiathèque kOA.

This module contains the app-side safety rules that decide whether metadata can
be accepted, needs human review, or must be blocked before public/UCKK export.
It intentionally returns plain dictionaries, not dataclass instances, so it can
be reused by validation, UI, XLSX tooling, and PS7 adapters without circular
imports.
"""

from __future__ import annotations

import json
from typing import Any, Final

try:
    from koa_mediatheque.constants import (
        CONTENT_FLAG_VALUES,
        DEFAULT_CANONICAL_VALIDATION_STATE,
        DEFAULT_EXPORT_TO_PUBLIC,
        DEFAULT_EXPORT_TO_UCKK,
        DEFAULT_HUMAN_REVIEW_REQUIRED,
        DEFAULT_PUBLIC_STATE,
        DEFAULT_RESTRICTION_STATE,
        DEFAULT_RIGHTS_STATUS,
        DEFAULT_SOURCE_OWNERSHIP,
        DEFAULT_SOURCE_TYPE,
        DEFAULT_TARGET_EXPORT_ALLOWED,
        DEFAULT_TARGET_SYSTEM,
        DEFAULT_UCKK_RELEVANCE,
        DEFAULT_VISIBILITY,
        EXPORT_DECISION_VALUES,
    )
except ImportError:  # pragma: no cover - defensive fallback for isolated tooling
    CONTENT_FLAG_VALUES = ()
    DEFAULT_CANONICAL_VALIDATION_STATE = "unverified"
    DEFAULT_EXPORT_TO_PUBLIC = "no"
    DEFAULT_EXPORT_TO_UCKK = "no"
    DEFAULT_HUMAN_REVIEW_REQUIRED = 0
    DEFAULT_PUBLIC_STATE = "unknown"
    DEFAULT_RESTRICTION_STATE = "none"
    DEFAULT_RIGHTS_STATUS = "unknown"
    DEFAULT_SOURCE_OWNERSHIP = "unknown_source"
    DEFAULT_SOURCE_TYPE = "unknown"
    DEFAULT_TARGET_EXPORT_ALLOWED = 0
    DEFAULT_TARGET_SYSTEM = "none"
    DEFAULT_UCKK_RELEVANCE = "unknown"
    DEFAULT_VISIBILITY = "private"
    EXPORT_DECISION_VALUES = ("yes", "no")

try:
    from koa_mediatheque.validation.allowed_values import normalize_allowed_value
except ImportError:  # pragma: no cover
    def normalize_allowed_value(field_name: str, value: Any) -> Any:
        return value


SEVERITY_BLOCKING: Final[str] = "blocking"
SEVERITY_ERROR: Final[str] = "error"
SEVERITY_WARNING: Final[str] = "warning"
SEVERITY_INFO: Final[str] = "info"

RULE_BLOCKED_VERIFIED_BY_AI: Final[str] = "ERR_BLOCKED_VERIFIED"
RULE_BLOCKED_PUBLIC_EXPORT: Final[str] = "ERR_BLOCKED_PUBLIC_EXPORT"
RULE_BLOCKED_UCKK_EXPORT: Final[str] = "ERR_BLOCKED_UCKK_EXPORT"
RULE_REVIEW_REQUIRED: Final[str] = "ERR_REVIEW_REQUIRED"
RULE_UNKNOWN_RIGHTS: Final[str] = "WARN_UNKNOWN_RIGHTS"
RULE_UNKNOWN_SOURCE: Final[str] = "WARN_UNKNOWN_SOURCE"
RULE_RESTRICTED_CONTENT: Final[str] = "WARN_RESTRICTED_CONTENT"
RULE_INVALID_EXPORT_DECISION: Final[str] = "ERR_INVALID_EXPORT_DECISION"
RULE_INVALID_CONTENT_FLAG: Final[str] = "ERR_INVALID_CONTENT_FLAG"

PUBLIC_EXPORT_BLOCKING_PUBLIC_STATES: Final[tuple[str, ...]] = (
    "non_public",
    "private",
    "restricted",
    "confidential",
    "unknown",
)
PUBLIC_EXPORT_BLOCKING_VISIBILITIES: Final[tuple[str, ...]] = (
    "private",
    "user",
    "group",
    "course",
    "cohort",
    "program",
    "institution",
    "restricted",
    "restricted_integrity",
    "restricted_cultural",
)
PUBLIC_EXPORT_BLOCKING_ACCESS_LEVELS: Final[tuple[str, ...]] = (
    "private",
    "limited",
    "internal",
    "restricted",
    "confidential",
    "unknown",
)
PUBLIC_EXPORT_BLOCKING_RESTRICTION_STATES: Final[tuple[str, ...]] = (
    "possible",
    "restricted",
    "confidential",
    "cultural",
    "integrity",
    "privacy",
    "copyright",
    "unknown",
)
PUBLIC_EXPORT_BLOCKING_RIGHTS_STATUSES: Final[tuple[str, ...]] = (
    "fair_use_reference",
    "third_party",
    "unknown",
)
PUBLIC_EXPORT_BLOCKING_SOURCE_TYPES: Final[tuple[str, ...]] = (
    "external_reference_only",
    "fair_use_reference",
    "restricted_reference",
    "unknown",
)
PUBLIC_EXPORT_BLOCKING_SOURCE_OWNERSHIPS: Final[tuple[str, ...]] = (
    "external_reference",
    "third_party_copy",
    "unknown_source",
)
PUBLIC_EXPORT_BLOCKING_OWNERSHIP_SCOPES: Final[tuple[str, ...]] = (
    "third_party",
    "mixed",
    "unknown",
)
PUBLIC_EXPORT_BLOCKING_CONTENT_FLAGS: Final[tuple[str, ...]] = (
    "copyright_uncertain",
    "third_party",
    "privacy",
    "sensitive",
    "cultural_protocol",
    "restricted",
)

UCKK_EXPORT_BLOCKING_RELEVANCE_VALUES: Final[tuple[str, ...]] = ("not_uckk",)
UCKK_EXPORT_REQUIRED_TARGET_SYSTEM: Final[str] = "uckkarchive"

# Review is intentionally narrower than public-export blocking.
# A private/non-public/unknown record is allowed locally when no export is requested.
REVIEW_REQUIRED_RIGHTS_STATUSES: Final[tuple[str, ...]] = (
    "unknown",
    "third_party",
    "fair_use_reference",
)
REVIEW_REQUIRED_SOURCE_TYPES: Final[tuple[str, ...]] = (
    "unknown",
    "external_reference_only",
    "fair_use_reference",
    "restricted_reference",
)
REVIEW_REQUIRED_SOURCE_OWNERSHIPS: Final[tuple[str, ...]] = (
    "unknown_source",
    "external_reference",
    "third_party_copy",
)
REVIEW_REQUIRED_OWNERSHIP_SCOPES: Final[tuple[str, ...]] = ()
REVIEW_REQUIRED_RESTRICTION_STATES: Final[tuple[str, ...]] = (
    "possible",
    "restricted",
    "confidential",
    "cultural",
    "integrity",
    "privacy",
    "copyright",
)
REVIEW_REQUIRED_PUBLIC_STATES: Final[tuple[str, ...]] = ()
REVIEW_REQUIRED_VISIBILITIES: Final[tuple[str, ...]] = (
    "restricted_integrity",
    "restricted_cultural",
)
REVIEW_REQUIRED_CONTENT_FLAGS: Final[tuple[str, ...]] = ()

_YES_VALUES: Final[set[str]] = {"1", "true", "yes", "y", "oui", "o"}
_NO_VALUES: Final[set[str]] = {"0", "false", "no", "n", "non", ""}

_DEFAULTS: Final[dict[str, Any]] = {
    "canonical_validation_state": DEFAULT_CANONICAL_VALIDATION_STATE,
    "uckk_relevance": DEFAULT_UCKK_RELEVANCE,
    "target_system": DEFAULT_TARGET_SYSTEM,
    "target_export_allowed": DEFAULT_TARGET_EXPORT_ALLOWED,
    "public_state": DEFAULT_PUBLIC_STATE,
    "visibility": DEFAULT_VISIBILITY,
    "source_type": DEFAULT_SOURCE_TYPE,
    "source_ownership": DEFAULT_SOURCE_OWNERSHIP,
    "rights_status": DEFAULT_RIGHTS_STATUS,
    "restriction_state": DEFAULT_RESTRICTION_STATE,
    "human_review_required": DEFAULT_HUMAN_REVIEW_REQUIRED,
    "export_to_uckk": DEFAULT_EXPORT_TO_UCKK,
    "export_to_public": DEFAULT_EXPORT_TO_PUBLIC,
    "content_flags": [],
}

_ENUM_FIELDS: Final[tuple[str, ...]] = (
    "canonical_validation_state",
    "uckk_relevance",
    "target_system",
    "public_state",
    "visibility",
    "source_type",
    "source_ownership",
    "rights_status",
    "restriction_state",
    "export_to_uckk",
    "export_to_public",
)


def evaluate_blocking_rules(
    metadata: dict[str, Any],
    *,
    allow_human_verified_override: bool = False,
) -> dict[str, Any]:
    """Evaluate all blocking rules and return a ValidationResult-like dict."""
    normalized = normalize_rule_input(metadata)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for checker in (
        check_export_decision_values,
        check_content_flag_rules,
    ):
        result = checker(normalized)
        errors.extend(result["errors"])
        warnings.extend(result["warnings"])

    result = check_canonical_validation_rule(
        normalized,
        allow_human_verified_override=allow_human_verified_override,
    )
    errors.extend(result["errors"])
    warnings.extend(result["warnings"])

    for checker in (
        check_public_export_rules,
        check_uckk_export_rules,
        check_restriction_review_rules,
        check_unknown_source_and_rights_rules,
    ):
        result = checker(normalized)
        errors.extend(result["errors"])
        warnings.extend(result["warnings"])

    return {
        "is_valid": not errors,
        "is_blocked": bool(errors),
        "normalized_data": normalized,
        "warnings": warnings,
        "errors": errors,
    }


def normalize_rule_input(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow normalized copy suitable for rule checks."""
    if not isinstance(metadata, dict):
        metadata = {}

    normalized = dict(metadata)

    for key, default in _DEFAULTS.items():
        if normalized.get(key) in (None, ""):
            normalized[key] = list(default) if isinstance(default, list) else default

    for field_name in _ENUM_FIELDS:
        if field_name in normalized and normalized[field_name] is not None:
            value = _clean_string(normalized[field_name])
            try:
                normalized[field_name] = normalize_allowed_value(field_name, value)
            except Exception:
                normalized[field_name] = value

    normalized["target_export_allowed"] = _as_int(
        normalized.get("target_export_allowed", DEFAULT_TARGET_EXPORT_ALLOWED)
    )
    normalized["human_review_required"] = _as_int(
        normalized.get("human_review_required", DEFAULT_HUMAN_REVIEW_REQUIRED)
    )
    normalized["content_flags"] = normalize_content_flags(normalized.get("content_flags"))

    return normalized


def apply_required_review_defaults(metadata: dict[str, Any]) -> dict[str, Any]:
    """Set review fields when current metadata requires human review."""
    normalized = normalize_rule_input(metadata)

    if should_require_human_review(normalized):
        normalized["human_review_required"] = 1
        normalized.setdefault("review_queue", "rights_review")
        if not _clean_string(normalized.get("review_queue")):
            normalized["review_queue"] = "rights_review"
        normalized.setdefault("review_reason", "Revue humaine requise.")
        if not _clean_string(normalized.get("review_reason")):
            normalized["review_reason"] = "Revue humaine requise."

    return normalized


def check_canonical_validation_rule(
    metadata: dict[str, Any],
    *,
    allow_human_verified_override: bool = False,
) -> dict[str, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []

    if is_verified_without_override(
        metadata,
        allow_human_verified_override=allow_human_verified_override,
    ):
        errors.append(
            make_rule_message(
                RULE_BLOCKED_VERIFIED_BY_AI,
                SEVERITY_BLOCKING,
                "ChatGPT cannot set canonical_validation_state = verified without explicit human override.",
                field="canonical_validation_state",
            )
        )

    return _rule_result(errors=errors)


def check_export_decision_values(metadata: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    allowed = set(EXPORT_DECISION_VALUES) if EXPORT_DECISION_VALUES else {"yes", "no"}

    for field_name in ("export_to_public", "export_to_uckk"):
        value = metadata.get(field_name)
        if value not in allowed:
            errors.append(
                make_rule_message(
                    RULE_INVALID_EXPORT_DECISION,
                    SEVERITY_BLOCKING,
                    f"Invalid export decision for {field_name}: {value}",
                    field=field_name,
                    details={"allowed": sorted(allowed)},
                )
            )

    return _rule_result(errors=errors)


def check_content_flag_rules(metadata: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    allowed = set(CONTENT_FLAG_VALUES or ())

    if not allowed:
        return _rule_result()

    for flag in normalize_content_flags(metadata.get("content_flags")):
        if flag not in allowed:
            errors.append(
                make_rule_message(
                    RULE_INVALID_CONTENT_FLAG,
                    SEVERITY_BLOCKING,
                    f"Invalid content flag: {flag}",
                    field="content_flags",
                    details={"allowed": sorted(allowed)},
                )
            )

    return _rule_result(errors=errors)


def check_public_export_rules(metadata: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if not is_public_export_blocked(metadata):
        return _rule_result()

    return _rule_result(
        errors=[
            make_rule_message(
                RULE_BLOCKED_PUBLIC_EXPORT,
                SEVERITY_BLOCKING,
                "Public export is blocked by visibility, rights, restrictions, source, ownership, or content flags.",
                field="export_to_public",
            )
        ]
    )


def check_uckk_export_rules(metadata: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if not is_uckk_export_blocked(metadata):
        return _rule_result()

    return _rule_result(
        errors=[
            make_rule_message(
                RULE_BLOCKED_UCKK_EXPORT,
                SEVERITY_BLOCKING,
                "UCKK export is blocked by relevance, target system, export permission, or restrictions.",
                field="export_to_uckk",
            )
        ]
    )


def check_restriction_review_rules(metadata: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if not _restriction_requires_review(metadata):
        return _rule_result()

    if _has_valid_review_marker(metadata):
        return _rule_result(
            warnings=[
                make_rule_message(
                    RULE_RESTRICTED_CONTENT,
                    SEVERITY_WARNING,
                    "Restricted content is marked for human review.",
                    field="human_review_required",
                )
            ]
        )

    return _rule_result(
        errors=[
            make_rule_message(
                RULE_REVIEW_REQUIRED,
                SEVERITY_BLOCKING,
                "Restricted content requires a human review marker before integration.",
                field="human_review_required",
            )
        ]
    )


def check_unknown_source_and_rights_rules(metadata: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if not _source_or_rights_require_review(metadata):
        return _rule_result()

    warnings = []

    if metadata.get("rights_status") in REVIEW_REQUIRED_RIGHTS_STATUSES:
        warnings.append(
            make_rule_message(
                RULE_UNKNOWN_RIGHTS,
                SEVERITY_WARNING,
                "Rights status requires human review.",
                field="rights_status",
            )
        )

    if (
        metadata.get("source_type") in REVIEW_REQUIRED_SOURCE_TYPES
        or metadata.get("source_ownership") in REVIEW_REQUIRED_SOURCE_OWNERSHIPS
    ):
        warnings.append(
            make_rule_message(
                RULE_UNKNOWN_SOURCE,
                SEVERITY_WARNING,
                "Source information requires human review.",
                field="source_type",
            )
        )

    if _has_valid_review_marker(metadata):
        return _rule_result(warnings=warnings)

    return _rule_result(
        warnings=warnings,
        errors=[
            make_rule_message(
                RULE_REVIEW_REQUIRED,
                SEVERITY_BLOCKING,
                "Unknown/third-party rights or source require a human review marker before integration.",
                field="human_review_required",
            )
        ],
    )


def is_verified_without_override(
    metadata: dict[str, Any],
    *,
    allow_human_verified_override: bool = False,
) -> bool:
    return (
        _clean_string(metadata.get("canonical_validation_state")) == "verified"
        and not allow_human_verified_override
    )


def is_public_export_blocked(metadata: dict[str, Any]) -> bool:
    """Return True only when a public export is requested and unsafe."""
    normalized = normalize_rule_input(metadata)

    if not _is_yes(normalized.get("export_to_public")):
        return False

    blocking_checks = (
        ("public_state", PUBLIC_EXPORT_BLOCKING_PUBLIC_STATES),
        ("visibility", PUBLIC_EXPORT_BLOCKING_VISIBILITIES),
        ("access_level", PUBLIC_EXPORT_BLOCKING_ACCESS_LEVELS),
        ("restriction_state", PUBLIC_EXPORT_BLOCKING_RESTRICTION_STATES),
        ("rights_status", PUBLIC_EXPORT_BLOCKING_RIGHTS_STATUSES),
        ("source_type", PUBLIC_EXPORT_BLOCKING_SOURCE_TYPES),
        ("source_ownership", PUBLIC_EXPORT_BLOCKING_SOURCE_OWNERSHIPS),
        ("ownership_scope", PUBLIC_EXPORT_BLOCKING_OWNERSHIP_SCOPES),
    )

    for field_name, blocked_values in blocking_checks:
        if normalized.get(field_name) in blocked_values:
            return True

    flags = set(normalize_content_flags(normalized.get("content_flags")))
    return bool(flags.intersection(PUBLIC_EXPORT_BLOCKING_CONTENT_FLAGS))


def is_public_export_safe(metadata: dict[str, Any]) -> bool:
    return _is_yes(metadata.get("export_to_public")) and not is_public_export_blocked(metadata)


def is_uckk_export_blocked(metadata: dict[str, Any]) -> bool:
    """Return True only when UCKK export is requested and unsafe."""
    normalized = normalize_rule_input(metadata)

    if not _is_yes(normalized.get("export_to_uckk")):
        return False

    if normalized.get("uckk_relevance") in UCKK_EXPORT_BLOCKING_RELEVANCE_VALUES:
        return True

    if normalized.get("target_system") != UCKK_EXPORT_REQUIRED_TARGET_SYSTEM:
        return True

    if _as_int(normalized.get("target_export_allowed")) != 1:
        return True

    if normalized.get("restriction_state") in REVIEW_REQUIRED_RESTRICTION_STATES:
        return True

    return False


def is_uckk_export_safe(metadata: dict[str, Any]) -> bool:
    return _is_yes(metadata.get("export_to_uckk")) and not is_uckk_export_blocked(metadata)


def should_require_human_review(metadata: dict[str, Any]) -> bool:
    normalized = normalize_rule_input(metadata)
    return _source_or_rights_require_review(normalized) or _restriction_requires_review(normalized)


def requires_human_review(metadata: dict[str, Any]) -> bool:
    return should_require_human_review(metadata)


def normalize_content_flags(value: Any) -> list[str]:
    if value in (None, "", []):
        return []

    if isinstance(value, list | tuple | set):
        return sorted({_clean_string(item) for item in value if _clean_string(item)})

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []

        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None

            if isinstance(parsed, list):
                return sorted({_clean_string(item) for item in parsed if _clean_string(item)})

        return sorted({_clean_string(part) for part in text.split(";") if _clean_string(part)})

    cleaned = _clean_string(value)
    return [cleaned] if cleaned else []


def make_rule_message(
    code: str,
    severity: str,
    message: str,
    *,
    field: str | None = None,
    row_number: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "field": field,
        "row_number": row_number,
        "details": details or {},
    }


def _source_or_rights_require_review(metadata: dict[str, Any]) -> bool:
    return (
        metadata.get("rights_status") in REVIEW_REQUIRED_RIGHTS_STATUSES
        or metadata.get("source_type") in REVIEW_REQUIRED_SOURCE_TYPES
        or metadata.get("source_ownership") in REVIEW_REQUIRED_SOURCE_OWNERSHIPS
    )


def _restriction_requires_review(metadata: dict[str, Any]) -> bool:
    if metadata.get("restriction_state") in REVIEW_REQUIRED_RESTRICTION_STATES:
        return True

    if metadata.get("visibility") in REVIEW_REQUIRED_VISIBILITIES:
        return True

    return False


def _has_valid_review_marker(metadata: dict[str, Any]) -> bool:
    if _as_int(metadata.get("human_review_required", 0)) != 1:
        return False

    review_reason = _clean_string(metadata.get("review_reason"))
    review_queue = _clean_string(metadata.get("review_queue"))
    return bool(review_reason or review_queue)


def _rule_result(
    *,
    warnings: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    return {
        "warnings": warnings or [],
        "errors": errors or [],
    }


def _is_yes(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value == 1

    return str(value).strip().lower() in _YES_VALUES


def _as_int(value: Any) -> int | Any:
    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _YES_VALUES:
            return 1
        if lowered in _NO_VALUES:
            return 0

    return value


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "PUBLIC_EXPORT_BLOCKING_ACCESS_LEVELS",
    "PUBLIC_EXPORT_BLOCKING_CONTENT_FLAGS",
    "PUBLIC_EXPORT_BLOCKING_OWNERSHIP_SCOPES",
    "PUBLIC_EXPORT_BLOCKING_PUBLIC_STATES",
    "PUBLIC_EXPORT_BLOCKING_RESTRICTION_STATES",
    "PUBLIC_EXPORT_BLOCKING_RIGHTS_STATUSES",
    "PUBLIC_EXPORT_BLOCKING_SOURCE_OWNERSHIPS",
    "PUBLIC_EXPORT_BLOCKING_SOURCE_TYPES",
    "PUBLIC_EXPORT_BLOCKING_VISIBILITIES",
    "REVIEW_REQUIRED_CONTENT_FLAGS",
    "REVIEW_REQUIRED_OWNERSHIP_SCOPES",
    "REVIEW_REQUIRED_PUBLIC_STATES",
    "REVIEW_REQUIRED_RESTRICTION_STATES",
    "REVIEW_REQUIRED_RIGHTS_STATUSES",
    "REVIEW_REQUIRED_SOURCE_OWNERSHIPS",
    "REVIEW_REQUIRED_SOURCE_TYPES",
    "REVIEW_REQUIRED_VISIBILITIES",
    "RULE_BLOCKED_PUBLIC_EXPORT",
    "RULE_BLOCKED_UCKK_EXPORT",
    "RULE_BLOCKED_VERIFIED_BY_AI",
    "RULE_INVALID_CONTENT_FLAG",
    "RULE_INVALID_EXPORT_DECISION",
    "RULE_RESTRICTED_CONTENT",
    "RULE_REVIEW_REQUIRED",
    "RULE_UNKNOWN_RIGHTS",
    "RULE_UNKNOWN_SOURCE",
    "SEVERITY_BLOCKING",
    "SEVERITY_ERROR",
    "SEVERITY_INFO",
    "SEVERITY_WARNING",
    "UCKK_EXPORT_BLOCKING_RELEVANCE_VALUES",
    "UCKK_EXPORT_REQUIRED_TARGET_SYSTEM",
    "apply_required_review_defaults",
    "check_canonical_validation_rule",
    "check_content_flag_rules",
    "check_export_decision_values",
    "check_public_export_rules",
    "check_restriction_review_rules",
    "check_uckk_export_rules",
    "check_unknown_source_and_rights_rules",
    "evaluate_blocking_rules",
    "is_public_export_blocked",
    "is_public_export_safe",
    "is_uckk_export_blocked",
    "is_uckk_export_safe",
    "is_verified_without_override",
    "make_rule_message",
    "normalize_content_flags",
    "normalize_rule_input",
    "requires_human_review",
    "should_require_human_review",
]