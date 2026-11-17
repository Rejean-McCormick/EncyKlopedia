"""Consumer-neutral source authority for Médiathèque kOA.

Médiathèque owns logical source identity, immutable acquisition snapshots,
physical representations and integrity facts. Consumer systems such as Kristal
or EncyK bind to these source identities without becoming the storage authority.

The schema-v3 ``kristal_*`` source tables remain only as migration/compatibility
inputs. New writes target the schema-v4 ``source_*`` authority tables.
"""

from __future__ import annotations

import hashlib
import sqlite3
from importlib import resources
from typing import Any

from koa_mediatheque.schema import utc_now_iso
from koa_mediatheque.workspace import resolve_content_path

SOURCE_CATALOG_PROFILE = "koa.source-catalog/2.0.0"


def ensure_source_catalog_schema(connection: sqlite3.Connection) -> None:
    """Ensure the legacy migration source and generic source authority exist."""
    package_root = resources.files("koa_mediatheque")
    for relative in (
        "sql/005_kristal_sources.sql",
        "sql/007_source_authority.sql",
    ):
        connection.executescript(package_root.joinpath(relative).read_text(encoding="utf-8"))
    now = utc_now_iso()
    connection.execute(
        """
        INSERT INTO schema_meta(key, value, updated_at)
        VALUES ('source_catalog_profile', ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """,
        (SOURCE_CATALOG_PROFILE, now),
    )
    connection.execute(
        """
        INSERT INTO schema_meta(key, value, updated_at)
        VALUES ('source_authority', 'koa_mediatheque', ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """,
        (now,),
    )
    connection.commit()


def get_source_stats(
    connection: sqlite3.Connection,
    *,
    consumer_system: str | None = None,
) -> dict[str, int]:
    """Return compact statistics for the canonical source catalog.

    With ``consumer_system`` set, counts are scoped to sources reachable from
    bindings owned by that consumer. Without it, counts describe the complete
    Médiathèque source authority.
    """
    ensure_source_catalog_schema(connection)
    if consumer_system:
        consumers = int(connection.execute(
            "SELECT COUNT(*) FROM source_consumer_registry WHERE consumer_system=?",
            (consumer_system,),
        ).fetchone()[0])
        bindings = int(connection.execute(
            "SELECT COUNT(*) FROM source_bindings WHERE consumer_system=?",
            (consumer_system,),
        ).fetchone()[0])
        sources = int(connection.execute(
            "SELECT COUNT(DISTINCT source_uuid) FROM source_bindings WHERE consumer_system=?",
            (consumer_system,),
        ).fetchone()[0])
        snapshots = int(connection.execute(
            """SELECT COUNT(DISTINCT ss.snapshot_uuid)
               FROM source_snapshots ss
               JOIN source_bindings b ON b.source_uuid=ss.source_uuid
               WHERE b.consumer_system=?""",
            (consumer_system,),
        ).fetchone()[0])
        available = int(connection.execute(
            """SELECT COUNT(DISTINCT ss.snapshot_uuid)
               FROM source_snapshots ss
               JOIN source_bindings b ON b.source_uuid=ss.source_uuid
               WHERE b.consumer_system=? AND ss.status='available'""",
            (consumer_system,),
        ).fetchone()[0])
        representations = int(connection.execute(
            """SELECT COUNT(DISTINCT r.representation_uuid)
               FROM source_representations r
               JOIN source_snapshots ss ON ss.snapshot_uuid=r.snapshot_uuid
               JOIN source_bindings b ON b.source_uuid=ss.source_uuid
               WHERE b.consumer_system=?""",
            (consumer_system,),
        ).fetchone()[0])
        physical_files = int(connection.execute(
            """SELECT COUNT(DISTINCT r.version_uuid)
               FROM source_representations r
               JOIN source_snapshots ss ON ss.snapshot_uuid=r.snapshot_uuid
               JOIN source_bindings b ON b.source_uuid=ss.source_uuid
               WHERE b.consumer_system=?""",
            (consumer_system,),
        ).fetchone()[0])
        return {
            "sources": sources,
            "snapshots": snapshots,
            "available_snapshots": available,
            "representations": representations,
            "physical_files": physical_files,
            "consumers": consumers,
            "bindings": bindings,
        }

    queries = {
        "sources": "SELECT COUNT(*) FROM source_registry",
        "snapshots": "SELECT COUNT(*) FROM source_snapshots",
        "available_snapshots": "SELECT COUNT(*) FROM source_snapshots WHERE status='available'",
        "representations": "SELECT COUNT(*) FROM source_representations",
        "physical_files": "SELECT COUNT(DISTINCT version_uuid) FROM source_representations",
        "consumers": "SELECT COUNT(*) FROM source_consumer_registry",
        "bindings": "SELECT COUNT(*) FROM source_bindings",
    }
    return {name: int(connection.execute(sql).fetchone()[0]) for name, sql in queries.items()}

def list_sources(
    connection: sqlite3.Connection,
    *,
    consumer_system: str | None = None,
    consumer_instance: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Return source inventory rows with optional consumer-binding context."""
    ensure_source_catalog_schema(connection)
    where: list[str] = []
    params: list[Any] = []
    if consumer_system:
        where.append("b.consumer_system = ?")
        params.append(consumer_system)
    if consumer_instance:
        where.append("b.consumer_instance = ?")
        params.append(consumer_instance)
    if status:
        where.append("s.status = ?")
        params.append(status)
    if search:
        like = f"%{search}%"
        where.append(
            "(s.title LIKE ? OR s.publisher LIKE ? OR s.canonical_url LIKE ? "
            "OR b.external_source_id LIKE ? OR b.consumer_instance LIKE ?)"
        )
        params.extend([like, like, like, like, like])
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    params.append(max(1, min(int(limit), 10_000)))

    rows = connection.execute(
        f"""
        SELECT
            b.consumer_system,
            b.consumer_instance,
            b.external_source_id,
            s.source_uuid,
            s.title,
            s.publisher,
            s.canonical_url,
            s.source_kind,
            s.source_family,
            s.status,
            b.role,
            b.evidence_class,
            b.authority_class,
            b.category,
            b.priority,
            COUNT(DISTINCT ss.snapshot_uuid) AS snapshot_count,
            SUM(CASE WHEN ss.status='available' THEN 1 ELSE 0 END) AS available_snapshot_count,
            COUNT(DISTINCT r.representation_uuid) AS representation_count
        FROM source_bindings b
        JOIN source_registry s ON s.source_uuid = b.source_uuid
        LEFT JOIN source_snapshots ss ON ss.source_uuid = s.source_uuid
        LEFT JOIN source_representations r ON r.snapshot_uuid = ss.snapshot_uuid
        {where_sql}
        GROUP BY b.id
        ORDER BY b.consumer_system, b.consumer_instance, s.publisher, s.title, b.external_source_id
        LIMIT ?
        """,
        tuple(params),
    ).fetchall()
    return [dict(row) for row in rows]


def list_source_snapshots(connection: sqlite3.Connection, source_uuid: str) -> list[dict[str, Any]]:
    """Return snapshots with representation counts for one logical source."""
    ensure_source_catalog_schema(connection)
    rows = connection.execute(
        """
        SELECT ss.*, COUNT(r.representation_uuid) AS representation_count
        FROM source_snapshots ss
        LEFT JOIN source_representations r ON r.snapshot_uuid=ss.snapshot_uuid
        WHERE ss.source_uuid=?
        GROUP BY ss.snapshot_uuid
        ORDER BY COALESCE(ss.retrieved_at, ss.created_at) DESC
        """,
        (source_uuid,),
    ).fetchall()
    return [dict(row) for row in rows]


def verify_source_storage(connection: sqlite3.Connection) -> dict[str, Any]:
    """Verify that source representations still resolve to valid local bytes."""
    ensure_source_catalog_schema(connection)
    rows = connection.execute(
        """
        SELECT DISTINCT lr.version_uuid, lr.storage_path, lr.sha256
        FROM source_representations r
        JOIN library_rows lr ON lr.version_uuid=r.version_uuid
        ORDER BY lr.version_uuid
        """
    ).fetchall()
    missing: list[str] = []
    mismatched: list[dict[str, str]] = []
    checked = 0
    for row in rows:
        path = resolve_content_path(str(row["storage_path"] or ""))
        if not path.is_file():
            missing.append(str(row["version_uuid"]))
            continue
        checked += 1
        actual = _sha256_file(path)
        expected = _normalize_sha256(row["sha256"])
        if expected and actual != expected:
            mismatched.append(
                {
                    "version_uuid": str(row["version_uuid"]),
                    "expected": expected,
                    "actual": actual,
                }
            )
    return {
        "ok": not missing and not mismatched,
        "physical_files": len(rows),
        "checked": checked,
        "missing_version_uuids": missing,
        "hash_mismatches": mismatched,
    }


def _normalize_sha256(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if text.startswith("sha256:"):
        text = text[7:]
    if len(text) == 64 and all(ch in "0123456789abcdef" for ch in text):
        return text
    return None


def _sha256_file(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
