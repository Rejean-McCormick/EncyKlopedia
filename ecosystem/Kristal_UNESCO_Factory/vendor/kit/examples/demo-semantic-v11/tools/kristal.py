#!/usr/bin/env python3
"""Kristal Local workspace utilities aligned with Kristal v11 opt-in.

The Local Kit preserves Kristal v9 semantic-state commitments while adding
explicit v10 hosted-network integration. GitHub/repository metadata is operational
and never enters logical commitments. The tool uses only Python's standard library.
"""
from __future__ import annotations

import argparse
import base64
from decimal import Decimal
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

KIT_VERSION = "4.0.0-draft.3"
FORMAT = "kristal.local-workspace/3.2.0"
V31_FORMAT = "kristal.authoring-workspace/3.1.0"
V3_FORMAT = "kristal.authoring-workspace/3.0.0"
V2_FORMAT = "kristal.authoring-workspace/2.0.0"
LEGACY_FORMAT = "kristal.authoring-workspace/1.0.0"
STATE_INDEX_FORMAT = "kristal.authoring-state-index/2.0.0"
SOURCE_CATALOG_FORMAT = "kristal.source-catalog/2.0.0"
PROJECTION_FORMAT = "kristal.projection-recipe/2.0.0"
HASH_MANIFEST_FORMAT = "kristal.local-hash-manifest/3.2.0"
PORTABLE_AI_FORMAT = "kristal.portable-ai/1.0"
AI_INDEX_FORMAT = "kristal.ai-index/1.0"
AI_COVERAGE_FORMAT = "kristal.ai-coverage/1.0"
GITHUB_HOSTING_FORMAT = "kristal.authoring-host/github/1.0"
LOCAL_INSPECTION_FORMAT = "kristal.local-inspection/1.0"
GITHUB_READ_SURFACE_FORMAT = "kristal.github-read-surface/1.0"
DISCOVERY_FORMAT = "kristal.discovery/1.0"
INVENTORY_FORMAT = "kristal.reader-inventory/1.0"
READER_FORMAT = "kristal.reader-profile/1.0"
HOSTED_NETWORK_BASELINE = "kristal.hosting/10.0"
GITHUB_HOST_PROFILE = "kristal.host/github/1.0"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPO_SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
LOGICAL_PROFILE = "kristal.logical/jcs-sha256-v1"
STATE_PROFILE = "kristal.state-commitment/jcs-sha256-v1"
STATUSES = {"stub", "design", "building", "validated", "released", "superseded"}
PROFILES = {"open", "invariant", "procedural", "research", "hierarchy-stub", "executable", "layered"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SHA256_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
MATERIALIZATION_MANIFEST_TYPE = "kristal_materialization_manifest"
V9_CAPABILITIES_TYPE = "kristal_v9_capabilities"
REFERENCE_MATERIALIZATION_PROFILES = {
    "kristal.materialization/inline-json/1",
    "kristal.materialization/native-blob/1",
    "kristal.materialization/segmented-jsonl/1",
    "kristal.materialization/kristal-state-v6/1",
}

DOC_TEMPLATES = {'00_INTENT_AND_SCOPE.md': '# Intent and scope\n'
                           '\n'
                           '## Why this Kristal exists\n'
                           '\n'
                           'TODO\n'
                           '\n'
                           '## Starting corpus and problem\n'
                           '\n'
                           'TODO\n'
                           '\n'
                           '## Expected outcomes\n'
                           '\n'
                           'TODO\n',
 '01_SEMANTIC_BOUNDARY.md': '# Semantic boundary\n'
                            '\n'
                            '## Subject and territory\n'
                            '\n'
                            'TODO\n'
                            '\n'
                            '## Owned knowledge\n'
                            '\n'
                            'TODO\n'
                            '\n'
                            '## Excluded knowledge\n'
                            '\n'
                            'TODO\n'
                            '\n'
                            '## Relationships to other Kristals\n'
                            '\n'
                            'TODO\n'
                            '\n'
                            '## V9 state identity\n'
                            '\n'
                            'The `state_ref` is declared in `kristal.workspace.json`. Pin '
                            'external semantic references to exact Logical Commitments before '
                            'relying on them for a qualified publication.\n',
 '02_NATIVE_MODEL.md': '# Native model\n'
                       '\n'
                       '## Domain primitives\n'
                       '\n'
                       'TODO\n'
                       '\n'
                       '## Relations and transformations\n'
                       '\n'
                       'TODO\n'
                       '\n'
                       '## Internal dimensions\n'
                       '\n'
                       'TODO\n'
                       '\n'
                       '## Chosen native shape\n'
                       '\n'
                       '`undecided`\n'
                       '\n'
                       '## V9 Logical Contracts\n'
                       '\n'
                       'TODO — define the domain Logical Contracts for admitted artifacts '
                       'without forcing one universal topology.\n'
                       '\n'
                       '## Why the shape preserves the essential information\n'
                       '\n'
                       'TODO\n'
                       '\n'
                       '## Rejected alternatives\n'
                       '\n'
                       'TODO\n',
 '03_EPISTEMIC_MODEL.md': '# Epistemic model\n'
                          '\n'
                          '## Information regimes\n'
                          '\n'
                          'TODO\n'
                          '\n'
                          '## Source and evidence provenance\n'
                          '\n'
                          'TODO\n'
                          '\n'
                          '## Authority\n'
                          '\n'
                          'TODO\n'
                          '\n'
                          '## Uncertainty, conflicts and unknowns\n'
                          '\n'
                          'TODO\n'
                          '\n'
                          '## Build provenance\n'
                          '\n'
                          'TODO — separate computational derivation from epistemic '
                          'provenance.\n'
                          '\n'
                          '## AI output policy\n'
                          '\n'
                          'AI outputs remain proposals until explicitly validated and '
                          'admitted.\n',
 '04_CANONICAL_DERIVED.md': '# Canonical and derived content\n'
                            '\n'
                            '## Source(s) of truth\n'
                            '\n'
                            'TODO\n'
                            '\n'
                            '## Canonical Logical Artifacts\n'
                            '\n'
                            'TODO — register domain artifacts in `canon/state.index.json`.\n'
                            '\n'
                            '## Derived artifacts and runtime\n'
                            '\n'
                            'TODO\n'
                            '\n'
                            '## Materializations\n'
                            '\n'
                            'TODO — distinguish physical representation from semantic '
                            'identity.\n'
                            '\n'
                            '## Reconstructability recipes\n'
                            '\n'
                            'TODO\n',
 '05_ORIENTATIONS.md': '# Orientations and reader surfaces\n'
                       '\n'
                       '## Useful orientations\n'
                       '\n'
                       'TODO\n'
                       '\n'
                       '## Internal dimensions that are not orientation axes\n'
                       '\n'
                       'TODO\n'
                       '\n'
                       '## Projections to materialize\n'
                       '\n'
                       'TODO\n'
                       '\n'
                       'A v6/v7 interoperable projection remains a reader projection and does '
                       'not automatically replace the native v9 Logical Artifact.\n',
 '06_VALIDATION.md': '# Domain validation and v10 lifecycle\n'
                     '\n'
                     '## Structural invariants\n'
                     '\n'
                     'TODO\n'
                     '\n'
                     '## Epistemic invariants\n'
                     '\n'
                     'TODO\n'
                     '\n'
                     '## Reconstructability tests\n'
                     '\n'
                     'TODO\n'
                     '\n'
                     '## Logical Commitments\n'
                     '\n'
                     'TODO — identify domain-specific commitment profiles and golden fixtures '
                     'when necessary.\n'
                     '\n'
                     '## Publication criteria\n'
                     '\n'
                     'TODO\n'
                     '\n'
                     'Suggested local path: `check` → `build-v9`. Use Manager for inventory '
                     'and **authorized** read-surface synchronization. Use independent C1 '
                     'qualification, owner C2 authorization and C3/Bootstrap controls for '
                     'network publication.\n',
 '07_HOSTING_AND_PUBLICATION.md': '# V10 hosting and publication\n'
                                  '\n'
                                  'The canon and logical commitments remain v9. Hosting is a '
                                  'separate v10 operational layer.\n'
                                  '\n'
                                  '## Node and repository\n'
                                  '\n'
                                  'TODO — choose an authorized GitHub collection node. '
                                  'Several independently owned Kristals may share a '
                                  'repository only if permission boundaries are appropriate.\n'
                                  '\n'
                                  '## State path\n'
                                  '\n'
                                  'TODO — choose a stable repository-relative path, for '
                                  'example `kristals/<slug>/state/state-snapshot.json`.\n'
                                  '\n'
                                  '## Qualification\n'
                                  '\n'
                                  'Independently qualify the exact revision and state being '
                                  'considered for publication.\n'
                                  '\n'
                                  '## Disclosure and publication\n'
                                  '\n'
                                  'Public synchronization is disclosure before any immutable '
                                  'release; it requires a separate authorized scope. '
                                  'Publication produces a verifiable bundle and immutable '
                                  'release without changing the v9 Logical Commitment.\n'
                                  '\n'
                                  '## Activation\n'
                                  '\n'
                                  'Activation is optional and separate. Publishing a release '
                                  'does not automatically change the active channel.\n',
 '08_GLOSSARY.md': '# Kristal glossary\n'
                   '\n'
                   'Define only domain-specific terminology whose meaning should not be left '
                   'ambiguous.\n'
                   '\n'
                   '## Terms\n'
                   '\n'
                   'TODO — leave this section empty if no domain-specific glossary is '
                   'needed.\n'}

PROFILE_NOTES = {'open': 'No native shape is presumed. Apply the Shape Probes before introducing domain '
         'schemas.',
 'invariant': 'Potential starting point: invariant, equivalent representations, consequences, '
              'witnesses/certificates and operationalizations.',
 'procedural': 'Potential starting point: objects, states, operations, partial order, DAG or '
               'hypergraph. Do not force a DAG if cycles are meaningful.',
 'research': 'Separate established/imported research, attempts, append-only observations, '
             'provenance and explicitly promoted conclusions.',
 'hierarchy-stub': 'Allows identity, scope and topology without invented content. A parent '
                   'references children without copying their canon.',
 'executable': 'Separate rules/transitions, observables, perturbations and derived output. '
               'Simulation is not execution authorization.',
 'layered': 'Identify distinct layers and type the transitions between mechanics, structure, '
            'interpretation and evidence.'}

def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")


def slugify(value: str) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "kristal"


def kit_root() -> Path:
    return Path(__file__).resolve().parent.parent


def template_text(name: str) -> str:
    candidates = [kit_root() / "templates" / name, Path(__file__).resolve().parent / "_templates" / name]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Template not found: {name}; searched {candidates}")


def ensure_empty_or_new(path: Path, force: bool) -> None:
    if path.exists() and any(path.iterdir()) and not force:
        raise SystemExit(f"Refus: {path} existe et n'est pas vide. Utiliser --force seulement si voulu.")
    path.mkdir(parents=True, exist_ok=True)


def hash_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- Minimal RFC 8785 / JCS implementation for the v9 baseline ----------

def _jcs_key(s: str):
    return tuple(int.from_bytes(s.encode("utf-16-be")[i:i+2], "big") for i in range(0, len(s.encode("utf-16-be")), 2))


def _number_to_jcs(value):
    if isinstance(value, bool):
        raise TypeError("bool is not a number here")
    if isinstance(value, int):
        return str(value)
    if not isinstance(value, float) or not math.isfinite(value):
        raise ValueError("JCS permits only finite JSON numbers")
    if value == 0.0:
        return "0"
    s = repr(value).lower()
    if s.endswith(".0") and "e" not in s:
        s = s[:-2]
    abs_v = abs(value)
    if 1e-6 <= abs_v < 1e21:
        if "e" in s:
            d = Decimal(s)
            s = format(d, "f")
            if "." in s:
                s = s.rstrip("0").rstrip(".")
        return s
    if "e" not in s:
        # Values outside the fixed range are required in exponent notation.
        d = Decimal(s).normalize()
        s = format(d, "e")
    mantissa, exponent = s.split("e", 1)
    if mantissa.endswith(".0"):
        mantissa = mantissa[:-2]
    exp_i = int(exponent)
    sign = "+" if exp_i >= 0 else "-"
    return f"{mantissa}e{sign}{abs(exp_i)}"


def canonicalize(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number_to_jcs(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(canonicalize(v) for v in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise TypeError("JCS object keys must be strings")
        return "{" + ",".join(
            json.dumps(k, ensure_ascii=False, separators=(",", ":")) + ":" + canonicalize(value[k])
            for k in sorted(value, key=_jcs_key)
        ) + "}"
    raise TypeError(f"Unsupported JSON value for JCS: {type(value).__name__}")


def _sha256_commit(domain: str, projection) -> str:
    b = domain.encode("utf-8") + canonicalize(projection).encode("utf-8")
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _normalize_artifact_ref(ref: dict) -> dict:
    out = {
        "artifact_id": ref["artifact_id"],
        "logical_commitment": dict(ref["logical_commitment"]),
    }
    if ref.get("logical_contract"):
        out["logical_contract"] = dict(ref["logical_contract"])
    return out


def _utf8_key(value: str) -> bytes:
    return str(value).encode("utf-8")


def _sort_artifact_refs(refs) -> list[dict]:
    out = [_normalize_artifact_ref(r) for r in (refs or [])]
    out.sort(key=lambda r: _utf8_key(f"{r.get('artifact_id','')}\0{(r.get('logical_commitment') or {}).get('digest','')}"))
    return out


def logical_artifact_commitment(artifact: dict, profile: str = LOGICAL_PROFILE) -> dict:
    if profile != LOGICAL_PROFILE:
        raise ValueError(f"Unsupported baseline logical profile: {profile}")
    contract = artifact.get("logical_contract") or {}
    cid, version = contract.get("id"), contract.get("version")
    if not isinstance(cid, str) or not cid or not isinstance(version, str) or not version:
        raise ValueError("logical_contract.id/version required")
    projection = {"payload": artifact.get("payload")}
    if "scope" in artifact:
        projection["scope"] = artifact["scope"]
    if "extensions" in artifact:
        projection["extensions"] = artifact["extensions"]
    if artifact.get("dependencies"):
        projection["dependencies"] = _sort_artifact_refs(artifact["dependencies"])
    domain = f"KRISTAL\x00LOGICAL-COMMITMENT\x00{profile}\x00{cid}\x00{version}\x00"
    return {"profile": profile, "digest": _sha256_commit(domain, projection)}


def state_commitment(state: dict, profile: str = STATE_PROFILE) -> dict:
    if profile != STATE_PROFILE:
        raise ValueError(f"Unsupported baseline state profile: {profile}")
    refs = []
    for ref in state.get("references") or []:
        if "artifact_id" in ref:
            refs.append({"kind": "artifact", "value": _normalize_artifact_ref(ref)})
        elif "state_ref" in ref:
            value = {"state_ref": ref["state_ref"], "logical_commitment": dict(ref["logical_commitment"])}
            refs.append({"kind": "state", "value": value})
    refs.sort(key=lambda r: _utf8_key(canonicalize(r)))
    projection = {"members": _sort_artifact_refs(state.get("members") or []), "references": refs}
    if "scope" in state:
        projection["scope"] = state["scope"]
    domain = f"KRISTAL\x00STATE-COMMITMENT\x00{profile}\x00"
    return {"profile": profile, "digest": _sha256_commit(domain, projection)}


def _valid_commitment(obj) -> bool:
    return isinstance(obj, dict) and isinstance(obj.get("profile"), str) and bool(SHA256_ID.fullmatch(str(obj.get("digest", ""))))


def _safe_name(artifact_id: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", artifact_id).strip("-") or "artifact"
    suffix = hashlib.sha256(artifact_id.encode("utf-8")).hexdigest()[:10]
    return f"{base[:80]}-{suffix}"


def _safe_local_locator(root: Path, locator: str) -> Path | None:
    """Resolve a workspace-local materialization locator without allowing escape.

    V9 locators may also name remote/object-store locations. The Authoring Kit only
    verifies byte-level integrity when a locator is a safe relative path inside the
    current workspace. Other locators remain valid descriptors but are not fetched.
    """
    raw = str(locator or "").replace("\\", "/").strip()
    if not raw or "://" in raw or raw.startswith("urn:") or raw.startswith("/"):
        return None
    parts = [p for p in raw.split("/") if p not in {"", "."}]
    if not parts or any(p == ".." for p in parts):
        return None
    candidate = (root / Path(*parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _materialization_manifest_issues(doc: dict) -> list[str]:
    """Minimal stdlib verifier aligned with the Framework v9 manifest schema."""
    issues: list[str] = []
    if not isinstance(doc, dict):
        return ["manifest must be an object"]
    if doc.get("schema_version") != "9.0":
        issues.append("schema_version must be '9.0'")
    if doc.get("artifact_type") != MATERIALIZATION_MANIFEST_TYPE:
        issues.append(f"artifact_type must be {MATERIALIZATION_MANIFEST_TYPE!r}")
    source = doc.get("source")
    if not isinstance(source, dict):
        issues.append("source must be an object")
    else:
        if not isinstance(source.get("artifact_id"), str) or not source.get("artifact_id"):
            issues.append("source.artifact_id is required")
        contract = source.get("logical_contract")
        if not isinstance(contract, dict) or not contract.get("id") or not contract.get("version"):
            issues.append("source.logical_contract id/version are required")
        if not _valid_commitment(source.get("logical_commitment")):
            issues.append("source.logical_commitment is invalid")
    if not isinstance(doc.get("profile"), str) or not doc.get("profile"):
        issues.append("profile is required")
    segments = doc.get("segments")
    if not isinstance(segments, list) or not segments:
        issues.append("segments must contain at least one segment")
    else:
        seen_keys = set()
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                issues.append(f"segments[{i}] must be an object")
                continue
            key = segment.get("segment_key")
            if not isinstance(key, str) or not key:
                issues.append(f"segments[{i}].segment_key is required")
            elif key in seen_keys:
                issues.append(f"duplicate segment_key: {key}")
            else:
                seen_keys.add(key)
            blob = segment.get("blob")
            if not isinstance(blob, dict):
                issues.append(f"segments[{i}].blob must be an object")
                continue
            if not isinstance(blob.get("media_type"), str) or not blob.get("media_type"):
                issues.append(f"segments[{i}].blob.media_type is required")
            if not SHA256_ID.fullmatch(str(blob.get("digest", ""))):
                issues.append(f"segments[{i}].blob.digest must be sha256:<64hex>")
            if not isinstance(blob.get("size"), int) or blob.get("size", -1) < 0:
                issues.append(f"segments[{i}].blob.size must be a non-negative integer")
    dictionaries = doc.get("dictionaries", [])
    if dictionaries is not None and not isinstance(dictionaries, list):
        issues.append("dictionaries must be an array when present")
    elif isinstance(dictionaries, list):
        for i, blob in enumerate(dictionaries):
            if not isinstance(blob, dict):
                issues.append(f"dictionaries[{i}] must be an object")
                continue
            if not isinstance(blob.get("media_type"), str) or not blob.get("media_type"):
                issues.append(f"dictionaries[{i}].media_type is required")
            if not SHA256_ID.fullmatch(str(blob.get("digest", ""))):
                issues.append(f"dictionaries[{i}].digest must be sha256:<64hex>")
            if not isinstance(blob.get("size"), int) or blob.get("size", -1) < 0:
                issues.append(f"dictionaries[{i}].size must be a non-negative integer")
    reconstructability = doc.get("reconstructability")
    if not isinstance(reconstructability, dict) or reconstructability.get("lossless") is not True:
        issues.append("reconstructability.lossless must be true")
    return issues


def _materialization_search_roots(root: Path) -> list[Path]:
    return [
        root / "materializations" / "v9" / "manifests",
        root / ".kristal" / "v9" / "materializations",
    ]


def _discover_materialization_manifests(root: Path) -> list[tuple[Path, dict]]:
    """Discover authoring manifests plus the established legacy .kristal/v9 layout."""
    found: list[tuple[Path, dict]] = []
    seen = set()
    for base in _materialization_search_roots(root):
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.json"), key=lambda p: p.relative_to(root).as_posix().encode("utf-8")):
            rel = path.relative_to(root).as_posix()
            if rel in seen:
                continue
            try:
                doc = read_json(path)
            except Exception:
                # collect_json_errors already reports malformed JSON during check.
                continue
            if isinstance(doc, dict) and doc.get("artifact_type") == MATERIALIZATION_MANIFEST_TYPE:
                seen.add(rel)
                found.append((path, doc))
    return found


def _canonical_ref_map(root: Path, idx: dict) -> dict[str, dict]:
    refs = {}
    for entry in idx.get("canonical_artifacts", []):
        if not isinstance(entry, dict) or not entry.get("artifact_id"):
            continue
        ref, _ = _resolve_artifact_entry(root, entry)
        refs[ref["artifact_id"]] = ref
    return refs


def _materialization_capability_hints(root: Path) -> list[dict]:
    """Read existing v9 capability descriptors as non-authoritative authoring hints."""
    candidates = [
        root / "materializations" / "v9" / "capabilities.json",
        root / ".kristal" / "v9" / "capabilities.json",
    ]
    hints = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            obj = read_json(path)
        except Exception:
            continue
        if obj.get("schema_version") == "9.0" and obj.get("artifact_type") == V9_CAPABILITIES_TYPE:
            hints.append(obj)
    return hints


def _materialization_feature_flags(root: Path, manifests: list[dict]) -> tuple[bool, bool]:
    segmentation = any(len(m.get("segments") or []) > 1 for m in manifests)
    factorization = any(bool(m.get("dictionaries")) for m in manifests)
    for m in manifests:
        ext = m.get("extensions") or {}
        caps = ext.get("capabilities") if isinstance(ext, dict) else None
        if isinstance(caps, dict):
            segmentation = segmentation or caps.get("segmentation") is True
            factorization = factorization or caps.get("factorization") is True
    profiles = {m.get("profile") for m in manifests if m.get("profile")}
    for hint in _materialization_capability_hints(root):
        mat = ((hint.get("capabilities") or {}).get("materialization") or {})
        hinted_profiles = set(mat.get("profiles") or [])
        # Only inherit feature flags when the hint describes at least one profile
        # that is actually present in the current discovered manifests.
        if profiles & hinted_profiles:
            segmentation = segmentation or mat.get("segmentation") is True
            factorization = factorization or mat.get("factorization") is True
    return segmentation, factorization


def _verify_materializations(root: Path, idx: dict) -> tuple[list[tuple[Path, dict]], list[str], list[str]]:
    """Validate manifests, their logical binding, and any locally available blobs."""
    errors: list[str] = []
    warnings: list[str] = []
    manifests = _discover_materialization_manifests(root)
    refs = _canonical_ref_map(root, idx)
    seen_ids = set()
    for path, doc in manifests:
        rel = path.relative_to(root).as_posix()
        for issue in _materialization_manifest_issues(doc):
            errors.append(f"Materialization {rel}: {issue}")
        mid = doc.get("materialization_id")
        if mid:
            if mid in seen_ids:
                errors.append(f"Duplicate materialization_id: {mid}")
            seen_ids.add(mid)
        source = doc.get("source") or {}
        expected = refs.get(source.get("artifact_id"))
        if expected is None:
            errors.append(f"Materialization {rel} references non-canonical artifact: {source.get('artifact_id')}")
        else:
            if source.get("logical_contract") != expected.get("logical_contract"):
                errors.append(f"Materialization {rel} logical_contract does not match registered artifact {source.get('artifact_id')}")
            if source.get("logical_commitment") != expected.get("logical_commitment"):
                errors.append(f"Materialization {rel} logical_commitment does not match registered artifact {source.get('artifact_id')}")
        blobs = [s.get("blob") for s in doc.get("segments", []) if isinstance(s, dict)] + list(doc.get("dictionaries") or [])
        for i, blob in enumerate(blobs):
            if not isinstance(blob, dict) or not blob.get("locator"):
                continue
            local = _safe_local_locator(root, blob.get("locator"))
            if local is None:
                warnings.append(f"Materialization {rel} blob[{i}] locator is not workspace-local; bytes not verified: {blob.get('locator')}")
                continue
            if not local.is_file():
                warnings.append(f"Materialization {rel} blob[{i}] is not locally available: {blob.get('locator')}")
                continue
            actual_size = local.stat().st_size
            if actual_size != blob.get("size"):
                errors.append(f"Materialization {rel} blob[{i}] size mismatch: declared={blob.get('size')} actual={actual_size}")
            actual_digest = "sha256:" + hash_file(local)
            if actual_digest != blob.get("digest"):
                errors.append(f"Materialization {rel} blob[{i}] digest mismatch: declared={blob.get('digest')} actual={actual_digest}")
    return manifests, errors, warnings


# ---------- noncanonical reader discovery and classification ----------

READER_FAMILY = {
    "diagnosis": "causal-graph", "procedures": "conditional-process", "procedure": "conditional-process",
    "education": "educational-navigation", "learning": "educational-navigation",
    "research": "proof-navigation", "mathematics": "proof-navigation",
    "social": "relational-network", "collections": "comparative-collection",
    "collection": "comparative-collection", "records": "longitudinal-record",
    "tracking": "longitudinal-record", "orchestration": "federated-resolution",
    "reference": "indexed-reference",
}
# Fallback on exact Arketype usage IDs; unknown IDs remain valid without claiming
# a semantic match. Profile labels are advisory, never executable instructions.
READER_USAGE = {
    "PRF-06": "federated-resolution", "PRF-07": "educational-navigation",
    "PRF-08": "comparative-collection", "PRF-09": "relational-network",
    "PRF-10": "proof-navigation", "PRF-11": "proof-navigation",
    "PRF-12": "longitudinal-record", "PRF-13": "longitudinal-record",
    "PRF-14": "longitudinal-record", "PRF-15": "causal-graph",
    "PRF-16": "conditional-process", "PRF-17": "conditional-process",
    "PRF-18": "federated-resolution", "PRF-19": "relational-network",
}


def _classification_issues(classification) -> list[str]:
    if classification is None:
        return []
    if not isinstance(classification, dict):
        return ["classification must be an object"]
    issues = []
    def string(name, pattern=None):
        val = classification.get(name)
        if val is not None and (not isinstance(val, str) or not val or (pattern and not re.fullmatch(pattern, val))):
            issues.append(f"classification.{name} invalid")
    for k in ("arketype_version", "usage_slug", "usage_family", "domain"):
        string(k)
    string("primary_archetype", r"ARK-[0-9]{2,}")
    string("primary_usage", r"PRF-[0-9]{2,}")
    for k in ("supporting_archetypes", "secondary_usages"):
        values = classification.get(k, [])
        pattern = r"ARK-[0-9]{2,}" if k == "supporting_archetypes" else r"PRF-[0-9]{2,}"
        if not isinstance(values, list) or any(not isinstance(v, str) or not re.fullmatch(pattern, v) for v in values) or len(values) != len(set(values)):
            issues.append(f"classification.{k} must contain unique known-format IDs")
    if classification.get("organization", "single") not in {"single", "collection", "federation", "hybrid", "unknown"}:
        issues.append("classification.organization invalid")
    return issues


def _classification_from_arketype(root: Path, catalog_dir: Path, profile: str) -> dict:
    cat = read_json(catalog_dir / "catalogue.json")
    index = read_json(catalog_dir / "inventaires/profils-usage.json")
    profiles = [p for p in index.get("profiles", []) if p.get("id") == profile or p.get("slug") == profile]
    if len(profiles) != 1:
        raise SystemExit(f"Unknown Arketype usage profile: {profile}")
    row = profiles[0]
    ids = {a.get("slug"): a.get("id") for a in cat.get("archetypes", [])}
    primary = ids.get(row.get("primary_archetype"))
    if not primary:
        raise SystemExit("Arketype catalogue is missing this profile's primary archetype")
    return {
        "arketype_version": cat.get("version"),
        "primary_archetype": primary,
        "supporting_archetypes": [ids[k] for k in row.get("supporting_archetypes", []) if k in ids],
        "primary_usage": row["id"], "usage_slug": row["slug"],
        "usage_family": row.get("usage_family"), "domain": row.get("domain"),
        "organization": "single",
    }


def _effective_classification(root: Path, ws: dict) -> dict:
    declared = ws.get("classification") or {}
    if declared:
        return dict(declared)
    # Arketype 1.4 historically places its identity in a noncanonical sidecar.
    # It is informative only: no automatic guessing from filenames or content.
    sidecar = root / "arketype.instance.json"
    if not sidecar.is_file():
        return {}
    try:
        doc = read_json(sidecar)
        if doc.get("format") != "arketype.instance-origin/1.0-non-normatif":
            return {}
        return {"arketype_version": doc.get("library_version"),
                "arketype_origin_slug": doc.get("primary_archetype"),
                "usage_slug": doc.get("use_case_profile"),
                "classification_source": "arketype.instance.json-unverified"}
    except (ValueError, OSError, TypeError):
        return {}


def _discovery_documents(root: Path) -> tuple[dict, dict, dict]:
    """Build lightweight, deterministic observations without reading domain JSON.

    Counts unavailable in local manifests are null, never guessed. This does not
    scan arbitrary files, follow remote locators, or assert workspace completeness.
    """
    root = root.resolve()
    ws = read_json(root / "kristal.workspace.json")
    idx = read_json(root / "canon/state.index.json")
    classification = _effective_classification(root, ws)
    if _classification_issues(ws.get("classification")):
        raise ValueError("Invalid workspace classification: " + "; ".join(_classification_issues(ws["classification"])))
    observed = {}
    def record(path: Path, kind: str):
        local = path.resolve()
        if not local.is_relative_to(root) or not local.is_file():
            return
        rel = local.relative_to(root).as_posix()
        observed[rel] = {"path": rel, "role": kind, "media_type": _media_type(local),
                         "size_bytes": local.stat().st_size, "sha256": "sha256:" + hash_file(local)}
    for item in idx.get("canonical_artifacts", []):
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            p = _safe_indexed_read_path(root, item["path"])
            if p:
                record(p, "canonical_source")
    descriptors = _discover_materialization_manifests(root)
    segments = []
    remote = 0
    absent = 0
    for path, doc in descriptors:
        record(path, "materialization_manifest")
        profile = doc.get("profile")
        for seg in doc.get("segments", []):
            if not isinstance(seg, dict):
                continue
            blob = seg.get("blob") or {}
            if not isinstance(blob, dict):
                continue
            local = _safe_local_locator(root, blob.get("locator")) if blob.get("locator") else None
            status = "unlocated" if not blob.get("locator") else "external" if local is None else "local" if local.is_file() else "missing"
            if status in ("external", "unlocated"):
                remote += 1
            elif status == "missing":
                absent += 1
            if status == "local":
                record(local, "materialization_blob")
            segments.append({"manifest": path.relative_to(root).as_posix(),
                             "segment_key": seg.get("segment_key"), "record_count_declared": seg.get("record_count"),
                             "media_type": blob.get("media_type"), "size_bytes_declared": blob.get("size"),
                             "digest_declared": blob.get("digest"), "availability": status,
                             "compression_declared": blob.get("compression"),
                             "encrypted_declared": bool(blob.get("encryption")),
                             "path": local.relative_to(root).as_posix() if status == "local" else None,
                             "materialization_profile": profile})
        for blob in doc.get("dictionaries", []) or []:
            if not isinstance(blob, dict):
                continue
            local = _safe_local_locator(root, blob.get("locator")) if blob.get("locator") else None
            if local is not None and local.is_file():
                record(local, "materialization_dictionary")
            elif local is None:
                remote += 1
            else:
                absent += 1
    # Local deterministic build representations are separate physical bytes.
    build = root / "build/v9"
    if (build / "state-snapshot.json").is_file():
        record(build / "state-snapshot.json", "state_candidate")
        for ap in sorted((build / "artifacts").glob("*.json")):
            record(ap, "generated_logical_artifact")
    ordered = [observed[k] for k in sorted(observed, key=lambda v: v.encode("utf-8"))]
    total = sum(r["size_bytes"] for r in ordered)
    max_size = max((r["size_bytes"] for r in ordered), default=0)
    scale = "tiny" if total < 1_000_000 else "small" if total < 50_000_000 else "medium" if total < 1_000_000_000 else "large" if total < 20_000_000_000 else "massive"
    fingerprints = [[name, hash_file(root / name)] for name in ("kristal.workspace.json", "canon/state.index.json")]
    sidecar = root / "arketype.instance.json"
    if sidecar.is_file():
        fingerprints.append([sidecar.name, hash_file(sidecar)])
    fingerprint_input = {"inputs": fingerprints, "physical_files": ordered, "segments": segments}
    fingerprint = "sha256:" + hashlib.sha256(canonicalize(fingerprint_input).encode("utf-8")).hexdigest()
    inventory = {
        "format": INVENTORY_FORMAT, "state_ref": ws.get("state_ref"),
        "source_fingerprint": fingerprint,
        "size_class": scale,
        "measurement": {"status": "partial" if remote or absent else "measured_referenced_local_files",
                        "scope": "registered canonical sources, materialization descriptors/blobs, and built v9 payloads",
                        "external_or_unlocated_blob_count": remote, "missing_local_blob_count": absent,
                        "not_measured": ["unregistered workspace files", "external payloads", "JSON nesting depth", "largest JSONL record"]},
        "storage": {"tracked_local_bytes": total, "tracked_file_count": len(ordered),
                    "max_tracked_file_bytes": max_size, "materialization_segment_count": len(segments),
                    "max_json_depth": None, "max_record_bytes": None},
        "cardinality": {"canonical_artifacts": len(idx.get("canonical_artifacts", [])),
                        "external_references": len(idx.get("external_references", [])),
                        "entities": None, "relations": None, "sub_kristals": None},
        "files": ordered, "segments": segments,
    }
    family = classification.get("usage_family") or ""
    specialization = READER_USAGE.get(classification.get("primary_usage")) or READER_FAMILY.get(family, "generic")
    organization = classification.get("organization") or "unknown"
    if organization == "federation":
        specialization = "federated-resolution"
    profiles = sorted({x.get("materialization_profile") for x in segments if x.get("materialization_profile")})
    jsonl = [x for x in segments if x.get("media_type") in ("application/x-ndjson", "application/jsonl", "application/ndjson") or "segmented-jsonl" in str(x.get("materialization_profile"))]
    # Decisions are scoped to measured local files; a consumer must verify
    # magic bytes, media type, bounds and permissions, not blindly trust hints.
    strategies = []
    local_segments = {x["path"]: x for x in segments if x.get("path")}
    for item in ordered:
        linked = local_segments.get(item["path"], {})
        # A registered manifest's MIME is a declaration, not a substitute for
        # independent payload verification. Compression/decryption take priority.
        typ = linked.get("media_type") or item["media_type"]
        compressed = linked.get("compression_declared")
        encrypted = linked.get("encrypted_declared", False)
        if encrypted:
            mode, engine = "authorized_decryption_required", None
        elif compressed and compressed not in {"identity", "none"}:
            mode, engine = "bounded_decompression_required", None
        elif typ == "application/json":
            mode = "on_demand_or_dom" if item["size_bytes"] < 32_000_000 else "selective_on_demand_with_capacity_guard"
            engine = "simdjson"
        elif typ == "application/x-ndjson":
            mode, engine = "document_stream_requires_record_bound", "simdjson"
        else:
            mode, engine = "format_specific_or_opaque", None
        strategies.append({"path": item["path"], "media_type_observed": item["media_type"],
                           "media_type_declared": linked.get("media_type"),
                           "compression_declared": compressed, "encrypted_declared": encrypted,
                           "size_bytes_measured": item["size_bytes"],
                           "suggested_parser_family": engine, "suggested_mode": mode,
                           "must_verify_digest": item["sha256"],
                           "authorization_required": True})
    reader = {
        "format": READER_FORMAT, "state_ref": ws.get("state_ref"),
        "source_fingerprint": fingerprint, "specialization": f"kristal.reader/{specialization}-v1",
        "configuration_status": "advisory_only",
        "access_pattern": "selective" if specialization != "generic" else "generic",
        "materialization_profiles": profiles,
        "artifact_strategies": strategies,
        "parser_candidates": [
            {"kind": "jsonl", "engine_family": "simdjson", "mode": "document_stream",
             "condition": "validated JSONL/NDJSON segments only", "segment_count": len(jsonl)},
            {"kind": "json", "engine_family": "simdjson", "mode": "on_demand_or_dom",
             "condition": "JSON files within parser capacity and memory limits"},
        ],
        "constraints": ["Verify actual media type, digest, size and local availability before selecting a parser.",
                        "Enforce memory, decompression and per-record bounds independently of metadata.",
                        "The reader must authorize all file/network access; this profile grants none.",
                        "Unrecognized profiles and missing discoveries must fall back to generic guarded parsing."],
    }
    discovery = {
        "format": DISCOVERY_FORMAT, "state_ref": ws.get("state_ref"), "classification": classification,
        "data_layout": {"state_architecture": (ws.get("target") or {}).get("state_architecture"),
                        "native_kind": (ws.get("native_model") or {}).get("kind"),
                        "organization": organization,
                        "materialization_profiles": profiles,
                        "inventory_ref": "derived/reader-inventory.json"},
        "reader": {"profile": reader["specialization"], "hints_ref": "derived/reader-profile.json"},
        "size": {"class": scale, "tracked_local_bytes": total,
                 "completeness": inventory["measurement"]["status"]},
        "source_fingerprint": fingerprint,
        "authority": "noncanonical_derived_metadata_not_access_or_publication_authority",
    }
    return discovery, inventory, reader


def _write_discovery(root: Path) -> None:
    discovery, inventory, reader = _discovery_documents(root)
    write_json(root / "derived/reader-inventory.json", inventory)
    write_json(root / "derived/reader-profile.json", reader)
    write_json(root / "kristal.discovery.json", discovery)


def cmd_build_discovery(args):
    root = Path(args.path).resolve()
    if not (root / "kristal.workspace.json").is_file():
        raise SystemExit("No Kristal Local workspace found")
    _write_discovery(root)
    print("Built noncanonical discovery and reader inventory for", root)


def cmd_classify(args):
    root = Path(args.path).resolve()
    ws_path = root / "kristal.workspace.json"
    ws = read_json(ws_path)
    c = dict(ws.get("classification") or {})
    if args.arketype_dir:
        if not args.usage:
            raise SystemExit("--arketype-dir requires --usage (PRF ID or slug)")
        c.update(_classification_from_arketype(root, Path(args.arketype_dir), args.usage))
    elif args.usage:
        c["primary_usage" if re.fullmatch(r"PRF-[0-9]{2,}", args.usage) else "usage_slug"] = args.usage
    for key, value in (("primary_archetype", args.archetype), ("arketype_version", args.arketype_version),
                       ("usage_family", args.family), ("domain", args.domain), ("organization", args.organization)):
        if value is not None:
            c[key] = value
    problems = _classification_issues(c)
    if problems:
        raise SystemExit("Invalid classification: " + "; ".join(problems))
    ws["classification"] = c
    write_json(ws_path, ws)
    _write_discovery(root)
    print("Saved design classification and refreshed derived reader discovery (no canon changes).")


def _check_discovery(root: Path, errors: list[str], warnings: list[str]):
    paths = [root / p for p in ("kristal.discovery.json", "derived/reader-inventory.json", "derived/reader-profile.json")]
    present = [x.is_file() for x in paths]
    if not any(present):
        # Legacy workspaces remain valid without migration or new required files.
        return
    if not all(present):
        errors.append("Incomplete reader discovery: regenerate with build-discovery")
        return
    expected = _discovery_documents(root)
    for path, wanted in zip(paths, expected):
        if read_json(path) != wanted:
            warnings.append(f"Stale or edited derived reader metadata: {path.relative_to(root)}; run build-discovery")



def audit_reader_discovery(root: Path) -> dict:
    """Read-only consumer preflight for Manager/Konstellation/Light.

    This is an integrity/freshness check, NOT a grant to read or publish.
    Summary only: do not leak local file paths or the complete inventory.
    """
    root = Path(root).resolve()
    relatives = (
        "kristal.discovery.json",
        "derived/reader-inventory.json",
        "derived/reader-profile.json",
    )
    paths = [root / rel for rel in relatives]
    result = {
        "format": "kristal.discovery-audit/1.0",
        "status": "absent",
        "usable_as_reader_hint": False,
        "authorization": "not_evaluated_no_access_or_publication_grant",
        "issues": [],
        "formats": [DISCOVERY_FORMAT, INVENTORY_FORMAT, READER_FORMAT],
    }
    # No implicit filesystem traversal or network access. Treat symlinks as
    # unsafe here even if they currently resolve inside the workspace.
    if any(path.is_symlink() or path.parent.is_symlink() for path in paths):
        result["status"] = "invalid"
        result["issues"].append("symlinked_discovery_path")
        return result
    present = [p.is_file() for p in paths]
    if not any(present):
        return result  # fully legacy Kristals are valid, with generic fallback
    if not all(present):
        result["status"] = "incomplete"
        result["issues"].append("incomplete_discovery_set")
        return result
    try:
        discovery, inventory, profile = [read_json(path) for path in paths]
        if not all(isinstance(doc, dict) for doc in (discovery, inventory, profile)):
            raise ValueError("non_object_document")
        if [discovery.get("format"), inventory.get("format"), profile.get("format")] != result["formats"]:
            raise ValueError("unknown_contract_format")
        ws = read_json(root / "kristal.workspace.json")
        state_ref = ws.get("state_ref")
        if not state_ref or any(doc.get("state_ref") != state_ref for doc in (discovery, inventory, profile)):
            raise ValueError("state_ref_mismatch")
        fingerprint = discovery.get("source_fingerprint")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint):
            raise ValueError("invalid_source_fingerprint")
        if any(doc.get("source_fingerprint") != fingerprint for doc in (inventory, profile)):
            raise ValueError("source_fingerprint_mismatch")
        layout, reader, size = discovery.get("data_layout"), discovery.get("reader"), discovery.get("size")
        if not all(isinstance(x, dict) for x in (layout, reader, size)):
            raise ValueError("invalid_discovery_structure")
        if layout.get("inventory_ref") != relatives[1] or reader.get("hints_ref") != relatives[2]:
            raise ValueError("unexpected_relative_ref")
        if reader.get("profile") != profile.get("specialization"):
            raise ValueError("reader_profile_mismatch")
        if profile.get("configuration_status") != "advisory_only":
            raise ValueError("reader_hints_not_advisory")
        if discovery.get("authority") != "noncanonical_derived_metadata_not_access_or_publication_authority":
            raise ValueError("unexpected_authority")
        storage, rows = inventory.get("storage"), inventory.get("files")
        strategies = profile.get("artifact_strategies")
        if not isinstance(storage, dict) or not isinstance(rows, list) or not isinstance(strategies, list):
            raise ValueError("invalid_inventory_or_profile")
        if size.get("tracked_local_bytes") != storage.get("tracked_local_bytes") or size.get("class") != inventory.get("size_class"):
            raise ValueError("size_summary_mismatch")
        if len(rows) != storage.get("tracked_file_count"):
            raise ValueError("file_count_mismatch")
        listed = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                raise ValueError("invalid_inventory_row")
            rel = row["path"]
            if rel in listed or not rel or rel.startswith("/") or "\\" in rel or any(p in ("", ".", "..") for p in rel.split("/")):
                raise ValueError("duplicate_or_unsafe_inventory_path")
            listed[rel] = row
        if len(strategies) != len(rows):
            raise ValueError("strategy_count_mismatch")
        seen = set()
        for strategy in strategies:
            if not isinstance(strategy, dict) or strategy.get("path") not in listed:
                raise ValueError("unlisted_strategy")
            rel = strategy["path"]
            if rel in seen:
                raise ValueError("duplicate_strategy")
            seen.add(rel)
            source = listed[rel]
            if (strategy.get("must_verify_digest") != source.get("sha256")
                or strategy.get("size_bytes_measured") != source.get("size_bytes")
                or strategy.get("authorization_required") is not True):
                raise ValueError("strategy_integrity_mismatch")
        # Consumer freshness is based on registered inputs and tracked blobs.
        # It intentionally does not scan the entire project or follow remote refs.
        expected = _discovery_documents(root)
        if any(actual != generated for actual, generated in zip((discovery, inventory, profile), expected)):
            result["status"] = "stale"
            result["issues"].append("source_inputs_changed_or_metadata_edited")
            return result
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        result["status"] = "invalid"
        result["issues"].append("invalid_discovery_or_inputs")
        # Avoid echoing untrusted file paths/contents in machine output.
        return result
    result["status"] = "fresh"
    result["usable_as_reader_hint"] = True
    result["tracked_file_count"] = len(rows)
    result["state_ref"] = state_ref
    result["reader_profile"] = reader["profile"]
    return result


def cmd_audit_discovery(args):
    result = audit_reader_discovery(Path(args.path))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=None if args.compact else 2))
    if args.require_fresh and result["status"] != "fresh":
        raise SystemExit(2)


# ---------- workspace creation / migration ----------

def cmd_init(args):
    root = Path(args.path).resolve()
    profile = args.profile
    if profile not in PROFILES:
        raise SystemExit(f"Profil inconnu: {profile}")
    ensure_empty_or_new(root, args.force)
    slug = args.slug or slugify(args.title or root.name)
    title = args.title or root.name

    for d in [
        "docs", "sources", "schemas", "canon/domain", "canon/epistemic", "canon/operations",
        "projections/recipes", "projections/materialized", "derived/indexes", "derived/views",
        "derived/ai-contexts", "materializations/v9/manifests", "runtime", "state", "build/v9", "build/v10", "release/v9/states", "release/v9/channels",
        "hosting", "validation", "tests", "tools"
    ] + (["ai"] if getattr(args, "with_ai", False) else []):
        (root / d).mkdir(parents=True, exist_ok=True)

    ws = json.loads(template_text("workspace.json").replace("__SLUG__", slug).replace("__TITLE__", title).replace("__PROFILE__", profile))
    if profile == "hierarchy-stub":
        ws["status"] = "stub"
        ws["native_model"]["kind"] = "identity_and_topology_reserved"
    write_json(root / "kristal.workspace.json", ws)
    write_json(root / "canon/state.index.json", json.loads(template_text("state.index.json")))
    write_json(root / "sources/source-catalog.json", json.loads(template_text("source-catalog.json")))

    readme = template_text("readme-kristal.md").replace("__TITLE__", title)
    (root / "README.md").write_text(readme, encoding="utf-8")
    (root / "AGENTS.md").write_text(template_text("AGENTS.kristal.md"), encoding="utf-8")
    if getattr(args, "with_ai", False):
        (root / "AI_START_HERE.md").write_text(template_text("AI_START_HERE.md"), encoding="utf-8")
        ws["portable_ai"]["enabled"] = True
        write_json(root / "kristal.workspace.json", ws)
    (root / ".gitignore").write_text(template_text("gitignore-kristal.txt"), encoding="utf-8")
    for name, content in DOC_TEMPLATES.items():
        (root / "docs" / name).write_text(content, encoding="utf-8")
    (root / "docs" / "PROFILE_NOTES.md").write_text(
        f"# Notes du profil `{profile}`\n\n{PROFILE_NOTES[profile]}\n\nCe profil est une amorce et non une contrainte normative.\n",
        encoding="utf-8",
    )
    for rel in ["canon/domain/.gitkeep", "canon/epistemic/.gitkeep", "canon/operations/.gitkeep", "runtime/.gitkeep", "state/.gitkeep"] + (["ai/.gitkeep"] if getattr(args, "with_ai", False) else []):
        (root / rel).write_text("", encoding="utf-8")

    local_tool = root / "tools" / "kristal.py"
    source_tool = Path(__file__).resolve()
    if source_tool != local_tool.resolve():
        shutil.copy2(source_tool, local_tool)
    # Companion v11 adapter remains local/offline even when the workspace is
    # initialized from the installed kit. No semantics are enabled by default.
    v11_module = source_tool.parent / "kristal_v11_core.py"
    if v11_module.is_file() and v11_module.resolve() != (root / "tools/kristal_v11_core.py").resolve():
        shutil.copy2(v11_module, root / "tools/kristal_v11_core.py")
    local_templates = root / "tools" / "_templates"
    local_templates.mkdir(parents=True, exist_ok=True)
    for name in ["workspace.json", "state.index.json", "source-catalog.json", "projection.json", "github-hosting.json", "readme-kristal.md", "AGENTS.kristal.md", "AI_START_HERE.md", "gitignore-kristal.txt"]:
        (local_templates / name).write_text(template_text(name), encoding="utf-8")

    print(f"Initialized Local Kristal workspace: {root}")
    print(f"Profile: {profile}")
    _write_discovery(root)
    print("Next: fill docs/00..04, register canonical Logical Artifacts, then run build-v9. Portable-AI/Kompiler support is optional: use build-ai or build-v9 --with-ai when needed.")


def _migrate_state_index_v1(idx: dict) -> dict:
    artifacts = []
    for item in idx.get("canonical_artifacts", []):
        if isinstance(item, str):
            artifacts.append({
                "artifact_id": f"urn:kristal:legacy-artifact:{hashlib.sha256(item.encode()).hexdigest()[:16]}",
                "path": item,
                "logical_contract": {"id": "authoring.legacy-json-artifact", "version": "1.0"},
                "commitment": {"mode": "compute-json-jcs", "profile": LOGICAL_PROFILE},
                "migration_note": "Generated placeholder metadata during v1→v2 authoring migration; review before release."
            })
        elif isinstance(item, dict):
            artifacts.append(item)
    return {
        "format": STATE_INDEX_FORMAT,
        "canonical_artifacts": artifacts,
        "external_references": [],
        "derived_artifacts": idx.get("derived_artifacts", []),
        "notes": idx.get("notes", "Declare actual authoritative inputs here."),
    }


def _upgrade_to_v32(root: Path, ws: dict) -> dict:
    if ws.get("format") not in {V2_FORMAT, V3_FORMAT, V31_FORMAT}:
        raise SystemExit(f"Expected legacy Local/authoring format, got {ws.get('format')!r}")
    ws["format"] = FORMAT
    target = ws.setdefault("target", {})
    target["hosted_network_baseline"] = HOSTED_NETWORK_BASELINE
    policy = ws.setdefault("release_policy", {})
    policy["build_publish_activate_separated"] = True
    policy["qualification_before_publication"] = True
    policy["exact_commit_publication"] = True
    policy.setdefault("activation_required", False)
    derived = list(ws.get("derived_paths", []))
    for rel in ["derived", "projections/materialized", "materializations", "runtime", "ai", "state", "build"]:
        if rel not in derived:
            derived.append(rel)
    ws["derived_paths"] = derived
    portable = ws.setdefault("portable_ai", {})
    portable.setdefault("enabled", (root / "AI_MANIFEST.json").is_file() or (root / "AI_START_HERE.md").is_file())
    portable["profile"] = PORTABLE_AI_FORMAT
    portable["entrypoint"] = "AI_START_HERE.md"
    portable["manifest"] = "AI_MANIFEST.json"
    portable["offline_first"] = True
    portable["github_required_for_reading"] = False
    for d in ["materializations/v9/manifests", "runtime", "state", "build/v9", "build/v10", "release/v9/states", "release/v9/channels", "hosting"] + (["ai"] if portable.get("enabled") else []):
        (root / d).mkdir(parents=True, exist_ok=True)
    return ws


def cmd_migrate_v10(args):
    root = Path(args.path).resolve()
    ws_path = root / "kristal.workspace.json"
    ws = read_json(ws_path)
    if ws.get("format") == FORMAT:
        print("Workspace already uses Local Kristal v3.2 alignment.")
        return
    if ws.get("format") == LEGACY_FORMAT:
        # Preserve the old v1→v2 semantic migration first, then add the v10 envelope.
        ws["format"] = V2_FORMAT
        ws["state_ref"] = ws.get("state_ref") or f"urn:kristal:state:{ws.get('slug') or slugify(ws.get('title','kristal'))}"
        ws["target"] = {
            "portable_contract": "kristal_state/6.0",
            "semantic_baseline": "kristall/7.0",
            "query_baseline": "kristall/8.0",
            "state_architecture": "kristal.state/9.0",
            "logical_commitment_profile": LOGICAL_PROFILE,
            "state_commitment_profile": STATE_PROFILE,
        }
        ws.setdefault("release_policy", {"build_publish_activate_separated": True, "activation_required": False})
        idx_path = root / "canon/state.index.json"
        idx = read_json(idx_path)
        if idx.get("format") != STATE_INDEX_FORMAT:
            write_json(idx_path, _migrate_state_index_v1(idx))
        src = root / "sources/source-catalog.json"
        if src.exists():
            cat = read_json(src); cat["format"] = SOURCE_CATALOG_FORMAT; write_json(src, cat)
        for q in (root / "projections/recipes").glob("*.json"):
            obj = read_json(q); obj["format"] = PROJECTION_FORMAT; write_json(q, obj)
    elif ws.get("format") not in {V2_FORMAT, V3_FORMAT, V31_FORMAT}:
        raise SystemExit(f"Unsupported source workspace format: {ws.get('format')!r}")

    ws = _upgrade_to_v32(root, ws)
    write_json(ws_path, ws)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    host_doc = root / "docs/07_HOSTING_AND_PUBLICATION.md"
    if not host_doc.exists():
        host_doc.write_text(DOC_TEMPLATES["07_HOSTING_AND_PUBLICATION.md"], encoding="utf-8")
    glossary_doc = root / "docs/08_GLOSSARY.md"
    if not glossary_doc.exists():
        glossary_doc.write_text(DOC_TEMPLATES["08_GLOSSARY.md"], encoding="utf-8")
    ai_start = root / "AI_START_HERE.md"
    if (ws.get("portable_ai") or {}).get("enabled"):
        if not ai_start.exists():
            ai_start.write_text(template_text("AI_START_HERE.md"), encoding="utf-8")
        (root / "ai").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)
    # Refresh local tool/templates if this is a self-contained workspace.
    local_tool = root / "tools/kristal.py"
    if local_tool.exists() and Path(__file__).resolve() != local_tool.resolve():
        shutil.copy2(Path(__file__).resolve(), local_tool)
    module = Path(__file__).resolve().parent / "kristal_v11_core.py"
    (root / "tools").mkdir(parents=True, exist_ok=True)
    if module.is_file() and module.resolve() != (root / "tools/kristal_v11_core.py").resolve():
        shutil.copy2(module, root / "tools/kristal_v11_core.py")
    local_templates = root / "tools/_templates"
    if local_templates.exists():
        for name in ["workspace.json", "state.index.json", "source-catalog.json", "projection.json", "github-hosting.json", "readme-kristal.md", "AGENTS.kristal.md", "AI_START_HERE.md", "gitignore-kristal.txt"]:
            (local_templates / name).write_text(template_text(name), encoding="utf-8")
    print("Migrated workspace to Local Kristal v3.2 alignment.")
    print("Semantic-state commitments remain v9. AI/Kompiler read layers remain optional and derived.")


def cmd_migrate_v9(args):
    print("NOTE: migrate-v9 is retained as a compatibility alias; it now migrates to the current v10 Local workspace envelope.")
    return cmd_migrate_v10(args)


# ---------- local workspace commands ----------

def cmd_add_source(args):
    root = Path(args.path).resolve()
    p = root / "sources/source-catalog.json"
    data = read_json(p)
    sources = data.setdefault("sources", [])
    if any(s.get("id") == args.id for s in sources):
        raise SystemExit(f"Source ID already exists: {args.id}")
    item = {
        "id": args.id, "title": args.title, "kind": args.kind, "locator": args.locator,
        "version_or_date": args.version_or_date, "sha256": args.sha256,
        "authority_scope": args.authority_scope, "trust_class": args.trust_class, "notes": args.notes,
    }
    sources.append({k: v for k, v in item.items() if v is not None})
    write_json(p, data)
    print(f"Added source {args.id}")


def cmd_new_projection(args):
    root = Path(args.path).resolve()
    slug = slugify(args.slug)
    p = root / "projections/recipes" / f"{slug}.projection.json"
    if p.exists() and not args.force:
        raise SystemExit(f"Projection already exists: {p}")
    obj = json.loads(template_text("projection.json").replace("__SLUG__", slug).replace("__SUBJECT_REF__", args.subject_ref).replace("__PRIMARY_AXIS__", args.primary_axis))
    if args.secondary_axis:
        obj["orientation"]["secondary_axis"] = args.secondary_axis
    write_json(p, obj)
    print(f"Created projection recipe: {p}")


def cmd_register_artifact(args):
    root = Path(args.path).resolve()
    rel = Path(args.file).as_posix().lstrip("/")
    full = root / rel
    # Discovery, sidecars, and derived reader hints are never domain canon.
    if (not full.resolve().is_relative_to(root)
            or rel in {"kristal.discovery.json", "arketype.instance.json"}
            or rel.startswith(("derived/", "materializations/", "build/", "state/", "release/", "ai/"))):
        raise SystemExit("Refusing to register derived/outside-workspace metadata as canonical")
    if not full.is_file():
        raise SystemExit(f"Canonical artifact file does not exist: {rel}")
    idx_path = root / "canon/state.index.json"
    idx = read_json(idx_path)
    arts = idx.setdefault("canonical_artifacts", [])
    if any(isinstance(a, dict) and a.get("artifact_id") == args.artifact_id for a in arts):
        raise SystemExit(f"artifact_id already registered: {args.artifact_id}")
    if any(isinstance(a, dict) and a.get("path") == rel for a in arts):
        raise SystemExit(f"path already registered as canonical: {rel}")
    entry = {
        "artifact_id": args.artifact_id,
        "path": rel,
        "logical_contract": {"id": args.contract_id, "version": args.contract_version},
        "commitment": {"mode": args.mode},
    }
    if args.mode == "compute-json-jcs":
        if full.suffix.lower() != ".json":
            raise SystemExit("compute-json-jcs requires a JSON canonical artifact")
        read_json(full)
        entry["commitment"]["profile"] = LOGICAL_PROFILE
    else:
        if not args.digest or not SHA256_ID.fullmatch(args.digest):
            raise SystemExit("precomputed mode requires --digest sha256:<64 lowercase hex>")
        entry["commitment"].update({"profile": args.commitment_profile, "digest": args.digest})
    if args.authority_ref:
        entry["authority_ref"] = args.authority_ref
    arts.append(entry)
    write_json(idx_path, idx)
    print(f"Registered canonical Logical Artifact: {args.artifact_id}")


def cmd_register_materialization(args):
    """Copy a v9 materialization manifest into the standard authoring registry."""
    root = Path(args.path).resolve()
    source_path = Path(args.manifest)
    if not source_path.is_absolute():
        candidate = root / source_path
        source_path = candidate if candidate.is_file() else source_path.resolve()
    if not source_path.is_file():
        raise SystemExit(f"Materialization manifest does not exist: {source_path}")
    doc = read_json(source_path)
    issues = _materialization_manifest_issues(doc)
    if issues:
        raise SystemExit("Invalid v9 materialization manifest:\n- " + "\n- ".join(issues))
    idx = read_json(root / "canon/state.index.json")
    refs = _canonical_ref_map(root, idx)
    source = doc.get("source") or {}
    expected = refs.get(source.get("artifact_id"))
    if expected is None:
        raise SystemExit(f"Manifest source is not a registered canonical artifact: {source.get('artifact_id')}")
    if source.get("logical_contract") != expected.get("logical_contract") or source.get("logical_commitment") != expected.get("logical_commitment"):
        raise SystemExit("Manifest source binding does not match the current canonical Logical Artifact commitment")
    blobs = [s.get("blob") for s in doc.get("segments", []) if isinstance(s, dict)] + list(doc.get("dictionaries") or [])
    for i, blob in enumerate(blobs):
        if not isinstance(blob, dict) or not blob.get("locator"):
            continue
        local = _safe_local_locator(root, blob.get("locator"))
        if local is None or not local.is_file():
            continue
        if local.stat().st_size != blob.get("size"):
            raise SystemExit(f"Manifest blob[{i}] size mismatch for {blob.get('locator')}")
        actual = "sha256:" + hash_file(local)
        if actual != blob.get("digest"):
            raise SystemExit(f"Manifest blob[{i}] digest mismatch for {blob.get('locator')}: declared={blob.get('digest')} actual={actual}")
    materialization_id = doc.get("materialization_id") or f"{source['artifact_id']}::{doc['profile']}"
    target_dir = root / "materializations" / "v9" / "manifests"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{_safe_name(materialization_id)}.materialization.json"
    if target.exists() and not args.force:
        existing = read_json(target)
        if existing == doc:
            print(f"Materialization already registered: {target.relative_to(root)}")
            return
        raise SystemExit(f"Refusing to overwrite different registered manifest: {target.relative_to(root)}; use --force after review")
    write_json(target, doc)
    print(f"Registered v9 materialization: {doc['profile']}")
    print(f"Manifest: {target.relative_to(root).as_posix()}")


def cmd_add_reference(args):
    root = Path(args.path).resolve()
    idx_path = root / "canon/state.index.json"
    idx = read_json(idx_path)
    refs = idx.setdefault("external_references", [])
    if not SHA256_ID.fullmatch(args.digest):
        raise SystemExit("--digest must be sha256:<64 lowercase hex>")
    if args.kind == "state":
        ref = {"state_ref": args.id, "logical_commitment": {"profile": args.commitment_profile or STATE_PROFILE, "digest": args.digest}}
    else:
        if not args.contract_id or not args.contract_version:
            raise SystemExit("artifact reference requires --contract-id and --contract-version")
        ref = {
            "artifact_id": args.id,
            "logical_contract": {"id": args.contract_id, "version": args.contract_version},
            "logical_commitment": {"profile": args.commitment_profile or LOGICAL_PROFILE, "digest": args.digest},
        }
    if args.authority_ref:
        ref["authority_ref"] = args.authority_ref
    refs.append(ref)
    write_json(idx_path, idx)
    print(f"Added pinned external {args.kind} reference: {args.id}")


# ---------- v10 hosted-network integration ----------

def _safe_repo_relative_path(value: str) -> str:
    raw = str(value or "").replace("\\", "/").strip()
    parts = [x for x in raw.split("/") if x not in {"", "."}]
    if not parts or raw.startswith("/") or any(x == ".." for x in parts):
        raise ValueError("state_path must be a non-empty repository-relative path without '..'")
    return "/".join(parts)


def _validate_github_hosting(cfg: dict) -> list[str]:
    errors = []
    if not isinstance(cfg, dict):
        return ["hosting/github.json must be an object"]
    if cfg.get("format") != GITHUB_HOSTING_FORMAT:
        errors.append(f"hosting format must be {GITHUB_HOSTING_FORMAT}")
    if cfg.get("profile") != GITHUB_HOST_PROFILE:
        errors.append(f"hosting profile must be {GITHUB_HOST_PROFILE}")
    if not REPO_SLUG.fullmatch(str(cfg.get("repository", ""))):
        errors.append("hosting.repository must be OWNER/REPOSITORY")
    if not isinstance(cfg.get("branch"), str) or not cfg.get("branch"):
        errors.append("hosting.branch is required")
    try:
        _safe_repo_relative_path(cfg.get("state_path", ""))
    except ValueError as exc:
        errors.append(str(exc))
    for key in ("qualify_workflow", "publish_workflow"):
        if not isinstance(cfg.get(key), str) or not cfg.get(key):
            errors.append(f"hosting.{key} is required")
    fw = cfg.get("framework") or {}
    if not REPO_SLUG.fullmatch(str(fw.get("repository", ""))):
        errors.append("hosting.framework.repository must be OWNER/REPOSITORY")
    if not SHA40.fullmatch(str(fw.get("commit", ""))):
        errors.append("hosting.framework.commit must be a full 40-character lowercase SHA")
    return errors


def _hosting_config(root: Path, required: bool = True) -> dict | None:
    p = root / "hosting/github.json"
    if not p.is_file():
        if required:
            raise SystemExit("No GitHub authoring host configured. Run configure-github first.")
        return None
    cfg = read_json(p)
    errors = _validate_github_hosting(cfg)
    if errors:
        raise SystemExit("Invalid hosting/github.json:\n- " + "\n- ".join(errors))
    return cfg


def cmd_configure_github(args):
    root = Path(args.path).resolve()
    ws = read_json(root / "kristal.workspace.json")
    if ws.get("format") != FORMAT:
        raise SystemExit("configure-github requires the current Local Kristal workspace format; run migrate-v10 first")
    state_path = _safe_repo_relative_path(args.state_path or f"kristals/{ws['slug']}/state/state-snapshot.json")
    if not REPO_SLUG.fullmatch(args.repository):
        raise SystemExit("--repository must be OWNER/REPOSITORY")
    if not REPO_SLUG.fullmatch(args.framework_repository):
        raise SystemExit("--framework-repository must be OWNER/REPOSITORY")
    if not SHA40.fullmatch(args.framework_sha):
        raise SystemExit("--framework-sha must be a full 40-character lowercase commit SHA")
    cfg = {
        "format": GITHUB_HOSTING_FORMAT,
        "profile": GITHUB_HOST_PROFILE,
        "repository": args.repository,
        "branch": args.branch,
        "state_path": state_path,
        "qualify_workflow": args.qualify_workflow,
        "publish_workflow": args.publish_workflow,
        "framework": {"repository": args.framework_repository, "commit": args.framework_sha},
    }
    write_json(root / "hosting/github.json", cfg)
    print(f"Configured GitHub host link: {args.repository}")
    print(f"State path: {state_path}")
    print("NOTE: repository/node identity remains external to the semantic state commitment.")


def cmd_configure_from_network(args):
    import tomllib
    root = Path(args.path).resolve()
    network_path = Path(args.network).resolve()
    with network_path.open("rb") as f:
        net = tomllib.load(f)
    owner = (net.get("account") or {}).get("owner")
    fw = net.get("framework") or {}
    if not owner or not fw.get("repository") or not fw.get("ref"):
        raise SystemExit("network.toml must contain account.owner and framework.repository/ref")
    repo_name = args.repository
    candidates = []
    hub = net.get("hub") or {}
    if hub.get("repository"):
        candidates.append(hub.get("repository"))
    candidates.extend(c.get("name") for c in net.get("collections", []) if isinstance(c, dict) and c.get("name"))
    if repo_name not in candidates:
        raise SystemExit(f"Repository {repo_name!r} is not declared in network.toml; choices={candidates}")
    class A: pass
    a=A(); a.path=str(root); a.repository=f"{owner}/{repo_name}"; a.branch=(net.get("policy") or {}).get("default_branch","main")
    a.state_path=args.state_path; a.framework_repository=fw["repository"]; a.framework_sha=fw["ref"]
    a.qualify_workflow=args.qualify_workflow; a.publish_workflow=args.publish_workflow
    cmd_configure_github(a)
    print(f"Loaded host/framework settings from: {network_path}")


def _verify_host_repo_layout(repo_dir: Path):
    if not (repo_dir / ".git").exists():
        raise SystemExit(f"Target host checkout is not a Git repository: {repo_dir}")
    for rel in [".kristal/node.json", ".kristal/bindings/github.json"]:
        if not (repo_dir / rel).is_file():
            raise SystemExit(f"Target host checkout is not a bootstrapped Kristal node; missing {rel}")


def cmd_export_hosted(args):
    root = Path(args.path).resolve()
    cfg = _hosting_config(root)
    build = root / "build/v9"
    if not (build / "state-snapshot.json").is_file():
        raise SystemExit("No v9 build candidate. Run build-v9 first.")
    state = _verify_built_state(build)
    repo_dir = Path(args.repo_dir).resolve()
    _verify_host_repo_layout(repo_dir)
    state_path = _safe_repo_relative_path(cfg["state_path"])
    target = repo_dir / Path(state_path)
    source_bytes = (build / "state-snapshot.json").read_bytes()
    if target.exists() and target.read_bytes() != source_bytes and not args.force:
        raise SystemExit(f"Refusing to overwrite different hosted state: {target}; use --force only after review")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.read_bytes() != source_bytes:
        target.write_bytes(source_bytes)
        action = "exported"
    else:
        action = "unchanged"
    receipt = {
        "format": "kristal.authoring-host-export/1.0",
        "kit_version": KIT_VERSION,
        "repository": cfg["repository"],
        "branch": cfg["branch"],
        "state_path": state_path,
        "state": {"state_ref": state["state_ref"], "logical_commitment": state["logical_commitment"]},
        "snapshot_blob_digest": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
        "host_checkout": str(repo_dir),
        "note": "Operational export metadata; not part of the v9 logical state commitment.",
    }
    write_json(root / "build/v10/host-export.json", receipt)
    print(f"Hosted state {action}: {target}")
    print(f"State Logical Commitment: {state['logical_commitment']['digest']}")


def _run_external(argv: list[str], *, cwd: Path | None = None, capture: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        p = subprocess.run(argv, cwd=cwd, text=True, capture_output=capture)
    except FileNotFoundError:
        raise SystemExit(f"Required executable not found: {argv[0]}")
    if p.returncode:
        detail = ((p.stderr or "") + "\n" + (p.stdout or "")).strip()
        raise SystemExit(f"Command failed ({p.returncode}): {' '.join(argv)}\n{detail}")
    return p


def _gh_json(*args: str):
    p = _run_external(["gh", *args])
    text = (p.stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Expected JSON from gh {' '.join(args)}: {exc}\n{text}")


def _gh_text(*args: str) -> str:
    return (_run_external(["gh", *args]).stdout or "").strip()


def _remote_branch_sha(cfg: dict) -> str:
    return _gh_text("api", f"repos/{cfg['repository']}/commits/{cfg['branch']}", "--jq", ".sha")


def _remote_state_bytes(cfg: dict, sha: str) -> bytes:
    path = _safe_repo_relative_path(cfg["state_path"])
    obj = _gh_json("api", f"repos/{cfg['repository']}/contents/{path}?ref={sha}")
    if not isinstance(obj, dict) or obj.get("type") != "file" or not obj.get("content"):
        raise SystemExit(f"Hosted state file not found at {cfg['repository']}:{path}@{sha}")
    try:
        return base64.b64decode(str(obj["content"]).replace("\n", ""), validate=False)
    except Exception as exc:
        raise SystemExit(f"Unable to decode hosted state bytes: {exc}")


def _assert_remote_state_matches(root: Path, cfg: dict, sha: str):
    build = root / "build/v9/state-snapshot.json"
    if not build.is_file():
        raise SystemExit("No v9 build candidate. Run build-v9 first.")
    local = build.read_bytes()
    remote = _remote_state_bytes(cfg, sha)
    if local != remote:
        raise SystemExit("Remote state bytes do not match build/v9/state-snapshot.json. Run export-hosted, commit and push before qualification/publication.")


def cmd_github_status(args):
    root = Path(args.path).resolve(); cfg = _hosting_config(root)
    auth = _run_external(["gh", "auth", "status"])
    repo = _gh_json("api", f"repos/{cfg['repository']}")
    fw = _gh_json("api", f"repos/{cfg['framework']['repository']}/git/commits/{cfg['framework']['commit']}")
    branch_sha = _remote_branch_sha(cfg)
    result = {
        "authenticated": auth.returncode == 0,
        "repository": cfg["repository"],
        "visibility": (repo or {}).get("visibility") if isinstance(repo, dict) else None,
        "branch": cfg["branch"],
        "branch_sha": branch_sha,
        "framework": {"repository": cfg["framework"]["repository"], "commit": cfg["framework"]["commit"], "resolved": isinstance(fw, dict) and fw.get("sha") == cfg["framework"]["commit"]},
        "state_path": cfg["state_path"],
    }
    try:
        _assert_remote_state_matches(root, cfg, branch_sha)
        result["remote_state_matches_build"] = True
    except SystemExit as exc:
        result["remote_state_matches_build"] = False
        result["remote_state_diagnostic"] = str(exc)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def _workflow_runs(cfg: dict, workflow: str, sha: str, event: str | None = None) -> list[dict]:
    query = f"head_sha={sha}&per_page=50"
    if event:
        query += f"&event={event}"
    obj = _gh_json("api", f"repos/{cfg['repository']}/actions/workflows/{workflow}/runs?{query}")
    return list((obj or {}).get("workflow_runs", [])) if isinstance(obj, dict) else []


def _wait_new_workflow_run(cfg: dict, workflow: str, sha: str, event: str, before: set[str], attempts: int = 45) -> dict:
    for _ in range(attempts):
        for run in _workflow_runs(cfg, workflow, sha, event):
            if str(run.get("id")) not in before and run.get("head_sha") == sha:
                return run
        time.sleep(2)
    raise SystemExit(f"Timed out waiting for {workflow} on {sha}")


def _watch_run(cfg: dict, run_id: str):
    p = subprocess.run(["gh", "run", "watch", str(run_id), "--repo", cfg["repository"], "--exit-status"])
    if p.returncode:
        subprocess.run(["gh", "run", "view", str(run_id), "--repo", cfg["repository"], "--log-failed"])
        raise SystemExit(f"GitHub workflow run failed: {run_id}")


def cmd_github_qualify(args):
    print("NOTE: compatibility command. Prefer Kristal GitHub Setup/Bootstrap for network qualification.")
    root = Path(args.path).resolve(); cfg = _hosting_config(root)
    sha = _remote_branch_sha(cfg)
    _assert_remote_state_matches(root, cfg, sha)
    workflow = cfg["qualify_workflow"]
    before = {str(r.get("id")) for r in _workflow_runs(cfg, workflow, sha, "workflow_dispatch")}
    _run_external(["gh", "workflow", "run", workflow, "--repo", cfg["repository"], "--ref", cfg["branch"]])
    run = _wait_new_workflow_run(cfg, workflow, sha, "workflow_dispatch", before)
    run_id = str(run["id"])
    print(f"Qualification run: {run_id}")
    _watch_run(cfg, run_id)
    final = _gh_json("run", "view", run_id, "--repo", cfg["repository"], "--json", "databaseId,status,conclusion,headSha,url")
    if not isinstance(final, dict) or final.get("conclusion") != "success" or final.get("headSha") != sha:
        raise SystemExit("Qualification did not succeed for the exact expected commit")
    artifacts = _gh_json("api", f"repos/{cfg['repository']}/actions/runs/{run_id}/artifacts")
    expected = f"kristal-qualification-{sha}"
    receipt = next((a for a in (artifacts or {}).get("artifacts", []) if a.get("name") == expected), None)
    if not receipt:
        raise SystemExit(f"Qualification succeeded but expected receipt is missing: {expected}")
    record = {"format":"kristal.authoring-github-qualification/1.0","repository":cfg["repository"],"source_commit":sha,"run_id":run_id,"run_url":final.get("url"),"receipt":{"name":receipt.get("name"),"digest":receipt.get("digest")}}
    write_json(root / "build/v10/github-qualification.json", record)
    print(json.dumps(record, indent=2, ensure_ascii=False))


def _qualification_record(root: Path, cfg: dict, sha: str) -> dict:
    p = root / "build/v10/github-qualification.json"
    if not p.is_file():
        raise SystemExit("No exact-commit GitHub qualification receipt recorded. Run github-qualify first.")
    q = read_json(p)
    if q.get("repository") != cfg["repository"] or q.get("source_commit") != sha:
        raise SystemExit("Recorded qualification is for a different repository/commit. Run github-qualify again.")
    run_id = str(q.get("run_id", ""))
    artifacts = _gh_json("api", f"repos/{cfg['repository']}/actions/runs/{run_id}/artifacts")
    expected = f"kristal-qualification-{sha}"
    if not any(a.get("name") == expected for a in (artifacts or {}).get("artifacts", [])):
        raise SystemExit("Recorded qualification receipt is no longer available on GitHub")
    return q


def cmd_github_publish(args):
    print("NOTE: compatibility command. Prefer Kristal GitHub Setup/Bootstrap for publication and activation.")
    if not args.yes:
        raise SystemExit("Refusing hosted publication without --yes")
    root = Path(args.path).resolve(); cfg = _hosting_config(root)
    sha = _remote_branch_sha(cfg)
    _assert_remote_state_matches(root, cfg, sha)
    _qualification_record(root, cfg, sha)
    workflow = cfg["publish_workflow"]
    before = {str(r.get("id")) for r in _workflow_runs(cfg, workflow, sha, "workflow_dispatch")}
    _run_external(["gh", "workflow", "run", workflow, "--repo", cfg["repository"], "--ref", cfg["branch"], "-f", f"state_file={cfg['state_path']}"])
    run = _wait_new_workflow_run(cfg, workflow, sha, "workflow_dispatch", before)
    run_id = str(run["id"]); print(f"Publication run: {run_id}")
    _watch_run(cfg, run_id)
    final = _gh_json("run", "view", run_id, "--repo", cfg["repository"], "--json", "status,conclusion,headSha,url")
    if not isinstance(final, dict) or final.get("conclusion") != "success" or final.get("headSha") != sha:
        raise SystemExit("Publication did not succeed for the exact qualified commit")
    releases = _gh_json("api", f"repos/{cfg['repository']}/releases?per_page=50") or []
    release = next((r for r in releases if r.get("target_commitish") == sha and str(r.get("tag_name", "")).startswith("kristal-pub-") and not r.get("draft")), None)
    if not release:
        raise SystemExit("Publication workflow succeeded but no finalized Kristal Release was found for the exact commit")
    required = {"state-snapshot.json", "bundle-manifest.json", "publication.json"}
    names = {a.get("name") for a in release.get("assets", [])}
    missing = sorted(required - names)
    if missing:
        raise SystemExit(f"Publication Release is missing required assets: {missing}")
    independent = None
    if args.framework_path:
        fw_path = Path(args.framework_path).resolve()
        cli = fw_path / "reference/js/bin/kristal-ref.mjs"
        if not cli.is_file():
            raise SystemExit(f"Kristal reference CLI not found under framework path: {cli}")
        local_sha = _run_external(["git", "-C", str(fw_path), "rev-parse", "HEAD"]).stdout.strip()
        if local_sha != cfg["framework"]["commit"]:
            raise SystemExit(f"Local framework HEAD {local_sha} does not match pinned {cfg['framework']['commit']}")
        with tempfile.TemporaryDirectory(prefix="kristal-authoring-release-") as td:
            _run_external(["gh", "release", "download", release["tag_name"], "--repo", cfg["repository"], "--dir", td])
            _run_external(["node", str(cli), "verify-publication-bundle-v10", td])
        independent = True
    record = {"format":"kristal.authoring-github-publication/1.0","repository":cfg["repository"],"source_commit":sha,"run_id":run_id,"run_url":final.get("url"),"release":{"tag":release.get("tag_name"),"url":release.get("html_url"),"immutable":release.get("immutable"),"assets":sorted(names)},"independent_bundle_verification":independent}
    write_json(root / "build/v10/github-publication.json", record)
    print(json.dumps(record, indent=2, ensure_ascii=False))


# ---------- offline portable-AI read layer ----------

AI_GENERATED_FILES = (
    "AI_MANIFEST.json",
    "ai/CONTEXT.md",
    "ai/INDEX.json",
    "ai/GLOSSARY.md",
    "ai/RELATIONS.json",
    "ai/COVERAGE.json",
    "ai/QUESTIONS.md",
    "state/state-snapshot.json",
)


def _media_type(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".ndjson": "application/x-ndjson",
        ".csv": "text/csv",
        ".tsv": "text/tab-separated-values",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".xml": "application/xml",
        ".html": "text/html",
        ".htm": "text/html",
    }.get(ext, "application/octet-stream")


def _materialization_read_inventory(root: Path) -> dict:
    """Describe materialization descriptors and physical bytes useful to readers.

    The Git tree read surface carries manifests, while blob rows remain a separate
    host-transport inventory. A later hosting layer may choose Git, Releases, GHCR,
    LFS or another resolver without changing semantic identity. Remote bytes are
    never fetched here.
    """
    manifests = _discover_materialization_manifests(root)
    blobs: list[dict] = []
    local_blobs: dict[str, dict] = {}
    external_locators = 0
    missing_local_locators = 0
    unlocated = 0
    for manifest_path, doc in manifests:
        manifest_rel = manifest_path.relative_to(root).as_posix()
        source = doc.get("source") or {}
        rows = []
        for segment in doc.get("segments", []):
            if isinstance(segment, dict) and isinstance(segment.get("blob"), dict):
                rows.append(("segment", segment.get("segment_key"), segment["blob"]))
        for i, blob in enumerate(doc.get("dictionaries") or []):
            if isinstance(blob, dict):
                rows.append(("dictionary", str(i), blob))
        for kind, key, blob in rows:
            locator = blob.get("locator")
            row = {
                "manifest": manifest_rel,
                "source_artifact_id": source.get("artifact_id"),
                "kind": kind,
                "key": key,
                "media_type": blob.get("media_type"),
                "size": blob.get("size"),
                "sha256": blob.get("digest"),
                "locator": locator,
                "transport_class": "materialization",
            }
            if not locator:
                row["availability"] = "unlocated"
                unlocated += 1
            else:
                local = _safe_local_locator(root, locator)
                if local is None:
                    row["availability"] = "external"
                    external_locators += 1
                else:
                    rel = local.relative_to(root).as_posix()
                    row["path"] = rel
                    if local.is_file():
                        row["availability"] = "workspace_local"
                        row["verified_sha256"] = "sha256:" + hash_file(local)
                        row["verified_size"] = local.stat().st_size
                        local_blobs.setdefault(rel, {
                            "path": local,
                            "media_type": blob.get("media_type") or _media_type(local),
                            "declared_digest": blob.get("digest"),
                            "declared_size": blob.get("size"),
                        })
                    else:
                        row["availability"] = "workspace_missing"
                        missing_local_locators += 1
            blobs.append(row)
    blobs.sort(key=lambda x: (str(x.get("manifest", "")).encode("utf-8"), str(x.get("kind", "")).encode("utf-8"), str(x.get("key", "")).encode("utf-8")))
    return {
        "manifests": manifests,
        "blobs": blobs,
        "local_blobs": [local_blobs[k] for k in sorted(local_blobs, key=lambda x: x.encode("utf-8"))],
        "external_locator_count": external_locators,
        "missing_local_locator_count": missing_local_locators,
        "unlocated_blob_count": unlocated,
    }

def _portable_source_files(root: Path):
    """Files that help an offline/GitHub AI understand the Kristal.

    Operational GitHub/build/release/tooling data is deliberately excluded. The exact
    semantic State Snapshot is exposed separately under state/. Current v9
    Materialization Manifests and any workspace-local bytes they explicitly locate are
    included so a reader can bridge logical identity to available representations.
    """
    seen = set()
    roots = ["canon", "sources", "schemas", "docs", "projections/recipes", "projections/materialized", "derived/indexes", "derived/views", "derived/ai-contexts"]
    for base in roots:
        d = root / base
        if not d.exists():
            continue
        for p in sorted(d.rglob("*"), key=lambda q: q.relative_to(root).as_posix().encode("utf-8")):
            if p.is_file() and p.name not in {".gitkeep", "desktop.ini"}:
                rel = p.relative_to(root).as_posix()
                if rel not in seen:
                    seen.add(rel)
                    yield p
    inv = _materialization_read_inventory(root)
    for p, _doc in inv["manifests"]:
        rel = p.relative_to(root).as_posix()
        if rel not in seen:
            seen.add(rel)
            yield p


def _portable_role(rel: str) -> str:
    if rel == "canon/state.index.json":
        return "semantic_index"
    if rel.startswith("canon/"):
        return "canonical_content"
    if rel == "sources/source-catalog.json":
        return "provenance_catalog"
    if rel.startswith("sources/"):
        return "source_material"
    if rel.startswith("schemas/"):
        return "schema"
    if rel.startswith("docs/"):
        return "documentation"
    if rel.startswith("projections/recipes/"):
        return "projection_recipe"
    if rel.startswith("projections/materialized/"):
        return "derived_projection"
    if rel.startswith("derived/ai-contexts/"):
        return "authored_or_derived_ai_context"
    if rel.startswith("derived/indexes/"):
        return "derived_index"
    if rel.startswith("derived/views/"):
        return "derived_view"
    if (rel.startswith("materializations/v9/manifests/") or rel.startswith(".kristal/v9/materializations/")) and rel.endswith(".json"):
        return "materialization_manifest"
    if rel.startswith("materializations/") or rel.startswith(".kristal/v9/"):
        return "materialization_blob"
    return "supporting_content"


def _essential_context_section(path: Path, max_chars: int = 12000) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n\n[Section truncated in compact context; read the source file for the remainder.]\n"
    return text.strip()


def _build_portable_ai(root: Path) -> dict:
    ai_start = root / "AI_START_HERE.md"
    if not ai_start.is_file():
        ai_start.write_text(template_text("AI_START_HERE.md"), encoding="utf-8")
    (root / "ai").mkdir(parents=True, exist_ok=True)
    build = root / "build/v9"
    if not (build / "state-snapshot.json").is_file():
        raise SystemExit("No v9 State Snapshot available. Run build-v9 before build-ai/pack-ai.")
    state = _verify_built_state(build)
    ws = read_json(root / "kristal.workspace.json")
    idx = read_json(root / "canon/state.index.json")
    src = read_json(root / "sources/source-catalog.json")
    materialization_inventory = _materialization_read_inventory(root)

    ai_dir = root / "ai"
    state_dir = root / "state"
    ai_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    # The portable state is byte-for-byte identical to the deterministic v9 build.
    portable_state = state_dir / "state-snapshot.json"
    portable_state.write_bytes((build / "state-snapshot.json").read_bytes())

    canonical_by_path = {
        a.get("path"): a for a in idx.get("canonical_artifacts", [])
        if isinstance(a, dict) and isinstance(a.get("path"), str)
    }
    files = []
    for p in _portable_source_files(root):
        rel = p.relative_to(root).as_posix()
        if _safe_indexed_read_path(root, rel) is None:
            raise SystemExit(f"Unsafe portable source path: {rel}")
        entry = {
            "path": rel,
            "role": _portable_role(rel),
            "media_type": _media_type(p),
            "size": p.stat().st_size,
            "sha256": "sha256:" + hash_file(p),
        }
        a = canonical_by_path.get(rel)
        if a:
            entry["artifact_id"] = a.get("artifact_id")
            entry["logical_contract"] = a.get("logical_contract")
        files.append(entry)
    files.append({
        "path": "state/state-snapshot.json",
        "role": "state_snapshot",
        "media_type": "application/vnd.kristal.state-snapshot+json",
        "size": portable_state.stat().st_size,
        "sha256": "sha256:" + hash_file(portable_state),
        "state_ref": state.get("state_ref"),
        "logical_commitment": state.get("logical_commitment"),
    })
    files.sort(key=lambda x: x["path"].encode("utf-8"))
    ai_index = {
        "format": AI_INDEX_FORMAT,
        "state_ref": state["state_ref"],
        "state_logical_commitment": state["logical_commitment"],
        "files": files,
        "materialization_blobs": materialization_inventory["blobs"],
    }
    write_json(ai_dir / "INDEX.json", ai_index)

    external_refs = idx.get("external_references", [])
    coverage = {
        "format": AI_COVERAGE_FORMAT,
        "state_ref": state["state_ref"],
        "state_logical_commitment": state["logical_commitment"],
        "subject": ws.get("subject") or {},
        "semantic_ownership": ws.get("semantic_ownership") or {"owns": [], "does_not_own": []},
        "canonical_artifact_count": len(idx.get("canonical_artifacts", [])),
        "source_count": len(src.get("sources", [])),
        "external_reference_count": len(external_refs),
        "materialization_manifest_count": len(materialization_inventory["manifests"]),
        "local_materialization_blob_count": len(materialization_inventory["local_blobs"]),
        "external_materialization_locator_count": materialization_inventory["external_locator_count"],
        "missing_local_materialization_locator_count": materialization_inventory["missing_local_locator_count"],
        "unlocated_materialization_blob_count": materialization_inventory["unlocated_blob_count"],
        "semantic_closure": "self_contained" if not external_refs else "contains_pinned_external_references",
        "limitations": [
            "AI read-model files are derived navigation aids, not canonical knowledge.",
            "Absence from this package is not proof that a proposition is false.",
            "AI output is proposal-only unless separately accepted into the canon.",
        ],
    }
    write_json(ai_dir / "COVERAGE.json", coverage)

    relations = {
        "format": "kristal.ai-relations/1.0",
        "state_ref": state["state_ref"],
        "state_logical_commitment": state["logical_commitment"],
        "members": state.get("members", []),
        "external_references": state.get("references", []),
        "parents": state.get("parents", []),
    }
    write_json(ai_dir / "RELATIONS.json", relations)

    glossary_source = root / "docs/08_GLOSSARY.md"
    if glossary_source.is_file():
        glossary = glossary_source.read_text(encoding="utf-8")
    else:
        glossary = "# Glossary\n\nNo project-specific glossary has been authored. Use the native terminology in the canonical files and documentation; do not invent definitions.\n"
    (ai_dir / "GLOSSARY.md").write_text(glossary, encoding="utf-8", newline="\n")

    questions = f"""# Questions and navigation hints\n\nThis file is a derived aid for an AI reading **{ws.get('title', ws.get('slug', 'this Kristal'))}** offline.\n\nUseful first questions:\n\n- What is the stated purpose and semantic boundary of this Kristal?\n- Which files are canonical, and which are derived or explanatory?\n- What sources and authority declarations support a claim?\n- What does `ai/COVERAGE.json` say is owned, excluded, or externally referenced?\n- Which State Snapshot and Logical Commitment does this package represent?\n\nWhen answering substantive questions, prefer canonical content and provenance over this derived file.\n"""
    (ai_dir / "QUESTIONS.md").write_text(questions, encoding="utf-8", newline="\n")

    context_parts = [
        f"# AI Context — {ws.get('title', ws.get('slug', 'Kristal'))}",
        "",
        "This is a deterministic, derived orientation document for offline AI reading. It is not the canon.",
        "",
        f"- State ref: `{state['state_ref']}`",
        f"- State Logical Commitment: `{state['logical_commitment']['digest']}`",
        f"- Workspace profile: `{ws.get('profile')}`",
        f"- Native model: `{(ws.get('native_model') or {}).get('kind')}`",
        f"- Canonical artifacts: `{len(idx.get('canonical_artifacts', []))}`",
        f"- Sources: `{len(src.get('sources', []))}`",
        f"- External pinned references: `{len(external_refs)}`",
        f"- Materialization manifests: `{len(materialization_inventory['manifests'])}`",
        f"- Workspace-local materialization blobs: `{len(materialization_inventory['local_blobs'])}`",
        "",
        "## Reading rule",
        "",
        "Treat `canon/` and the exact `state/state-snapshot.json` as the semantic basis. Treat `ai/` as derived navigation. Use `sources/` for provenance. Materialization manifests describe physical representations and may point to local or external bytes without changing semantic identity. Do not require GitHub or any executable tool to read this package.",
    ]
    for rel in ["docs/00_INTENT_AND_SCOPE.md", "docs/01_SEMANTIC_BOUNDARY.md", "docs/02_NATIVE_MODEL.md", "docs/03_EPISTEMIC_MODEL.md", "docs/04_CANONICAL_DERIVED.md"]:
        body = _essential_context_section(root / rel)
        if body:
            context_parts.extend(["", f"---\n\n## Included orientation from `{rel}`\n", body])
    (ai_dir / "CONTEXT.md").write_text("\n".join(context_parts).rstrip() + "\n", encoding="utf-8", newline="\n")

    materialization_roots = []
    for manifest_path, _doc in materialization_inventory["manifests"]:
        rel = manifest_path.relative_to(root).as_posix()
        if rel.startswith("materializations/v9/manifests/"):
            base = "materializations/v9/manifests/"
        elif rel.startswith(".kristal/v9/materializations/"):
            base = ".kristal/v9/materializations/"
        else:
            base = str(Path(rel).parent).replace("\\", "/") + "/"
        if base not in materialization_roots:
            materialization_roots.append(base)
    read_order = [
        "AI_START_HERE.md",
        "AI_MANIFEST.json",
        "ai/CONTEXT.md",
        "ai/COVERAGE.json",
        "ai/GLOSSARY.md",
        "ai/INDEX.json",
        "canon/state.index.json",
        "sources/source-catalog.json",
    ] + materialization_roots

    manifest = {
        "format": PORTABLE_AI_FORMAT,
        "kit_version": KIT_VERSION,
        "title": ws.get("title"),
        "slug": ws.get("slug"),
        "languages": (ws.get("portable_ai") or {}).get("languages", []),
        "state_ref": state["state_ref"],
        "state_logical_commitment": state["logical_commitment"],
        "entrypoint": "AI_START_HERE.md",
        "read_order": read_order,
        "state_snapshot": "state/state-snapshot.json",
        "canonical_root": "canon/",
        "sources_root": "sources/",
        "documentation_root": "docs/",
        "ai_read_model_root": "ai/",
        "index": "ai/INDEX.json",
        "context": "ai/CONTEXT.md",
        "coverage": "ai/COVERAGE.json",
        "glossary": "ai/GLOSSARY.md",
        "relations": "ai/RELATIONS.json",
        "questions": "ai/QUESTIONS.md",
        "materializations": {
            "manifest_count": len(materialization_inventory["manifests"]),
            "local_blob_count": len(materialization_inventory["local_blobs"]),
            "external_locator_count": materialization_inventory["external_locator_count"],
            "missing_local_locator_count": materialization_inventory["missing_local_locator_count"],
            "unlocated_blob_count": materialization_inventory["unlocated_blob_count"],
            "indexed": True,
            "blob_transport": "host_policy",
        },
        "github_read_surface": {
            "contract": GITHUB_READ_SURFACE_FORMAT,
            "target_root_template": "kristals/<slug>/",
            "entrypoint": "AI_START_HERE.md",
            "note": "Operational projection only; never part of the v9 logical commitment.",
        },
        "portable_reading": {
            "offline": True,
            "github_required": False,
            "network_required": False,
            "python_required": False,
            "node_required": False,
            "executable_tools_required": False,
        },
        "external_dependencies": [
            {
                "kind": "pinned_semantic_reference",
                "reference": r,
            } for r in external_refs
        ],
        "rules": {
            "canonical_content": "canon/",
            "derived_ai_content_is_authoritative": False,
            "ai_output_is_canonical": False,
            "absence_implies_false": False,
        },
    }
    write_json(root / "AI_MANIFEST.json", manifest)
    return manifest


def cmd_build_ai(args):
    root = Path(args.path).resolve()
    manifest = _build_portable_ai(root)
    print(f"Built offline portable-AI read layer: {root / 'AI_MANIFEST.json'}")
    print(f"State Logical Commitment: {manifest['state_logical_commitment']['digest']}")
    print("Reading requires no GitHub, network access, Python, Node, or Kristal tooling.")


# Only these paths may be carried by the portable index into a hosted read surface.
# This is an operational transport boundary, not a change to the v9 canon.
_READ_SURFACE_INDEX_PREFIXES = (
    "canon/", "sources/", "schemas/", "docs/", "projections/recipes/",
    "projections/materialized/", "derived/indexes/", "derived/views/",
    "derived/ai-contexts/", "materializations/v9/manifests/",
    ".kristal/v9/materializations/",
)


def _safe_indexed_read_path(root: Path, rel: str) -> Path | None:
    """Never read or publish paths outside the allowed workspace read model.

    A SHA-256 in ai/INDEX.json does not authorize reading any arbitrary path.
    This check also rejects symlink escapes even if a path looks relative.
    """
    if not isinstance(rel, str) or not rel or "\\" in rel or rel.startswith("/"):
        return None
    parts = rel.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    if rel != "state/state-snapshot.json" and not rel.startswith(_READ_SURFACE_INDEX_PREFIXES):
        return None
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _check_portable_ai(root: Path) -> list[str]:
    errors = []
    manifest_path = root / "AI_MANIFEST.json"
    if not manifest_path.is_file():
        return ["AI_MANIFEST.json is missing; run build-v9 or build-ai"]
    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        return [f"Invalid AI_MANIFEST.json: {exc}"]
    if manifest.get("format") != PORTABLE_AI_FORMAT:
        errors.append(f"Unsupported portable AI manifest format: {manifest.get('format')!r}")
    reading = manifest.get("portable_reading") or {}
    expected_reading = {"offline": True, "github_required": False, "network_required": False, "python_required": False, "node_required": False, "executable_tools_required": False}
    for key, value in expected_reading.items():
        if reading.get(key) is not value:
            errors.append(f"portable_reading.{key} must be {value!r}")
    required_paths = {
        "entrypoint": "AI_START_HERE.md", "state_snapshot": "state/state-snapshot.json",
        "index": "ai/INDEX.json", "context": "ai/CONTEXT.md",
        "coverage": "ai/COVERAGE.json", "glossary": "ai/GLOSSARY.md",
        "relations": "ai/RELATIONS.json", "questions": "ai/QUESTIONS.md",
    }
    for key, rel in required_paths.items():
        if manifest.get(key) != rel:
            errors.append(f"Portable AI {key} must reference {rel}")
        if not (root / rel).is_file():
            errors.append(f"Portable AI required file missing: {rel!r}")
    index_path = root / "ai/INDEX.json"
    if index_path.is_file():
        try:
            index = read_json(index_path)
            indexed_files = index.get("files", [])
            if not isinstance(indexed_files, list):
                errors.append("AI index files must be an array")
                indexed_files = []
            seen_paths = set()
            for item in indexed_files:
                if not isinstance(item, dict):
                    errors.append("AI index file entry must be an object")
                    continue
                rel = item.get("path")
                target = _safe_indexed_read_path(root, rel)
                if target is None:
                    errors.append(f"Unsafe AI index path: {rel!r}")
                    continue
                if rel in seen_paths:
                    errors.append(f"Duplicate AI index path: {rel}")
                    continue
                seen_paths.add(rel)
                if not target.is_file():
                    errors.append(f"AI index file missing: {rel}")
                    continue
                expected_role = "state_snapshot" if rel == "state/state-snapshot.json" else _portable_role(rel)
                if item.get("role") != expected_role:
                    errors.append(f"AI index role mismatch: {rel}")
                if item.get("size") != target.stat().st_size:
                    errors.append(f"AI index size mismatch: {rel}")
                if item.get("sha256") != "sha256:" + hash_file(target):
                    errors.append(f"AI index digest mismatch: {rel}")
        except Exception as exc:
            errors.append(f"Invalid AI index: {exc}")
    try:
        idx = read_json(root / "canon/state.index.json")
        _manifests, mat_errors, _mat_warnings = _verify_materializations(root, idx)
        errors.extend(mat_errors)
    except Exception as exc:
        errors.append(f"Unable to validate portable materializations: {exc}")
    state_path = root / "state/state-snapshot.json"
    if state_path.is_file():
        try:
            state = read_json(state_path)
            actual = state_commitment(state)
            if state.get("logical_commitment") != actual:
                errors.append("Portable state snapshot has an invalid Logical Commitment")
            if manifest.get("state_logical_commitment") != actual:
                errors.append("AI manifest is not bound to the portable State Snapshot commitment")
        except Exception as exc:
            errors.append(f"Invalid portable State Snapshot: {exc}")
    return errors


def cmd_check_ai(args):
    root = Path(args.path).resolve()
    errors = _check_portable_ai(root)
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        raise SystemExit(1)
    print("OK: offline portable-AI read layer is complete and internally bound to the exact v9 State Snapshot.")


def _github_read_surface(root: Path) -> dict:
    """Return the exact derived file projection intended for GitHub/AI traversal.

    The projection is intentionally narrower than a full workspace mirror and wider
    than a state-only export. It is safe to regenerate and does not affect semantics.
    """
    root = root.resolve()
    ws_path = root / "kristal.workspace.json"
    ws = read_json(ws_path) if ws_path.is_file() else {}
    slug = str(ws.get("slug") or slugify(root.name))
    errors = _check_portable_ai(root) if (root / "AI_MANIFEST.json").is_file() else ["Portable AI read layer is missing; run build-ai first"]
    files: dict[str, dict] = {}

    def add_file(rel: str, role: str, *, media_type: str | None = None, sha256: str | None = None, size: int | None = None, trusted: bool = False):
        # The index is descriptive metadata, never an authority to read a file
        # outside the workspace or to alter its verified byte properties.
        indexed = (root / rel).resolve() if trusted else _safe_indexed_read_path(root, rel)
        try:
            indexed.relative_to(root)
        except (ValueError, TypeError, AttributeError):
            errors.append(f"Unsafe read surface path: {rel!r}")
            return
        if indexed is None or not indexed.is_file():
            return
        actual_size = indexed.stat().st_size
        actual_sha = "sha256:" + hash_file(indexed)
        if size is not None and size != actual_size:
            errors.append(f"Read surface size mismatch: {rel}")
            return
        if sha256 is not None and sha256 != actual_sha:
            errors.append(f"Read surface digest mismatch: {rel}")
            return
        files[rel] = {
            "path": rel,
            "role": role,
            "media_type": media_type or _media_type(indexed),
            "size": actual_size,
            "sha256": actual_sha,
        }

    for rel, role in [
        ("kristal.discovery.json", "reader_discovery"),
        ("derived/reader-inventory.json", "reader_inventory"),
        ("derived/reader-profile.json", "reader_profile"),
        ("README.md", "overview"),
        ("AGENTS.md", "ai_instructions"),
        ("AI_START_HERE.md", "ai_entrypoint"),
        ("AI_MANIFEST.json", "ai_manifest"),
        ("ai/CONTEXT.md", "ai_context"),
        ("ai/COVERAGE.json", "ai_coverage"),
        ("ai/GLOSSARY.md", "ai_glossary"),
        ("ai/INDEX.json", "ai_index"),
        ("ai/RELATIONS.json", "ai_relations"),
        ("ai/QUESTIONS.md", "ai_navigation"),
    ]:
        add_file(rel, role, trusted=True)

    manifest = None
    index = None
    try:
        if (root / "AI_MANIFEST.json").is_file():
            manifest = read_json(root / "AI_MANIFEST.json")
        if (root / "ai/INDEX.json").is_file():
            index = read_json(root / "ai/INDEX.json")
            for item in index.get("files", []):
                if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                    errors.append("Invalid AI index file entry")
                    continue
                if _safe_indexed_read_path(root, item["path"]) is None:
                    errors.append(f"Unsafe AI index path: {item['path']!r}")
                    continue
                add_file(
                    item["path"], item.get("role") or "indexed_content",
                    media_type=item.get("media_type"), sha256=item.get("sha256"), size=item.get("size"),
                )
    except Exception as exc:
        errors.append(f"Unable to read AI navigation metadata: {exc}")

    ordered = [files[k] for k in sorted(files, key=lambda x: x.encode("utf-8"))]
    materialization_objects = list((index or {}).get("materialization_blobs") or [])
    state_ref = (manifest or {}).get("state_ref")
    commitment = (manifest or {}).get("state_logical_commitment")
    projection = {
        "format": GITHUB_READ_SURFACE_FORMAT,
        "slug": slug,
        "state_ref": state_ref,
        "state_logical_commitment": commitment,
        "entrypoint": "AI_START_HERE.md",
        "files": [{"path": x["path"], "role": x["role"], "size": x["size"], "sha256": x["sha256"]} for x in ordered],
        "materialization_objects": materialization_objects,
    }
    surface_digest = "sha256:" + hashlib.sha256(canonicalize(projection).encode("utf-8")).hexdigest()
    return {
        "format": GITHUB_READ_SURFACE_FORMAT,
        "kit_version": KIT_VERSION,
        "slug": slug,
        "target_root": f"kristals/{slug}",
        "entrypoint": "AI_START_HERE.md",
        "state_ref": state_ref,
        "state_logical_commitment": commitment,
        "ready": not errors,
        "errors": errors,
        "surface_digest": surface_digest,
        "file_count": len(ordered),
        "total_bytes": sum(x["size"] for x in ordered),
        "files": ordered,
        "materialization_object_count": len(materialization_objects),
        "materialization_objects": materialization_objects,
        "note": "Derived GitHub/AI read projection. Materialization bytes are separate host-transport candidates; neither surface nor transport is a semantic commitment or publication.",
    }


def cmd_read_surface(args):
    root = Path(args.path).resolve()
    surface = _github_read_surface(root)
    print(json.dumps(surface, ensure_ascii=False, indent=None if args.compact else 2))
    if getattr(args, "require_ready", False) and not surface["ready"]:
        raise SystemExit(1)


def _portable_capsule_paths(root: Path):
    # Use the same exact reader projection as GitHub, plus the local workspace envelope
    # needed by offline tooling. This keeps pack-ai and GitHub traversal aligned.
    surface = _github_read_surface(root)
    seen = set()
    for item in surface.get("files", []):
        rel = item.get("path")
        if not isinstance(rel, str) or rel in seen:
            continue
        p = root / rel
        if p.is_file():
            seen.add(rel)
            yield p
    ws = root / "kristal.workspace.json"
    if ws.is_file() and "kristal.workspace.json" not in seen:
        yield ws


def cmd_pack_ai(args):
    root = Path(args.path).resolve()
    _build_portable_ai(root)
    errors = _check_portable_ai(root)
    if errors:
        raise SystemExit("Portable AI validation failed before packaging: " + "; ".join(errors))
    output = Path(args.output).resolve() if args.output else root.with_name(root.name + "-portable-ai.zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    fixed = (2020, 1, 1, 0, 0, 0)
    seen = set()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in _portable_capsule_paths(root):
            rel0 = p.relative_to(root).as_posix()
            if rel0 in seen:
                continue
            seen.add(rel0)
            rel = f"{root.name}/{rel0}"
            info = zipfile.ZipInfo(rel, fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 << 16)
            zf.writestr(info, p.read_bytes())
    print(f"Packed deterministic offline AI capsule: {output}")
    print("The capsule contains no GitHub/tooling dependency for reading.")


# ---------- validation ----------

def collect_json_errors(root: Path):
    errors = []
    for p in sorted(root.rglob("*.json")):
        try:
            read_json(p)
        except Exception as e:
            errors.append(f"Invalid JSON {p.relative_to(root)}: {e}")
    return errors


def _check_v3(root: Path, ws: dict, idx: dict, errors: list[str], warnings: list[str]):
    if ws.get("format") != FORMAT:
        errors.append(f"Unsupported workspace format: {ws.get('format')!r}")
    errors.extend(_classification_issues(ws.get("classification")))
    if ws.get("status") not in STATUSES:
        errors.append(f"Unknown lifecycle status: {ws.get('status')!r}")
    if not ws.get("slug"):
        errors.append("Workspace slug is empty")
    if not isinstance(ws.get("state_ref"), str) or not ws.get("state_ref"):
        errors.append("Workspace state_ref is required for v9")
    target = ws.get("target") or {}
    expected = {
        "portable_contract": "kristal_state/6.0",
        "semantic_baseline": "kristall/7.0",
        "query_baseline": "kristall/8.0",
        "state_architecture": "kristal.state/9.0",
        "hosted_network_baseline": HOSTED_NETWORK_BASELINE,
        "logical_commitment_profile": LOGICAL_PROFILE,
        "state_commitment_profile": STATE_PROFILE,
    }
    for k, v in expected.items():
        if target.get(k) != v:
            errors.append(f"target.{k} must be {v!r}, got {target.get(k)!r}")
    portable = ws.get("portable_ai") or {}
    if portable:
        if portable.get("profile") != PORTABLE_AI_FORMAT:
            errors.append(f"portable_ai.profile must be {PORTABLE_AI_FORMAT!r}")
        if portable.get("entrypoint") != "AI_START_HERE.md":
            errors.append("portable_ai.entrypoint must be AI_START_HERE.md")
        if portable.get("manifest") != "AI_MANIFEST.json":
            errors.append("portable_ai.manifest must be AI_MANIFEST.json")
        if portable.get("offline_first") is not True or portable.get("github_required_for_reading") is not False:
            errors.append("portable_ai must declare offline_first=true and github_required_for_reading=false")
        if portable.get("enabled") not in {True, False, None}:
            errors.append("portable_ai.enabled must be boolean when present")
    if idx.get("format") != STATE_INDEX_FORMAT:
        errors.append(f"Unsupported state index format: {idx.get('format')!r}")
    derived_roots = tuple(dict.fromkeys([str(x).rstrip("/") for x in ws.get("derived_paths", [])] + ["materializations"]))
    seen_ids, seen_paths = set(), set()
    for i, a in enumerate(idx.get("canonical_artifacts", [])):
        if not isinstance(a, dict):
            errors.append(f"canonical_artifacts[{i}] must be an object in authoring v2")
            continue
        aid, rel = a.get("artifact_id"), a.get("path")
        if not aid: errors.append(f"canonical_artifacts[{i}].artifact_id missing")
        elif aid in seen_ids: errors.append(f"Duplicate canonical artifact_id: {aid}")
        else: seen_ids.add(aid)
        if not rel: errors.append(f"canonical_artifacts[{i}].path missing")
        elif rel in seen_paths: errors.append(f"Duplicate canonical artifact path: {rel}")
        else: seen_paths.add(rel)
        if rel:
            if rel in {"kristal.discovery.json", "arketype.instance.json"} or any(rel == d or rel.startswith(d + "/") for d in derived_roots):
                errors.append(f"Derived path declared canonical: {rel}")
            if not (root / rel).is_file():
                errors.append(f"Declared canonical artifact does not exist: {rel}")
        contract = a.get("logical_contract") or {}
        if not contract.get("id") or not contract.get("version"):
            errors.append(f"Canonical artifact lacks logical_contract id/version: {aid or i}")
        commit = a.get("commitment") or {}
        mode = commit.get("mode")
        if mode == "compute-json-jcs":
            if commit.get("profile") != LOGICAL_PROFILE:
                errors.append(f"JSON artifact must use baseline profile {LOGICAL_PROFILE}: {aid}")
            if rel and (root / rel).suffix.lower() != ".json":
                errors.append(f"compute-json-jcs artifact is not JSON: {rel}")
        elif mode == "precomputed":
            if not _valid_commitment(commit):
                errors.append(f"precomputed commitment invalid: {aid}")
        else:
            errors.append(f"Unknown commitment mode for {aid}: {mode!r}")
    for i, ref in enumerate(idx.get("external_references", [])):
        if not isinstance(ref, dict) or not _valid_commitment(ref.get("logical_commitment")):
            errors.append(f"external_references[{i}] requires a valid logical_commitment")
        if "artifact_id" not in ref and "state_ref" not in ref:
            errors.append(f"external_references[{i}] requires artifact_id or state_ref")
        if "artifact_id" in ref:
            c = ref.get("logical_contract") or {}
            if not c.get("id") or not c.get("version"):
                errors.append(f"external artifact reference lacks logical_contract: {ref.get('artifact_id')}")


def cmd_check(args):
    root = Path(args.path).resolve()
    errors, warnings = [], []
    materialization_summary = None
    required = [
        "kristal.workspace.json", "README.md", "AGENTS.md", "sources/source-catalog.json",
        "canon/state.index.json", "docs/00_INTENT_AND_SCOPE.md", "docs/01_SEMANTIC_BOUNDARY.md",
        "docs/02_NATIVE_MODEL.md", "docs/03_EPISTEMIC_MODEL.md", "docs/04_CANONICAL_DERIVED.md",
        "docs/05_ORIENTATIONS.md", "docs/06_VALIDATION.md", "docs/07_HOSTING_AND_PUBLICATION.md",
    ]
    for rel in required:
        if not (root / rel).exists(): errors.append(f"Missing required workspace file: {rel}")
    errors.extend(collect_json_errors(root))
    if errors:
        for x in errors: print(f"ERROR: {x}")
        raise SystemExit(1)
    ws = read_json(root / "kristal.workspace.json")
    idx = read_json(root / "canon/state.index.json")
    if ws.get("format") in {LEGACY_FORMAT, V2_FORMAT, V3_FORMAT, V31_FORMAT}:
        errors.append(f"Legacy workspace detected ({ws.get('format')}). Run: kristal.py migrate-v10 <path>")
    else:
        _check_v3(root, ws, idx, errors, warnings)

    if not errors:
        try:
            _check_discovery(root, errors, warnings)
        except (ValueError, OSError) as exc:
            errors.append(f"Invalid reader discovery: {exc}")
    if not errors:
        try:
            manifests, mat_errors, mat_warnings = _verify_materializations(root, idx)
            errors.extend(mat_errors)
            warnings.extend(mat_warnings)
            if manifests:
                profiles = sorted({m.get("profile") for _, m in manifests if m.get("profile")})
                segmentation, factorization = _materialization_feature_flags(root, [m for _, m in manifests])
                materialization_summary = (
                    f"v9 materializations: {len(manifests)} manifest(s), profiles={profiles}, "
                    f"segmentation={segmentation}, factorization={factorization}"
                )
        except Exception as exc:
            errors.append(f"Unable to validate v9 materializations: {exc}")

    src = read_json(root / "sources/source-catalog.json")
    if src.get("format") != SOURCE_CATALOG_FORMAT:
        warnings.append(f"Source catalog format is {src.get('format')!r}; expected {SOURCE_CATALOG_FORMAT!r}")
    seen = set()
    for s in src.get("sources", []):
        sid = s.get("id")
        if not sid: errors.append("Source without id")
        elif sid in seen: errors.append(f"Duplicate source id: {sid}")
        else: seen.add(sid)

    for p in sorted((root / "projections/recipes").glob("*.json")):
        obj = read_json(p); ori = obj.get("orientation") or {}
        if obj.get("format") != PROJECTION_FORMAT: warnings.append(f"Legacy projection recipe format: {p.relative_to(root)}")
        if not ori.get("primary_axis"): errors.append(f"Projection missing primary_axis: {p.relative_to(root)}")
        sec = ori.get("secondary_axis")
        if isinstance(sec, list) and len(sec) > 1: errors.append(f"Projection has >1 secondary axis: {p.relative_to(root)}")
        if isinstance(sec, dict): errors.append(f"secondary_axis should be null/string, not object: {p.relative_to(root)}")

    canonical = idx.get("canonical_artifacts", [])
    if ws.get("status") == "released" and not canonical: errors.append("Released workspace has no declared canonical_artifacts")
    if ws.get("status") == "stub" and canonical: warnings.append("Stub workspace already declares canonical artifacts; verify lifecycle intent")
    if ws.get("native_model", {}).get("kind") == "undecided" and ws.get("status") in {"validated", "released"}:
        errors.append("Validated/released workspace still has native_model.kind=undecided")

    hosting = _hosting_config(root, required=False)
    if hosting is not None:
        errors.extend(_validate_github_hosting(hosting))

    built_state = root / "build/v9/state-snapshot.json"
    portable_enabled = bool((ws.get("portable_ai") or {}).get("enabled"))
    if built_state.is_file() and portable_enabled:
        ai_manifest = root / "AI_MANIFEST.json"
        if not ai_manifest.is_file():
            warnings.append("Portable AI is enabled but the read layer is missing; run build-ai")
        else:
            try:
                m = read_json(ai_manifest); st = read_json(built_state)
                if m.get("state_logical_commitment") != st.get("logical_commitment"):
                    warnings.append("Portable AI layer is stale relative to build/v9; run build-ai")
            except Exception as exc:
                warnings.append(f"Unable to inspect portable AI layer: {exc}")

    # Opt-in strict semantic graph profile. All historical v9/v10 workspaces
    # without a v11 profile retain their original validation behavior.
    profile_path = root / ".kristal/v11/authoring.json"
    if profile_path.is_file() and not errors:
        try:
            import kristal_v11_core as v11
            verified = v11.validate(root)
            print(f"OK: Framework v11 identity profile: {verified['graph_id']} ({verified['namespace_id']})")
        except (ValueError, OSError, ImportError, KeyError, TypeError) as exc:
            errors.append(f"v11 canonical identity validation failed: {exc}")

    for x in warnings: print(f"WARN: {x}")
    for x in errors: print(f"ERROR: {x}")
    if errors: raise SystemExit(1)
    print("OK: Local Kristal is structurally coherent: v9 semantic state + optional derived AI read layer + optional v10 hosting envelope.")
    if materialization_summary:
        print(f"INFO: {materialization_summary}")
    print("NOTE: this does not establish semantic truth or replace independent KristalDiag/framework qualification.")


def _local_state_candidates(root: Path) -> list[tuple[str, Path]]:
    """Return state candidates in the shared Local Kit/Manager/Kompiler precedence.

    This is an operational discovery convention only. It does not participate in
    any logical or state commitment.
    """
    rows: list[tuple[str, Path]] = [
        ("state_export", root / "state" / "state-snapshot.json"),
        ("build_v9", root / "build" / "v9" / "state-snapshot.json"),
        ("legacy_dot_kristal", root / ".kristal" / "v9" / "state-snapshot.json"),
        ("legacy_root", root / "state-snapshot.json"),
    ]
    legacy_dir = root / ".kristal" / "v9"
    if legacy_dir.is_dir():
        for q in sorted(legacy_dir.glob("*.state-snapshot.json"), key=lambda x: x.as_posix().encode("utf-8")):
            if q != root / ".kristal" / "v9" / "state-snapshot.json":
                rows.append(("legacy_dot_kristal", q))
    release_root = root / "release" / "v9" / "states"
    if release_root.is_dir():
        for q in sorted(release_root.glob("**/state-snapshot.json"), key=lambda x: x.as_posix().encode("utf-8"), reverse=True):
            rows.append(("local_release", q))
    return rows


def _valid_v9_snapshot_obj(obj) -> bool:
    return isinstance(obj, dict) and obj.get("schema_version") == "9.0" and obj.get("artifact_type") == "kristal_state_snapshot"


def inspect_local(root: Path) -> dict:
    """Build a read-only machine description for Manager/Kompiler/Setup interop."""
    root = root.resolve()
    ws_path = root / "kristal.workspace.json"
    ws = read_json(ws_path) if ws_path.is_file() else {}
    available = []
    selected = None
    for kind, path in _local_state_candidates(root):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
        row = {"kind": kind, "path": rel}
        try:
            obj = read_json(path)
            row["valid_v9_envelope"] = _valid_v9_snapshot_obj(obj)
            if _valid_v9_snapshot_obj(obj):
                row["state_ref"] = obj.get("state_ref")
                row["logical_commitment"] = obj.get("logical_commitment")
                if selected is None:
                    selected = {**row, "absolute_path": str(path.resolve())}
        except Exception as exc:
            row["valid_v9_envelope"] = False
            row["error"] = str(exc)
        available.append(row)
    slug = str(ws.get("slug") or slugify(root.name))
    portable = ws.get("portable_ai") if isinstance(ws.get("portable_ai"), dict) else {}
    materializations = _discover_materialization_manifests(root)
    materialization_docs = [m for _, m in materializations]
    segmentation, factorization = _materialization_feature_flags(root, materialization_docs)
    return {
        "format": LOCAL_INSPECTION_FORMAT,
        "kit_version": KIT_VERSION,
        "workspace": {
            "root": str(root),
            "format": ws.get("format"),
            "slug": slug,
            "title": ws.get("title"),
            "status": ws.get("status"),
            "declared_state_ref": ws.get("state_ref"),
        },
        "state": selected,
        "state_candidates": available,
        "portable_ai": {
            "enabled": bool(portable.get("enabled")),
            "profile": portable.get("profile"),
        },
        "materializations": {
            "manifest_count": len(materializations),
            "profiles": sorted({m.get("profile") for m in materialization_docs if m.get("profile")}, key=lambda s: s.encode("utf-8")),
            "segmentation": segmentation,
            "factorization": factorization,
        },
        "reader_discovery": read_json(root / "kristal.discovery.json") if (root / "kristal.discovery.json").is_file() else None,
        "github_read_surface": _github_read_surface(root),
        "interop": {
            "suggested_collection_root": f"kristals/{slug}",
            "suggested_collection_state_path": f"kristals/{slug}/state/state-snapshot.json",
            "suggested_channel_suffix": f"{slug}/stable",
            "backup_owner": "Kristal Manager (legacy compatibility label)",
            "github_sync_owner": "Kristal Manager",
            "network_lifecycle_owner": "Kristal GitHub Setup / Bootstrap",
            "reader": "Kompiler (optional)",
        },
    }


def cmd_inspect(args):
    root = Path(args.path).resolve()
    print(json.dumps(inspect_local(root), ensure_ascii=False, indent=None if args.compact else 2))


def cmd_status(args):
    root = Path(args.path).resolve(); ws = read_json(root / "kristal.workspace.json"); idx = read_json(root / "canon/state.index.json"); src = read_json(root / "sources/source-catalog.json")
    recipes = list((root / "projections/recipes").glob("*.json"))
    print(f"Title: {ws.get('title')}")
    print(f"Slug: {ws.get('slug')}")
    print(f"Status: {ws.get('status')}")
    print(f"State ref: {ws.get('state_ref')}")
    print(f"Profile: {ws.get('profile')}")
    print(f"Native model: {ws.get('native_model', {}).get('kind')}")
    if (root / "kristal.discovery.json").is_file():
        d = read_json(root / "kristal.discovery.json")
        print(f"Usage: {(d.get('classification') or {}).get('primary_usage') or (d.get('classification') or {}).get('usage_slug') or 'unspecified'}")
        print(f"Reader: {(d.get('reader') or {}).get('profile')}")
        print(f"Measured scale: {(d.get('size') or {}).get('class')} ({(d.get('size') or {}).get('tracked_local_bytes')} tracked local bytes)")
    print(f"Sources: {len(src.get('sources', []))}")
    print(f"Canonical Logical Artifacts: {len(idx.get('canonical_artifacts', []))}")
    print(f"Pinned external references: {len(idx.get('external_references', []))}")
    print(f"Projection recipes: {len(recipes)}")
    materializations = _discover_materialization_manifests(root)
    if materializations:
        docs = [m for _, m in materializations]
        segmentation, factorization = _materialization_feature_flags(root, docs)
        profiles = sorted({m.get("profile") for m in docs if m.get("profile")}, key=lambda s: s.encode("utf-8"))
        print(f"Materializations: {len(materializations)} manifest(s)")
        print(f"Materialization profiles: {', '.join(profiles)}")
        print(f"Physical optimization: segmentation={segmentation}, factorization={factorization}")
    else:
        print("Materializations: none registered/discovered (inline build fallback remains available)")
    inspection = inspect_local(root)
    selected = inspection.get("state")
    if selected:
        print(f"Current v9 state: {selected.get('path')} [{selected.get('kind')}]")
        print(f"Current state commitment: {(selected.get('logical_commitment') or {}).get('digest')}")
    else:
        print("Current v9 state: none")
    hosting = _hosting_config(root, required=False)
    if hosting:
        print(f"GitHub host: {hosting.get('repository')} @ {hosting.get('branch')}")
        print(f"Hosted state path: {hosting.get('state_path')}")
        print(f"Pinned framework: {(hosting.get('framework') or {}).get('repository')}@{(hosting.get('framework') or {}).get('commit')}")
    else:
        print("GitHub host: not configured")
    ai_manifest = root / "AI_MANIFEST.json"
    if ai_manifest.is_file():
        m = read_json(ai_manifest); print(f"Portable AI: {m.get('format')} @ {(m.get('state_logical_commitment') or {}).get('digest')}")
    else:
        print("Portable AI: not built")


# ---------- v9 build / publish / activate ----------

def _resolve_artifact_entry(root: Path, entry: dict):
    contract = entry["logical_contract"]
    commit_cfg = entry.get("commitment") or {}
    mode = commit_cfg.get("mode")
    ref = {"artifact_id": entry["artifact_id"], "logical_contract": dict(contract)}
    if entry.get("authority_ref"): ref["authority_ref"] = entry["authority_ref"]
    generated = None
    if mode == "compute-json-jcs":
        payload = read_json(root / entry["path"])
        generated = {
            "schema_version": "9.0", "artifact_type": "kristal_logical_artifact",
            "artifact_id": entry["artifact_id"], "logical_contract": dict(contract), "payload": payload,
        }
        if "scope" in entry: generated["scope"] = entry["scope"]
        if "extensions" in entry: generated["extensions"] = entry["extensions"]
        if entry.get("dependencies"): generated["dependencies"] = entry["dependencies"]
        if entry.get("authority_ref"): generated["authority_ref"] = entry["authority_ref"]
        generated["logical_commitment"] = logical_artifact_commitment(generated)
        ref["logical_commitment"] = dict(generated["logical_commitment"])
    elif mode == "precomputed":
        ref["logical_commitment"] = {"profile": commit_cfg["profile"], "digest": commit_cfg["digest"]}
    else:
        raise ValueError(f"Unsupported commitment mode for {entry.get('artifact_id')}: {mode}")
    return ref, generated


def _blob_descriptor(path: Path, media_type: str):
    return {"media_type": media_type, "digest": "sha256:" + hash_file(path), "size": path.stat().st_size}


def cmd_build_v9(args):
    root = Path(args.path).resolve()
    # Reuse the full workspace checks before building.
    class A: path = str(root)
    cmd_check(A())
    ws = read_json(root / "kristal.workspace.json"); idx = read_json(root / "canon/state.index.json")
    build = root / "build/v9"
    if build.exists(): shutil.rmtree(build)
    (build / "artifacts").mkdir(parents=True); (build / "materializations").mkdir(parents=True)
    members = []
    generated_count = 0
    emitted_profiles = set()
    for entry in idx.get("canonical_artifacts", []):
        ref, artifact = _resolve_artifact_entry(root, entry); members.append(ref)
        if artifact is not None:
            generated_count += 1
            name = _safe_name(entry["artifact_id"])
            ap = build / "artifacts" / f"{name}.logical-artifact.json"; write_json(ap, artifact)
            manifest = {
                "schema_version": "9.0", "artifact_type": "kristal_materialization_manifest",
                "materialization_id": f"urn:kristal:materialization:{ws['slug']}:{name}",
                "source": ref,
                "profile": "kristal.materialization/inline-json/1",
                "segments": [{"segment_key": "all", "record_count": 1, "blob": _blob_descriptor(ap, "application/vnd.kristal.logical-artifact+json")}],
                "reconstructability": {"lossless": True, "profile": f"{entry['logical_contract']['id']}/{entry['logical_contract']['version']}"},
            }
            write_json(build / "materializations" / f"{name}.materialization.json", manifest)
            emitted_profiles.add(manifest["profile"])
    imported_materializations = _discover_materialization_manifests(root)
    imported_docs = []
    for source_path, manifest in imported_materializations:
        imported_docs.append(manifest)
        materialization_id = manifest.get("materialization_id") or f"{manifest['source']['artifact_id']}::{manifest['profile']}"
        name = _safe_name(materialization_id)
        target = build / "materializations" / f"imported-{name}.materialization.json"
        write_json(target, manifest)
        emitted_profiles.add(manifest["profile"])
    state = {
        "schema_version": "9.0", "artifact_type": "kristal_state_snapshot", "state_ref": ws["state_ref"],
        "logical_commitment": {"profile": STATE_PROFILE, "digest": "sha256:" + "0" * 64},
        "members": members, "references": idx.get("external_references", []), "parents": [],
    }
    if ws.get("state_scope") is not None: state["scope"] = ws["state_scope"]
    if ws.get("authority_ref"): state["authority_ref"] = ws["authority_ref"]
    state["logical_commitment"] = state_commitment(state)
    write_json(build / "state-snapshot.json", state)
    segmentation, factorization = _materialization_feature_flags(root, imported_docs)
    caps = {
        "schema_version": "9.0", "artifact_type": "kristal_v9_capabilities",
        "compatibility": {"reads": ["kristal_state/6.0", "kristall/7.0", "kristall/8.0", "kristal.state/9.0"], "portable_state": "kristal_state/6.0", "semantic_baseline": "kristall/7.0", "query_baseline": "kristall/8.0"},
        "capabilities": {
            "state_architecture": {"logical_artifacts": True, "immutable_snapshots": True, "logical_commitments": True, "external_pinned_references": True},
            "materialization": {
                "profiles": sorted(emitted_profiles, key=lambda s: s.encode("utf-8")),
                "multiple_representations": True,
                "segmentation": segmentation,
                "factorization": factorization,
            },
            "lifecycle": {"build_publish_activate": True, "atomic_activation": True, "rollback": True},
        },
    }
    write_json(build / "v9-capabilities.json", caps)
    receipt = {
        "format": "kristal.local-build-receipt/3.2.0", "kit_version": KIT_VERSION,
        "workspace_format": ws["format"], "state_ref": ws["state_ref"], "state_logical_commitment": state["logical_commitment"],
        "generated_logical_artifacts": generated_count,
        "precomputed_logical_artifacts": len(members) - generated_count,
        "imported_materialization_manifests": len(imported_materializations),
        "materialization_profiles": sorted(emitted_profiles, key=lambda s: s.encode("utf-8")),
        "materialization_features": {"segmentation": segmentation, "factorization": factorization},
        "note": "Build receipt is operational metadata and is not part of the state logical commitment.",
    }
    write_json(build / "build-receipt.json", receipt)
    _write_discovery(root)
    with_ai = bool(getattr(args, "with_ai", False) or (ws.get("portable_ai") or {}).get("enabled", False))
    if with_ai:
        _build_portable_ai(root)
    print(f"Built v9 candidate: {build}")
    if with_ai:
        print(f"Built optional offline portable-AI read layer: {root / 'AI_MANIFEST.json'}")
    else:
        print("AI read layer not built (optional). Use build-ai or build-v9 --with-ai when needed.")
    print(f"State Logical Commitment: {state['logical_commitment']['digest']}")
    print(f"Logical Artifacts: {len(members)} ({generated_count} computed, {len(members)-generated_count} precomputed)")
    if imported_materializations:
        print(f"Preserved v9 materializations: {len(imported_materializations)} manifest(s), profiles={sorted(emitted_profiles)}")


def _verify_built_state(build: Path):
    state = read_json(build / "state-snapshot.json")
    actual = state_commitment(state)
    if state.get("logical_commitment") != actual:
        raise SystemExit(f"Built state commitment mismatch: declared={state.get('logical_commitment')} actual={actual}")
    for p in (build / "artifacts").glob("*.json"):
        a = read_json(p); actual_a = logical_artifact_commitment(a)
        if a.get("logical_commitment") != actual_a:
            raise SystemExit(f"Logical artifact commitment mismatch: {p.name}")
    return state


def _snapshot_blob_digest(build: Path) -> str:
    return "sha256:" + hash_file(build / "state-snapshot.json")


def cmd_publish_v9(args):
    root = Path(args.path).resolve(); build = root / "build/v9"
    if not (build / "state-snapshot.json").is_file(): raise SystemExit("No v9 build candidate. Run build-v9 first.")
    state = _verify_built_state(build)
    logical = state["logical_commitment"]["digest"].split(":", 1)[1]
    blob = _snapshot_blob_digest(build).split(":", 1)[1]
    # Physical publication is keyed by both logical content and snapshot bytes:
    # LOGICAL COMMITMENT != BLOB DIGEST. Multiple attestations/representations
    # may therefore coexist without pretending to be different logical states.
    target = root / "release/v9/states" / logical / blob
    if target.exists():
        existing = target / "state-snapshot.json"
        if not existing.is_file() or existing.read_bytes() != (build / "state-snapshot.json").read_bytes():
            raise SystemExit(f"Immutable release collision at {target}")
        print(f"Already published: {target}"); return
    tmp = target.with_name(target.name + f".tmp-{os.getpid()}")
    if tmp.exists(): shutil.rmtree(tmp)
    shutil.copytree(build, tmp)
    target.parent.mkdir(parents=True, exist_ok=True); os.replace(tmp, target)
    print(f"Published immutable v9 state: {target}")
    print(f"Snapshot Blob Digest: sha256:{blob}")


def _resolve_release_dir(states: Path, logical: str, blob: str | None):
    logical_dir = states / logical
    if blob:
        candidate = logical_dir / blob.removeprefix("sha256:")
        return candidate
    if not logical_dir.is_dir(): return logical_dir
    variants = sorted(p for p in logical_dir.iterdir() if p.is_dir() and (p / "state-snapshot.json").is_file())
    if len(variants) == 1: return variants[0]
    if len(variants) > 1: raise SystemExit("Multiple physical snapshots share this Logical Commitment; specify --blob-digest")
    return logical_dir


def cmd_activate_v9(args):
    root = Path(args.path).resolve(); channel = slugify(args.channel); states = root / "release/v9/states"
    if args.digest:
        logical = args.digest.removeprefix("sha256:")
        if not HEX64.fullmatch(logical): raise SystemExit("--digest must be sha256:<64hex> or 64hex")
        release_dir = _resolve_release_dir(states, logical, args.blob_digest)
    else:
        build = root / "build/v9"; build_state = _verify_built_state(build)
        logical = build_state["logical_commitment"]["digest"].split(":",1)[1]
        blob = _snapshot_blob_digest(build).split(":",1)[1]
        release_dir = _resolve_release_dir(states, logical, blob)
    if not (release_dir / "state-snapshot.json").is_file(): raise SystemExit(f"State not published: {release_dir}")
    state = read_json(release_dir / "state-snapshot.json")
    blob_digest = "sha256:" + hash_file(release_dir / "state-snapshot.json")
    pointer = root / "release/v9/channels" / f"{channel}.activation.json"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    lock = pointer.with_suffix(pointer.suffix + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit(f"Activation lock busy: {lock}")
    try:
        os.write(fd, str(os.getpid()).encode("ascii")); os.fsync(fd)
        previous = read_json(pointer) if pointer.is_file() else None
        active_ref = {"state_ref": state["state_ref"], "logical_commitment": state["logical_commitment"]}
        activation = {"schema_version":"9.0","artifact_type":"kristal_activation","channel_id":channel,"active_state":active_ref,"sequence": int((previous or {}).get("sequence",0))+1,
                      "extensions":{"authoring_snapshot_blob_digest": blob_digest}}
        if previous:
            activation["previous_state"] = previous["active_state"]
            activation["expected_previous"] = previous["active_state"]
        tmp = pointer.with_name(pointer.name + f".tmp-{os.getpid()}")
        try:
            write_json(tmp, activation)
            with tmp.open("rb") as f: os.fsync(f.fileno())
            os.replace(tmp, pointer)
        finally:
            if tmp.exists(): tmp.unlink()
    finally:
        os.close(fd)
        try: lock.unlink()
        except FileNotFoundError: pass
    print(f"Activated {state['logical_commitment']['digest']} / {blob_digest} on channel {channel} (sequence {activation['sequence']})")


def cmd_qualify_v9(args):
    root = Path(args.path).resolve(); target = root / (args.target or "build/v9")
    exe = shutil.which("kristaldiag")
    if not exe:
        raise SystemExit("KristalDiag not found on PATH. Install/connect the independent examiner, then rerun qualify-v9.")
    cmd = [exe, "conform", str(target), "--profile", args.profile]
    print("Running independent qualification:", " ".join(cmd))
    raise SystemExit(subprocess.run(cmd).returncode)


# ---------- deterministic local manifest / package ----------

def cmd_hash_manifest(args):
    root = Path(args.path).resolve(); output = root / "validation/manifest.sha256.json"; entries = []
    for p in sorted(root.rglob("*")):
        if not p.is_file(): continue
        rel = p.relative_to(root).as_posix()
        if rel == "validation/manifest.sha256.json" or rel.endswith(".zip"): continue
        entries.append({"path": rel, "sha256": hash_file(p), "size": p.stat().st_size})
    obj = {"format": HASH_MANIFEST_FORMAT, "algorithm": "sha256", "workspace_format": read_json(root / "kristal.workspace.json").get("format"), "files": entries}
    write_json(output, obj); print(f"Wrote deterministic {output} ({len(entries)} files)")


def cmd_pack(args):
    root = Path(args.path).resolve()
    output = Path(args.output).resolve() if args.output else root.with_suffix(".zip"); output.parent.mkdir(parents=True, exist_ok=True)
    fixed = (2020, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.resolve() == output: continue
            rel = f"{root.name}/{p.relative_to(root).as_posix()}"; info = zipfile.ZipInfo(rel, fixed); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = (p.stat().st_mode & 0xFFFF) << 16; zf.writestr(info, p.read_bytes())
    print(f"Packed deterministic archive: {output}")


# ---------- strict v11 semantic authoring (opt-in) ----------

def _v11_core():
    import kristal_v11_core as v11
    return v11


def cmd_v11_enable(args):
    """Activate only after the exact registered canonical inputs already validate."""
    root = Path(args.path).resolve()
    v11 = _v11_core()
    config = {"format": "kristal.authoring-v11-profile/1.0",
              "semantic_profile": v11.PROFILE,
              "registry": args.registry, "graph": args.graph,
              "crosswalk": args.crosswalk, "catalog": args.catalog}
    profile_file = root / v11.CONFIG
    if profile_file.exists():
        raise SystemExit('v11 profile already exists; refusing to overwrite versioned configuration')
    try:
        for rel in (args.registry, args.graph, args.crosswalk, args.catalog):
            v11.safe(root, rel)
        data = v11.validate(root, config)
    except (v11.V11Error, ValueError, OSError) as exc:
        raise SystemExit(f'v11 enable failed; no profile changed: {exc}') from exc
    profile_file.parent.mkdir(parents=True, exist_ok=True)
    write_json(profile_file, config)
    module = Path(__file__).resolve().parent / 'kristal_v11_core.py'
    if module.is_file() and module.resolve() != (root / 'tools/kristal_v11_core.py').resolve():
        shutil.copy2(module, root / 'tools/kristal_v11_core.py')
    print(f"Enabled strict v11 semantics: {data['graph_id']} / {data['namespace_id']}")
    print('The v9 commitments remain unchanged until a deliberate new build.')


def cmd_v11_check(args):
    root = Path(args.path).resolve();v11 = _v11_core()
    try:info = v11.validate(root)
    except (v11.V11Error,ValueError,OSError,KeyError,TypeError) as exc:
        raise SystemExit(f'v11 check failed: {exc}') from exc
    print(json.dumps({k:v for k,v in info.items() if k not in ('languages','lexical_terms','files')},ensure_ascii=False,indent=2))


def cmd_v11_coverage(args):
    root = Path(args.path).resolve();v11 = _v11_core()
    try:
        report = v11.coverage(root, locales=args.locales.split(',') if args.locales else None)
        if args.output:
            output = v11.safe(root, args.output, exists=False)
            if output.exists():raise v11.V11Error('coverage output exists; do not overwrite a previous report')
            must_under=(root/'derived').resolve()
            if not output.is_relative_to(must_under):raise v11.V11Error('coverage output must stay under derived/')
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
            print(f'v11 coverage report written: {output}')
        else:print(json.dumps(report,ensure_ascii=False,indent=2))
    except (v11.V11Error,ValueError,OSError,KeyError,TypeError) as exc:
        raise SystemExit(f'v11 coverage failed: {exc}') from exc


def _v11_plan_input(root,args):
    v11=_v11_core();config=v11.load_profile(root)
    if config is None:raise v11.V11Error('enable-v11 before checking or applying migration plans')
    data=v11.validate(root)
    src=v11.safe(root,args.source);plan=v11.read(v11.safe(root,args.plan))
    registry=v11.read(data['files']['registry'])
    role_map=None
    if getattr(args,'roles',None):
        roles=v11.read(v11.safe(root,args.roles))
        v11.must(roles.get('format')=='kristal.identity-role-map/11.0' and roles.get('source_sha256')==v11.digest(src), 'identity roles manifest must match source digest')
        rev=roles.get('review',{})
        v11.must(all(rev.get(k) for k in ('decision_id','reviewer','reason')),'identity roles manifest lacks explicit reviewer')
        v11.must(bool(rev.get('evidence_refs')) and all(v11.registry_check(v11.read(data['files']['registry']))[1].get(ref)=='source' for ref in rev['evidence_refs']), 'identity roles manifest needs registered KS evidence')
        role_map={}
        for row in roles.get('roles',[]):
            pointer=row['path'];v11.must(pointer not in role_map and row['role'] in ('entity','property'), 'duplicate/bad identity role')
            role_map[pointer]=row['role']
    return v11, data, src, plan, registry, role_map


def cmd_v11_select_graph(args):
    """Explicitly switch the active graph pointer after separate registration/review."""
    root=Path(args.path).resolve();v11=_v11_core()
    try:
        config=v11.load_profile(root)
        v11._assert_no_pending(root)
        v11.must(config is not None,'v11 profile not enabled')
        v11.must(args.graph != config['graph'],'graph is already active')
        newconfig=dict(config);newconfig['graph']=args.graph
        data=v11.validate(root,newconfig)
        profile_path=root/v11.CONFIG
        old_bytes=profile_path.read_bytes()
        archive=root/'.kristal/v11/history'
        archive.mkdir(parents=True,exist_ok=True)
        old_digest=hashlib.sha256(old_bytes).hexdigest()
        history_file=archive/f'{old_digest}.json'
        if not history_file.exists():
            with history_file.open('xb') as f:f.write(old_bytes)
        tmp=profile_path.with_name('authoring.json.new')
        if tmp.exists():raise v11.V11Error('stale temporary profile exists')
        try:
            with tmp.open('x',encoding='utf8') as f:json.dump(newconfig,f,ensure_ascii=False,indent=2);f.write('\n')
            os.replace(tmp,profile_path)
        finally:
            tmp.unlink(missing_ok=True)
        print(f'Selected reviewed v11 graph: {data["graph_id"]}; old profile retained by digest in .kristal/v11/history')
        print('Run check and build-v9 to create a deliberate new state; publication/activation remain separate.')
    except (ValueError,KeyError,TypeError,OSError) as exc:
        raise SystemExit(f'v11 graph selection refused: {exc}') from exc


def cmd_v11_plan_check(args):
    root=Path(args.path).resolve()
    try:
        v11,data,src,plan,registry,roles=_v11_plan_input(root,args)
        result=v11.plan_verify(plan,src,registry,roles,require_approved=False)
        print(json.dumps({'plan_id':plan['plan_id'],'proposed_operation_count':len(plan['operations']),
          'source_digest_verified':True,'source_preserved':True,
          'output_is_executable':False,'target_shape':'not_a_complete_migration_without_v11_graph_validation'},indent=2))
    except (ValueError,KeyError,TypeError,OSError) as exc:
        raise SystemExit(f'v11 plan invalid: {exc}') from exc


def cmd_v11_apply_plan(args):
    root=Path(args.path).resolve()
    try:
        v11,data,src,plan,registry,roles=_v11_plan_input(root,args)
        v11.must(roles is not None,'--roles reviewed identity paths are mandatory for canonical migration')
        new=v11.plan_verify(plan,src,registry,roles)
        # A generic legacy JSON file cannot become canonical merely because
        # its words changed. Only a *complete* v11-shaped graph is writable.
        ns,ids=v11.registry_check(registry)
        v11.graph_check(new,ns,ids)
        output=v11.safe(root,args.output,exists=False)
        canon=(root/'canon/domain').resolve()
        v11.must(output.is_relative_to(canon) and output.suffix=='.json','new graph must be a fresh canon/domain/*.json path')
        v11.must(not output.exists(),'migration output already exists')
        v11.must(output!=src,'cannot overwrite source')
        idx_path=root/'canon/state.index.json';idx=read_json(idx_path)
        entries=idx.get('canonical_artifacts',[])
        rel=output.relative_to(root).as_posix()
        v11.must(all(x.get('artifact_id')!=args.artifact_id and x.get('path')!=rel for x in entries if isinstance(x,dict)), 'artifact ID/path already registered')
        v11.must(bool(args.artifact_id) and bool(args.contract_id), 'new artifact identity and contract required')
        # Double-check the source immediately before writing; never overwrite.
        v11.must(v11.digest(src)==plan['source']['sha256'],'source changed since validation')
        v11.register_artifact_recoverably(root,rel=rel,payload=(json.dumps(new,ensure_ascii=False,indent=2)+'\n').encode('utf8'),
            artifact_id=args.artifact_id,contract_id=args.contract_id)
        print('Converted graph registered as NEW v11 canonical artifact; source unchanged.')
        print('Run check and build-v9 deliberately to create new v9 commitments. Publication/activation remain separate.')
    except (ValueError,KeyError,TypeError,OSError) as exc:
        raise SystemExit(f'v11 plan application refused: {exc}') from exc


def cmd_v11_import_dik(args):
    root=Path(args.path).resolve();v11=_v11_core()
    try:
        result=v11.build_dik_catalog_revision(root,args.catalog,args.revision)
        # A diK import is not a signed approval; register only a new candidate.
        if args.register:
            v11.must(bool(args.artifact_id) and bool(args.contract_id),'--artifact-id and --contract-id required with --register')
            result['transaction']=v11.register_artifact_recoverably(root,
                rel=result['catalog'], payload=(root/result['catalog']).read_bytes(),
                artifact_id=args.artifact_id, contract_id=args.contract_id,allow_existing=True)
            result['registered']=True
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (v11.V11Error,ValueError,KeyError,TypeError,OSError) as exc:
        raise SystemExit(f'diK catalog import refused: {exc}') from exc


def cmd_v11_select_catalog(args):
    root=Path(args.path).resolve();v11=_v11_core()
    try:
        v11._assert_no_pending(root)
        config=v11.load_profile(root)
        v11.must(config is not None,'v11 profile missing')
        v11.must(args.catalog!=config['catalog'],'catalog already selected')
        candidate=dict(config,catalog=args.catalog)
        result=v11.validate(root,candidate)
        # A single-file os.replace preserves the previous profile on power loss.
        profile=root/v11.CONFIG;previous=profile.read_bytes()
        history=root/'.kristal/v11/history';history.mkdir(parents=True,exist_ok=True)
        backup=history/(hashlib.sha256(previous).hexdigest()+'.json')
        if not backup.exists():
            try:v11._write_exclusive_synced(backup,previous)
            except FileExistsError:pass
        v11._replace_synced(profile,v11._json_bytes(candidate))
        print(json.dumps({'selected':args.catalog,'catalog_id':result['catalog_id'],
            'previous_profile_sha256':hashlib.sha256(previous).hexdigest(),
            'requires_explicit_build_v9':True},indent=2))
    except (v11.V11Error,ValueError,KeyError,TypeError,OSError) as exc:
        raise SystemExit(f'v11 catalog selection refused: {exc}') from exc


def cmd_v11_recover(args):
    v11=_v11_core()
    try:print(json.dumps(v11.recover_v11(args.path,mode=args.mode),indent=2))
    except (v11.V11Error,ValueError,KeyError,TypeError,OSError) as exc:
        raise SystemExit(f'v11 recovery refused: {exc}') from exc


def cmd_v11_qualify(args):
    """Optional offline qualification via the authoritative pinned Framework draft.3.

    Only this qualification operation needs jsonschema; routine local authoring
    remains Python standard-library-only. Never modifies a workspace.
    """
    script=Path(__file__).resolve().parents[1]/'scripts/qualify_framework_v11.py'
    if not script.is_file():
        raise SystemExit('qualify-v11 requires the full Authoring Kit checkout, not a copied workspace-only tool')
    cmd=[sys.executable,str(script),'--project',str(Path(args.path).resolve()),
         '--framework',str(Path(args.framework).resolve())]
    if args.integration_pack:cmd+=['--integration-pack',str(Path(args.integration_pack).resolve())]
    if args.locales:cmd+=['--locales',args.locales]
    result=subprocess.run(cmd,check=False)
    if result.returncode:raise SystemExit(result.returncode)


def build_parser():
    p = argparse.ArgumentParser(prog="kristal.py", description="Kristal Local utilities: v9 semantic state + optional AI read layer + optional v10 hosted-network integration")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init", help="create a normalized Local Kristal workspace (v9 semantic state; AI and hosting optional)"); s.add_argument("path"); s.add_argument("--slug"); s.add_argument("--title"); s.add_argument("--profile", default="open", choices=sorted(PROFILES)); s.add_argument("--with-ai", action="store_true", help="also seed the optional portable-AI read layer"); s.add_argument("--force", action="store_true"); s.set_defaults(func=cmd_init)
    s = sub.add_parser("build-discovery", help="regenerate deterministic noncanonical discovery/size/reader metadata"); s.add_argument("path"); s.set_defaults(func=cmd_build_discovery)
    s = sub.add_parser("audit-discovery", help="read-only non-authoritative consumer preflight for Manager/Konstellation"); s.add_argument("path"); s.add_argument("--compact", action="store_true"); s.add_argument("--require-fresh", action="store_true"); s.set_defaults(func=cmd_audit_discovery)
    s = sub.add_parser("classify", help="declare Arketype classification (optionally resolve a local Arketype 1.4 catalog)"); s.add_argument("path"); s.add_argument("--arketype-dir"); s.add_argument("--usage"); s.add_argument("--archetype"); s.add_argument("--arketype-version"); s.add_argument("--family"); s.add_argument("--domain"); s.add_argument("--organization", choices=["single", "collection", "federation", "hybrid", "unknown"]); s.set_defaults(func=cmd_classify)
    s = sub.add_parser("migrate-v9", help="compatibility alias: migrate legacy workspace to current v10 Local workspace envelope"); s.add_argument("path"); s.set_defaults(func=cmd_migrate_v9)
    s = sub.add_parser("migrate-v10", help="migrate legacy workspace to Local Kristal v3.2 alignment"); s.add_argument("path"); s.set_defaults(func=cmd_migrate_v10)
    s = sub.add_parser("add-source", help="append a source"); s.add_argument("path"); s.add_argument("--id", required=True); s.add_argument("--title", required=True); s.add_argument("--kind", default="document"); s.add_argument("--locator", required=True); s.add_argument("--version-or-date"); s.add_argument("--sha256"); s.add_argument("--authority-scope"); s.add_argument("--trust-class"); s.add_argument("--notes"); s.set_defaults(func=cmd_add_source)
    s = sub.add_parser("new-projection", help="create a portable projection recipe stub"); s.add_argument("path"); s.add_argument("--slug", required=True); s.add_argument("--subject-ref", required=True); s.add_argument("--primary-axis", required=True); s.add_argument("--secondary-axis"); s.add_argument("--force", action="store_true"); s.set_defaults(func=cmd_new_projection)
    s = sub.add_parser("register-artifact", help="register an existing canonical file as a v9 Logical Artifact"); s.add_argument("path"); s.add_argument("--file", required=True); s.add_argument("--artifact-id", required=True); s.add_argument("--contract-id", required=True); s.add_argument("--contract-version", default="1.0"); s.add_argument("--mode", choices=["compute-json-jcs","precomputed"], default="compute-json-jcs"); s.add_argument("--commitment-profile", default=LOGICAL_PROFILE); s.add_argument("--digest"); s.add_argument("--authority-ref"); s.set_defaults(func=cmd_register_artifact)
    s = sub.add_parser("register-materialization", help="register/preserve an existing v9 Materialization Manifest without changing logical identity"); s.add_argument("path"); s.add_argument("--manifest", required=True); s.add_argument("--force", action="store_true"); s.set_defaults(func=cmd_register_materialization)
    s = sub.add_parser("add-reference", help="add a pinned external artifact/state reference"); s.add_argument("path"); s.add_argument("--kind", choices=["artifact","state"], required=True); s.add_argument("--id", required=True); s.add_argument("--digest", required=True); s.add_argument("--commitment-profile"); s.add_argument("--contract-id"); s.add_argument("--contract-version"); s.add_argument("--authority-ref"); s.set_defaults(func=cmd_add_reference)
    s = sub.add_parser("check", help="validate Local Kristal envelope and v9 registration"); s.add_argument("path"); s.set_defaults(func=cmd_check)
    s = sub.add_parser("status", help="print concise workspace status"); s.add_argument("path"); s.set_defaults(func=cmd_status)
    s = sub.add_parser("inspect", help="emit read-only machine JSON for Manager/Kompiler/Setup interop"); s.add_argument("path"); s.add_argument("--compact", action="store_true"); s.set_defaults(func=cmd_inspect)
    s = sub.add_parser("read-surface", help="emit the exact derived GitHub/AI read surface for Manager sync"); s.add_argument("path"); s.add_argument("--compact", action="store_true"); s.add_argument("--require-ready", action="store_true"); s.set_defaults(func=cmd_read_surface)
    s = sub.add_parser("build-v9", help="build deterministic v9 Logical Artifacts + State Snapshot candidate"); s.add_argument("path"); s.add_argument("--with-ai", action="store_true", help="also rebuild the optional derived AI read layer"); s.set_defaults(func=cmd_build_v9)
    s = sub.add_parser("publish-v9", help="publish current v9 build as an immutable local release"); s.add_argument("path"); s.set_defaults(func=cmd_publish_v9)
    s = sub.add_parser("activate-v9", help="atomically advance a local activation channel to a published state"); s.add_argument("path"); s.add_argument("--channel", default="current"); s.add_argument("--digest"); s.add_argument("--blob-digest"); s.set_defaults(func=cmd_activate_v9)
    s = sub.add_parser("qualify-v9", help="invoke independent KristalDiag qualification if installed"); s.add_argument("path"); s.add_argument("--target"); s.add_argument("--profile", default="V9-State-Reader"); s.set_defaults(func=cmd_qualify_v9)
    s = sub.add_parser("configure-github", help="link this Local Kristal to a bootstrapped Kristal v10 GitHub node"); s.add_argument("path"); s.add_argument("--repository", required=True); s.add_argument("--branch", default="main"); s.add_argument("--state-path"); s.add_argument("--framework-repository", required=True); s.add_argument("--framework-sha", required=True); s.add_argument("--qualify-workflow", default="kristal-qualify.yml"); s.add_argument("--publish-workflow", default="kristal-publish.yml"); s.set_defaults(func=cmd_configure_github)
    s = sub.add_parser("configure-from-network", help="derive GitHub host/framework settings from a Bootstrap network.toml"); s.add_argument("path"); s.add_argument("--network", required=True); s.add_argument("--repository", required=True, help="repository name declared in network.toml, e.g. kristal-public"); s.add_argument("--state-path"); s.add_argument("--qualify-workflow", default="kristal-qualify.yml"); s.add_argument("--publish-workflow", default="kristal-publish.yml"); s.set_defaults(func=cmd_configure_from_network)
    s = sub.add_parser("export-hosted", help="copy the exact v9 state candidate into a local bootstrapped host checkout"); s.add_argument("path"); s.add_argument("--repo-dir", required=True); s.add_argument("--force", action="store_true"); s.set_defaults(func=cmd_export_hosted)
    s = sub.add_parser("github-status", help="inspect configured GitHub host, pinned framework and remote state match"); s.add_argument("path"); s.set_defaults(func=cmd_github_status)
    s = sub.add_parser("github-qualify", help="compatibility: exact-commit GitHub qualification (prefer Kristal GitHub Setup)"); s.add_argument("path"); s.set_defaults(func=cmd_github_qualify)
    s = sub.add_parser("github-publish", help="compatibility: publish via v10 GitHub workflow (prefer Kristal GitHub Setup)"); s.add_argument("path"); s.add_argument("--framework-path"); s.add_argument("--yes", action="store_true"); s.set_defaults(func=cmd_github_publish)
    s = sub.add_parser("build-ai", help="compile the deterministic offline portable-AI read layer from the exact v9 state"); s.add_argument("path"); s.set_defaults(func=cmd_build_ai)
    s = sub.add_parser("check-ai", help="verify the offline portable-AI read layer and its binding to the v9 State Snapshot"); s.add_argument("path"); s.set_defaults(func=cmd_check_ai)
    s = sub.add_parser("pack-ai", help="create a deterministic self-contained AI-reading capsule without GitHub/tooling dependencies"); s.add_argument("path"); s.add_argument("--output"); s.set_defaults(func=cmd_pack_ai)
    s = sub.add_parser("hash-manifest", help="write deterministic validation/manifest.sha256.json"); s.add_argument("path"); s.set_defaults(func=cmd_hash_manifest)
    s = sub.add_parser("pack", help="create deterministic zip of workspace"); s.add_argument("path"); s.add_argument("--output"); s.set_defaults(func=cmd_pack)
    s = sub.add_parser("enable-v11", help="opt in to strict v11 identities after registering graph, registry, crosswalk, catalog as v9 logical artifacts"); s.add_argument("path"); s.add_argument("--graph",required=True); s.add_argument("--registry",required=True); s.add_argument("--crosswalk",required=True); s.add_argument("--catalog",required=True); s.set_defaults(func=cmd_v11_enable)
    s = sub.add_parser("check-v11", help="validate v11 canonical graph, identifiers, crosswalk and lexical catalog"); s.add_argument("path"); s.set_defaults(func=cmd_v11_check)
    s = sub.add_parser("import-dik-catalog", help="validate diK snapshot, create distinct versioned dictionary catalog, optionally register; never activate automatically")
    s.add_argument("path");s.add_argument("--catalog",required=True);s.add_argument("--revision",required=True)
    s.add_argument("--register",action="store_true");s.add_argument("--artifact-id");s.add_argument("--contract-id");s.set_defaults(func=cmd_v11_import_dik)
    s = sub.add_parser("select-v11-catalog",help="activate independently registered and validated catalog pointer without building a state")
    s.add_argument("path");s.add_argument("--catalog",required=True);s.set_defaults(func=cmd_v11_select_catalog)
    s = sub.add_parser("recover-v11",help="inspect, finish or rollback interrupted v11 artifact registrations")
    s.add_argument("path");s.add_argument("--mode",choices=["status","finish","rollback"],default="status");s.set_defaults(func=cmd_v11_recover)
    s = sub.add_parser("qualify-v11", help="read-only pinned qualification against actual Framework v11, optionally Integration Pack (requires jsonschema)"); s.add_argument("path"); s.add_argument("--framework",required=True); s.add_argument("--integration-pack"); s.add_argument("--locales"); s.set_defaults(func=cmd_v11_qualify)
    s = sub.add_parser("coverage-v11", help="diK-compatible direct/fallback/missing lexical coverage (read only)"); s.add_argument("path"); s.add_argument("--locales"); s.add_argument("--output"); s.set_defaults(func=cmd_v11_coverage)
    s = sub.add_parser("select-v11-graph", help="switch active graph only after validation and v9 registration; retain previous profile history"); s.add_argument("path"); s.add_argument("--graph",required=True); s.set_defaults(func=cmd_v11_select_graph)
    s = sub.add_parser("check-v11-plan", help="verify a reviewed diK plan without writing"); s.add_argument("path"); s.add_argument("--source",required=True); s.add_argument("--plan",required=True); s.add_argument("--roles"); s.set_defaults(func=cmd_v11_plan_check)
    s = sub.add_parser("apply-v11-plan", help="write NEW v11-shaped graph from fully approved plan + reviewed identity paths, never overwrite historical canon"); s.add_argument("path"); s.add_argument("--source",required=True); s.add_argument("--plan",required=True); s.add_argument("--roles",required=True); s.add_argument("--output",required=True); s.add_argument("--artifact-id",required=True); s.add_argument("--contract-id",required=True); s.set_defaults(func=cmd_v11_apply_plan)
    return p


def main():
    args = build_parser().parse_args(); args.func(args)


if __name__ == "__main__":
    main()
