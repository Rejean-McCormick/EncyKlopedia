# tests/python/test_chatgpt_intake_service.py

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from conftest import assert_operation_result_shape, import_app_callable


def _service_callable(name: str):
    return import_app_callable("services.chatgpt_intake_service", name)


def _table_count(connection: sqlite3.Connection, table_name: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    assert row is not None
    return int(row["count"])


def _row_by_version_uuid(
    connection: sqlite3.Connection,
    version_uuid: str,
) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT * FROM library_rows WHERE version_uuid = ?",
        (version_uuid,),
    ).fetchone()


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


def _extract_preview_row(result_data: dict[str, Any]) -> dict[str, Any]:
    payload = result_data.get("data", {})

    for key in ("preview_row", "library_row", "row"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value

    pytest.fail(
        "preview_chatgpt_intake() result.data must contain preview_row, library_row or row.",
        pytrace=False,
    )


def _extract_version_uuid(result_data: dict[str, Any]) -> str:
    if result_data.get("version_uuid"):
        return str(result_data["version_uuid"])

    row = _extract_preview_row(result_data)
    version_uuid = row.get("version_uuid")

    assert version_uuid
    return str(version_uuid)


def _extract_media_uuid(result_data: dict[str, Any]) -> str:
    if result_data.get("media_uuid"):
        return str(result_data["media_uuid"])

    row = _extract_preview_row(result_data)
    media_uuid = row.get("media_uuid")

    assert media_uuid
    return str(media_uuid)


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_chatgpt_intake_service_public_api_exists() -> None:
    required_callables = [
        "preview_chatgpt_intake",
        "integrate_chatgpt_intake",
    ]

    for callable_name in required_callables:
        assert callable(_service_callable(callable_name))


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_preview_chatgpt_intake_returns_operation_result_without_db_insert(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_valid_json: str,
) -> None:
    preview_chatgpt_intake = _service_callable("preview_chatgpt_intake")

    before_library_rows = _table_count(initialized_connection, "library_rows")
    before_intake_logs = _table_count(initialized_connection, "chatgpt_intake_log")

    result = preview_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_valid_json,
        storage_root=storage_root,
        import_batch="test_preview_batch",
        copy_mode="copy_to_storage",
        allow_human_verified_override=False,
    )
    data = assert_operation_result_shape(result)

    after_library_rows = _table_count(initialized_connection, "library_rows")
    after_intake_logs = _table_count(initialized_connection, "chatgpt_intake_log")

    assert data["success"] is True
    assert data["operation"] == "preview_chatgpt_intake"
    assert data["result"] in {"preview", "validated", "ready"}
    assert data["errors"] == []

    assert after_library_rows == before_library_rows
    assert after_intake_logs == before_intake_logs

    preview_row = _extract_preview_row(data)
    assert preview_row["title"] == "Document de test kOA"
    assert preview_row["filename"] == sample_file_path.name
    assert preview_row["original_path"] == str(sample_file_path)
    assert preview_row["canonical_validation_state"] == "unverified"


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_preview_chatgpt_intake_generates_missing_uuids_locally(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_valid_json: str,
) -> None:
    preview_chatgpt_intake = _service_callable("preview_chatgpt_intake")

    result = preview_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_valid_json,
        storage_root=storage_root,
        import_batch="test_uuid_batch",
        copy_mode="reference_only",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is True

    media_uuid = _extract_media_uuid(data)
    version_uuid = _extract_version_uuid(data)

    assert media_uuid
    assert version_uuid
    assert isinstance(media_uuid, str)
    assert isinstance(version_uuid, str)
    assert media_uuid != version_uuid


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_preview_chatgpt_intake_recalculates_file_facts_locally(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_valid: dict[str, Any],
) -> None:
    preview_chatgpt_intake = _service_callable("preview_chatgpt_intake")

    metadata = dict(sample_metadata_valid)
    metadata["filename"] = "ai_invented_name.pdf"
    metadata["extension"] = ".pdf"
    metadata["mimetype"] = "application/fake"
    metadata["filesize"] = 999999
    metadata["sha256"] = "f" * 64
    metadata["original_path"] = "/ai/invented/path"

    result = preview_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=json.dumps(metadata, ensure_ascii=False),
        storage_root=storage_root,
        import_batch="test_file_facts_batch",
        copy_mode="reference_only",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is True

    preview_row = _extract_preview_row(data)

    assert preview_row["filename"] == sample_file_path.name
    assert preview_row["extension"] == ".txt"
    assert preview_row["filesize"] == sample_file_path.stat().st_size
    assert preview_row["sha256"] != "f" * 64
    assert preview_row["original_path"] == str(sample_file_path)


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_preview_chatgpt_intake_rejects_invalid_json(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    preview_chatgpt_intake = _service_callable("preview_chatgpt_intake")

    result = preview_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response="{not valid json",
        storage_root=storage_root,
        import_batch="test_invalid_json_batch",
        copy_mode="reference_only",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]

    codes = _message_codes(data["errors"])
    assert "ERR_JSON_PARSE" in codes


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_preview_chatgpt_intake_rejects_invalid_enum(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_invalid_enum_json: str,
) -> None:
    preview_chatgpt_intake = _service_callable("preview_chatgpt_intake")

    result = preview_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_invalid_enum_json,
        storage_root=storage_root,
        import_batch="test_invalid_enum_batch",
        copy_mode="reference_only",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]

    codes = _message_codes(data["errors"])
    assert "ERR_INVALID_ENUM" in codes


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_preview_chatgpt_intake_blocks_verified_without_human_override(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_verified_blocked_json: str,
) -> None:
    preview_chatgpt_intake = _service_callable("preview_chatgpt_intake")

    result = preview_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_verified_blocked_json,
        storage_root=storage_root,
        import_batch="test_verified_blocked_batch",
        copy_mode="reference_only",
        allow_human_verified_override=False,
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_VERIFIED" in codes


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_integrate_chatgpt_intake_inserts_library_row_and_log(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_valid_json: str,
) -> None:
    integrate_chatgpt_intake = _service_callable("integrate_chatgpt_intake")

    before_library_rows = _table_count(initialized_connection, "library_rows")
    before_intake_logs = _table_count(initialized_connection, "chatgpt_intake_log")

    result = integrate_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_valid_json,
        storage_root=storage_root,
        import_batch="test_integrate_batch",
        copy_mode="copy_to_storage",
        actor="pytest",
        allow_human_verified_override=False,
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    after_library_rows = _table_count(initialized_connection, "library_rows")
    after_intake_logs = _table_count(initialized_connection, "chatgpt_intake_log")

    assert data["success"] is True
    assert data["operation"] == "integrate_chatgpt_intake"
    assert data["result"] in {"inserted", "integrated", "created"}
    assert data["errors"] == []

    assert after_library_rows == before_library_rows + 1
    assert after_intake_logs == before_intake_logs + 1

    version_uuid = _extract_version_uuid(data)
    media_uuid = _extract_media_uuid(data)

    row = _row_by_version_uuid(initialized_connection, version_uuid)

    assert row is not None
    assert row["version_uuid"] == version_uuid
    assert row["media_uuid"] == media_uuid
    assert row["title"] == "Document de test kOA"
    assert row["filename"] == sample_file_path.name
    assert row["original_path"] == str(sample_file_path)
    assert row["storage_path"]
    assert row["import_batch"] == "test_integrate_batch"
    assert row["canonical_validation_state"] == "unverified"
    assert row["human_review_required"] == 1

    log = initialized_connection.execute(
        """
        SELECT *
        FROM chatgpt_intake_log
        WHERE version_uuid = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (version_uuid,),
    ).fetchone()

    assert log is not None
    assert log["file_path"] == str(sample_file_path)
    assert log["raw_response"] == sample_metadata_valid_json
    assert log["validation_status"] in {"valid", "integrated", "success"}


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_integrate_chatgpt_intake_copies_file_to_storage(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_valid_json: str,
) -> None:
    integrate_chatgpt_intake = _service_callable("integrate_chatgpt_intake")

    result = integrate_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_valid_json,
        storage_root=storage_root,
        import_batch="test_storage_copy_batch",
        copy_mode="copy_to_storage",
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is True

    version_uuid = _extract_version_uuid(data)
    row = _row_by_version_uuid(initialized_connection, version_uuid)

    assert row is not None
    assert row["storage_path"]

    stored_path = Path(row["storage_path"])
    assert stored_path.exists()
    assert stored_path.is_file()
    assert stored_path.parent == storage_root / "media_original"
    assert stored_path.read_bytes() == sample_file_path.read_bytes()


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_integrate_chatgpt_intake_reference_only_does_not_copy_file(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_valid_json: str,
) -> None:
    integrate_chatgpt_intake = _service_callable("integrate_chatgpt_intake")

    result = integrate_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_valid_json,
        storage_root=storage_root,
        import_batch="test_reference_only_batch",
        copy_mode="reference_only",
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is True

    version_uuid = _extract_version_uuid(data)
    row = _row_by_version_uuid(initialized_connection, version_uuid)

    assert row is not None
    assert row["storage_path"] in {"", None, str(sample_file_path)}
    assert not any((storage_root / "media_original").iterdir())


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_integrate_chatgpt_intake_rejects_missing_file(
    initialized_connection: sqlite3.Connection,
    tmp_path: Path,
    storage_root: Path,
    sample_metadata_valid_json: str,
) -> None:
    integrate_chatgpt_intake = _service_callable("integrate_chatgpt_intake")

    missing_file = tmp_path / "missing.txt"

    before_library_rows = _table_count(initialized_connection, "library_rows")

    result = integrate_chatgpt_intake(
        initialized_connection,
        file_path=missing_file,
        raw_response=sample_metadata_valid_json,
        storage_root=storage_root,
        import_batch="test_missing_file_batch",
        copy_mode="copy_to_storage",
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    after_library_rows = _table_count(initialized_connection, "library_rows")

    assert data["success"] is False
    assert data["errors"]
    assert after_library_rows == before_library_rows

    codes = _message_codes(data["errors"])
    assert "ERR_FILE_NOT_FOUND" in codes or data["errors"]


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_integrate_chatgpt_intake_does_not_insert_when_validation_blocked(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_verified_blocked_json: str,
) -> None:
    integrate_chatgpt_intake = _service_callable("integrate_chatgpt_intake")

    before_library_rows = _table_count(initialized_connection, "library_rows")

    result = integrate_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_verified_blocked_json,
        storage_root=storage_root,
        import_batch="test_blocked_insert_batch",
        copy_mode="copy_to_storage",
        actor="pytest",
        allow_human_verified_override=False,
    )
    data = assert_operation_result_shape(result)

    after_library_rows = _table_count(initialized_connection, "library_rows")

    assert data["success"] is False
    assert data["errors"]
    assert after_library_rows == before_library_rows

    codes = _message_codes(data["errors"])
    assert "ERR_BLOCKED_VERIFIED" in codes


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_integrate_chatgpt_intake_allows_verified_with_explicit_override(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_verified_blocked_json: str,
) -> None:
    integrate_chatgpt_intake = _service_callable("integrate_chatgpt_intake")

    result = integrate_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_verified_blocked_json,
        storage_root=storage_root,
        import_batch="test_verified_override_batch",
        copy_mode="reference_only",
        actor="pytest",
        allow_human_verified_override=True,
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is True

    version_uuid = _extract_version_uuid(data)
    row = _row_by_version_uuid(initialized_connection, version_uuid)

    assert row is not None
    assert row["canonical_validation_state"] == "verified"


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_integrate_chatgpt_intake_detects_duplicate_sha256_warning(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_valid: dict[str, Any],
) -> None:
    integrate_chatgpt_intake = _service_callable("integrate_chatgpt_intake")

    first_json = json.dumps(sample_metadata_valid, ensure_ascii=False)

    first = assert_operation_result_shape(
        integrate_chatgpt_intake(
            initialized_connection,
            file_path=sample_file_path,
            raw_response=first_json,
            storage_root=storage_root,
            import_batch="test_duplicate_first_batch",
            copy_mode="reference_only",
            actor="pytest",
        )
    )
    initialized_connection.commit()

    assert first["success"] is True

    second_metadata = dict(sample_metadata_valid)
    second_metadata["title"] = "Document de test kOA — doublon exact"

    second = assert_operation_result_shape(
        integrate_chatgpt_intake(
            initialized_connection,
            file_path=sample_file_path,
            raw_response=json.dumps(second_metadata, ensure_ascii=False),
            storage_root=storage_root,
            import_batch="test_duplicate_second_batch",
            copy_mode="reference_only",
            actor="pytest",
        )
    )
    initialized_connection.commit()

    assert second["success"] is True

    codes = _message_codes(second["warnings"])
    assert "WARN_DUPLICATE_SHA256" in codes or second["warnings"]


@pytest.mark.contract
@pytest.mark.validation
@pytest.mark.files
@pytest.mark.db
def test_integrate_chatgpt_intake_writes_audit_log(
    initialized_connection: sqlite3.Connection,
    sample_file_path: Path,
    storage_root: Path,
    sample_metadata_valid_json: str,
) -> None:
    integrate_chatgpt_intake = _service_callable("integrate_chatgpt_intake")

    before_audit_count = _table_count(initialized_connection, "audit_log")

    result = integrate_chatgpt_intake(
        initialized_connection,
        file_path=sample_file_path,
        raw_response=sample_metadata_valid_json,
        storage_root=storage_root,
        import_batch="test_audit_batch",
        copy_mode="reference_only",
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    after_audit_count = _table_count(initialized_connection, "audit_log")

    assert data["success"] is True
    assert after_audit_count >= before_audit_count + 1

    version_uuid = _extract_version_uuid(data)

    audit = initialized_connection.execute(
        """
        SELECT *
        FROM audit_log
        WHERE entity_uuid = ?
           OR after_json LIKE ?
           OR note LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            version_uuid,
            f"%{version_uuid}%",
            f"%{version_uuid}%",
        ),
    ).fetchone()

    assert audit is not None
    assert audit["action"] in {
        "chatgpt_intake_integrated",
        "library_row_inserted",
        "file_copied_to_storage",
    }
