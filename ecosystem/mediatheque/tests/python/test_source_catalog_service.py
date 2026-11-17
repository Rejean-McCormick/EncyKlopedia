from __future__ import annotations

from contextlib import closing
from pathlib import Path

from conftest import import_app_callable


def test_initialized_database_has_consumer_neutral_source_authority(tmp_path: Path, project_root: Path) -> None:
    initialize_database = import_app_callable("db", "initialize_database")
    get_db_connection = import_app_callable("db", "get_db_connection")
    get_source_stats = import_app_callable("services.source_catalog_service", "get_source_stats")

    db = tmp_path / "koa.sqlite"
    result = initialize_database(db, project_root / "schemas" / "sqlite")
    assert result.success
    assert result.data["schema_version"] == "4"

    with closing(get_db_connection(db)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert {
            "source_consumer_registry",
            "source_registry",
            "source_bindings",
            "source_snapshots",
            "source_representations",
            "source_import_log",
        }.issubset(tables)
        stats = get_source_stats(connection)
        assert stats == {
            "sources": 0,
            "snapshots": 0,
            "available_snapshots": 0,
            "representations": 0,
            "physical_files": 0,
            "consumers": 0,
            "bindings": 0,
        }
