# tests/python/test_file_facts.py

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from conftest import import_app_callable


def _service_callable(name: str):
    return import_app_callable("services.file_facts", name)


def _file_facts_to_dict(file_facts: Any) -> dict[str, Any]:
    if isinstance(file_facts, dict):
        return file_facts

    data: dict[str, Any] = {}
    for key in (
        "original_path",
        "filename",
        "extension",
        "mimetype",
        "filesize",
        "sha256",
    ):
        if hasattr(file_facts, key):
            data[key] = getattr(file_facts, key)

    if not data:
        pytest.fail(
            f"Expected FileFacts-like object or dict, got {type(file_facts)!r}",
            pytrace=False,
        )

    return data


@pytest.mark.contract
@pytest.mark.files
def test_file_facts_public_api_exists() -> None:
    required_callables = [
        "calculate_sha256",
        "detect_mimetype",
        "get_file_facts",
        "is_external_reference_path",
    ]

    for callable_name in required_callables:
        assert callable(_service_callable(callable_name))


@pytest.mark.contract
@pytest.mark.files
def test_calculate_sha256_returns_lowercase_hex_digest(
    sample_file_path: Path,
) -> None:
    calculate_sha256 = _service_callable("calculate_sha256")

    expected = hashlib.sha256(sample_file_path.read_bytes()).hexdigest()
    actual = calculate_sha256(sample_file_path)

    assert actual == expected
    assert len(actual) == 64
    assert actual == actual.lower()
    assert all(character in "0123456789abcdef" for character in actual)


@pytest.mark.contract
@pytest.mark.files
def test_calculate_sha256_is_stable_for_same_file(
    sample_file_path: Path,
) -> None:
    calculate_sha256 = _service_callable("calculate_sha256")

    first = calculate_sha256(sample_file_path)
    second = calculate_sha256(sample_file_path)

    assert first == second


@pytest.mark.contract
@pytest.mark.files
def test_calculate_sha256_changes_when_file_content_changes(
    tmp_path: Path,
) -> None:
    calculate_sha256 = _service_callable("calculate_sha256")

    path = tmp_path / "hash_test.txt"
    path.write_text("first content\n", encoding="utf-8")
    first = calculate_sha256(path)

    path.write_text("second content\n", encoding="utf-8")
    second = calculate_sha256(path)

    assert first != second


@pytest.mark.contract
@pytest.mark.files
def test_calculate_sha256_raises_for_missing_file(
    tmp_path: Path,
) -> None:
    calculate_sha256 = _service_callable("calculate_sha256")

    missing = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        calculate_sha256(missing)


@pytest.mark.contract
@pytest.mark.files
def test_detect_mimetype_returns_text_plain_for_txt_file(
    sample_file_path: Path,
) -> None:
    detect_mimetype = _service_callable("detect_mimetype")

    mimetype = detect_mimetype(sample_file_path)

    assert mimetype is None or isinstance(mimetype, str)
    if mimetype is not None:
        assert mimetype in {
            "text/plain",
            "text/x-python",
            "application/octet-stream",
        } or mimetype.startswith("text/")


@pytest.mark.contract
@pytest.mark.files
def test_get_file_facts_returns_required_shape(
    sample_file_path: Path,
) -> None:
    get_file_facts = _service_callable("get_file_facts")

    file_facts = get_file_facts(sample_file_path)
    data = _file_facts_to_dict(file_facts)

    assert set(data) >= {
        "original_path",
        "filename",
        "extension",
        "mimetype",
        "filesize",
        "sha256",
    }

    assert data["original_path"] == str(sample_file_path)
    assert data["filename"] == sample_file_path.name
    assert data["extension"] == ".txt"
    assert data["filesize"] == sample_file_path.stat().st_size
    assert data["sha256"] == hashlib.sha256(sample_file_path.read_bytes()).hexdigest()


@pytest.mark.contract
@pytest.mark.files
def test_get_file_facts_does_not_invent_missing_file_facts(
    tmp_path: Path,
) -> None:
    get_file_facts = _service_callable("get_file_facts")

    missing = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        get_file_facts(missing)


@pytest.mark.contract
@pytest.mark.files
def test_get_file_facts_handles_file_without_extension(
    tmp_path: Path,
) -> None:
    get_file_facts = _service_callable("get_file_facts")

    path = tmp_path / "README"
    path.write_text("No extension file.\n", encoding="utf-8")

    file_facts = get_file_facts(path)
    data = _file_facts_to_dict(file_facts)

    assert data["filename"] == "README"
    assert data["extension"] == ""
    assert data["filesize"] == path.stat().st_size
    assert data["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.contract
@pytest.mark.files
def test_get_file_facts_handles_uppercase_extension_without_renaming(
    tmp_path: Path,
) -> None:
    get_file_facts = _service_callable("get_file_facts")

    path = tmp_path / "Document.PDF"
    path.write_bytes(b"%PDF-1.4\n% test pdf fixture\n")

    file_facts = get_file_facts(path)
    data = _file_facts_to_dict(file_facts)

    assert data["filename"] == "Document.PDF"
    assert data["extension"] == ".pdf"
    assert data["filesize"] == path.stat().st_size
    assert data["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.contract
@pytest.mark.files
@pytest.mark.parametrize(
    "path_value",
    [
        "https://example.org/document.pdf",
        "http://example.org/document.pdf",
        "doi:10.1234/example",
        "urn:isbn:9780000000000",
        "external://third-party-work",
    ],
)
def test_is_external_reference_path_returns_true_for_external_references(
    path_value: str,
) -> None:
    is_external_reference_path = _service_callable("is_external_reference_path")

    assert is_external_reference_path(path_value) is True


@pytest.mark.contract
@pytest.mark.files
@pytest.mark.parametrize(
    "path_value",
    [
        "/tmp/local-file.pdf",
        "C:/Users/example/local-file.pdf",
        "C:\\Users\\example\\local-file.pdf",
        "./relative-file.pdf",
        "../relative-file.pdf",
        "media_original/file.pdf",
    ],
)
def test_is_external_reference_path_returns_false_for_local_paths(
    path_value: str,
) -> None:
    is_external_reference_path = _service_callable("is_external_reference_path")

    assert is_external_reference_path(path_value) is False


@pytest.mark.contract
@pytest.mark.files
def test_file_facts_are_computed_locally_not_from_metadata(
    sample_file_path: Path,
    sample_metadata_valid: dict[str, Any],
) -> None:
    get_file_facts = _service_callable("get_file_facts")

    metadata = dict(sample_metadata_valid)
    metadata["sha256"] = "f" * 64
    metadata["filesize"] = 999999
    metadata["mimetype"] = "application/fake"
    metadata["filename"] = "ai_invented.txt"
    metadata["extension"] = ".fake"

    file_facts = get_file_facts(sample_file_path)
    data = _file_facts_to_dict(file_facts)

    assert data["sha256"] != metadata["sha256"]
    assert data["filesize"] != metadata["filesize"]
    assert data["filename"] == sample_file_path.name
    assert data["extension"] == ".txt"