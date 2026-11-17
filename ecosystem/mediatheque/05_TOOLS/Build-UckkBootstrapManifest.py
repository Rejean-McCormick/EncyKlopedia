#!/usr/bin/env python3
"""Build and validate a deployable UCKK Médiathèque bootstrap manifest.

The bootstrap contains three independent inputs:
- the UCKK Kristal hierarchy (1 university, 10 voies, 100 courses);
- the Korpus media inventory;
- a snapshot-grounded catalog of public GitHub repository references.

The generated manifest never conflates semantic Kristal identity with
Médiathèque media/version identity. Stable UUID5 values are only catalog/import
identifiers; ``kristal_ref`` remains the semantic identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

FORMAT = "koa.mediatheque.uckk-bootstrap/1.1.0"
PORTABLE_CONTRACT = "kristal_state/6.0"
KRISTALL_BASELINE = "7.0.0-draft.3.2"
LIBRARY_SLUG = "uckk"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_uuid(label: str) -> str:
    return str(uuid5(NAMESPACE_URL, label))


def build_kristals(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Missing Kristal hierarchy manifest: {manifest_path}")
    hierarchy = load_json(manifest_path)
    entries = hierarchy.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Kristal hierarchy manifest entries must be a list")

    refs = {str(e.get("kristal_ref")) for e in entries}
    if len(refs) != len(entries):
        raise ValueError("Duplicate kristal_ref in hierarchy manifest")

    result: list[dict[str, Any]] = []
    kind_counts: dict[str, int] = {}
    for entry in entries:
        ref = str(entry.get("kristal_ref") or "").strip()
        kind = str(entry.get("kind") or "").strip()
        title = str(entry.get("title") or "").strip()
        parent = entry.get("parent_kristal_ref")
        if not ref or not kind or not title:
            raise ValueError(f"Malformed hierarchy entry: {entry}")
        if parent is not None and parent not in refs:
            raise ValueError(f"Unresolved parent {parent} for {ref}")

        rel = str(entry.get("path") or "")
        marker = "local/uckk/atlas/kristals/"
        if marker in rel:
            rel = rel.split(marker, 1)[1]
        stub_path = root / rel
        if not stub_path.is_file():
            raise ValueError(f"Missing Kristal stub for {ref}: {stub_path}")
        stub = load_json(stub_path)
        if stub.get("kristal_id") != ref or stub.get("kind") != kind:
            raise ValueError(f"Stub identity mismatch for {ref}")
        target = stub.get("target") or {}
        if target.get("portable_contract") != PORTABLE_CONTRACT:
            raise ValueError(f"Unexpected portable contract for {ref}")
        if target.get("kristall_baseline") != KRISTALL_BASELINE:
            raise ValueError(f"Unexpected Kristall baseline for {ref}")

        digest = sha256_file(stub_path)
        course = stub.get("course") if isinstance(stub.get("course"), dict) else {}
        voie = stub.get("voie") if isinstance(stub.get("voie"), dict) else {}
        sortorder = int(entry.get("order") or voie.get("order") or course.get("order") or 0)
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        result.append({
            "kristal_ref": ref,
            "catalog_uuid": stable_uuid(f"koa:uckk:kristal-artifact:{ref}"),
            "media_uuid": stable_uuid(f"koa:uckk:kristal-media:{ref}"),
            "kind": kind,
            "parent_kristal_ref": parent,
            "title": title,
            "voie_code": str(entry.get("code") or course.get("voie_code") or voie.get("code") or "") or None,
            "course_code": str(entry.get("course_id") or course.get("course_id") or "") or None,
            "sortorder": sortorder,
            "status": str(stub.get("status") or "stub"),
            "portable_contract": PORTABLE_CONTRACT,
            "kristall_baseline": KRISTALL_BASELINE,
            "source_relative_path": rel.replace("\\", "/"),
            "sha256": digest,
            "bytes": stub_path.stat().st_size,
            "mimetype": "application/json",
        })

    declared = hierarchy.get("counts") or {}
    actual = {
        "university": kind_counts.get("university", 0),
        "voie": kind_counts.get("voie", 0),
        "course": kind_counts.get("course", 0),
        "total": len(result),
    }
    expected = {
        "university": int(declared.get("university_kristals", 0)),
        "voie": int(declared.get("voie_kristals", 0)),
        "course": int(declared.get("course_kristals", 0)),
        "total": int(declared.get("total_kristals", 0)),
    }
    if actual != expected:
        raise ValueError(f"Hierarchy count mismatch: expected {expected}, got {actual}")
    if actual != {"university": 1, "voie": 10, "course": 100, "total": 111}:
        raise ValueError(f"UCKK hierarchy invariant failed: {actual}")
    return result, hierarchy


def build_korpus(inventory_path: Path, korpus_root: Path | None) -> list[dict[str, Any]]:
    inventory = load_json(inventory_path)
    files = inventory.get("files")
    if not isinstance(files, list):
        raise ValueError("Korpus inventory files must be a list")
    if len(files) != 64:
        raise ValueError(f"Expected 64 Korpus files, got {len(files)}")

    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in files:
        ops = item.get("file_operations") or {}
        media = item.get("uckkarchive_media") or {}
        source = item.get("uckkarchive_media_source") or {}
        proposed = str(ops.get("proposed_filename") or "").strip()
        if not proposed or proposed in seen:
            raise ValueError(f"Missing/duplicate proposed_filename: {proposed!r}")
        seen.add(proposed)

        path = korpus_root / "Sorted" / proposed if korpus_root else None
        digest = None
        size = None
        if path is not None:
            if not path.is_file():
                raise ValueError(f"Missing Korpus file: {path}")
            digest = sha256_file(path)
            size = path.stat().st_size
        mimetype = str(ops.get("mimetype") or mimetypes.guess_type(proposed)[0] or "application/octet-stream")
        result.append({
            "inventory_key": proposed,
            "media_uuid": stable_uuid(f"koa:uckk:korpus:{proposed}"),
            "title": str(media.get("title") or proposed),
            "description": str(media.get("description") or ""),
            "filename": proposed,
            "original_filename": str(ops.get("original_filename") or proposed),
            "mimetype": mimetype,
            "mediatype": str(media.get("mediatype") or "document"),
            "status": str(media.get("status") or "active"),
            "visibility": str(media.get("visibility") or "institution"),
            "audiencesuitability": str(media.get("audiencesuitability") or "general"),
            "language": str(media.get("language") or ""),
            "retentionclass": str(media.get("retentionclass") or ""),
            "redactionstate": str(media.get("redactionstate") or ""),
            "source": source,
            "tags": item.get("uckkarchive_media_tags") or [],
            "content_advisories": item.get("uckkarchive_content_advisories") or [],
            "relations": item.get("uckkarchive_relations") or [],
            "sha256": digest,
            "bytes": size,
            "source_relative_path": f"Sorted/{proposed}",
        })
    return result



def build_repositories(catalog_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    catalog = load_json(catalog_path)
    if catalog.get("format") != "koa.mediatheque.github-repository-catalog/1.0.0":
        raise ValueError(f"Unsupported repository catalog: {catalog_path}")
    repositories = catalog.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("Repository catalog must contain repositories")
    seen_urls: set[str] = set()
    seen_uuids: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in repositories:
        url = str(item.get("github_url") or "").strip()
        name = str(item.get("repository_name") or "").strip()
        if not name or not url.startswith("https://github.com/"):
            raise ValueError(f"Malformed GitHub repository entry: {item}")
        if url in seen_urls:
            raise ValueError(f"Duplicate GitHub URL: {url}")
        seen_urls.add(url)
        media_uuid = str(item.get("media_uuid") or stable_uuid(f"uckk-github-media:{url}"))
        source_uuid = str(item.get("source_uuid") or stable_uuid(f"uckk-github-source:{url}"))
        if media_uuid in seen_uuids:
            raise ValueError(f"Duplicate repository media UUID: {media_uuid}")
        seen_uuids.add(media_uuid)
        result.append({
            "repository_name": name,
            "github_url": url,
            "github_slug": str(item.get("github_slug") or url.split("github.com/", 1)[1]),
            "media_uuid": media_uuid,
            "source_uuid": source_uuid,
            "boundary": str(item.get("boundary") or ""),
            "role": str(item.get("role") or ""),
            "local_observation": str(item.get("local_observation") or ""),
            "source_registry_id": item.get("source_registry_id"),
            "pinned_commit": item.get("pinned_commit"),
            "pinned_commit_url": item.get("pinned_commit_url"),
            "observed_at": item.get("observed_at"),
            "authority_note": item.get("authority_note"),
            "sortorder": int(item.get("sortorder") or len(result) + 1),
            "tags": list(item.get("tags") or ["github", "repository"]),
        })
    return result, catalog

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kristal-root", required=True, type=Path)
    parser.add_argument("--korpus-inventory", required=True, type=Path)
    parser.add_argument("--korpus-root", type=Path)
    parser.add_argument("--repository-catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    kristals, hierarchy = build_kristals(args.kristal_root)
    korpus = build_korpus(args.korpus_inventory, args.korpus_root)
    repositories, repository_catalog = build_repositories(args.repository_catalog)
    payload = {
        "format": FORMAT,
        "library": {
            "slug": LIBRARY_SLUG,
            "name": "Médiathèque UCKK",
            "backend": "moodle",
        },
        "identity_rule": {
            "kristal_ref": "semantic identity owned by Kristal/Kristall",
            "catalog_uuid": "Médiathèque catalog identity",
            "media_uuid": "Médiathèque stored-artifact identity",
            "version_uuid": "created by the backend per immutable stored version",
            "must_not_equal": ["kristal_ref", "catalog_uuid", "media_uuid", "version_uuid"],
        },
        "kristal_contract": {
            "portable_contract": PORTABLE_CONTRACT,
            "kristall_baseline": KRISTALL_BASELINE,
            "hierarchy_format": hierarchy.get("format"),
            "root_kristal_ref": hierarchy.get("root_kristal_ref"),
        },
        "ecosystem_repository_catalog": {
            "relative_path": "repositories/github-repositories.json",
            "format": repository_catalog.get("format"),
            "source_package": "Kristal-kOA-Ecosystem-v0.6.3",
            "source_package_sha256": (repository_catalog.get("generated_from") or {}).get("snapshot_zip_sha256"),
            "public_repositories": len(repositories),
            "commit_pinned_repositories": sum(bool(r.get("pinned_commit")) for r in repositories),
        },
        "counts": {
            "kristal_artifacts": len(kristals),
            "korpus_media": len(korpus),
            "github_repositories": len(repositories),
            "total_bootstrap_objects": len(kristals) + len(korpus) + len(repositories),
        },
        "kristals": kristals,
        "korpus": korpus,
        "repositories": repositories,
        "import_order": ["kristals", "korpus", "repositories"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
