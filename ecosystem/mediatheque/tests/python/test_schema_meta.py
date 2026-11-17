# tests/python/test_schema_meta.py

from __future__ import annotations

import sqlite3

import pytest

from conftest import import_app_callable


@pytest.mark.contract
@pytest.mark.db
def test_schema_meta_public_api_exists() -> None:
    assert callable(import_app_callable("db", "get_schema_version"))
    assert callable(import_app_callable("db", "set_schema_meta"))


@pytest.mark.contract
@pytest.mark.db
def test_get_schema_version_returns_seeded_value(
    initialized_connection: sqlite3.Connection,
) -> None:
    get_schema_version = import_app_callable("db", "get_schema_version")

    schema_version = get_schema_version(initialized_connection)

    assert schema_version is not None
    assert isinstance(schema_version, str)
    assert schema_version.strip() != ""


@pytest.mark.contract
@pytest.mark.db
def test_set_schema_meta_inserts_new_key(
    initialized_connection: sqlite3.Connection,
) -> None:
    set_schema_meta = import_app_callable("db", "set_schema_meta")

    set_schema_meta(initialized_connection, "test_key", "test_value")
    initialized_connection.commit()

    row = initialized_connection.execute(
        "SELECT key, value FROM schema_meta WHERE key = ?",
        ("test_key",),
    ).fetchone()

    assert row is not None
    assert row["key"] == "test_key"
    assert row["value"] == "test_value"


@pytest.mark.contract
@pytest.mark.db
def test_set_schema_meta_updates_existing_key(
    initialized_connection: sqlite3.Connection,
) -> None:
    set_schema_meta = import_app_callable("db", "set_schema_meta")

    set_schema_meta(initialized_connection, "test_key", "first_value")
    set_schema_meta(initialized_connection, "test_key", "second_value")
    initialized_connection.commit()

    rows = initialized_connection.execute(
        "SELECT key, value FROM schema_meta WHERE key = ?",
        ("test_key",),
    ).fetchall()

    assert len(rows) == 1
    assert rows[0]["value"] == "second_value"


@pytest.mark.contract
@pytest.mark.db
def test_set_schema_meta_updates_timestamp(
    initialized_connection: sqlite3.Connection,
) -> None:
    set_schema_meta = import_app_callable("db", "set_schema_meta")

    set_schema_meta(initialized_connection, "timestamp_key", "first_value")
    initialized_connection.commit()

    first = initialized_connection.execute(
        "SELECT updated_at FROM schema_meta WHERE key = ?",
        ("timestamp_key",),
    ).fetchone()

    set_schema_meta(initialized_connection, "timestamp_key", "second_value")
    initialized_connection.commit()

    second = initialized_connection.execute(
        "SELECT updated_at FROM schema_meta WHERE key = ?",
        ("timestamp_key",),
    ).fetchone()

    assert first is not None
    assert second is not None
    assert second["updated_at"] is not None
    assert second["updated_at"] >= first["updated_at"]


@pytest.mark.contract
@pytest.mark.db
def test_schema_meta_contains_app_identity(
    initialized_connection: sqlite3.Connection,
) -> None:
    rows = initialized_connection.execute(
        "SELECT key, value FROM schema_meta"
    ).fetchall()

    meta = {row["key"]: row["value"] for row in rows}

    assert "app_public_name" in meta
    assert meta["app_public_name"] == "Médiathèque kOA"

    assert "app_technical_name" in meta
    assert meta["app_technical_name"] == "koa-mediatheque"

    assert "app_component" in meta
    assert meta["app_component"] == "koa_mediatheque"

    assert "schema_version" in meta
    assert str(meta["schema_version"]).strip() != ""


@pytest.mark.contract
@pytest.mark.db
def test_schema_meta_key_is_unique(
    initialized_connection: sqlite3.Connection,
) -> None:
    set_schema_meta = import_app_callable("db", "set_schema_meta")

    set_schema_meta(initialized_connection, "unique_key", "value_1")
    set_schema_meta(initialized_connection, "unique_key", "value_2")
    initialized_connection.commit()

    count = initialized_connection.execute(
        "SELECT COUNT(*) AS count FROM schema_meta WHERE key = ?",
        ("unique_key",),
    ).fetchone()

    assert count is not None
    assert count["count"] == 1