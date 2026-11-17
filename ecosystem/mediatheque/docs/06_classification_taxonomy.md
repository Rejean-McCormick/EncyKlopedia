# 06 — Classification Taxonomy

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Purpose

This document defines controlled values and classification logic for Médiathèque kOA.

The taxonomy must support non-UCKK documents, UCKK-related documents, non-public documents, private documents, third-party documents, AI-generated documents, uncertain-source documents, and future export candidates.

---

## 2. UCKK relevance

```text
uckk_core = directly belongs to UCKK work or UCKK-controlled documentation
uckk_related = useful to UCKK but not necessarily owned or controlled by UCKK
uckk_reference = external reference connected to UCKK work
not_uckk = belongs in kOA but not UCKK
unknown = cannot determine
```

Rules:

```text
not_uckk -> export_to_uckk = no by default
unknown -> human_review_required = 1
uckk_reference with third-party rights -> export_to_uckk = review_required
```

---

## 3. Public state

```text
public = already public or intended for public distribution
non_public = not public but not necessarily secret
private = personal/private context
restricted = controlled access required
confidential = high restriction
unknown = cannot determine
```

Rules:

```text
public_state != public -> export_to_public must not be yes by default
confidential/restricted/unknown -> human_review_required = 1
```

---

## 4. Rights and content flags

```text
owned
licensed
open_license
public_domain
fair_use_reference
third_party
unknown
```

Content flags are not bans. They describe responsible handling requirements.

Allowed examples:

```text
culturally_sensitive
sacred_content
ceremonial_content
restricted_knowledge
requires_context
not_for_children
privacy_sensitive
non_public
confidential
copyright_uncertain
colonial_violence
violence
racism
death
grief_or_mourning
self_harm
substance_use
nudity
explicit_language
sexual_violence
```

---

## 5. Collections and tags

Format rule:

```text
lowercase
ascii preferred
no spaces
use underscores
short and stable
```

Examples:

```text
collections: koa_inbox, ai_generated, uckk_docs, moodle_specs, personal_archive, external_references
tags: mediatheque, sqlite, ps7, chatgpt_intake, xlsx_roundtrip, non_public, not_uckk
```
