# tests/python/test_repair_service.py

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from conftest import assert_operation_result_shape, import_app_callable


def _service_callable(name: str):
    return import_app_callable("services.repair_service", name)


def _row_by_version_uuid(
    connection: sqlite3.Connection,
    version_uuid: str,
) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT * FROM library_rows WHERE version_uuid = ?",
        (version_uuid,),
    ).fetchone()


def _table_count(connection: sqlite3.Connection, table_name: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    assert row is not None
    return int(row["count"])


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
@pytest.mark.repair
@pytest.mark.db
@pytest.mark.files
def test_repair_service_public_api_exists() -> None:
    required_callables = [
        "recalculate_file_facts_for_row",
        "repair_protected_fields",
    ]

    for callable_name in required_callables:
        assert callable(_service_callable(callable_name))


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
@pytest.mark.files
def test_recalculate_file_facts_for_row_updates_local_file_facts(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
    sample_file_path: Path,
) -> None:
    recalculate_file_facts_for_row = _service_callable("recalculate_file_facts_for_row")

    version_uuid = inserted_library_row["version_uuid"]

    initialized_connection.execute(
        """
        UPDATE library_rows
        SET
            filename = ?,
            extension = ?,
            mimetype = ?,
            filesize = ?,
            sha256 = ?
        WHERE version_uuid = ?
        """,
        (
            "ai_or_xlsx_wrong_name.pdf",
            ".pdf",
            "application/fake",
            999999,
            "f" * 64,
            version_uuid,
        ),
    )
    initialized_connection.commit()

    result = recalculate_file_facts_for_row(
        initialized_connection,
        version_uuid,
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    expected_sha256 = hashlib.sha256(sample_file_path.read_bytes()).hexdigest()

    assert data["success"] is True
    assert data["operation"] == "recalculate_file_facts_for_row"
    assert data["result"] in {"updated", "recalculated", "repaired"}

    row = _row_by_version_uuid(initialized_connection, version_uuid)

    assert row is not None
    assert row["filename"] == sample_file_path.name
    assert row["extension"] == ".txt"
    assert row["filesize"] == sample_file_path.stat().st_size
    assert row["sha256"] == expected_sha256
    assert row["mimetype"] != "application/fake"


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
@pytest.mark.files
def test_recalculate_file_facts_for_row_uses_storage_path_when_present(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
    sample_file_path: Path,
    storage_root: Path,
) -> None:
    recalculate_file_facts_for_row = _service_callable("recalculate_file_facts_for_row")

    version_uuid = inserted_library_row["version_uuid"]
    stored_path = storage_root / "media_original" / f"{version_uuid}.txt"
    stored_path.write_text(
        "Different stored content used for repair service test.\n",
        encoding="utf-8",
    )

    initialized_connection.execute(
        """
        UPDATE library_rows
        SET
            storage_path = ?,
            filename = ?,
            extension = ?,
            mimetype = ?,
            filesize = ?,
            sha256 = ?
        WHERE version_uuid = ?
        """,
        (
            str(stored_path),
            sample_file_path.name,
            ".txt",
            "text/plain",
            sample_file_path.stat().st_size,
            hashlib.sha256(sample_file_path.read_bytes()).hexdigest(),
            version_uuid,
        ),
    )
    initialized_connection.commit()

    result = recalculate_file_facts_for_row(
        initialized_connection,
        version_uuid,
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    expected_sha256 = hashlib.sha256(stored_path.read_bytes()).hexdigest()

    assert data["success"] is True

    row = _row_by_version_uuid(initialized_connection, version_uuid)

    assert row is not None
    assert row["filename"] == stored_path.name
    assert row["filesize"] == stored_path.stat().st_size
    assert row["sha256"] == expected_sha256
    assert row["sha256"] != hashlib.sha256(sample_file_path.read_bytes()).hexdigest()


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
@pytest.mark.files
def test_recalculate_file_facts_for_row_returns_no_changes_when_already_current(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
    sample_file_path: Path,
) -> None:
    recalculate_file_facts_for_row = _service_callable("recalculate_file_facts_for_row")

    version_uuid = inserted_library_row["version_uuid"]
    expected_sha256 = hashlib.sha256(sample_file_path.read_bytes()).hexdigest()

    initialized_connection.execute(
        """
        UPDATE library_rows
        SET
            filename = ?,
            extension = ?,
            mimetype = ?,
            filesize = ?,
            sha256 = ?
        WHERE version_uuid = ?
        """,
        (
            sample_file_path.name,
            ".txt",
            "text/plain",
            sample_file_path.stat().st_size,
            expected_sha256,
            version_uuid,
        ),
    )
    initialized_connection.commit()

    result = recalculate_file_facts_for_row(
        initialized_connection,
        version_uuid,
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is True
    assert data["result"] in {"no_changes", "unchanged", "recalculated"}


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
@pytest.mark.files
def test_recalculate_file_facts_for_row_rejects_missing_version_uuid(
    initialized_connection: sqlite3.Connection,
) -> None:
    recalculate_file_facts_for_row = _service_callable("recalculate_file_facts_for_row")

    result = recalculate_file_facts_for_row(
        initialized_connection,
        "99999999-9999-4999-8999-999999999999",
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]

    codes = _message_codes(data["errors"])
    assert "ERR_VERSION_UUID_MISSING" in codes or data["errors"]


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
@pytest.mark.files
def test_recalculate_file_facts_for_row_rejects_missing_file(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
    tmp_path: Path,
) -> None:
    recalculate_file_facts_for_row = _service_callable("recalculate_file_facts_for_row")

    version_uuid = inserted_library_row["version_uuid"]
    missing_path = tmp_path / "missing_file.txt"

    initialized_connection.execute(
        """
        UPDATE library_rows
        SET original_path = ?, storage_path = ''
        WHERE version_uuid = ?
        """,
        (str(missing_path), version_uuid),
    )
    initialized_connection.commit()

    result = recalculate_file_facts_for_row(
        initialized_connection,
        version_uuid,
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]

    codes = _message_codes(data["errors"])
    assert "ERR_FILE_NOT_FOUND" in codes or data["errors"]


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
@pytest.mark.files
def test_recalculate_file_facts_for_row_writes_audit_log(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    recalculate_file_facts_for_row = _service_callable("recalculate_file_facts_for_row")

    version_uuid = inserted_library_row["version_uuid"]

    initialized_connection.execute(
        """
        UPDATE library_rows
        SET sha256 = ?, filesize = ?
        WHERE version_uuid = ?
        """,
        ("f" * 64, 999999, version_uuid),
    )
    initialized_connection.commit()

    before_count = _table_count(initialized_connection, "audit_log")

    result = recalculate_file_facts_for_row(
        initialized_connection,
        version_uuid,
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    after_count = _table_count(initialized_connection, "audit_log")

    assert data["success"] is True
    assert after_count >= before_count + 1

    audit = initialized_connection.execute(
        """
        SELECT *
        FROM audit_log
        WHERE action = 'repair_applied'
           OR action = 'library_row_updated'
           OR note LIKE ?
           OR entity_uuid = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (f"%{version_uuid}%", version_uuid),
    ).fetchone()

    assert audit is not None


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
def test_repair_protected_fields_updates_explicit_repair_fields(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
    tmp_path: Path,
) -> None:
    repair_protected_fields = _service_callable("repair_protected_fields")

    version_uuid = inserted_library_row["version_uuid"]
    repaired_file = tmp_path / "repaired_file.pdf"
    repaired_file.write_bytes(b"%PDF-1.4\n% repaired fixture\n")

    updates = {
        "original_path": str(repaired_file),
        "storage_path": str(repaired_file),
        "filename": repaired_file.name,
        "extension": ".pdf",
        "mimetype": "application/pdf",
        "filesize": repaired_file.stat().st_size,
        "sha256": hashlib.sha256(repaired_file.read_bytes()).hexdigest(),
    }

    result = repair_protected_fields(
        initialized_connection,
        version_uuid,
        updates,
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is True
    assert data["operation"] == "repair_protected_fields"
    assert data["result"] in {"updated", "repaired", "protected_fields_repaired"}

    row = _row_by_version_uuid(initialized_connection, version_uuid)

    assert row is not None
    for key, value in updates.items():
        assert row[key] == value


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
def test_repair_protected_fields_rejects_version_uuid_mutation(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    repair_protected_fields = _service_callable("repair_protected_fields")

    original_version_uuid = inserted_library_row["version_uuid"]
    forbidden_version_uuid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    result = repair_protected_fields(
        initialized_connection,
        original_version_uuid,
        {"version_uuid": forbidden_version_uuid},
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is False
    assert data["errors"]

    original = _row_by_version_uuid(initialized_connection, original_version_uuid)
    forbidden = _row_by_version_uuid(initialized_connection, forbidden_version_uuid)

    assert original is not None
    assert forbidden is None


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
def test_repair_protected_fields_rejects_media_uuid_mutation(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    repair_protected_fields = _service_callable("repair_protected_fields")

    version_uuid = inserted_library_row["version_uuid"]
    original_media_uuid = inserted_library_row["media_uuid"]

    result = repair_protected_fields(
        initialized_connection,
        version_uuid,
        {"media_uuid": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"},
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is False
    assert data["errors"]

    row = _row_by_version_uuid(initialized_connection, version_uuid)

    assert row is not None
    assert row["media_uuid"] == original_media_uuid


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
def test_repair_protected_fields_rejects_unknown_fields(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    repair_protected_fields = _service_callable("repair_protected_fields")

    result = repair_protected_fields(
        initialized_connection,
        inserted_library_row["version_uuid"],
        {"not_a_library_rows_field": "value"},
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
def test_repair_protected_fields_rejects_missing_version_uuid(
    initialized_connection: sqlite3.Connection,
) -> None:
    repair_protected_fields = _service_callable("repair_protected_fields")

    result = repair_protected_fields(
        initialized_connection,
        "99999999-9999-4999-8999-999999999999",
        {"sha256": "a" * 64},
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]

    codes = _message_codes(data["errors"])
    assert "ERR_VERSION_UUID_MISSING" in codes or data["errors"]


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
def test_repair_protected_fields_rejects_invalid_sha256(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    repair_protected_fields = _service_callable("repair_protected_fields")

    result = repair_protected_fields(
        initialized_connection,
        inserted_library_row["version_uuid"],
        {"sha256": "not-a-valid-sha256"},
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
def test_repair_protected_fields_rejects_negative_filesize(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    repair_protected_fields = _service_callable("repair_protected_fields")

    result = repair_protected_fields(
        initialized_connection,
        inserted_library_row["version_uuid"],
        {"filesize": -1},
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"]


@pytest.mark.contract
@pytest.mark.repair
@pytest.mark.db
def test_repair_protected_fields_writes_audit_log(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    repair_protected_fields = _service_callable("repair_protected_fields")

    version_uuid = inserted_library_row["version_uuid"]
    before_count = _table_count(initialized_connection, "audit_log")

    result = repair_protected_fields(
        initialized_connection,
        version_uuid,
        {"sha256": "a" * 64},
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    after_count = _table_count(initialized_connection, "audit_log")

    assert data["success"] is True
    assert after_count >= before_count + 1

    audit = initialized_connection.execute(
        """
        SELECT *
        FROM audit_log
        WHERE action = 'repair_applied'
           OR action = 'library_row_updated'
           OR note LIKE ?
           OR entity_uuid = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (f"%{version_uuid}%", version_uuid),
    ).fetchone()

    assert audit is not None