# tests/python/test_blocking_rules.py

from __future__ import annotations

from typing import Any

import pytest

from conftest import assert_validation_result_shape, import_app_callable


def _rules_callable(name: str):
    return import_app_callable("validation.blocking_rules", name)


def _message_codes(messages: list[Any]) -> set[str]:
    codes: set[str] = set()

    for message in messages:
        if isinstance(message, dict):
            code = message.get("code")
        else:
            code = getattr(message, "code", None)

        if code:
            codes.add(str(code))

    return codes


@pytest.mark.contract
@pytest.mark.validation
def test_blocking_rules_public_api_exists() -> None:
    required_callables = [
        "evaluate_blocking_rules",
        "requires_human_review",
        "is_public_export_blocked",
        "is_uckk_export_blocked",
        "is_verified_without_override",
    ]

    for callable_name in required_callables:
        assert callable(_rules_callable(callable_name))


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_accepts_safe_unverified_metadata(
    sample_metadata_valid: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_valid)
    metadata["canonical_validation_state"] = "unverified"
    metadata["rights_status"] = "owned"
    metadata["source_type"] = "produced_by_uckk"
    metadata["source_ownership"] = "uckk_created"
    metadata["human_review_required"] = 0
    metadata["review_reason"] = ""
    metadata["export_to_public"] = "no"
    metadata["export_to_uckk"] = "no"

    result = evaluate_blocking_rules(
        metadata,
        allow_human_verified_override=False,
    )
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False
    assert data["errors"] == []


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_blocks_verified_without_override(
    sample_metadata_verified_blocked: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    result = evaluate_blocking_rules(
        sample_metadata_verified_blocked,
        allow_human_verified_override=False,
    )
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_VERIFIED" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_allows_verified_with_human_override(
    sample_metadata_verified_blocked: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_verified_blocked)
    metadata["rights_status"] = "owned"
    metadata["source_type"] = "produced_by_uckk"
    metadata["source_ownership"] = "uckk_created"

    result = evaluate_blocking_rules(
        metadata,
        allow_human_verified_override=True,
    )
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False


@pytest.mark.contract
@pytest.mark.validation
def test_is_verified_without_override_detects_ai_verified_state(
    sample_metadata_verified_blocked: dict[str, Any],
) -> None:
    is_verified_without_override = _rules_callable("is_verified_without_override")

    assert (
        is_verified_without_override(
            sample_metadata_verified_blocked,
            allow_human_verified_override=False,
        )
        is True
    )

    assert (
        is_verified_without_override(
            sample_metadata_verified_blocked,
            allow_human_verified_override=True,
        )
        is False
    )


@pytest.mark.contract
@pytest.mark.validation
def test_requires_human_review_returns_true_for_unknown_rights(
    sample_metadata_valid: dict[str, Any],
) -> None:
    requires_human_review = _rules_callable("requires_human_review")

    metadata = dict(sample_metadata_valid)
    metadata["rights_status"] = "unknown"
    metadata["source_type"] = "unknown"
    metadata["source_ownership"] = "unknown_source"
    metadata["human_review_required"] = 0
    metadata["review_reason"] = ""

    assert requires_human_review(metadata) is True


@pytest.mark.contract
@pytest.mark.validation
def test_requires_human_review_returns_false_when_rights_are_clear(
    sample_metadata_valid: dict[str, Any],
) -> None:
    requires_human_review = _rules_callable("requires_human_review")

    metadata = dict(sample_metadata_valid)
    metadata["rights_status"] = "owned"
    metadata["source_type"] = "produced_by_uckk"
    metadata["source_ownership"] = "uckk_created"
    metadata["ownership_scope"] = "uckk_owned"
    metadata["human_review_required"] = 0
    metadata["review_reason"] = ""

    assert requires_human_review(metadata) is False


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_blocks_unknown_rights_without_review_flag(
    sample_metadata_valid: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_valid)
    metadata["rights_status"] = "unknown"
    metadata["source_type"] = "unknown"
    metadata["source_ownership"] = "unknown_source"
    metadata["human_review_required"] = 0
    metadata["review_reason"] = ""

    result = evaluate_blocking_rules(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_REVIEW_REQUIRED" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_accepts_unknown_rights_with_review_flag(
    sample_metadata_valid: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_valid)
    metadata["rights_status"] = "unknown"
    metadata["source_type"] = "unknown"
    metadata["source_ownership"] = "unknown_source"
    metadata["human_review_required"] = 1
    metadata["review_queue"] = "rights_review"
    metadata["review_reason"] = "Droits inconnus."

    result = evaluate_blocking_rules(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False


@pytest.mark.contract
@pytest.mark.validation
def test_is_public_export_blocked_returns_true_for_non_public_record(
    sample_metadata_valid: dict[str, Any],
) -> None:
    is_public_export_blocked = _rules_callable("is_public_export_blocked")

    metadata = dict(sample_metadata_valid)
    metadata["public_state"] = "non_public"
    metadata["visibility"] = "private"
    metadata["export_to_public"] = "yes"

    assert is_public_export_blocked(metadata) is True


@pytest.mark.contract
@pytest.mark.validation
def test_is_public_export_blocked_returns_false_for_non_exported_private_record(
    sample_metadata_valid: dict[str, Any],
) -> None:
    is_public_export_blocked = _rules_callable("is_public_export_blocked")

    metadata = dict(sample_metadata_valid)
    metadata["public_state"] = "private"
    metadata["visibility"] = "private"
    metadata["export_to_public"] = "no"

    assert is_public_export_blocked(metadata) is False


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_blocks_public_export_for_private_record(
    sample_metadata_valid: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_valid)
    metadata["public_state"] = "private"
    metadata["visibility"] = "private"
    metadata["export_to_public"] = "yes"
    metadata["human_review_required"] = 1
    metadata["review_reason"] = "Private record cannot be public-exported."

    result = evaluate_blocking_rules(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_PUBLIC_EXPORT" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_is_uckk_export_blocked_returns_true_for_not_uckk_record(
    sample_metadata_valid: dict[str, Any],
) -> None:
    is_uckk_export_blocked = _rules_callable("is_uckk_export_blocked")

    metadata = dict(sample_metadata_valid)
    metadata["uckk_relevance"] = "not_uckk"
    metadata["target_system"] = "none"
    metadata["target_export_allowed"] = 1
    metadata["export_to_uckk"] = "yes"

    assert is_uckk_export_blocked(metadata) is True


@pytest.mark.contract
@pytest.mark.validation
def test_is_uckk_export_blocked_returns_false_for_candidate_export(
    sample_metadata_valid: dict[str, Any],
) -> None:
    is_uckk_export_blocked = _rules_callable("is_uckk_export_blocked")

    metadata = dict(sample_metadata_valid)
    metadata["uckk_relevance"] = "uckk_related"
    metadata["target_system"] = "uckkarchive"
    metadata["target_export_allowed"] = 1
    metadata["export_to_uckk"] = "yes"

    assert is_uckk_export_blocked(metadata) is False


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_blocks_uckk_export_for_not_uckk_record(
    sample_metadata_valid: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_valid)
    metadata["uckk_relevance"] = "not_uckk"
    metadata["target_system"] = "none"
    metadata["target_export_allowed"] = 1
    metadata["export_to_uckk"] = "yes"
    metadata["human_review_required"] = 1
    metadata["review_reason"] = "Not UCKK."

    result = evaluate_blocking_rules(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_UCKK_EXPORT" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_blocks_confidential_public_export(
    sample_metadata_valid: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_valid)
    metadata["public_state"] = "confidential"
    metadata["visibility"] = "restricted"
    metadata["access_level"] = "confidential"
    metadata["restriction_state"] = "confidential"
    metadata["export_to_public"] = "yes"
    metadata["human_review_required"] = 1
    metadata["review_reason"] = "Confidential record."

    result = evaluate_blocking_rules(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_PUBLIC_EXPORT" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_requires_review_for_cultural_restriction(
    sample_metadata_valid: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_valid)
    metadata["restriction_state"] = "cultural"
    metadata["visibility"] = "restricted_cultural"
    metadata["audience_suitability"] = "restricted_cultural"
    metadata["human_review_required"] = 0
    metadata["review_reason"] = ""

    result = evaluate_blocking_rules(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_REVIEW_REQUIRED" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_evaluate_blocking_rules_normalizes_no_errors_for_non_exportable_record(
    sample_metadata_valid: dict[str, Any],
) -> None:
    evaluate_blocking_rules = _rules_callable("evaluate_blocking_rules")

    metadata = dict(sample_metadata_valid)
    metadata["uckk_relevance"] = "not_uckk"
    metadata["target_system"] = "none"
    metadata["target_export_allowed"] = 0
    metadata["export_to_uckk"] = "no"
    metadata["export_to_public"] = "no"
    metadata["public_state"] = "private"
    metadata["visibility"] = "private"
    metadata["rights_status"] = "owned"
    metadata["source_type"] = "imported"
    metadata["source_ownership"] = "member_submitted"
    metadata["human_review_required"] = 0
    metadata["review_reason"] = ""

    result = evaluate_blocking_rules(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False
    assert data["errors"] == []