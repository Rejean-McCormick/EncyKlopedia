# 14 — Manifest and Export

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Purpose

Manifests make exports portable, explainable, and importable into future systems.

---

## 2. Canonical manifest filename

```text
manifest.json
```

---

## 3. Export types

```text
xlsx_inventory
koa_manifest
uckkarchive_candidate
public_review_package
backup_snapshot
```

---

## 4. Manifest structure

```json
{
  "app_public_name": "Médiathèque kOA",
  "app_component": "koa_mediatheque",
  "export_uuid": "",
  "export_timestamp": "",
  "export_actor": "",
  "export_reason": "",
  "export_type": "koa_manifest",
  "row_count": 0,
  "media_uuids": [],
  "version_uuids": [],
  "files": [],
  "classification_summary": {},
  "restrictions_summary": {},
  "validation_summary": {},
  "records": []
}
```

Each record must include media UUID, version UUID, title, filename, storage path, sha256, size, MIME type, media type, UCKK relevance, public state, visibility, rights status, restriction state, suitability, provenance, validation states, collections, tags, relations, content flags, and export policies.

---

## 5. Export restrictions

Public export blockers:

```text
public_state != public
visibility != public
rights_status in unknown, third_party
restriction_state != none
human_review_required = 1
export_to_public != yes
```

UCKK export blockers:

```text
uckk_relevance = not_uckk
export_to_uckk = no
rights_status = unknown without review
restriction_state in cultural, integrity, privacy, copyright without review
```
