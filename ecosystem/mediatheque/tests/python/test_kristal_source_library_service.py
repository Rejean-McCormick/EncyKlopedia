from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

from conftest import import_app_callable


def _write_store(root: Path, kristal_name: str, *, source_url: str, content: bytes) -> Path:
    store_root = root / kristal_name / "external-source-library"
    snap_dir = store_root / "snapshots" / "example-org" / "sample" / "20261002T120000Z"
    snap_dir.mkdir(parents=True)
    source_file = snap_dir / "original.html"
    source_file.write_bytes(content)

    import hashlib

    sha = hashlib.sha256(content).hexdigest()
    metadata = snap_dir / "metadata.json"
    metadata.write_text(json.dumps({"ok": True}), encoding="utf-8")

    payload = {
        "format": "test.source-store/v0.1",
        "version": "0.1.0",
        "kristal": {
            "state_id": "sha256:" + "1" * 64,
            "artifact_type": "structured_epistemic_state",
            "artifact_status": "working",
        },
        "entries": {
            "src:test": {
                "source_id": "src:test",
                "source_url": source_url,
                "source_type": "web_page",
                "title": "Example source",
                "publisher": "Example Org",
                "role": "reference",
                "evidence_class": "official",
                "authority": {"authority_class": "government_science"},
                "catalog": {"category": "history", "priority": "core"},
                "snapshots": [
                    {
                        "snapshot_id": "20261002T120000Z",
                        "retrieved_at": "2026-10-02T12:00:00Z",
                        "status": "available",
                        "requested_url": source_url,
                        "canonical_source_url": source_url,
                        "final_url": source_url,
                        "http_status": 200,
                        "acquisition_method": "direct_http",
                        "metadata_path": "snapshots/example-org/sample/20261002T120000Z/metadata.json",
                        "representations": [
                            {
                                "kind": "original",
                                "path": "snapshots/example-org/sample/20261002T120000Z/original.html",
                                "sha256": sha,
                                "size_bytes": len(content),
                                "mime_type": "text/html",
                            }
                        ],
                    }
                ],
            }
        },
    }
    store_path = store_root / "source-store.json"
    store_path.write_text(json.dumps(payload), encoding="utf-8")
    return store_path


def test_discover_and_plan_source_store(tmp_path: Path) -> None:
    discover = import_app_callable("services.kristal_source_library_service", "discover_kristal_source_stores")
    plan = import_app_callable("services.kristal_source_library_service", "plan_kristal_source_store")

    store = _write_store(tmp_path, "Kristal-Test", source_url="https://example.org/page", content=b"<html>ok</html>")
    found = discover(tmp_path)
    assert len(found) == 1
    assert found[0]["kristal_id"] == "Kristal-Test"
    assert found[0]["entries"] == 1
    assert found[0]["representations"] == 1

    planned = plan(store)
    assert planned["sources"] == 1
    assert planned["snapshots"] == 1
    assert planned["representations"] == 2  # original + metadata sidecar
    assert planned["missing_files"] == 0


def test_import_deduplicates_same_source_across_kristals(
    tmp_path: Path,
    project_root: Path,
) -> None:
    initialize_database = import_app_callable("db", "initialize_database")
    get_db_connection = import_app_callable("db", "get_db_connection")
    import_store = import_app_callable("services.kristal_source_library_service", "import_kristal_source_store")
    stats_fn = import_app_callable("services.kristal_source_library_service", "get_kristal_source_stats")
    list_sources = import_app_callable("services.kristal_source_library_service", "list_kristal_sources")
    verify = import_app_callable("services.kristal_source_library_service", "verify_kristal_source_storage")

    db = tmp_path / "koa.sqlite"
    schema_dir = project_root / "schemas" / "sqlite"
    init = initialize_database(db, schema_dir)
    assert init.success

    source_url = "https://example.org/shared"
    content = b"<html>shared</html>"
    store_a = _write_store(tmp_path / "kristals", "Kristal-A", source_url=source_url, content=content)
    store_b = _write_store(tmp_path / "kristals", "Kristal-B", source_url=source_url, content=content)
    storage_root = tmp_path / "02_STORAGE"

    with closing(get_db_connection(db)) as connection:
        result_a = import_store(connection, store_a, storage_root)
        result_b = import_store(connection, store_b, storage_root)
        assert result_a.success
        assert result_b.success

        stats = stats_fn(connection)
        assert stats["kristals"] == 2
        assert stats["sources"] == 1
        assert stats["links"] == 2
        assert stats["snapshots"] == 1
        assert stats["representations"] == 2  # original + metadata, shared snapshot identity
        assert stats["physical_files"] == 2  # original + metadata, no duplicate copies

        inventory = list_sources(connection)
        assert {row["kristal_id"] for row in inventory} == {"Kristal-A", "Kristal-B"}
        assert all(row["status"] == "available" for row in inventory)

        verification = verify(connection)
        assert verification["ok"] is True
        assert verification["physical_files"] == 2

    stored = list((storage_root / "source_files").glob("*"))
    assert len(stored) == 2


def test_import_blocks_declared_hash_mismatch(tmp_path: Path, project_root: Path) -> None:
    initialize_database = import_app_callable("db", "initialize_database")
    get_db_connection = import_app_callable("db", "get_db_connection")
    import_store = import_app_callable("services.kristal_source_library_service", "import_kristal_source_store")

    db = tmp_path / "koa.sqlite"
    schema_dir = project_root / "schemas" / "sqlite"
    assert initialize_database(db, schema_dir).success

    store = _write_store(tmp_path / "kristals", "Kristal-Bad", source_url="https://example.org/bad", content=b"real")
    data = json.loads(store.read_text(encoding="utf-8"))
    data["entries"]["src:test"]["snapshots"][0]["representations"][0]["sha256"] = "0" * 64
    store.write_text(json.dumps(data), encoding="utf-8")

    with closing(get_db_connection(db)) as connection:
        result = import_store(connection, store, tmp_path / "02_STORAGE")
        assert result.success is False
        assert result.data["hash_mismatches"] == 1
        assert result.data["files_copied"] == 1  # metadata sidecar still imports


def test_schema_v4_migrates_legacy_kristal_source_catalog(tmp_path: Path, project_root: Path) -> None:
    import sqlite3

    db = tmp_path / "legacy-v3.sqlite"
    schema_dir = project_root / "schemas" / "sqlite"
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        for name in (
            "001_initial_schema.sql",
            "002_indexes.sql",
            "003_triggers.sql",
            "004_seed_schema_meta.sql",
            "005_kristal_sources.sql",
            "006_kristal_catalog.sql",
        ):
            connection.executescript((schema_dir / name).read_text(encoding="utf-8"))

        connection.execute(
            """
            INSERT INTO kristal_registry(
                kristal_id, last_seen_at, metadata_json
            ) VALUES ('Kristal-Legacy', '2026-10-03T00:00:00Z', '{}')
            """
        )
        connection.execute(
            """
            INSERT INTO kristal_registry(
                kristal_id, last_seen_at, metadata_json
            ) VALUES ('Kristal-Artifact-Only', '2026-10-03T00:00:00Z', '{}')
            """
        )
        connection.execute(
            """
            INSERT INTO kristal_sources(
                source_uuid, canonical_url, canonical_url_key, title, status,
                source_metadata_json, created_at, updated_at
            ) VALUES (
                'source-legacy', 'https://example.org/legacy', 'https://example.org/legacy',
                'Legacy source', 'declared', '{}',
                '2026-10-03T00:00:00Z', '2026-10-03T00:00:00Z'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO kristal_source_links(
                kristal_id, source_uuid, source_id, link_metadata_json,
                created_at, updated_at
            ) VALUES (
                'Kristal-Legacy', 'source-legacy', 'src:legacy', '{}',
                '2026-10-03T00:00:00Z', '2026-10-03T00:00:00Z'
            )
            """
        )
        connection.commit()

        connection.executescript(
            (schema_dir / "007_source_authority.sql").read_text(encoding="utf-8")
        )

        consumer = connection.execute(
            "SELECT * FROM source_consumer_registry WHERE consumer_instance='Kristal-Legacy'"
        ).fetchone()
        source = connection.execute(
            "SELECT * FROM source_registry WHERE source_uuid='source-legacy'"
        ).fetchone()
        binding = connection.execute(
            "SELECT * FROM source_bindings WHERE external_source_id='src:legacy'"
        ).fetchone()

        assert consumer is not None
        assert consumer["consumer_system"] == "kristal"
        consumer_count = connection.execute(
            "SELECT COUNT(*) FROM source_consumer_registry"
        ).fetchone()[0]
        assert consumer_count == 1  # artifact-only Kristals are not source consumers
        assert source is not None
        assert source["title"] == "Legacy source"
        assert binding is not None
        assert binding["consumer_instance"] == "Kristal-Legacy"
    finally:
        connection.close()
