# tests/python/test_backup_service.py
"""Tests for koa_mediatheque.services.backup_service."""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from koa_mediatheque.models import OperationResult
from koa_mediatheque.services.backup_service import backup_database


def test_backup_database_creates_backup_file(tmp_path: Path) -> None:
    db_path = tmp_path / "koa_mediatheque.sqlite"
    backup_dir = tmp_path / "backups"

    _create_sample_database(db_path)

    result = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="unit_test",
        actor="pytest",
    )

    assert isinstance(result, OperationResult)
    assert result.success is True
    assert result.operation == "backup_database"
    assert result.result in {"created", "backup_created", "ok"}
    assert result.path is not None
    assert result.errors == []

    backup_path = Path(result.path)
    assert backup_path.exists()
    assert backup_path.is_file()
    assert backup_path.parent == backup_dir
    assert backup_path.name.startswith("koa_mediatheque_")
    assert backup_path.name.endswith("_unit_test.sqlite")


def test_backup_database_creates_backup_directory_when_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "koa_mediatheque.sqlite"
    backup_dir = tmp_path / "nested" / "backup" / "dir"

    _create_sample_database(db_path)

    assert backup_dir.exists() is False

    result = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="unit_test",
        actor="pytest",
    )

    assert result.success is True
    assert backup_dir.exists()
    assert backup_dir.is_dir()
    assert result.path is not None
    assert Path(result.path).exists()


def test_backup_database_preserves_sqlite_content(tmp_path: Path) -> None:
    db_path = tmp_path / "koa_mediatheque.sqlite"
    backup_dir = tmp_path / "backups"

    _create_sample_database(db_path)

    result = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="content_check",
        actor="pytest",
    )

    assert result.success is True
    assert result.path is not None

    backup_path = Path(result.path)

    assert _read_schema_meta(db_path, "app_component") == "koa_mediatheque"
    assert _read_schema_meta(backup_path, "app_component") == "koa_mediatheque"
    assert _read_schema_meta(backup_path, "schema_version") == "001"


def test_backup_database_does_not_modify_source_database(tmp_path: Path) -> None:
    db_path = tmp_path / "koa_mediatheque.sqlite"
    backup_dir = tmp_path / "backups"

    _create_sample_database(db_path)

    before = _read_schema_meta(db_path, "schema_version")

    result = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="no_source_change",
        actor="pytest",
    )

    after = _read_schema_meta(db_path, "schema_version")

    assert result.success is True
    assert before == "001"
    assert after == before


def test_backup_database_returns_failure_when_db_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "missing.sqlite"
    backup_dir = tmp_path / "backups"

    result = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="missing_db",
        actor="pytest",
    )

    assert isinstance(result, OperationResult)
    assert result.success is False
    assert result.operation == "backup_database"
    assert result.result in {"source_missing", "db_not_found", "file_not_found", "error"}
    assert result.errors

    if backup_dir.exists():
        assert not list(backup_dir.glob("*.sqlite"))


def test_backup_database_uses_contract_filename_format(tmp_path: Path) -> None:
    db_path = tmp_path / "koa_mediatheque.sqlite"
    backup_dir = tmp_path / "backups"

    _create_sample_database(db_path)

    result = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="contract",
        actor="pytest",
    )

    assert result.success is True
    assert result.path is not None

    backup_name = Path(result.path).name

    assert re.fullmatch(
        r"koa_mediatheque_\d{8}_\d{6}_contract(?:_\d+)?\.sqlite",
        backup_name,
    )


def test_backup_database_sanitizes_reason_for_filename(tmp_path: Path) -> None:
    db_path = tmp_path / "koa_mediatheque.sqlite"
    backup_dir = tmp_path / "backups"

    _create_sample_database(db_path)

    result = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="manual backup / before import",
        actor="pytest",
    )

    assert result.success is True
    assert result.path is not None

    backup_path = Path(result.path)

    assert backup_path.exists()
    assert backup_path.suffix == ".sqlite"
    assert "/" not in backup_path.name
    assert "\\" not in backup_path.name
    assert " " not in backup_path.name


def test_backup_database_result_contains_expected_data(tmp_path: Path) -> None:
    db_path = tmp_path / "koa_mediatheque.sqlite"
    backup_dir = tmp_path / "backups"

    _create_sample_database(db_path)

    result = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="result_data",
        actor="pytest",
    )

    assert result.success is True
    assert result.entity_type in {"backup", "database", None}
    assert isinstance(result.data, dict)

    assert result.data.get("reason") in {"result_data", None}
    assert result.data.get("actor") in {"pytest", None}

    if "source_path" in result.data:
        assert Path(result.data["source_path"]) == db_path

    if "backup_path" in result.data:
        assert Path(result.data["backup_path"]).exists()


def test_backup_database_can_create_multiple_backups_without_overwriting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "koa_mediatheque.sqlite"
    backup_dir = tmp_path / "backups"

    _create_sample_database(db_path)

    result_1 = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="multi",
        actor="pytest",
    )

    result_2 = backup_database(
        db_path=db_path,
        backup_dir=backup_dir,
        reason="multi",
        actor="pytest",
    )

    assert result_1.success is True
    assert result_2.success is True
    assert result_1.path is not None
    assert result_2.path is not None

    backups = sorted(backup_dir.glob("koa_mediatheque_*_multi*.sqlite"))

    assert len(backups) >= 2
    assert Path(result_1.path).exists()
    assert Path(result_2.path).exists()
    assert Path(result_1.path) != Path(result_2.path)


def _create_sample_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute(
            """
            CREATE TABLE schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            INSERT INTO schema_meta (key, value)
            VALUES
                ('app_component', 'koa_mediatheque'),
                ('schema_version', '001')
            """
        )
        connection.commit()


def _read_schema_meta(db_path: Path, key: str) -> str | None:
    with closing(sqlite3.connect(db_path)) as connection:
        cursor = connection.execute(
            """
            SELECT value
            FROM schema_meta
            WHERE key = ?
            LIMIT 1
            """,
            (key,),
        )
        try:
            row = cursor.fetchone()
        finally:
            cursor.close()

    if row is None:
        return None

    return str(row[0])