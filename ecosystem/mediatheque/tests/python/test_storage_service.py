# tests/python/test_storage_service.py

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from conftest import assert_operation_result_shape, import_app_callable


def _service_callable(name: str):
    return import_app_callable("services.storage_service", name)


def _result_data(result: Any) -> dict[str, Any]:
    data = assert_operation_result_shape(result)
    assert "data" in data
    assert isinstance(data["data"], dict)
    return data


@pytest.mark.contract
@pytest.mark.files
def test_storage_service_public_api_exists() -> None:
    required_callables = [
        "resolve_storage_dir",
        "build_canonical_storage_filename",
        "copy_into_storage",
    ]

    for callable_name in required_callables:
        assert callable(_service_callable(callable_name))


@pytest.mark.contract
@pytest.mark.files
def test_resolve_storage_dir_returns_existing_canonical_area(
    storage_root: Path,
) -> None:
    resolve_storage_dir = _service_callable("resolve_storage_dir")

    path = resolve_storage_dir(storage_root, "media_original")

    assert isinstance(path, Path)
    assert path == storage_root / "media_original"
    assert path.exists()
    assert path.is_dir()


@pytest.mark.contract
@pytest.mark.files
def test_resolve_storage_dir_creates_missing_canonical_area(
    tmp_path: Path,
) -> None:
    resolve_storage_dir = _service_callable("resolve_storage_dir")

    storage_root = tmp_path / "02_STORAGE"
    target = resolve_storage_dir(storage_root, "media_original")

    assert target == storage_root / "media_original"
    assert target.exists()
    assert target.is_dir()


@pytest.mark.contract
@pytest.mark.files
@pytest.mark.parametrize(
    "filearea",
    [
        "media_original",
        "media_preview",
        "media_thumbnail",
        "media_derivative",
        "media_caption",
        "media_transcript",
        "media_attachment",
        "content_review_files",
        "external_work_reference_files",
        "cultural_protocol_files",
    ],
)
def test_resolve_storage_dir_accepts_all_canonical_fileareas(
    storage_root: Path,
    filearea: str,
) -> None:
    resolve_storage_dir = _service_callable("resolve_storage_dir")

    path = resolve_storage_dir(storage_root, filearea)

    assert path == storage_root / filearea
    assert path.exists()
    assert path.is_dir()


@pytest.mark.contract
@pytest.mark.files
def test_resolve_storage_dir_rejects_unknown_filearea(
    storage_root: Path,
) -> None:
    resolve_storage_dir = _service_callable("resolve_storage_dir")

    with pytest.raises(ValueError):
        resolve_storage_dir(storage_root, "not_a_canonical_filearea")


@pytest.mark.contract
@pytest.mark.files
@pytest.mark.parametrize(
    ("original_filename", "expected_suffix"),
    [
        ("sample_file.txt", ".txt"),
        ("Document.PDF", ".pdf"),
        ("archive.tar.gz", ".gz"),
        ("README", ""),
    ],
)
def test_build_canonical_storage_filename_preserves_version_uuid_and_extension(
    original_filename: str,
    expected_suffix: str,
) -> None:
    build_canonical_storage_filename = _service_callable(
        "build_canonical_storage_filename"
    )

    version_uuid = "22222222-2222-4222-8222-222222222222"
    filename = build_canonical_storage_filename(version_uuid, original_filename)

    assert filename.startswith(version_uuid)
    assert filename.endswith(expected_suffix)
    assert "/" not in filename
    assert "\\" not in filename


@pytest.mark.contract
@pytest.mark.files
def test_build_canonical_storage_filename_rejects_empty_version_uuid() -> None:
    build_canonical_storage_filename = _service_callable(
        "build_canonical_storage_filename"
    )

    with pytest.raises(ValueError):
        build_canonical_storage_filename("", "sample_file.txt")


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_copies_file_to_default_media_original(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    version_uuid = "22222222-2222-4222-8222-222222222222"
    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="media_original",
        version_uuid=version_uuid,
        mode="copy_to_storage",
    )
    data = _result_data(result)

    assert data["success"] is True
    assert data["operation"] == "copy_into_storage"
    assert data["result"] in {"copied", "stored", "created"}
    assert data["path"]

    stored_path = Path(data["path"])

    assert stored_path.exists()
    assert stored_path.is_file()
    assert stored_path.parent == storage_root / "media_original"
    assert stored_path.name.startswith(version_uuid)
    assert stored_path.suffix == ".txt"
    assert stored_path.read_bytes() == sample_file_path.read_bytes()


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_returns_file_facts_in_result_data(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="media_original",
        version_uuid="33333333-3333-4333-8333-333333333333",
        mode="copy_to_storage",
    )
    data = _result_data(result)

    expected_hash = hashlib.sha256(sample_file_path.read_bytes()).hexdigest()

    assert data["success"] is True
    assert data["data"]["filename"] == sample_file_path.name
    assert data["data"]["extension"] == ".txt"
    assert data["data"]["filesize"] == sample_file_path.stat().st_size
    assert data["data"]["sha256"] == expected_hash
    assert data["data"]["filearea"] == "media_original"


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_supports_non_default_canonical_filearea(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="media_attachment",
        version_uuid="44444444-4444-4444-8444-444444444444",
        mode="copy_to_storage",
    )
    data = _result_data(result)

    assert data["success"] is True

    stored_path = Path(data["path"])
    assert stored_path.exists()
    assert stored_path.parent == storage_root / "media_attachment"
    assert data["data"]["filearea"] == "media_attachment"


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_generates_version_uuid_when_absent(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="media_original",
        version_uuid=None,
        mode="copy_to_storage",
    )
    data = _result_data(result)

    assert data["success"] is True
    assert data["version_uuid"]
    assert isinstance(data["version_uuid"], str)

    stored_path = Path(data["path"])
    assert stored_path.exists()
    assert stored_path.name.startswith(data["version_uuid"])


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_reference_only_does_not_copy_file(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="media_original",
        version_uuid="55555555-5555-4555-8555-555555555555",
        mode="reference_only",
    )
    data = _result_data(result)

    assert data["success"] is True
    assert data["result"] in {"referenced", "reference_only"}
    assert data["path"] == str(sample_file_path)
    assert not any((storage_root / "media_original").iterdir())


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_copy_and_rename_uses_canonical_filename(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    version_uuid = "66666666-6666-4666-8666-666666666666"
    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="media_original",
        version_uuid=version_uuid,
        mode="copy_and_rename",
    )
    data = _result_data(result)

    assert data["success"] is True

    stored_path = Path(data["path"])
    assert stored_path.exists()
    assert stored_path.name == f"{version_uuid}.txt"


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_rejects_missing_source_file(
    tmp_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    missing = tmp_path / "missing.txt"

    result = copy_into_storage(
        missing,
        storage_root,
        filearea="media_original",
        version_uuid="77777777-7777-4777-8777-777777777777",
        mode="copy_to_storage",
    )
    data = _result_data(result)

    assert data["success"] is False
    assert data["errors"]


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_rejects_invalid_filearea(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="invalid_area",
        version_uuid="88888888-8888-4888-8888-888888888888",
        mode="copy_to_storage",
    )
    data = _result_data(result)

    assert data["success"] is False
    assert data["errors"]


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_rejects_invalid_mode(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="media_original",
        version_uuid="99999999-9999-4999-8999-999999999999",
        mode="invalid_mode",
    )
    data = _result_data(result)

    assert data["success"] is False
    assert data["errors"]


@pytest.mark.contract
@pytest.mark.files
def test_copy_into_storage_does_not_mutate_source_file(
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    copy_into_storage = _service_callable("copy_into_storage")

    before = sample_file_path.read_bytes()

    result = copy_into_storage(
        sample_file_path,
        storage_root,
        filearea="media_original",
        version_uuid="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        mode="copy_to_storage",
    )
    data = _result_data(result)

    after = sample_file_path.read_bytes()

    assert data["success"] is True
    assert after == before
    assert Path(data["path"]).read_bytes() == before