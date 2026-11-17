# tests/python/test_json_validation.py

from __future__ import annotations

import json
from typing import Any

import pytest

from conftest import assert_validation_result_shape, import_app_callable


def _service_callable(name: str):
    return import_app_callable("services.json_validation_service", name)


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
def test_json_validation_public_api_exists() -> None:
    required_callables = [
        "parse_json_text",
        "validate_chatgpt_json",
        "validate_metadata_dict",
        "normalize_metadata_dict",
    ]

    for callable_name in required_callables:
        assert callable(_service_callable(callable_name))


@pytest.mark.contract
@pytest.mark.validation
def test_parse_json_text_accepts_valid_json(
    sample_metadata_valid_json: str,
) -> None:
    parse_json_text = _service_callable("parse_json_text")

    result = parse_json_text(sample_metadata_valid_json)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False
    assert data["normalized_data"]["title"] == "Document de test kOA"
    assert data["errors"] == []


@pytest.mark.contract
@pytest.mark.validation
def test_parse_json_text_rejects_invalid_json() -> None:
    parse_json_text = _service_callable("parse_json_text")

    result = parse_json_text("{not valid json")
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True
    assert data["errors"]

    codes = _message_codes(data["errors"])
    assert "ERR_JSON_PARSE" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_validate_chatgpt_json_accepts_valid_metadata(
    sample_metadata_valid_json: str,
) -> None:
    validate_chatgpt_json = _service_callable("validate_chatgpt_json")

    result = validate_chatgpt_json(
        sample_metadata_valid_json,
        allow_human_verified_override=False,
    )
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False
    assert data["errors"] == []

    normalized = data["normalized_data"]
    assert normalized["title"] == "Document de test kOA"
    assert normalized["canonical_validation_state"] == "unverified"
    assert normalized["human_review_required"] == 1
    assert normalized["visibility"] == "private"


@pytest.mark.contract
@pytest.mark.validation
def test_validate_chatgpt_json_blocks_invalid_enum(
    sample_metadata_invalid_enum_json: str,
) -> None:
    validate_chatgpt_json = _service_callable("validate_chatgpt_json")

    result = validate_chatgpt_json(sample_metadata_invalid_enum_json)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True
    assert data["errors"]

    codes = _message_codes(data["errors"])
    assert "ERR_INVALID_ENUM" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_validate_chatgpt_json_blocks_verified_without_human_override(
    sample_metadata_verified_blocked_json: str,
) -> None:
    validate_chatgpt_json = _service_callable("validate_chatgpt_json")

    result = validate_chatgpt_json(
        sample_metadata_verified_blocked_json,
        allow_human_verified_override=False,
    )
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_VERIFIED" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_validate_chatgpt_json_allows_verified_with_explicit_human_override(
    sample_metadata_verified_blocked_json: str,
) -> None:
    validate_chatgpt_json = _service_callable("validate_chatgpt_json")

    result = validate_chatgpt_json(
        sample_metadata_verified_blocked_json,
        allow_human_verified_override=True,
    )
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False
    assert data["normalized_data"]["canonical_validation_state"] == "verified"


@pytest.mark.contract
@pytest.mark.validation
def test_validate_metadata_dict_accepts_dict_input(
    sample_metadata_valid: dict[str, Any],
) -> None:
    validate_metadata_dict = _service_callable("validate_metadata_dict")

    result = validate_metadata_dict(sample_metadata_valid)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False
    assert data["normalized_data"]["title"] == sample_metadata_valid["title"]


@pytest.mark.contract
@pytest.mark.validation
def test_validate_metadata_dict_rejects_missing_required_field(
    sample_metadata_valid: dict[str, Any],
) -> None:
    validate_metadata_dict = _service_callable("validate_metadata_dict")

    metadata = dict(sample_metadata_valid)
    metadata.pop("title")

    result = validate_metadata_dict(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_REQUIRED_FIELD" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_validate_metadata_dict_rejects_invalid_type(
    sample_metadata_valid: dict[str, Any],
) -> None:
    validate_metadata_dict = _service_callable("validate_metadata_dict")

    metadata = dict(sample_metadata_valid)
    metadata["human_review_required"] = "yes"

    result = validate_metadata_dict(metadata)
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_INVALID_TYPE" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_normalize_metadata_dict_preserves_controlled_values(
    sample_metadata_valid: dict[str, Any],
) -> None:
    normalize_metadata_dict = _service_callable("normalize_metadata_dict")

    normalized = normalize_metadata_dict(sample_metadata_valid)

    assert isinstance(normalized, dict)
    assert normalized["visibility"] == "private"
    assert normalized["public_state"] == "unknown"
    assert normalized["canonical_validation_state"] == "unverified"
    assert normalized["export_to_uckk"] == "no"
    assert normalized["export_to_public"] == "no"


@pytest.mark.contract
@pytest.mark.validation
def test_normalize_metadata_dict_defaults_missing_validation_state(
    sample_metadata_valid: dict[str, Any],
) -> None:
    normalize_metadata_dict = _service_callable("normalize_metadata_dict")

    metadata = dict(sample_metadata_valid)
    metadata.pop("canonical_validation_state")

    normalized = normalize_metadata_dict(metadata)

    assert normalized["canonical_validation_state"] == "unverified"


@pytest.mark.contract
@pytest.mark.validation
def test_validate_chatgpt_json_does_not_accept_technical_file_facts_from_ai(
    sample_metadata_valid: dict[str, Any],
) -> None:
    validate_chatgpt_json = _service_callable("validate_chatgpt_json")

    metadata = dict(sample_metadata_valid)
    metadata["sha256"] = "f" * 64
    metadata["filesize"] = 999999
    metadata["mimetype"] = "application/fake"
    metadata["filename"] = "ai_invented_filename.pdf"
    metadata["extension"] = ".pdf"
    metadata["original_path"] = "/ai/invented/path"
    metadata["storage_path"] = "/ai/invented/storage"

    result = validate_chatgpt_json(json.dumps(metadata, ensure_ascii=False))
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is True
    assert data["is_blocked"] is False

    normalized = data["normalized_data"]
    for forbidden_field in (
        "sha256",
        "filesize",
        "mimetype",
        "filename",
        "extension",
        "original_path",
        "storage_path",
    ):
        assert forbidden_field not in normalized


@pytest.mark.contract
@pytest.mark.validation
def test_validate_chatgpt_json_requires_review_for_unknown_rights(
    sample_metadata_valid: dict[str, Any],
) -> None:
    validate_chatgpt_json = _service_callable("validate_chatgpt_json")

    metadata = dict(sample_metadata_valid)
    metadata["rights_status"] = "unknown"
    metadata["source_type"] = "unknown"
    metadata["human_review_required"] = 0
    metadata["review_reason"] = ""

    result = validate_chatgpt_json(json.dumps(metadata, ensure_ascii=False))
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_REVIEW_REQUIRED" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_validate_chatgpt_json_blocks_public_export_for_non_public_record(
    sample_metadata_valid: dict[str, Any],
) -> None:
    validate_chatgpt_json = _service_callable("validate_chatgpt_json")

    metadata = dict(sample_metadata_valid)
    metadata["public_state"] = "non_public"
    metadata["visibility"] = "private"
    metadata["export_to_public"] = "yes"
    metadata["human_review_required"] = 1
    metadata["review_reason"] = "Non-public record cannot be publicly exported."

    result = validate_chatgpt_json(json.dumps(metadata, ensure_ascii=False))
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_PUBLIC_EXPORT" in codes


@pytest.mark.contract
@pytest.mark.validation
def test_validate_chatgpt_json_blocks_uckk_export_when_not_uckk(
    sample_metadata_valid: dict[str, Any],
) -> None:
    validate_chatgpt_json = _service_callable("validate_chatgpt_json")

    metadata = dict(sample_metadata_valid)
    metadata["uckk_relevance"] = "not_uckk"
    metadata["target_system"] = "none"
    metadata["export_to_uckk"] = "yes"
    metadata["target_export_allowed"] = 1
    metadata["human_review_required"] = 1
    metadata["review_reason"] = "Non-UCKK record cannot be exported to UCKK."

    result = validate_chatgpt_json(json.dumps(metadata, ensure_ascii=False))
    data = assert_validation_result_shape(result)

    assert data["is_valid"] is False
    assert data["is_blocked"] is True

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_UCKK_EXPORT" in codes