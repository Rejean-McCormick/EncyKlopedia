# 05 — Library Row Schema

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. One-row rule

One `library_rows` row represents one file version or one external-reference version.

```text
media_uuid = stable identity of the intellectual object
version_uuid = stable identity of the exact file/reference version
```

---

## 2. Required insertion fields

```text
media_uuid
version_uuid
title
original_path
filename
sha256 or external_reference marker
media_type
library_scope
public_state
visibility
source_type
source_ownership
rights_status
status
provenance
ai_validation_state
canonical_validation_state
```

The app may generate UUIDs and technical fields.

---

## 3. Protected technical fields

These fields are calculated locally and must not be trusted from ChatGPT or XLSX:

```text
filename
extension
mimetype
filesize
sha256
storage_path
created_at
updated_at
```

---

## 4. Editable descriptive and classification fields

```text
title
subtitle
description
summary
media_type
language
collections_json
tags_json
relations_json
content_flags_json
notes
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
rights_note
restriction_state
restriction_reason
redaction_required
human_review_required
review_queue
review_reason
audience_suitability
export_to_uckk
export_to_public
export_policy_note
```

---

## 5. Safety defaults

```text
unknown rights -> human_review_required = 1
unknown source -> human_review_required = 1
non_public/private/restricted/confidential -> export_to_public != yes
not_uckk -> export_to_uckk = no unless human overrides
restricted/cultural/integrity/privacy/copyright -> human_review_required = 1
```
