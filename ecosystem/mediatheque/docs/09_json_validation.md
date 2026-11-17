# 09 — JSON Validation

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Purpose

This document defines validation performed after pasting a ChatGPT JSON response.

---

## 2. Required schema fields

```text
title
description
summary
media_type
language
library_scope
uckk_relevance
target_system
target_export_allowed
public_state
visibility
access_level
ownership_scope
source_type
source_ownership
rights_status
restriction_state
redaction_required
status
provenance
ai_validation_state
ai_confidence
canonical_validation_state
human_review_required
review_queue
collections
tags
relations
content_flags
audience_suitability
export_to_uckk
export_to_public
notes
```

---

## 3. Type and enum validation

```text
strings: text fields
booleans: target_export_allowed, redaction_required, human_review_required
number 0..1: ai_confidence
arrays: collections, tags, relations, content_flags
```

All enum fields must match `01_alignment_variables.md`.

---

## 4. Blocking rules

```text
canonical_validation_state = verified without override
export_to_public = yes while public_state != public
export_to_uckk = yes while uckk_relevance = not_uckk
rights_status = unknown and human_review_required = false
source_type = unknown and human_review_required = false
restriction_state != none and human_review_required = false
```

---

## 5. App-side enrichment

After JSON validation, app adds or recalculates:

```text
media_uuid
version_uuid
original_path
storage_path
filename
extension
mimetype
filesize
sha256
filearea
created_at
updated_at
import_batch
```
