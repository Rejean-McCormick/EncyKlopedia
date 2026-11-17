"""Fail-closed EncyK Source Evidence Handoff 2.0 importer.

The producer owns scope/acquisition; Médiathèque owns durable source objects.
This service never creates Kristal identities, never publishes, and imports only
verified local bytes. It is intentionally opt-in (not part of DB startup).
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import sqlite3
from importlib import resources
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import NAMESPACE_URL, uuid5

from jsonschema import Draft202012Validator, FormatChecker
from koa_mediatheque.constants import SOURCE_FILES_FILEAREA
from koa_mediatheque.services.source_catalog_service import ensure_source_catalog_schema

CONTRACT = "encyk.source-evidence-handoff/2.0.0"
RECEIPT_FORMAT = "koa.encyk-source-handoff-receipt/1.0.0"


class EncyKHandoffError(ValueError):
    """A handoff cannot be safely accepted; no new records should be committed."""


def _canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _digest_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1_048_576), b""):
            h.update(chunk)
    return h.hexdigest()


def _schema():
    return json.loads(resources.files("koa_mediatheque").joinpath(
        "contracts/encyk_source_handoff_2/schema.json").read_text(encoding="utf-8"))


def _normalized_url(value: str):
    parts = urlsplit(value.strip())
    if parts.scheme not in ("https", "http") or not parts.netloc or parts.username or parts.password:
        raise EncyKHandoffError("Invalid canonical URL")
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def _safe_file(root: Path, raw: str):
    if not raw or raw.startswith(("/", "\\")) or "\\" in raw or ":" in raw:
        raise EncyKHandoffError("Unsafe file path")
    parts = raw.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise EncyKHandoffError("Unsafe file path segment")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise EncyKHandoffError("Symlink not allowed in evidence path")
    candidate = current.resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise EncyKHandoffError(f"Evidence missing or outside root: {raw}")
    return candidate


def plan_encyk_handoff(manifest_path: str | Path, evidence_root: str | Path) -> dict:
    """Validate the exact producer schema, identity, paths, sizes and hashes; no writes."""
    manifest = Path(manifest_path).expanduser().resolve()
    root = Path(evidence_root).expanduser().resolve()
    if not manifest.is_file() or not root.is_dir():
        raise EncyKHandoffError("Missing manifest or evidence root")
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise EncyKHandoffError(f"Invalid manifest JSON: {exc}") from exc
    errors = sorted(Draft202012Validator(_schema(), format_checker=FormatChecker()).iter_errors(payload),
                    key=lambda x: str(x.absolute_path))
    if errors:
        raise EncyKHandoffError("Schema validation failed: " + "; ".join(e.message for e in errors[:4]))
    signed_payload = {k: v for k, v in payload.items() if k not in ("created_at", "handoff_id")}
    expected = "handoff-" + hashlib.sha256(_canonical(signed_payload)).hexdigest()[:20]
    if payload["handoff_id"] != expected:
        raise EncyKHandoffError("handoff_id does not match the EncyK producer algorithm")
    entries = ([payload["scope_config"]] if "scope_config" in payload else []) + payload["files"]
    roles, paths = set(), set()
    checked = []
    for entry in entries:
        role, relative = entry["role"], entry["path"]
        if role in roles or relative in paths:
            raise EncyKHandoffError("Duplicate role or evidence path")
        roles.add(role)
        paths.add(relative)
        p = _safe_file(root, relative)
        if p.stat().st_size != entry["bytes"] or "sha256:" + _digest_file(p) != entry["sha256"]:
            raise EncyKHandoffError(f"Evidence content mismatch: {relative}")
        checked.append({"role": role, "path": relative, "absolute": p,
                        "sha256": entry["sha256"][7:], "bytes": entry["bytes"]})
    required = {"frozen_scope", "evidence_manifest", "lossless_source_evidence", "entity_content_manifest"}
    if not required.issubset(roles):
        raise EncyKHandoffError("Missing canonical EncyK evidence roles")
    url = _normalized_url(payload["source_descriptor"]["canonical_url"])
    return {"handoff_id": payload["handoff_id"], "contract": CONTRACT, "payload": payload,
            "payload_sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
            "canonical_url_key": url, "files": checked, "total_bytes": sum(i["bytes"] for i in checked)}


def _ensure_receipts(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS encyk_handoff_receipts (
        handoff_id TEXT PRIMARY KEY,
        payload_sha256 TEXT NOT NULL,
        source_uuid TEXT NOT NULL,
        snapshot_uuid TEXT NOT NULL,
        receipt_json TEXT NOT NULL,
        accepted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        FOREIGN KEY(source_uuid) REFERENCES source_registry(source_uuid),
        FOREIGN KEY(snapshot_uuid) REFERENCES source_snapshots(snapshot_uuid)
    )""")
    connection.commit()


def _existing_receipt(connection, plan):
    row = connection.execute("SELECT payload_sha256, receipt_json FROM encyk_handoff_receipts WHERE handoff_id=?",
                             (plan["handoff_id"],)).fetchone()
    if row is None:
        return None
    if row[0] != plan["payload_sha256"]:
        raise EncyKHandoffError("Conflicting replay of handoff_id")
    receipt = json.loads(row[1])
    for entry in receipt["representations"]:
        lib = connection.execute("SELECT storage_path, sha256, filesize FROM library_rows WHERE version_uuid=?",
                                 (entry["version_uuid"],)).fetchone()
        if not lib or str(lib[1]).lower() != entry["sha256"] or lib[2] != entry["bytes"]:
            raise EncyKHandoffError("Previously accepted bytes are not available in library")
        p = Path(lib[0])
        if not p.is_file() or p.stat().st_size != entry["bytes"] or _digest_file(p) != entry["sha256"]:
            raise EncyKHandoffError("Previously stored content has been altered")
    return {**receipt, "status": "already_accepted"}


def import_encyk_handoff(connection: sqlite3.Connection, manifest_path: str | Path,
                         evidence_root: str | Path, storage_root: str | Path) -> dict:
    """Admit verified evidence privately into source_* + library_rows, idempotently.

    Preflight is read-only; database writes use one SQLite transaction. New file
    copies are removed on a handled failure. A process crash can leave orphan
    files, which are non-public and safe to clean up manually after inspection.
    """
    plan = plan_encyk_handoff(manifest_path, evidence_root)
    ensure_source_catalog_schema(connection)
    _ensure_receipts(connection)
    replay = _existing_receipt(connection, plan)
    if replay is not None:
        return replay
    payload = plan["payload"]
    descriptor = payload["source_descriptor"]
    source_url = plan["canonical_url_key"]
    source_record = connection.execute("SELECT source_uuid FROM source_registry WHERE canonical_url_key=?",
                                       (source_url,)).fetchone()
    # Preserve shared source identity; the EncyK external ID remains a binding only.
    source_uuid = source_record[0] if source_record else str(uuid5(NAMESPACE_URL, f"koa-kristal-source:url:{source_url}"))
    snap_key = f"encyk:{payload['scope_key']}:{payload['snapshot_id']}"
    snapshot_uuid = str(uuid5(NAMESPACE_URL, f"koa-encyk-snapshot:{source_uuid}:{snap_key}"))
    existing = connection.execute("SELECT 1 FROM source_snapshots WHERE source_uuid=? AND snapshot_id=?",
                                  (source_uuid, snap_key)).fetchone()
    if existing:
        raise EncyKHandoffError("Snapshot already exists without matching acceptance receipt")
    import_id = payload["handoff_id"]
    target_root = Path(storage_root).expanduser().resolve() / SOURCE_FILES_FILEAREA
    copied = []
    receipt_reps = []
    try:
        connection.execute("BEGIN IMMEDIATE")
        # Two workers may pass the first replay check concurrently. Serialize
        # admission and re-read inside the write lock before copying bytes.
        locked_replay = _existing_receipt(connection, plan)
        if locked_replay is not None:
            connection.rollback()
            return locked_replay
        locked_source = connection.execute(
            "SELECT source_uuid FROM source_registry WHERE canonical_url_key=?", (source_url,)
        ).fetchone()
        source_uuid = locked_source[0] if locked_source else str(uuid5(
            NAMESPACE_URL, f"koa-kristal-source:url:{source_url}"))
        snapshot_uuid = str(uuid5(NAMESPACE_URL,
            f"koa-encyk-snapshot:{source_uuid}:{snap_key}"))
        if connection.execute(
            "SELECT 1 FROM source_snapshots WHERE source_uuid=? AND snapshot_id=?",
            (source_uuid, snap_key)
        ).fetchone():
            raise EncyKHandoffError("Snapshot already exists without matching acceptance receipt")
        connection.execute("""INSERT OR IGNORE INTO source_registry
        (source_uuid,canonical_url,canonical_url_key,title,publisher,source_kind,source_family,status,source_metadata_json)
        VALUES(?,?,?,?,?,?,?,'available',?)""", (source_uuid, descriptor["canonical_url"], source_url,
        descriptor["title"], descriptor.get("publisher"), descriptor["source_kind"], descriptor["source_family"],
        json.dumps({"source_descriptor": descriptor},ensure_ascii=False)))
        connection.execute("""INSERT INTO source_consumer_registry
        (consumer_system,consumer_instance,consumer_root,source_store_format,source_store_version,last_seen_at,metadata_json)
        VALUES('encyk',?,?,?,? ,strftime('%Y-%m-%dT%H:%M:%SZ','now'),?)
        ON CONFLICT(consumer_system,consumer_instance) DO UPDATE SET last_seen_at=excluded.last_seen_at,
        metadata_json=excluded.metadata_json""", (payload["scope_key"],str(Path(evidence_root).resolve()), CONTRACT,
        payload["producer"]["version"],json.dumps({"scope_key":payload["scope_key"]})))
        bind = connection.execute("SELECT source_uuid FROM source_bindings WHERE consumer_system='encyk' AND consumer_instance=? AND external_source_id=?",
                                  (payload["scope_key"],descriptor["external_source_id"])).fetchone()
        if bind and bind[0] != source_uuid:
            raise EncyKHandoffError("External EncyK binding already points to another source")
        connection.execute("""INSERT OR IGNORE INTO source_bindings
        (consumer_system,consumer_instance,source_uuid,external_source_id,binding_metadata_json)
        VALUES('encyk',?,?,?,?)""",(payload["scope_key"],source_uuid,descriptor["external_source_id"],
        json.dumps({"scope_key":payload["scope_key"]})))
        connection.execute("""INSERT INTO source_snapshots
        (snapshot_uuid,source_uuid,snapshot_id,retrieved_at,status,acquisition_method,metadata_json)
        VALUES(?,?,?,?,'available','encyk_source_evidence_handoff',?)""",(snapshot_uuid,source_uuid,snap_key,
        payload["created_at"],json.dumps({"source_snapshot":payload["source_snapshot"],
        "encyk_snapshot_id":payload["snapshot_id"],"scope_key":payload["scope_key"],"handoff_id":import_id},ensure_ascii=False)))
        for entry in plan["files"]:
            sha, role = entry["sha256"], entry["role"]
            row = connection.execute("SELECT version_uuid,storage_path,sha256,filesize FROM library_rows WHERE sha256=? AND filearea=? AND visibility='private' LIMIT 1",(sha,SOURCE_FILES_FILEAREA)).fetchone()
            if row:
                target=Path(row[1])
                if not target.is_file() or target.stat().st_size != entry["bytes"] or _digest_file(target)!=sha:
                    raise EncyKHandoffError("Existing stored candidate failed integrity check")
                version_uuid=row[0]
            else:
                version_uuid=str(uuid5(NAMESPACE_URL,f"koa-encyk-version:{source_uuid}:{snap_key}:{role}:{sha}"))
                suffix=entry["absolute"].suffix.lower()
                target=target_root / (version_uuid + suffix)
                target_root.mkdir(parents=True,exist_ok=True)
                if target.exists():
                    if target.stat().st_size!=entry["bytes"] or _digest_file(target)!=sha:
                        raise EncyKHandoffError("Storage filename conflict")
                else:
                    temp=target.with_name(target.name+'.partial-'+import_id)
                    try:
                        shutil.copyfile(entry["absolute"],temp)
                        if _digest_file(temp)!=sha:raise EncyKHandoffError("Copy integrity mismatch")
                        os.replace(temp,target)
                        copied.append(target)
                    finally:
                        temp.unlink(missing_ok=True)
                mime=mimetypes.guess_type(entry["absolute"].name)[0] or 'application/octet-stream'
                fields={"media_uuid":str(uuid5(NAMESPACE_URL,f"koa-encyk-media:{source_uuid}:{role}")),
                 "version_uuid":version_uuid,"title":descriptor["title"]+' — '+role,
                 "original_path":str(entry["absolute"]),"storage_path":str(target),
                 "filename":entry["absolute"].name,"extension":suffix,"mimetype":mime,
                 "filesize":entry["bytes"],"sha256":sha,"filearea":SOURCE_FILES_FILEAREA,
                 "visibility":"private","access_level":"private","target_export_allowed":0,
                 "export_to_uckk":"no","export_to_public":"no","provenance":"imported",
                 "source_type":"imported","source_ownership":"external_reference","rights_status":"unknown",
                 "canonical_validation_state":"unverified","import_batch":import_id,
                 "notes":"EncyK source-evidence handoff; content evidence only, not semantic canon"}
                cols=','.join(fields)
                marks=','.join('?' for _ in fields)
                connection.execute(f"INSERT INTO library_rows ({cols}) VALUES ({marks})",tuple(fields.values()))
            rep_uuid=str(uuid5(NAMESPACE_URL,f"koa-encyk-representation:{snapshot_uuid}:{role}:{sha}"))
            connection.execute("""INSERT INTO source_representations
            (representation_uuid,snapshot_uuid,version_uuid,representation_kind,original_relative_path,declared_sha256,declared_size_bytes,declared_mime_type)
            VALUES(?,?,?,?,?,?,?,?)""",(rep_uuid,snapshot_uuid,version_uuid,role,entry["path"],sha,entry["bytes"],
            mimetypes.guess_type(entry["path"])[0] or 'application/octet-stream'))
            connection.execute("""INSERT INTO source_import_log
            (import_uuid,consumer_system,consumer_instance,external_source_id,snapshot_id,representation_kind,source_path,version_uuid,result)
            VALUES(?,'encyk',?,?,?,?,?,?,?)""",(import_id,payload["scope_key"],descriptor["external_source_id"],
            snap_key,role,entry["path"],version_uuid,'accepted'))
            receipt_reps.append({"role":role,"path":entry["path"],"bytes":entry["bytes"],
                  "sha256":sha,"version_uuid":version_uuid,"locator":"koa-media://version/"+version_uuid})
        receipt={"format":RECEIPT_FORMAT,"status":"accepted","handoff_id":import_id,
                 "contract":CONTRACT,"payload_sha256":"sha256:"+plan["payload_sha256"],
                 "source_uuid":source_uuid,"snapshot_uuid":snapshot_uuid,
                 "snapshot_id":snap_key,"scope_key":payload["scope_key"],"representations":receipt_reps,
                 "visibility":"private","semantic_identity_assigned":False}
        connection.execute("""INSERT INTO encyk_handoff_receipts
           (handoff_id,payload_sha256,source_uuid,snapshot_uuid,receipt_json) VALUES(?,?,?,?,?)""",
            (import_id,plan["payload_sha256"],source_uuid,snapshot_uuid,json.dumps(receipt,ensure_ascii=False)))
        connection.commit()
        return receipt
    except Exception:
        connection.rollback()
        for path in copied:
            path.unlink(missing_ok=True)
        raise
