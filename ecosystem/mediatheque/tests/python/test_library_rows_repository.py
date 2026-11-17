# tests/python/test_library_rows_repository.py

from __future__ import annotations

import copy
import sqlite3
from typing import Any

import pytest

from conftest import assert_operation_result_shape, import_app_callable


def _repo_callable(name: str):
    return import_app_callable("repositories.library_rows_repository", name)


def _fetch_row_by_version_uuid(
    connection: sqlite3.Connection,
    version_uuid: str,
) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT * FROM library_rows WHERE version_uuid = ?",
        (version_uuid,),
    ).fetchone()


def _make_row_variant(
    base: dict[str, Any],
    *,
    media_uuid: str,
    version_uuid: str,
    sha256: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    row = copy.deepcopy(base)
    row["media_uuid"] = media_uuid
    row["version_uuid"] = version_uuid
    if sha256 is not None:
        row["sha256"] = sha256
    if title is not None:
        row["title"] = title
    return row


@pytest.mark.contract
@pytest.mark.db
def test_library_rows_repository_public_api_exists() -> None:
    required_callables = [
        "list_library_rows",
        "get_library_row_by_id",
        "get_library_row_by_version_uuid",
        "get_library_rows_by_media_uuid",
        "get_library_rows_by_sha256",
        "insert_library_row",
        "update_library_row_by_version_uuid",
        "soft_delete_library_row",
    ]

    for callable_name in required_callables:
        assert callable(_repo_callable(callable_name))


@pytest.mark.contract
@pytest.mark.db
def test_insert_library_row_writes_required_identity_fields(
    initialized_connection: sqlite3.Connection,
    sample_library_row_data: dict[str, Any],
) -> None:
    insert_library_row = _repo_callable("insert_library_row")

    result = insert_library_row(initialized_connection, sample_library_row_data)
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is True
    assert data["operation"] == "insert_library_row"
    assert data["result"] in {"inserted", "created"}
    assert data.get("media_uuid") == sample_library_row_data["media_uuid"]
    assert data.get("version_uuid") == sample_library_row_data["version_uuid"]

    row = _fetch_row_by_version_uuid(
        initialized_connection,
        sample_library_row_data["version_uuid"],
    )

    assert row is not None
    assert row["media_uuid"] == sample_library_row_data["media_uuid"]
    assert row["version_uuid"] == sample_library_row_data["version_uuid"]
    assert row["title"] == sample_library_row_data["title"]
    assert row["filename"] == sample_library_row_data["filename"]
    assert row["sha256"] == sample_library_row_data["sha256"]


@pytest.mark.contract
@pytest.mark.db
def test_insert_library_row_enforces_unique_version_uuid(
    initialized_connection: sqlite3.Connection,
    sample_library_row_data: dict[str, Any],
) -> None:
    insert_library_row = _repo_callable("insert_library_row")

    first = assert_operation_result_shape(
        insert_library_row(initialized_connection, sample_library_row_data)
    )
    initialized_connection.commit()

    assert first["success"] is True

    duplicate = copy.deepcopy(sample_library_row_data)
    duplicate["title"] = "Duplicate version UUID"

    second = assert_operation_result_shape(
        insert_library_row(initialized_connection, duplicate)
    )

    assert second["success"] is False
    assert second["errors"], "Duplicate version_uuid must produce a contract error."

    count = initialized_connection.execute(
        "SELECT COUNT(*) AS count FROM library_rows WHERE version_uuid = ?",
        (sample_library_row_data["version_uuid"],),
    ).fetchone()

    assert count is not None
    assert count["count"] == 1


@pytest.mark.contract
@pytest.mark.db
def test_get_library_row_by_version_uuid_returns_inserted_row(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    get_library_row_by_version_uuid = _repo_callable("get_library_row_by_version_uuid")

    row = get_library_row_by_version_uuid(
        initialized_connection,
        inserted_library_row["version_uuid"],
    )

    assert row is not None
    assert row["version_uuid"] == inserted_library_row["version_uuid"]
    assert row["media_uuid"] == inserted_library_row["media_uuid"]
    assert row["title"] == inserted_library_row["title"]


@pytest.mark.contract
@pytest.mark.db
def test_get_library_row_by_id_returns_inserted_row(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    get_library_row_by_id = _repo_callable("get_library_row_by_id")

    stored = _fetch_row_by_version_uuid(
        initialized_connection,
        inserted_library_row["version_uuid"],
    )
    assert stored is not None

    row = get_library_row_by_id(initialized_connection, stored["id"])

    assert row is not None
    assert row["id"] == stored["id"]
    assert row["version_uuid"] == inserted_library_row["version_uuid"]


@pytest.mark.contract
@pytest.mark.db
def test_get_library_rows_by_media_uuid_returns_all_versions(
    initialized_connection: sqlite3.Connection,
    sample_library_row_data: dict[str, Any],
) -> None:
    insert_library_row = _repo_callable("insert_library_row")
    get_library_rows_by_media_uuid = _repo_callable("get_library_rows_by_media_uuid")

    media_uuid = "33333333-3333-4333-8333-333333333333"

    row_a = _make_row_variant(
        sample_library_row_data,
        media_uuid=media_uuid,
        version_uuid="33333333-3333-4333-8333-000000000001",
        title="Version A",
    )
    row_b = _make_row_variant(
        sample_library_row_data,
        media_uuid=media_uuid,
        version_uuid="33333333-3333-4333-8333-000000000002",
        title="Version B",
    )

    assert_operation_result_shape(insert_library_row(initialized_connection, row_a))
    assert_operation_result_shape(insert_library_row(initialized_connection, row_b))
    initialized_connection.commit()

    rows = get_library_rows_by_media_uuid(initialized_connection, media_uuid)

    assert len(rows) == 2
    assert {row["version_uuid"] for row in rows} == {
        row_a["version_uuid"],
        row_b["version_uuid"],
    }


@pytest.mark.contract
@pytest.mark.db
def test_get_library_rows_by_sha256_returns_exact_duplicates(
    initialized_connection: sqlite3.Connection,
    sample_library_row_data: dict[str, Any],
) -> None:
    insert_library_row = _repo_callable("insert_library_row")
    get_library_rows_by_sha256 = _repo_callable("get_library_rows_by_sha256")

    duplicate_hash = "a" * 64

    row_a = _make_row_variant(
        sample_library_row_data,
        media_uuid="44444444-4444-4444-8444-000000000001",
        version_uuid="44444444-4444-4444-8444-000000000001",
        sha256=duplicate_hash,
        title="Duplicate hash A",
    )
    row_b = _make_row_variant(
        sample_library_row_data,
        media_uuid="44444444-4444-4444-8444-000000000002",
        version_uuid="44444444-4444-4444-8444-000000000002",
        sha256=duplicate_hash,
        title="Duplicate hash B",
    )
    row_c = _make_row_variant(
        sample_library_row_data,
        media_uuid="44444444-4444-4444-8444-000000000003",
        version_uuid="44444444-4444-4444-8444-000000000003",
        sha256="b" * 64,
        title="Different hash",
    )

    for row in (row_a, row_b, row_c):
        result = assert_operation_result_shape(
            insert_library_row(initialized_connection, row)
        )
        assert result["success"] is True

    initialized_connection.commit()

    rows = get_library_rows_by_sha256(initialized_connection, duplicate_hash)

    assert len(rows) == 2
    assert {row["version_uuid"] for row in rows} == {
        row_a["version_uuid"],
        row_b["version_uuid"],
    }


@pytest.mark.contract
@pytest.mark.db
def test_list_library_rows_returns_inserted_rows(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    list_library_rows = _repo_callable("list_library_rows")

    rows = list_library_rows(initialized_connection)

    assert isinstance(rows, list)
    assert any(
        row["version_uuid"] == inserted_library_row["version_uuid"]
        for row in rows
    )


@pytest.mark.contract
@pytest.mark.db
def test_list_library_rows_applies_simple_filters(
    initialized_connection: sqlite3.Connection,
    sample_library_row_data: dict[str, Any],
) -> None:
    insert_library_row = _repo_callable("insert_library_row")
    list_library_rows = _repo_callable("list_library_rows")

    private_row = _make_row_variant(
        sample_library_row_data,
        media_uuid="55555555-5555-4555-8555-000000000001",
        version_uuid="55555555-5555-4555-8555-000000000001",
        title="Private row",
    )
    private_row["visibility"] = "private"

    restricted_row = _make_row_variant(
        sample_library_row_data,
        media_uuid="55555555-5555-4555-8555-000000000002",
        version_uuid="55555555-5555-4555-8555-000000000002",
        title="Restricted row",
    )
    restricted_row["visibility"] = "restricted"

    for row in (private_row, restricted_row):
        result = assert_operation_result_shape(
            insert_library_row(initialized_connection, row)
        )
        assert result["success"] is True

    initialized_connection.commit()

    rows = list_library_rows(initialized_connection, {"visibility": "restricted"})

    assert rows
    assert all(row["visibility"] == "restricted" for row in rows)
    assert any(row["version_uuid"] == restricted_row["version_uuid"] for row in rows)


@pytest.mark.contract
@pytest.mark.db
def test_update_library_row_by_version_uuid_updates_allowed_fields(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    update_library_row_by_version_uuid = _repo_callable(
        "update_library_row_by_version_uuid"
    )

    updates = {
        "title": "Titre modifié par repository",
        "notes": "Notes modifiées par test de contrat.",
        "human_review_required": 0,
        "review_queue": "",
        "review_reason": "",
    }

    result = update_library_row_by_version_uuid(
        initialized_connection,
        inserted_library_row["version_uuid"],
        updates,
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is True
    assert data["operation"] == "update_library_row_by_version_uuid"
    assert data["result"] in {"updated", "modified"}

    row = _fetch_row_by_version_uuid(
        initialized_connection,
        inserted_library_row["version_uuid"],
    )

    assert row is not None
    assert row["title"] == updates["title"]
    assert row["notes"] == updates["notes"]
    assert row["human_review_required"] == 0
    assert row["review_queue"] == ""
    assert row["review_reason"] == ""


@pytest.mark.contract
@pytest.mark.db
def test_update_library_row_by_version_uuid_rejects_missing_row(
    initialized_connection: sqlite3.Connection,
) -> None:
    update_library_row_by_version_uuid = _repo_callable(
        "update_library_row_by_version_uuid"
    )

    result = update_library_row_by_version_uuid(
        initialized_connection,
        "99999999-9999-4999-8999-999999999999",
        {"title": "Missing"},
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"], "Updating a missing version_uuid must report errors."


@pytest.mark.contract
@pytest.mark.db
def test_update_library_row_by_version_uuid_does_not_change_version_uuid(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    update_library_row_by_version_uuid = _repo_callable(
        "update_library_row_by_version_uuid"
    )

    original_version_uuid = inserted_library_row["version_uuid"]
    forbidden_version_uuid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    result = update_library_row_by_version_uuid(
        initialized_connection,
        original_version_uuid,
        {
            "version_uuid": forbidden_version_uuid,
            "title": "Tentative de changement version_uuid",
        },
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is False
    assert data["errors"], "Repository must reject version_uuid mutation."

    original = _fetch_row_by_version_uuid(initialized_connection, original_version_uuid)
    forbidden = _fetch_row_by_version_uuid(initialized_connection, forbidden_version_uuid)

    assert original is not None
    assert forbidden is None


@pytest.mark.contract
@pytest.mark.db
def test_soft_delete_library_row_sets_deleted_soft_status(
    initialized_connection: sqlite3.Connection,
    inserted_library_row: dict[str, Any],
) -> None:
    soft_delete_library_row = _repo_callable("soft_delete_library_row")

    result = soft_delete_library_row(
        initialized_connection,
        inserted_library_row["version_uuid"],
        actor="pytest",
    )
    data = assert_operation_result_shape(result)
    initialized_connection.commit()

    assert data["success"] is True
    assert data["operation"] == "soft_delete_library_row"
    assert data["result"] in {"deleted_soft", "archived", "updated"}

    row = _fetch_row_by_version_uuid(
        initialized_connection,
        inserted_library_row["version_uuid"],
    )

    assert row is not None
    assert row["status"] == "deleted_soft"


@pytest.mark.contract
@pytest.mark.db
def test_soft_delete_library_row_rejects_missing_row(
    initialized_connection: sqlite3.Connection,
) -> None:
    soft_delete_library_row = _repo_callable("soft_delete_library_row")

    result = soft_delete_library_row(
        initialized_connection,
        "99999999-9999-4999-8999-999999999999",
        actor="pytest",
    )
    data = assert_operation_result_shape(result)

    assert data["success"] is False
    assert data["errors"], "Soft delete of missing row must report errors."