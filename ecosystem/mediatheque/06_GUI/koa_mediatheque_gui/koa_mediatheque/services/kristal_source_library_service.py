"""Legacy Kristal-source import adapter for the canonical Médiathèque source catalog.

Kristal ``external-source-library`` stores are accepted as an input format, but
Médiathèque owns the resulting generic Source → Snapshot → Representation
records. Kristal is recorded only as a consumer binding. New writes target the
schema-v4 ``source_*`` authority tables; schema-v3 ``kristal_*`` source tables
are migration/compatibility inputs only.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import sqlite3
from pathlib import Path

from koa_mediatheque.workspace import resolve_content_path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit, urlunsplit
from uuid import NAMESPACE_URL, uuid4, uuid5

from koa_mediatheque.constants import SOURCE_FILES_FILEAREA
from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.repositories.library_rows_repository import (
    get_library_rows_by_sha256,
    insert_library_row,
    update_library_row_by_version_uuid,
)
from koa_mediatheque.schema import utc_now_iso
from koa_mediatheque.services.file_facts import get_file_facts
from koa_mediatheque.services.source_catalog_service import (
    ensure_source_catalog_schema,
    get_source_stats,
    list_source_snapshots as list_catalog_source_snapshots,
    list_sources as list_catalog_sources,
    verify_source_storage,
)
from koa_mediatheque.services.storage_service import copy_into_storage

SOURCE_STORE_FILENAME = "source-store.json"
SOURCE_LIBRARY_DIRNAME = "external-source-library"
KRISTAL_IMPORT_ADAPTER_PROFILE = "koa.kristal-source-import/2.0.0"
KRISTAL_CONSUMER_SYSTEM = "kristal"


class KristalSourceLibraryError(ValueError):
    """Raised when a Kristal source store cannot be interpreted safely."""


def ensure_kristal_source_schema(connection: sqlite3.Connection) -> None:
    """Ensure the generic source authority and record the Kristal import adapter."""
    ensure_source_catalog_schema(connection)
    connection.execute(
        """
        INSERT INTO schema_meta(key, value, updated_at)
        VALUES ('kristal_source_import_adapter_profile', ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """,
        (KRISTAL_IMPORT_ADAPTER_PROFILE, utc_now_iso()),
    )
    connection.commit()

def discover_kristal_source_stores(root: str | Path) -> list[dict[str, Any]]:
    """Discover canonical ``external-source-library/source-store.json`` stores."""
    base = Path(root).expanduser().resolve()
    if not base.exists():
        return []

    stores: list[dict[str, Any]] = []
    for path in sorted(base.rglob(SOURCE_STORE_FILENAME)):
        if path.parent.name != SOURCE_LIBRARY_DIRNAME:
            continue
        try:
            data = _read_json_object(path)
            entries = data.get("entries") if isinstance(data.get("entries"), dict) else {}
            snapshot_count = sum(
                len(entry.get("snapshots") or [])
                for entry in entries.values()
                if isinstance(entry, dict)
            )
            representation_count = sum(
                len(snapshot.get("representations") or [])
                for entry in entries.values()
                if isinstance(entry, dict)
                for snapshot in (entry.get("snapshots") or [])
                if isinstance(snapshot, dict)
            )
            available_count = sum(
                1
                for entry in entries.values()
                if isinstance(entry, dict)
                for snapshot in (entry.get("snapshots") or [])
                if isinstance(snapshot, dict) and snapshot.get("status") == "available"
            )
            kristal_id = _kristal_id_for_store(path)
            stores.append(
                {
                    "kristal_id": kristal_id,
                    "kristal_root": str(path.parent.parent),
                    "source_library_path": str(path.parent),
                    "source_store_path": str(path),
                    "format": data.get("format"),
                    "version": data.get("version"),
                    "entries": len(entries),
                    "snapshots": snapshot_count,
                    "available_snapshots": available_count,
                    "representations": representation_count,
                }
            )
        except Exception as exc:
            stores.append(
                {
                    "kristal_id": _kristal_id_for_store(path),
                    "kristal_root": str(path.parent.parent),
                    "source_library_path": str(path.parent),
                    "source_store_path": str(path),
                    "error": str(exc),
                }
            )
    return stores


def discover_source_library_candidates(root: str | Path) -> list[dict[str, Any]]:
    """List canonical stores plus source-like directories needing an adapter."""
    base = Path(root).expanduser().resolve()
    canonical = {Path(item["source_library_path"]) for item in discover_kristal_source_stores(base)}
    candidates: list[dict[str, Any]] = []
    names = {"external-source-library", "knowledge-sources", "canonical-corpus"}
    for directory in sorted(path for path in base.rglob("*") if path.is_dir() and path.name in names):
        kind = "canonical" if directory in canonical else "adapter_required"
        candidates.append(
            {
                "kristal_id": _nearest_kristal_name(directory),
                "path": str(directory),
                "directory_kind": directory.name,
                "management_state": kind,
            }
        )
    return candidates


def plan_kristal_source_store(store_path: str | Path) -> dict[str, Any]:
    """Return a no-write import plan for one source-store.json."""
    path = Path(store_path).expanduser().resolve()
    data = _read_json_object(path)
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise KristalSourceLibraryError("source-store.json must contain an object named 'entries'.")

    files: list[dict[str, Any]] = []
    snapshot_count = 0
    available_count = 0
    error_count = 0
    missing_count = 0
    declared_bytes = 0

    for source_id, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        for snapshot in entry.get("snapshots") or []:
            if not isinstance(snapshot, dict):
                continue
            snapshot_count += 1
            if snapshot.get("status") == "available":
                available_count += 1
            elif snapshot.get("status") == "error":
                error_count += 1
            for representation in _snapshot_representations(snapshot, path.parent):
                relative_path = representation.get("path")
                if not relative_path:
                    continue
                local_path = (path.parent / str(relative_path)).resolve()
                exists = local_path.is_file()
                if not exists:
                    missing_count += 1
                declared_bytes += int(representation.get("size_bytes") or 0)
                files.append(
                    {
                        "source_id": str(source_id),
                        "snapshot_id": snapshot.get("snapshot_id"),
                        "kind": representation.get("kind"),
                        "relative_path": str(relative_path),
                        "path": str(local_path),
                        "exists": exists,
                        "declared_sha256": representation.get("sha256"),
                        "declared_size_bytes": representation.get("size_bytes"),
                        "declared_mime_type": representation.get("mime_type"),
                    }
                )

    return {
        "kristal_id": _kristal_id_for_store(path),
        "store_path": str(path),
        "format": data.get("format"),
        "version": data.get("version"),
        "sources": len(entries),
        "snapshots": snapshot_count,
        "available_snapshots": available_count,
        "error_snapshots": error_count,
        "representations": len(files),
        "missing_files": missing_count,
        "declared_bytes": declared_bytes,
        "files": files,
    }


def import_kristal_source_store(
    connection: sqlite3.Connection,
    store_path: str | Path,
    storage_root: str | Path,
    *,
    actor: str = "kristal_source_migrator",
) -> OperationResult:
    """Copy one canonical Kristal source store into the shared kOA catalog."""
    ensure_kristal_source_schema(connection)
    path = Path(store_path).expanduser().resolve()
    storage = Path(storage_root).expanduser().resolve()
    import_uuid = str(uuid4())

    try:
        data = _read_json_object(path)
        entries = data.get("entries")
        if not isinstance(entries, dict):
            raise KristalSourceLibraryError("source-store.json must contain an object named 'entries'.")
    except Exception as exc:
        return _failure("import_kristal_source_store", "invalid_store", "ERR_KRISTAL_SOURCE_STORE", str(exc))

    kristal_id = _kristal_id_for_store(path)
    now = utc_now_iso()
    kristal_meta = data.get("kristal") if isinstance(data.get("kristal"), dict) else {}
    _upsert_registry(connection, kristal_id, path, data, kristal_meta, now)

    counters = {
        "sources_seen": 0,
        "sources_created_or_updated": 0,
        "links_upserted": 0,
        "snapshots_upserted": 0,
        "representations_linked": 0,
        "files_copied": 0,
        "files_deduplicated": 0,
        "files_missing": 0,
        "hash_mismatches": 0,
    }
    warnings: list[KoaMessage] = []

    for source_id, raw_entry in entries.items():
        if not isinstance(raw_entry, dict):
            continue
        source_id = str(source_id)
        counters["sources_seen"] += 1
        source_uuid = _source_uuid(kristal_id, source_id, raw_entry.get("source_url"))
        source_status = _entry_status(raw_entry)
        _upsert_source(connection, source_uuid, raw_entry, source_status, now)
        counters["sources_created_or_updated"] += 1
        _upsert_source_link(connection, kristal_id, source_uuid, source_id, raw_entry, kristal_meta, now)
        counters["links_upserted"] += 1

        for snapshot in raw_entry.get("snapshots") or []:
            if not isinstance(snapshot, dict):
                continue
            snapshot_id = str(snapshot.get("snapshot_id") or "").strip()
            if not snapshot_id:
                snapshot_id = f"legacy-{uuid5(NAMESPACE_URL, json.dumps(snapshot, sort_keys=True, default=str))}"
            snapshot_uuid = _snapshot_uuid(source_uuid, snapshot_id)
            _upsert_snapshot(connection, snapshot_uuid, source_uuid, snapshot_id, snapshot, now)
            counters["snapshots_upserted"] += 1

            for representation in _snapshot_representations(snapshot, path.parent):
                rel_path = str(representation.get("path") or "").strip()
                if not rel_path:
                    continue
                local_path = (path.parent / rel_path).resolve()
                kind = str(representation.get("kind") or "unknown")
                if not local_path.is_file():
                    counters["files_missing"] += 1
                    _write_import_log(
                        connection, import_uuid, kristal_id, source_id, snapshot_id, kind,
                        local_path, None, "missing", "Referenced representation file is missing."
                    )
                    warnings.append(
                        KoaMessage(
                            code="WARN_KRISTAL_SOURCE_FILE_MISSING",
                            severity="warning",
                            message=f"Fichier source introuvable: {local_path}",
                            details={"kristal_id": kristal_id, "source_id": source_id, "kind": kind},
                        )
                    )
                    continue

                facts = get_file_facts(local_path)
                actual_sha = str(facts.sha256 or "").lower()
                declared_sha = _normalize_sha256(representation.get("sha256"))
                if declared_sha and actual_sha != declared_sha:
                    counters["hash_mismatches"] += 1
                    _write_import_log(
                        connection, import_uuid, kristal_id, source_id, snapshot_id, kind,
                        local_path, None, "hash_mismatch",
                        f"declared={declared_sha} actual={actual_sha}"
                    )
                    warnings.append(
                        KoaMessage(
                            code="WARN_KRISTAL_SOURCE_HASH_MISMATCH",
                            severity="warning",
                            message=f"SHA-256 différent pour {local_path.name}; import bloqué pour ce fichier.",
                            details={"declared": declared_sha, "actual": actual_sha},
                        )
                    )
                    continue

                row, deduplicated = _ensure_library_row(
                    connection,
                    local_path=local_path,
                    storage_root=storage,
                    source_uuid=source_uuid,
                    kristal_id=kristal_id,
                    source_id=source_id,
                    source_entry=raw_entry,
                    snapshot_id=snapshot_id,
                    snapshot_uuid=snapshot_uuid,
                    representation=representation,
                    actor=actor,
                )
                if row is None:
                    _write_import_log(
                        connection, import_uuid, kristal_id, source_id, snapshot_id, kind,
                        local_path, None, "failed", "Could not create/reuse library row."
                    )
                    continue

                if deduplicated:
                    counters["files_deduplicated"] += 1
                else:
                    counters["files_copied"] += 1

                version_uuid = str(row["version_uuid"])
                _upsert_representation(
                    connection,
                    snapshot_uuid=snapshot_uuid,
                    version_uuid=version_uuid,
                    representation=representation,
                    actual_sha=actual_sha,
                )
                counters["representations_linked"] += 1
                _write_import_log(
                    connection, import_uuid, kristal_id, source_id, snapshot_id, kind,
                    local_path, version_uuid, "deduplicated" if deduplicated else "copied", None
                )

    return OperationResult(
        success=counters["hash_mismatches"] == 0,
        operation="import_kristal_source_store",
        result="imported" if counters["hash_mismatches"] == 0 else "imported_with_hash_mismatches",
        entity_type="kristal_source_store",
        entity_uuid=kristal_id,
        path=str(path),
        data={"import_uuid": import_uuid, "kristal_id": kristal_id, **counters},
        warnings=warnings,
        errors=[] if counters["hash_mismatches"] == 0 else [
            KoaMessage(
                code="ERR_KRISTAL_SOURCE_HASH_MISMATCH",
                severity="error",
                message="Au moins une représentation avait un SHA-256 différent du catalogue source; ces fichiers n'ont pas été importés.",
                details={"count": counters["hash_mismatches"]},
            )
        ],
    )


def import_discovered_kristal_stores(
    connection: sqlite3.Connection,
    kristal_root: str | Path,
    storage_root: str | Path,
) -> list[OperationResult]:
    """Import every canonical source store discovered under a Kristal root."""
    results: list[OperationResult] = []
    for store in discover_kristal_source_stores(kristal_root):
        if store.get("error"):
            results.append(
                _failure(
                    "import_discovered_kristal_stores",
                    "invalid_store",
                    "ERR_KRISTAL_SOURCE_STORE",
                    str(store["error"]),
                )
            )
            continue
        results.append(
            import_kristal_source_store(
                connection,
                store["source_store_path"],
                storage_root,
            )
        )
    return results


def get_kristal_source_stats(connection: sqlite3.Connection) -> dict[str, int]:
    """Compatibility view of source-catalog statistics for Kristal bindings."""
    stats = get_source_stats(connection, consumer_system=KRISTAL_CONSUMER_SYSTEM)
    return {"kristals": stats["consumers"], "links": stats["bindings"], **stats}


def list_kristal_sources(
    connection: sqlite3.Connection,
    *,
    kristal_id: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Return Kristal consumer bindings over the generic source authority."""
    rows = list_catalog_sources(
        connection,
        consumer_system=KRISTAL_CONSUMER_SYSTEM,
        consumer_instance=kristal_id,
        status=status,
        search=search,
        limit=limit,
    )
    for row in rows:
        row["kristal_id"] = row.get("consumer_instance")
        row["source_id"] = row.get("external_source_id")
    return rows


def list_source_snapshots(connection: sqlite3.Connection, source_uuid: str) -> list[dict[str, Any]]:
    """Compatibility wrapper over the canonical source snapshot inventory."""
    return list_catalog_source_snapshots(connection, source_uuid)

def export_kristal_bindings(
    connection: sqlite3.Connection,
    output_dir: str | Path,
    *,
    kristal_id: str | None = None,
) -> list[str]:
    """Export read-only pointer manifests; no files are copied back into Kristals."""
    ensure_kristal_source_schema(connection)
    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    if kristal_id:
        kristals = [kristal_id]
    else:
        kristals = [str(row[0]) for row in connection.execute("SELECT consumer_instance FROM source_consumer_registry WHERE consumer_system='kristal' ORDER BY consumer_instance")]

    written: list[str] = []
    for kid in kristals:
        links = connection.execute(
            """
            SELECT l.*, s.title, s.publisher, s.canonical_url, s.source_kind, s.status AS source_status
            FROM source_bindings l
            JOIN source_registry s ON s.source_uuid=l.source_uuid
            WHERE l.consumer_system='kristal' AND l.consumer_instance=?
            ORDER BY l.external_source_id
            """,
            (kid,),
        ).fetchall()
        sources: list[dict[str, Any]] = []
        for link_row in links:
            link = dict(link_row)
            snapshots = connection.execute(
                "SELECT * FROM source_snapshots WHERE source_uuid=? ORDER BY COALESCE(retrieved_at, created_at)",
                (link["source_uuid"],),
            ).fetchall()
            snapshot_items: list[dict[str, Any]] = []
            for snap_row in snapshots:
                snap = dict(snap_row)
                reps = connection.execute(
                    """
                    SELECT r.*, lr.sha256, lr.mimetype, lr.filesize, lr.filename, lr.storage_path
                    FROM source_representations r
                    JOIN library_rows lr ON lr.version_uuid=r.version_uuid
                    WHERE r.snapshot_uuid=?
                    ORDER BY r.representation_kind
                    """,
                    (snap["snapshot_uuid"],),
                ).fetchall()
                snapshot_items.append(
                    {
                        "snapshot_id": snap["snapshot_id"],
                        "snapshot_uuid": snap["snapshot_uuid"],
                        "retrieved_at": snap["retrieved_at"],
                        "status": snap["status"],
                        "representations": [
                            {
                                "kind": rep["representation_kind"],
                                "version_uuid": rep["version_uuid"],
                                "locator": f"koa-media://version/{rep['version_uuid']}",
                                "sha256": rep["sha256"],
                                "mimetype": rep["mimetype"],
                                "filesize": rep["filesize"],
                                "filename": rep["filename"],
                            }
                            for rep in reps
                        ],
                    }
                )
            sources.append(
                {
                    "source_id": link["external_source_id"],
                    "source_uuid": link["source_uuid"],
                    "title": link["title"],
                    "publisher": link["publisher"],
                    "source_url": link["canonical_url"],
                    "source_kind": link["source_kind"],
                    "status": link["source_status"],
                    "classification": {
                        "role": link["role"],
                        "evidence_class": link["evidence_class"],
                        "authority_class": link["authority_class"],
                        "category": link["category"],
                        "priority": link["priority"],
                    },
                    "snapshots": snapshot_items,
                }
            )
        payload = {
            "format": "koa.kristal-source-bindings/v1",
            "generated_at": utc_now_iso(),
            "kristal_id": kid,
            "source_count": len(sources),
            "sources": sources,
        }
        out = target / f"{_safe_slug(kid)}.kristal-source-bindings.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(str(out))
    return written


def verify_kristal_source_storage(connection: sqlite3.Connection) -> dict[str, Any]:
    """Compatibility wrapper for generic source-storage verification."""
    return verify_source_storage(connection)

def _ensure_library_row(
    connection: sqlite3.Connection,
    *,
    local_path: Path,
    storage_root: Path,
    source_uuid: str,
    kristal_id: str,
    source_id: str,
    source_entry: Mapping[str, Any],
    snapshot_id: str,
    snapshot_uuid: str,
    representation: Mapping[str, Any],
    actor: str,
) -> tuple[dict[str, Any] | None, bool]:
    facts = get_file_facts(local_path)
    sha = str(facts.sha256 or "").lower()
    existing = get_library_rows_by_sha256(connection, sha)
    relation = f"source:{source_uuid}"
    snapshot_relation = f"source:snapshot:{snapshot_uuid}"
    consumer_relation = f"consumer:kristal:{kristal_id}/{source_id}"
    if existing:
        row = existing[0]
        _merge_relations(connection, row, [relation, snapshot_relation, consumer_relation], actor=actor)
        return row, True

    kind = str(representation.get("kind") or "unknown")
    media_uuid = str(uuid5(NAMESPACE_URL, f"koa-kristal-media:{source_uuid}:{kind}"))
    version_uuid = str(uuid5(NAMESPACE_URL, f"koa-kristal-version:{source_uuid}:{kind}:{snapshot_id}:{sha}"))
    copy_result = copy_into_storage(
        local_path,
        storage_root,
        filearea=SOURCE_FILES_FILEAREA,
        version_uuid=version_uuid,
        mode="copy_and_rename",
    )
    if not copy_result.success:
        return None, False

    title = str(source_entry.get("title") or source_id)
    publisher = str(source_entry.get("publisher") or "").strip() or None
    mime = facts.mimetype or mimetypes.guess_type(local_path.name)[0]
    row_data = {
        "media_uuid": media_uuid,
        "version_uuid": version_uuid,
        "title": f"{title} — {kind}",
        "subtitle": publisher,
        "description": f"Représentation locale '{kind}' d'une source du catalogue Médiathèque.",
        "summary": str(source_entry.get("source_url") or ""),
        "original_path": str(local_path),
        "storage_path": copy_result.path,
        "filename": local_path.name,
        "extension": local_path.suffix.lower(),
        "mimetype": mime,
        "filesize": facts.filesize,
        "sha256": sha,
        "filearea": SOURCE_FILES_FILEAREA,
        "media_type": _media_type_for(mime, local_path.suffix),
        "language": "und",
        "library_scope": "koa",
        "uckk_relevance": "unknown",
        "target_system": "other",
        "target_export_allowed": 0,
        "public_state": "unknown",
        "visibility": "private",
        "access_level": "private",
        "ownership_scope": "unknown",
        "source_type": "imported",
        "source_ownership": "external_reference",
        "rights_status": "unknown",
        "rights_note": str(source_entry.get("license") or "") or None,
        "restriction_state": "none",
        "redaction_required": 0,
        "status": "active",
        "provenance": "imported",
        "ai_validation_state": "ai_uncertain",
        "canonical_validation_state": "unverified",
        "human_review_required": 0,
        "collections_json": json.dumps(["sources", f"consumer:kristal:{kristal_id}"], ensure_ascii=False),
        "tags_json": json.dumps(["source-representation", kind], ensure_ascii=False),
        "relations_json": json.dumps([relation, snapshot_relation, consumer_relation], ensure_ascii=False),
        "content_flags_json": "[]",
        "audience_suitability": "unknown",
        "export_to_uckk": "no",
        "export_to_public": "no",
        "import_batch": f"source-import:kristal:{kristal_id}",
        "notes": f"source_uuid={source_uuid}; source_id={source_id}; snapshot_id={snapshot_id}",
    }
    inserted = insert_library_row(connection, row_data)
    if not inserted.success:
        return None, False
    return inserted.data.get("row"), False


def _merge_relations(connection: sqlite3.Connection, row: Mapping[str, Any], additions: Iterable[str], *, actor: str) -> None:
    try:
        current = json.loads(str(row.get("relations_json") or "[]"))
    except json.JSONDecodeError:
        current = []
    if not isinstance(current, list):
        current = []
    merged = list(current)
    changed = False
    for value in additions:
        if value not in merged:
            merged.append(value)
            changed = True
    if changed:
        update_library_row_by_version_uuid(
            connection,
            str(row["version_uuid"]),
            {"relations_json": json.dumps(merged, ensure_ascii=False)},
            actor=actor,
        )


def _upsert_registry(connection: sqlite3.Connection, kristal_id: str, path: Path, data: Mapping[str, Any], kristal_meta: Mapping[str, Any], now: str) -> None:
    connection.execute(
        """
        INSERT INTO source_consumer_registry(
            consumer_system, consumer_instance, consumer_root, source_library_path,
            source_store_format, source_store_version, consumer_state_id,
            artifact_type, artifact_status, last_seen_at, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(consumer_system, consumer_instance) DO UPDATE SET
            consumer_root=excluded.consumer_root,
            source_library_path=excluded.source_library_path,
            source_store_format=excluded.source_store_format,
            source_store_version=excluded.source_store_version,
            consumer_state_id=excluded.consumer_state_id,
            artifact_type=excluded.artifact_type,
            artifact_status=excluded.artifact_status,
            last_seen_at=excluded.last_seen_at,
            metadata_json=excluded.metadata_json
        """,
        (
            KRISTAL_CONSUMER_SYSTEM, kristal_id, str(path.parent.parent), str(path.parent),
            data.get("format"), data.get("version"), kristal_meta.get("state_id"),
            kristal_meta.get("artifact_type"), kristal_meta.get("artifact_status"), now,
            json.dumps(dict(kristal_meta), ensure_ascii=False, sort_keys=True),
        ),
    )
    connection.commit()


def _upsert_source(connection: sqlite3.Connection, source_uuid: str, entry: Mapping[str, Any], status: str, now: str) -> None:
    canonical_url = str(entry.get("source_url") or "").strip() or None
    connection.execute(
        """
        INSERT INTO source_registry(
            source_uuid, canonical_url, canonical_url_key, title, publisher,
            source_kind, source_family, rights_note, status, source_metadata_json,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_uuid) DO UPDATE SET
            canonical_url=COALESCE(excluded.canonical_url, source_registry.canonical_url),
            canonical_url_key=COALESCE(excluded.canonical_url_key, source_registry.canonical_url_key),
            title=excluded.title,
            publisher=COALESCE(excluded.publisher, source_registry.publisher),
            source_kind=excluded.source_kind,
            source_family=COALESCE(excluded.source_family, source_registry.source_family),
            rights_note=COALESCE(excluded.rights_note, source_registry.rights_note),
            status=excluded.status,
            source_metadata_json=excluded.source_metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            source_uuid, canonical_url, _normalize_url(canonical_url),
            str(entry.get("title") or entry.get("source_id") or source_uuid),
            entry.get("publisher"), str(entry.get("source_type") or "unknown"),
            entry.get("source_family"), entry.get("license"), status,
            json.dumps(_entry_without_snapshots(entry), ensure_ascii=False, sort_keys=True), now, now,
        ),
    )
    connection.commit()


def _upsert_source_link(connection: sqlite3.Connection, kristal_id: str, source_uuid: str, source_id: str, entry: Mapping[str, Any], kristal_meta: Mapping[str, Any], now: str) -> None:
    authority = entry.get("authority") if isinstance(entry.get("authority"), dict) else {}
    catalog = entry.get("catalog") if isinstance(entry.get("catalog"), dict) else {}
    connection.execute(
        """
        INSERT INTO source_bindings(
            consumer_system, consumer_instance, source_uuid, external_source_id,
            role, evidence_class, authority_class, category, priority,
            declared_in_current_consumer, consumer_state_id, binding_metadata_json,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(consumer_system, consumer_instance, external_source_id) DO UPDATE SET
            source_uuid=excluded.source_uuid,
            role=excluded.role,
            evidence_class=excluded.evidence_class,
            authority_class=excluded.authority_class,
            category=excluded.category,
            priority=excluded.priority,
            declared_in_current_consumer=excluded.declared_in_current_consumer,
            consumer_state_id=excluded.consumer_state_id,
            binding_metadata_json=excluded.binding_metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            KRISTAL_CONSUMER_SYSTEM, kristal_id, source_uuid, source_id,
            entry.get("role"), entry.get("evidence_class"), authority.get("authority_class"),
            catalog.get("category"), catalog.get("priority"),
            1 if entry.get("declared_in_current_kristal", True) else 0,
            kristal_meta.get("state_id"),
            json.dumps(_entry_without_snapshots(entry), ensure_ascii=False, sort_keys=True), now, now,
        ),
    )
    connection.commit()


def _upsert_snapshot(connection: sqlite3.Connection, snapshot_uuid: str, source_uuid: str, snapshot_id: str, snapshot: Mapping[str, Any], now: str) -> None:
    connection.execute(
        """
        INSERT INTO source_snapshots(
            snapshot_uuid, source_uuid, snapshot_id, retrieved_at, status,
            requested_url, canonical_source_url, final_url, http_status,
            acquisition_method, error, metadata_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_uuid, snapshot_id) DO UPDATE SET
            retrieved_at=excluded.retrieved_at,
            status=excluded.status,
            requested_url=excluded.requested_url,
            canonical_source_url=excluded.canonical_source_url,
            final_url=excluded.final_url,
            http_status=excluded.http_status,
            acquisition_method=excluded.acquisition_method,
            error=excluded.error,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            snapshot_uuid, source_uuid, snapshot_id, snapshot.get("retrieved_at"),
            str(snapshot.get("status") or "declared"), snapshot.get("requested_url"),
            snapshot.get("canonical_source_url"), snapshot.get("final_url"),
            snapshot.get("http_status"), snapshot.get("acquisition_method"), snapshot.get("error"),
            json.dumps(_snapshot_without_representations(snapshot), ensure_ascii=False, sort_keys=True), now, now,
        ),
    )
    connection.commit()


def _upsert_representation(connection: sqlite3.Connection, *, snapshot_uuid: str, version_uuid: str, representation: Mapping[str, Any], actual_sha: str) -> None:
    kind = str(representation.get("kind") or "unknown")
    # Preserve the legacy UUID namespace so migrated catalogs remain idempotent.
    rep_uuid = str(uuid5(NAMESPACE_URL, f"koa-kristal-representation:{snapshot_uuid}:{kind}:{actual_sha}"))
    connection.execute(
        """
        INSERT INTO source_representations(
            representation_uuid, snapshot_uuid, version_uuid, representation_kind,
            original_relative_path, declared_sha256, declared_size_bytes, declared_mime_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(representation_uuid) DO UPDATE SET
            version_uuid=excluded.version_uuid,
            original_relative_path=excluded.original_relative_path,
            declared_sha256=excluded.declared_sha256,
            declared_size_bytes=excluded.declared_size_bytes,
            declared_mime_type=excluded.declared_mime_type
        """,
        (
            rep_uuid, snapshot_uuid, version_uuid, kind, representation.get("path"),
            _normalize_sha256(representation.get("sha256")) or actual_sha,
            representation.get("size_bytes"), representation.get("mime_type"),
        ),
    )
    connection.commit()


def _write_import_log(connection: sqlite3.Connection, import_uuid: str, kristal_id: str, source_id: str, snapshot_id: str, kind: str, source_path: Path, version_uuid: str | None, result: str, message: str | None) -> None:
    connection.execute(
        """
        INSERT INTO source_import_log(
            import_uuid, consumer_system, consumer_instance, external_source_id,
            snapshot_id, representation_kind, source_path, version_uuid, result, message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            import_uuid, KRISTAL_CONSUMER_SYSTEM, kristal_id, source_id, snapshot_id, kind,
            str(source_path), version_uuid, result, message,
        ),
    )
    connection.commit()

def _snapshot_representations(snapshot: Mapping[str, Any], store_root: Path) -> list[dict[str, Any]]:
    reps = [dict(item) for item in snapshot.get("representations") or [] if isinstance(item, dict)]
    seen_paths = {str(item.get("path") or "") for item in reps}
    metadata_path = str(snapshot.get("metadata_path") or "").strip()
    if metadata_path and metadata_path not in seen_paths:
        local = (store_root / metadata_path).resolve()
        if local.is_file():
            facts = get_file_facts(local)
            reps.append(
                {
                    "kind": "snapshot_metadata",
                    "path": metadata_path,
                    "sha256": facts.sha256,
                    "size_bytes": facts.filesize,
                    "mime_type": facts.mimetype or "application/json",
                }
            )
    return reps


def _source_uuid(kristal_id: str, source_id: str, source_url: Any) -> str:
    normalized = _normalize_url(str(source_url or "").strip() or None)
    basis = f"url:{normalized}" if normalized else f"local:{kristal_id}:{source_id}"
    return str(uuid5(NAMESPACE_URL, f"koa-kristal-source:{basis}"))


def _snapshot_uuid(source_uuid: str, snapshot_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"koa-kristal-snapshot:{source_uuid}:{snapshot_id}"))


def _normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return value.strip()
    if not parts.scheme or not parts.netloc:
        return value.strip()
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def _normalize_sha256(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if text.startswith("sha256:"):
        text = text[7:]
    if len(text) == 64 and all(ch in "0123456789abcdef" for ch in text):
        return text
    return None


def _entry_status(entry: Mapping[str, Any]) -> str:
    snapshots = [item for item in entry.get("snapshots") or [] if isinstance(item, dict)]
    if not snapshots:
        return "declared"
    if any(item.get("status") == "available" for item in snapshots):
        return "available"
    if any(item.get("status") == "error" for item in snapshots):
        return "error"
    return "declared"


def _entry_without_snapshots(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in entry.items() if key != "snapshots"}


def _snapshot_without_representations(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in snapshot.items() if key != "representations"}


def _media_type_for(mimetype: str | None, suffix: str) -> str:
    mime = str(mimetype or "").lower()
    ext = str(suffix or "").lower()
    if mime == "application/pdf" or ext == ".pdf":
        return "pdf"
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("audio/"):
        return "audio"
    if mime.startswith("video/"):
        return "video"
    if ext in {".mhtml", ".mht"} or mime.startswith("multipart/"):
        return "source_package"
    return "document"


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise KristalSourceLibraryError(f"Missing source store: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise KristalSourceLibraryError(f"Expected JSON object: {path}")
    return data


def _kristal_id_for_store(store_path: Path) -> str:
    return store_path.parent.parent.name


def _nearest_kristal_name(path: Path) -> str:
    for current in (path, *path.parents):
        if current.name.startswith("Kristal-"):
            return current.name
    return path.parent.name


def _safe_slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in value).strip("._") or "kristal"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _failure(operation: str, result: str, code: str, message: str) -> OperationResult:
    return OperationResult(
        success=False,
        operation=operation,
        result=result,
        errors=[KoaMessage(code=code, severity="error", message=message)],
    )
