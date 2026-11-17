# tests/python/test_db_initialize.py

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest

from conftest import assert_operation_result_shape, import_app_callable


REQUIRED_TABLES = {
    "schema_meta",
    "library_rows",
    "chatgpt_intake_log",
    "xlsx_import_log",
    "file_scan_log",
    "audit_log",
}

REQUIRED_LIBRARY_ROW_COLUMNS = {
    "id",
    "media_uuid",
    "version_uuid",
    "title",
    "original_path",
    "filename",
    "sha256",
    "filearea",
    "media_type",
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
    "status",
    "provenance",
    "ai_validation_state",
    "canonical_validation_state",
    "human_review_required",
    "collections_json",
    "tags_json",
    "relations_json",
    "content_flags_json",
    "audience_suitability",
    "export_to_uckk",
    "export_to_public",
    "import_batch",
    "created_at",
    "updated_at",
}

REQUIRED_INDEXES = {
    "idx_library_rows_media_uuid",
    "idx_library_rows_version_uuid",
    "idx_library_rows_sha256",
    "idx_library_rows_status",
    "idx_library_rows_visibility",
    "idx_library_rows_uckk_relevance",
    "idx_library_rows_public_state",
    "idx_library_rows_review",
}


def _schema_source_dir(project_root: Path) -> Path:
    return project_root / "schemas" / "sqlite"


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def _fetch_all(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[sqlite3.Row | tuple[Any, ...]]:
    cursor = connection.execute(sql, params)
    try:
        return cursor.fetchall()
    finally:
        cursor.close()


def _fetch_one(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> sqlite3.Row | tuple[Any, ...] | None:
    cursor = connection.execute(sql, params)
    try:
        return cursor.fetchone()
    finally:
        cursor.close()


def _execute(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> None:
    cursor = connection.execute(sql, params)
    try:
        return None
    finally:
        cursor.close()


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = _fetch_all(
        connection,
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """,
    )
    return {str(row[0]) for row in rows}


def _column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = _fetch_all(connection, f"PRAGMA table_info({table_name})")
    return {str(row[1]) for row in rows}


def _index_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = _fetch_all(connection, f"PRAGMA index_list({table_name})")
    return {str(row[1]) for row in rows}


def _schema_meta(connection: sqlite3.Connection) -> dict[str, str]:
    rows = _fetch_all(connection, "SELECT key, value FROM schema_meta")
    return {str(row[0]): str(row[1]) for row in rows}


@pytest.mark.contract
@pytest.mark.db
def test_initialize_database_public_api_exists() -> None:
    assert callable(import_app_callable("db", "initialize_database"))
    assert callable(import_app_callable("db", "get_db_connection"))
    assert callable(import_app_callable("db", "database_exists"))
    assert callable(import_app_callable("db", "get_schema_version"))
    assert callable(import_app_callable("db", "set_schema_meta"))


@pytest.mark.contract
@pytest.mark.db
def test_initialize_database_creates_sqlite_file(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")
    database_exists = import_app_callable("db", "database_exists")

    db_path = tmp_path / "01_DB" / "koa_mediatheque.sqlite"
    schema_dir = _schema_source_dir(project_root)

    assert schema_dir.exists(), f"Missing schema directory: {schema_dir}"
    assert database_exists(db_path) is False

    result = initialize_database(db_path, schema_dir, overwrite=False)
    data = assert_operation_result_shape(result)

    assert data["success"] is True
    assert data["operation"]
    assert data["errors"] == []
    assert db_path.exists()
    assert database_exists(db_path) is True


@pytest.mark.contract
@pytest.mark.db
def test_initialize_database_creates_required_tables(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")

    db_path = tmp_path / "01_DB" / "koa_mediatheque.sqlite"
    schema_dir = _schema_source_dir(project_root)

    result = initialize_database(db_path, schema_dir, overwrite=False)
    data = assert_operation_result_shape(result)
    assert data["success"] is True

    with closing(_connect(db_path)) as connection:
        actual_tables = _table_names(connection)

    missing = REQUIRED_TABLES - actual_tables
    assert not missing, f"Missing required SQLite tables: {sorted(missing)}"


@pytest.mark.contract
@pytest.mark.db
def test_initialize_database_creates_library_rows_contract_columns(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")

    db_path = tmp_path / "01_DB" / "koa_mediatheque.sqlite"
    schema_dir = _schema_source_dir(project_root)

    result = initialize_database(db_path, schema_dir, overwrite=False)
    data = assert_operation_result_shape(result)
    assert data["success"] is True

    with closing(_connect(db_path)) as connection:
        actual_columns = _column_names(connection, "library_rows")

    missing = REQUIRED_LIBRARY_ROW_COLUMNS - actual_columns
    assert not missing, f"Missing library_rows columns: {sorted(missing)}"


@pytest.mark.contract
@pytest.mark.db
def test_initialize_database_creates_required_indexes(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")

    db_path = tmp_path / "01_DB" / "koa_mediatheque.sqlite"
    schema_dir = _schema_source_dir(project_root)

    result = initialize_database(db_path, schema_dir, overwrite=False)
    data = assert_operation_result_shape(result)
    assert data["success"] is True

    with closing(_connect(db_path)) as connection:
        actual_indexes = _index_names(connection, "library_rows")

    missing = REQUIRED_INDEXES - actual_indexes
    assert not missing, f"Missing library_rows indexes: {sorted(missing)}"


@pytest.mark.contract
@pytest.mark.db
def test_initialize_database_seeds_schema_meta(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")
    get_schema_version = import_app_callable("db", "get_schema_version")

    db_path = tmp_path / "01_DB" / "koa_mediatheque.sqlite"
    schema_dir = _schema_source_dir(project_root)

    result = initialize_database(db_path, schema_dir, overwrite=False)
    data = assert_operation_result_shape(result)
    assert data["success"] is True

    with closing(_connect(db_path)) as connection:
        meta = _schema_meta(connection)
        schema_version = get_schema_version(connection)

    assert meta, "schema_meta must be seeded during database initialization"
    assert schema_version is not None
    assert str(schema_version).strip() != ""


@pytest.mark.contract
@pytest.mark.db
def test_initialize_database_does_not_overwrite_existing_db_without_flag(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")

    db_path = tmp_path / "01_DB" / "koa_mediatheque.sqlite"
    schema_dir = _schema_source_dir(project_root)

    first = assert_operation_result_shape(
        initialize_database(db_path, schema_dir, overwrite=False)
    )
    assert first["success"] is True

    with closing(_connect(db_path)) as connection:
        _execute(
            connection,
            "INSERT INTO schema_meta(key, value) VALUES (?, ?)",
            ("sentinel_key", "sentinel_value"),
        )
        connection.commit()

    second = assert_operation_result_shape(
        initialize_database(db_path, schema_dir, overwrite=False)
    )

    assert second["success"] is False

    with closing(_connect(db_path)) as connection:
        sentinel = _fetch_one(
            connection,
            "SELECT value FROM schema_meta WHERE key = ?",
            ("sentinel_key",),
        )

    assert sentinel is not None
    assert sentinel[0] == "sentinel_value"


@pytest.mark.contract
@pytest.mark.db
def test_initialize_database_overwrite_recreates_existing_db(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")

    db_path = tmp_path / "01_DB" / "koa_mediatheque.sqlite"
    schema_dir = _schema_source_dir(project_root)

    first = assert_operation_result_shape(
        initialize_database(db_path, schema_dir, overwrite=False)
    )
    assert first["success"] is True

    with closing(_connect(db_path)) as connection:
        _execute(
            connection,
            "INSERT INTO schema_meta(key, value) VALUES (?, ?)",
            ("sentinel_key", "sentinel_value"),
        )
        connection.commit()

    second = assert_operation_result_shape(
        initialize_database(db_path, schema_dir, overwrite=True)
    )

    assert second["success"] is True

    with closing(_connect(db_path)) as connection:
        sentinel = _fetch_one(
            connection,
            "SELECT value FROM schema_meta WHERE key = ?",
            ("sentinel_key",),
        )

    assert sentinel is None


@pytest.mark.contract
@pytest.mark.db
def test_get_db_connection_returns_row_access_connection(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")
    get_db_connection = import_app_callable("db", "get_db_connection")

    db_path = tmp_path / "01_DB" / "koa_mediatheque.sqlite"
    schema_dir = _schema_source_dir(project_root)

    result = initialize_database(db_path, schema_dir, overwrite=False)
    data = assert_operation_result_shape(result)
    assert data["success"] is True

    with closing(get_db_connection(db_path)) as connection:
        assert isinstance(connection, sqlite3.Connection)

        row = _fetch_one(
            connection,
            "SELECT key, value FROM schema_meta LIMIT 1",
        )
        assert row is not None

        try:
            _ = row["key"]
        except (TypeError, IndexError):
            pytest.fail("get_db_connection() must configure sqlite3.Row access.")