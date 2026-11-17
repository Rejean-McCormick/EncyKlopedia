\
"""Adjacent local content support for the single Médiathèque application."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from koa_mediatheque.repositories.library_rows_repository import get_library_row_by_version_uuid, get_library_rows_by_sha256, insert_library_row
from koa_mediatheque.services.file_facts import get_file_facts
from koa_mediatheque.services.kristal_catalog_service import discover_kristal_corpora, register_kristal_corpus

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

_DEFAULT_EXCLUDED_DIRS={".git",".hg",".svn",".venv","venv","node_modules","__pycache__",".pytest_cache","dist","build"}
_DEFAULT_EXCLUDED_SUFFIXES={".tmp",".bak",".part",".crdownload",".pyc",".pyo"}

@dataclass(frozen=True)
class LocalWorkspaceConfig:
    config_path: Path
    mode: str
    kristal_roots: tuple[Path, ...]
    document_roots: tuple[Path, ...]
    recursive_documents: bool = True
    document_mode: str = "reference_only"


def load_local_workspace_config(config_path: str | Path) -> LocalWorkspaceConfig:
    if tomllib is None: raise RuntimeError("Python 3.11+ is required for TOML workspace configuration")
    path=Path(config_path).expanduser().resolve()
    data=tomllib.loads(path.read_text(encoding="utf-8"))
    section=data.get("workspace") or {}
    mode=str(section.get("mode") or "local_private")
    if mode != "local_private": raise ValueError("workspace.mode must be 'local_private' for this distribution")
    base=path.parent
    return LocalWorkspaceConfig(
        config_path=path,
        mode=mode,
        kristal_roots=tuple(_resolve(base,v) for v in section.get("kristal_roots",[])),
        document_roots=tuple(_resolve(base,v) for v in section.get("document_roots",[])),
        recursive_documents=bool(section.get("recursive_documents",True)),
        document_mode=str(section.get("document_mode") or "reference_only"),
    )


def plan_local_workspace(config: LocalWorkspaceConfig) -> dict[str, Any]:
    kristals=[]
    for root in config.kristal_roots:
        kristals.extend(discover_kristal_corpora(root))
    docs=discover_document_files(config.document_roots, recursive=config.recursive_documents)
    return {"mode":config.mode,"config_path":str(config.config_path),"kristal_roots":[str(p) for p in config.kristal_roots],"document_roots":[str(p) for p in config.document_roots],"kristals":kristals,"kristal_count":len(kristals),"document_count":len(docs),"documents":[str(p) for p in docs]}


def discover_document_files(roots: tuple[Path, ...] | list[Path], *, recursive: bool=True) -> list[Path]:
    found=[]
    for root in roots:
        base=Path(root).expanduser().resolve()
        if not base.is_dir(): continue
        iterator=base.rglob("*") if recursive else base.iterdir()
        for path in iterator:
            if not path.is_file(): continue
            rel=path.relative_to(base)
            if any(part in _DEFAULT_EXCLUDED_DIRS for part in rel.parts): continue
            if path.suffix.lower() in _DEFAULT_EXCLUDED_SUFFIXES: continue
            found.append(path.resolve())
    return sorted(set(found))


def apply_local_workspace(connection: sqlite3.Connection, config: LocalWorkspaceConfig) -> dict[str, Any]:
    plan=plan_local_workspace(config)
    kristal_results=[]
    for item in plan["kristals"]:
        result=register_kristal_corpus(connection,item["root"])
        kristal_results.append({"kristal_id":item["kristal_id"],"success":result.success,"result":result.result})
    doc_result=index_private_documents(connection,[Path(p) for p in plan["documents"]])
    return {"mode":config.mode,"kristals":kristal_results,"documents":doc_result}


def index_private_documents(connection: sqlite3.Connection, files: list[Path]) -> dict[str, int]:
    counters={"seen":0,"inserted":0,"existing":0,"deduplicated":0,"errors":0}
    for file_path in files:
        counters["seen"]+=1
        try:
            facts=get_file_facts(file_path)
            sha=str(facts.sha256 or "")
            resolved=str(file_path.resolve())
            media_uuid=str(uuid5(NAMESPACE_URL,f"koa-private-document:{resolved}"))
            version_uuid=str(uuid5(NAMESPACE_URL,f"koa-private-document-version:{resolved}:{sha}"))
            if get_library_row_by_version_uuid(connection,version_uuid): counters["existing"]+=1; continue
            if sha and get_library_rows_by_sha256(connection,sha): counters["deduplicated"]+=1; continue
            result=insert_library_row(connection,{
                "media_uuid":media_uuid,"version_uuid":version_uuid,"title":file_path.stem,"original_path":resolved,"storage_path":None,
                "filename":facts.filename,"extension":facts.extension,"mimetype":facts.mimetype,"filesize":facts.filesize,"sha256":facts.sha256,
                "filearea":"media_original","media_type":_media_type(facts.mimetype,facts.extension),"language":"und","library_scope":"koa","uckk_relevance":"unknown",
                "target_system":"none","target_export_allowed":0,"public_state":"private","visibility":"private","access_level":"private","ownership_scope":"personal",
                "source_type":"imported","source_ownership":"unknown_source","rights_status":"unknown","restriction_state":"privacy","redaction_required":0,"status":"active",
                "provenance":"imported","ai_validation_state":"ai_uncertain","canonical_validation_state":"unverified","human_review_required":0,
                "collections_json":"[]","tags_json":"[]","relations_json":"[]","content_flags_json":"[\"non_public\"]","audience_suitability":"restricted",
                "export_to_uckk":"no","export_to_public":"no","export_policy_note":"Private local workspace: export disabled by default.","import_batch":"local_private_workspace",
                "notes":"Indexed by reference; file bytes remain at the original private path.",
            })
            if result.success: counters["inserted"]+=1
            else: counters["errors"]+=1
        except (OSError,ValueError): counters["errors"]+=1
    return counters


def _media_type(mimetype: str | None, extension: str | None) -> str:
    mime=(mimetype or "").lower(); ext=(extension or "").lower()
    if mime=="application/pdf" or ext==".pdf": return "pdf"
    if mime.startswith("image/"): return "image"
    if mime.startswith("audio/"): return "audio"
    if mime.startswith("video/"): return "video"
    if "spreadsheet" in mime or ext in {".xlsx",".xls",".ods",".csv"}: return "spreadsheet"
    if "presentation" in mime or ext in {".ppt",".pptx",".odp"}: return "presentation"
    return "document"


def _resolve(base: Path, value: Any) -> Path:
    path=Path(str(value)).expanduser()
    return (base/path).resolve() if not path.is_absolute() else path.resolve()
