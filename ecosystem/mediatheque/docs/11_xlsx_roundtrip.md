# 11 — XLSX Round-Trip

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Purpose

XLSX is a bulk-edit interface, not the source of truth.

```text
SQLite -> export XLSX -> edit -> validate import -> apply to SQLite
```

---

## 2. Workbook sheets

Required sheets:

```text
Library
Lists
Import_Report
```

Optional sheets:

```text
Readme
Change_Preview
```

---

## 3. Library sheet columns

```text
action, media_uuid, version_uuid, title, subtitle, description, summary, filename, original_path, storage_path,
media_type, language, library_scope, uckk_relevance, target_system, target_export_allowed,
public_state, visibility, access_level, ownership_scope, source_type, source_ownership, rights_status, rights_note,
restriction_state, restriction_reason, redaction_required, status, provenance, ai_validation_state, ai_confidence,
canonical_validation_state, human_review_required, review_queue, review_reason, collections, tags, relations,
content_flags, audience_suitability, export_to_uckk, export_to_public, export_policy_note, notes, sha256,
filesize, mimetype, updated_at
```

---

## 4. Protected columns

```text
media_uuid
version_uuid
filename
original_path
storage_path
sha256
filesize
mimetype
updated_at
```

Protected fields may be displayed but cannot overwrite SQLite during normal import.

---

## 5. Action column

Allowed values:

```text
update
ignore
archive
new
```

Deleting a row in Excel must not delete a SQLite row.

---

## 6. Multi-value representation

In XLSX:

```text
collections = collection_a; collection_b
tags = tag_a; tag_b
relations = references:uuid; duplicates:uuid
content_flags = non_public; privacy_sensitive
```

In SQLite these values become JSON arrays.
