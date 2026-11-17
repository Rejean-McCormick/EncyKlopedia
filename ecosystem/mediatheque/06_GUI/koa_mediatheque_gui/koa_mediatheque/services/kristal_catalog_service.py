\
"""Private local catalog of Kristal corpora.

This module catalogs Kristal repositories that exist on the local machine. It
never publishes them to UCKK, never copies the repository into this codebase,
and never turns UCKK into a canonical authority. The local Médiathèque application
stores only local catalog metadata and hashes in SQLite.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from importlib import resources
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from koa_mediatheque.models import KoaMessage, OperationResult
from koa_mediatheque.schema import utc_now_iso
from koa_mediatheque.services.file_facts import get_file_facts

_EXCLUDED_DIR_NAMES = {".git", ".hg", ".svn", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__", "node_modules", "dist", "build", ".venv"}
_EXCLUDED_FILE_SUFFIXES = {".pyc", ".pyo", ".tmp", ".swp"}

class KristalCatalogError(ValueError):
    pass


def ensure_kristal_catalog_schema(connection: sqlite3.Connection) -> None:
    sql = resources.files("koa_mediatheque").joinpath("sql/006_kristal_catalog.sql").read_text(encoding="utf-8")
    connection.executescript(sql)
    connection.execute(
        """INSERT INTO schema_meta(key, value, updated_at) VALUES ('kristal_catalog_profile', ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
        ("koa.kristal-local-catalog/1.0.0", utc_now_iso()),
    )
    connection.commit()


def discover_kristal_corpora(root: str | Path) -> list[dict[str, Any]]:
    base = Path(root).expanduser().resolve()
    if not base.exists():
        return []
    candidates: list[Path] = []
    if base.is_dir() and _looks_like_kristal(base):
        candidates.append(base)
    elif base.is_dir():
        candidates.extend(p for p in sorted(base.iterdir()) if p.is_dir() and _looks_like_kristal(p))
    return [inspect_kristal_corpus(path, calculate_hash=False) for path in candidates]


def inspect_kristal_corpus(kristal_root: str | Path, *, calculate_hash: bool = True) -> dict[str, Any]:
    root = Path(kristal_root).expanduser().resolve()
    if not root.is_dir():
        raise KristalCatalogError(f"Kristal root is not a directory: {root}")
    store_path = root / "external-source-library" / "source-store.json"
    store: dict[str, Any] = {}
    if store_path.is_file():
        store = _read_json_object(store_path)
    meta = store.get("kristal") if isinstance(store.get("kristal"), dict) else {}
    entries = store.get("entries") if isinstance(store.get("entries"), dict) else {}
    manifest = _choose_manifest(root)
    title = _read_title(root / "README.md") or root.name
    result: dict[str, Any] = {
        "kristal_id": root.name,
        "root": str(root),
        "title": title,
        "state_id": _as_text(meta.get("state_id")),
        "artifact_type": _as_text(meta.get("artifact_type")) or "knowledge_artifact",
        "artifact_status": _as_text(meta.get("artifact_status")) or "working",
        "source_store_path": str(store_path) if store_path.is_file() else None,
        "source_count": len(entries),
        "manifest_path": str(manifest) if manifest else None,
    }
    if calculate_hash:
        result.update(calculate_kristal_corpus_hash(root))
    return result


def calculate_kristal_corpus_hash(kristal_root: str | Path) -> dict[str, Any]:
    root = Path(kristal_root).expanduser().resolve()
    files = list(_iter_corpus_files(root))
    aggregate = hashlib.sha256()
    total_bytes = 0
    for path in files:
        rel = path.relative_to(root).as_posix()
        facts = get_file_facts(path)
        sha = str(facts.sha256 or "").lower()
        size = int(facts.filesize or 0)
        aggregate.update(rel.encode("utf-8")); aggregate.update(b"\0")
        aggregate.update(sha.encode("ascii")); aggregate.update(b"\0")
        aggregate.update(str(size).encode("ascii")); aggregate.update(b"\n")
        total_bytes += size
    return {"corpus_hash": aggregate.hexdigest(), "corpus_hash_algorithm": "sha256", "corpus_file_count": len(files), "corpus_bytes": total_bytes}


def register_kristal_corpus(connection: sqlite3.Connection, kristal_root: str | Path, *, domain: str | None = None, actor: str = "local_private") -> OperationResult:
    ensure_kristal_catalog_schema(connection)
    try:
        info = inspect_kristal_corpus(kristal_root, calculate_hash=True)
    except (OSError, KristalCatalogError, json.JSONDecodeError) as exc:
        return _error("register_kristal_corpus", "invalid_kristal", str(exc))
    now = utc_now_iso(); kristal_id = str(info["kristal_id"]); corpus_hash = str(info["corpus_hash"])
    kristal_uuid = str(uuid5(NAMESPACE_URL, f"koa-kristal:{kristal_id}"))
    version_uuid = str(uuid5(NAMESPACE_URL, f"koa-kristal-version:{kristal_id}:{corpus_hash}"))
    store_path = Path(info["source_store_path"]) if info.get("source_store_path") else None
    connection.execute(
        """INSERT INTO kristal_registry(kristal_id,kristal_root,source_library_path,source_store_format,source_store_version,state_id,artifact_type,artifact_status,last_seen_at,metadata_json)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(kristal_id) DO UPDATE SET kristal_root=excluded.kristal_root,source_library_path=excluded.source_library_path,state_id=COALESCE(excluded.state_id,kristal_registry.state_id),artifact_type=excluded.artifact_type,artifact_status=excluded.artifact_status,last_seen_at=excluded.last_seen_at,metadata_json=excluded.metadata_json""",
        (kristal_id, info["root"], str(store_path.parent) if store_path else None, None, None, info.get("state_id"), info.get("artifact_type"), info.get("artifact_status"), now, json.dumps({"catalog":"local_private"})),
    )
    connection.execute(
        """INSERT INTO kristal_artifacts(kristal_uuid,kristal_id,title,domain,corpus_kind,canonical_root_path,canonical_locator,lifecycle_status,metadata_json,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(kristal_id) DO UPDATE SET title=excluded.title,domain=COALESCE(excluded.domain,kristal_artifacts.domain),corpus_kind=excluded.corpus_kind,canonical_root_path=excluded.canonical_root_path,canonical_locator=excluded.canonical_locator,lifecycle_status=excluded.lifecycle_status,metadata_json=excluded.metadata_json,updated_at=excluded.updated_at""",
        (kristal_uuid,kristal_id,info["title"],domain,info.get("artifact_type") or "knowledge_artifact",info["root"],f"koa-kristal://artifact/{kristal_uuid}",info.get("artifact_status") or "working",json.dumps({"private":True},ensure_ascii=False),now,now),
    )
    connection.execute(
        """INSERT INTO kristal_versions(kristal_version_uuid,kristal_uuid,version_label,state_id,corpus_hash_algorithm,corpus_hash,manifest_path,status,source_count,corpus_file_count,corpus_bytes,metadata_json,observed_at,created_at,updated_at)
        VALUES (?,?,?,?, 'sha256', ?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(kristal_uuid,corpus_hash) DO UPDATE SET state_id=COALESCE(excluded.state_id,kristal_versions.state_id),manifest_path=COALESCE(excluded.manifest_path,kristal_versions.manifest_path),status=excluded.status,source_count=excluded.source_count,corpus_file_count=excluded.corpus_file_count,corpus_bytes=excluded.corpus_bytes,metadata_json=excluded.metadata_json,observed_at=excluded.observed_at,updated_at=excluded.updated_at""",
        (version_uuid,kristal_uuid,_version_label(info.get("state_id"),corpus_hash),info.get("state_id"),corpus_hash,info.get("manifest_path"),info.get("artifact_status") or "working",int(info.get("source_count") or 0),int(info.get("corpus_file_count") or 0),int(info.get("corpus_bytes") or 0),json.dumps({"actor":actor,"private":True},ensure_ascii=False),now,now,now),
    )
    connection.commit()
    return OperationResult(success=True, operation="register_kristal_corpus", result="registered", entity_type="kristal_version", entity_uuid=version_uuid, data={**info,"kristal_uuid":kristal_uuid,"kristal_version_uuid":version_uuid})


def register_all_kristal_corpora(connection: sqlite3.Connection, root: str | Path) -> OperationResult:
    found = discover_kristal_corpora(root); rows=[]; errors=[]
    for item in found:
        result=register_kristal_corpus(connection,item["root"]); rows.append({"kristal_id":item["kristal_id"],"success":result.success,**result.data}); errors.extend(result.errors)
    return OperationResult(success=not errors,operation="register_all_kristal_corpora",result="registered" if not errors else "partial",entity_type="kristal_catalog",data={"count":len(rows),"results":rows},errors=errors)


def list_kristal_artifacts(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    ensure_kristal_catalog_schema(connection)
    rows=connection.execute("""SELECT a.*, COUNT(v.kristal_version_uuid) AS version_count, MAX(v.observed_at) AS last_observed_at FROM kristal_artifacts a LEFT JOIN kristal_versions v ON v.kristal_uuid=a.kristal_uuid GROUP BY a.kristal_uuid ORDER BY a.kristal_id""").fetchall()
    return [dict(r) for r in rows]


def list_kristal_versions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    ensure_kristal_catalog_schema(connection)
    rows=connection.execute("""SELECT a.kristal_id, v.* FROM kristal_versions v JOIN kristal_artifacts a ON a.kristal_uuid=v.kristal_uuid ORDER BY a.kristal_id, v.observed_at DESC""").fetchall()
    return [dict(r) for r in rows]


def get_kristal_catalog_stats(connection: sqlite3.Connection) -> dict[str, int]:
    ensure_kristal_catalog_schema(connection)
    return {"kristals": int(connection.execute("SELECT COUNT(*) FROM kristal_artifacts").fetchone()[0]), "versions": int(connection.execute("SELECT COUNT(*) FROM kristal_versions").fetchone()[0])}


def _looks_like_kristal(path: Path) -> bool:
    return path.name.lower().startswith("kristal-") or (path / "external-source-library" / "source-store.json").is_file() or (path / "kristal_state").exists()


def _iter_corpus_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel=path.relative_to(root)
        if any(part in _EXCLUDED_DIR_NAMES for part in rel.parts):
            continue
        if len(rel.parts)>=2 and rel.parts[0]=="external-source-library" and rel.parts[1]=="snapshots":
            continue
        if path.suffix.lower() in _EXCLUDED_FILE_SUFFIXES:
            continue
        yield path


def _choose_manifest(root: Path) -> Path | None:
    for name in ("manifest.json", "MANIFEST.json", "kristal-manifest.json", "state.json"):
        p=root/name
        if p.is_file(): return p
    candidates=sorted(root.glob("*manifest*.json"))
    return candidates[0] if candidates else None


def _read_title(path: Path) -> str | None:
    if not path.is_file(): return None
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
        text=line.strip()
        if text.startswith("# "): return text[2:].strip()
    return None


def _version_label(state_id: Any, corpus_hash: str) -> str:
    return str(state_id).strip() if state_id else corpus_hash[:12]


def _read_json_object(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise KristalCatalogError(f"Expected JSON object: {path}")
    return value


def _as_text(value: Any) -> str | None:
    if value is None: return None
    text=str(value).strip(); return text or None


def _error(operation: str, result: str, message: str) -> OperationResult:
    return OperationResult(success=False,operation=operation,result=result,errors=[KoaMessage(code="ERR_KRISTAL_CATALOG",severity="error",message=message)])
