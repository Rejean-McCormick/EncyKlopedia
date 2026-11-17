# 02 — App Definition

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Purpose

Médiathèque kOA is a local cataloging application for documents, media files, AI-generated files, non-public files, UCKK-related records, non-UCKK records, and future export candidates.

The app exists because files currently live in folders such as Google Drive, but need a structured local inventory that can later export clean metadata.

---

## 2. User perspective

The user experiences the app as:

```text
an Excel-like table
with file preview
with buttons for ChatGPT intake
with XLSX export/import
with reliable local file opening
```

The user should not be exposed to a complex multi-table media system.

---

## 3. Internal perspective

Internally, one flat table preserves enough structure to be migrated or exported to a richer media library.

```text
library_rows.media_uuid = media object identity
library_rows.version_uuid = media version identity
collections_json = collection membership
tags_json = tags
relations_json = media graph relations
source_type/source_ownership/rights_status = source and rights metadata
```

---

## 4. Boundary with UCKK

Médiathèque kOA is not UCKK.

UCKK is represented through fields:

```text
uckk_relevance
target_system
target_export_allowed
export_to_uckk
```

Non-UCKK records must be supported without hacks.

---


## 4.1 Boundary with DaaT and Kristal/Kristall

Médiathèque kOA owns local source/media bytes, physical versions, integrity facts and storage locators. Kristal/Kristall owns Kristal semantic identity and crystallization. **DaaT** (`daat`) is only the optional Interaction Kernel admission/explicit contract-mapping boundary.

A Kristal may reference immutable Médiathèque content, and the Kristal artifact itself may also be stored/versioned by Médiathèque. The identities remain distinct:

```text
kristal_ref != media_uuid != version_uuid
locator: koa-media://version/<version_uuid>
integrity: sha256
portable Kristal contract: kristal_state/6.0
Kristal/Kristall baseline: 7.0.0-draft.3.2
```

The bridge never grants direct write access to the Médiathèque database and never exports local filesystem paths as locators.

## 5. Boundary with public access

Public access is not assumed.

The app distinguishes:

```text
public_state
visibility
access_level
restriction_state
rights_status
export_to_public
```

A file can be public but not UCKK, UCKK-related but non-public, personal but cataloged, third-party but referenced, or unknown and blocked from export.

---

## 6. AI role

ChatGPT classifies and validates locally.

The app validates structure and technical facts.

Canonical/human validation remains distinct.

```text
ai_validation_state = local AI classification result
canonical_validation_state = formal validation state for future systems
```

---

## 7. Final product rule

The app must remain small but not temporary.

The data model must be durable from the first version.
