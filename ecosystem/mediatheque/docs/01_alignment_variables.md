# 01 — Alignment Variables

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Identity variables

```text
APP_PUBLIC_NAME = Médiathèque kOA
APP_SHORT_NAME = kOA
APP_TECHNICAL_NAME = koa-mediatheque
APP_COMPONENT = koa_mediatheque
APP_DB_FILENAME = koa_mediatheque.sqlite
APP_DOC_MODE = final_state_specification
APP_DOC_AUDIENCE = ai_only
APP_PRIMARY_LANGUAGE = fr
APP_STORAGE_MODEL = local_filesystem
APP_DB_MODEL = sqlite_single_sheet_with_support_logs
```

---

## 2. Product formula

```text
Médiathèque kOA = local library table + local file storage + ChatGPT intake + XLSX round-trip + compact GUI.
```

The app must feel like a controllable Excel-like media inventory.

The app must not become a heavy enterprise DAM.

The app must not require Moodle.

The app must remain compatible with future exports to UCKK/media-library-like systems.

---

## 3. Canonical paths

```text
KOA_ROOT = KOA_MEDIATHEQUE
KOA_DB_DIR = 01_DB
KOA_DB_PATH = 01_DB/koa_mediatheque.sqlite
KOA_STORAGE_DIR = 02_STORAGE
KOA_IMPORTS_DIR = 03_IMPORTS
KOA_EXPORTS_DIR = 04_EXPORTS
KOA_TOOLS_DIR = 05_TOOLS
KOA_GUI_DIR = 06_GUI
KOA_DOCS_DIR = docs
```

Canonical local storage areas:

```text
media_original
media_preview
media_thumbnail
media_derivative
media_caption
media_transcript
media_attachment
content_review_files
external_work_reference_files
cultural_protocol_files
source_files
```

### Source authority

```text
SOURCE_CATALOG_PROFILE = koa.source-catalog/2.0.0
SOURCE_FILES_FILEAREA = source_files
SCHEMA_VERSION = 4
```

`source_*` est l'autorité commune. Les tables source `kristal_*` restent des surfaces de migration.

### Kristal media bridge

```text
INTERACTION_KERNEL_VERSION = 2.0.0-dev.2
INTERACTION_KERNEL_SCHEMA_VERSION = 1.1
DAAT_HUMAN_NAME = DaaT
DAAT_SYSTEM_ID = daat
KRISTAL_PORTABLE_STANDARD_VERSION = 6.0.0
KRISTAL_PORTABLE_CONTRACT = kristal_state/6.0
KRISTALL_DESIGN_BASELINE = 7.0.0-draft.3.2
KRISTAL_MEDIA_BRIDGE_PROFILE = koa.mediatheque.kristal-media/1.1.0
KRISTAL_MEDIA_RELATION_PREFIX = kristal:
KRISTAL_MEDIA_LOCATOR_PREFIX = koa-media://version/
KOA_KRISTAL_EXPORT_DIR = 04_EXPORTS/kristal
```

Rules:

```text
library_rows remains authoritative.
Kristal linkage is stored in relations_json.
ArtifactRef locators must not expose original_path or storage_path.
Every exported local media version must have a valid local SHA-256.
```

---

## 4. Core database tables

The app uses one main table and support tables.

Main table:

```text
library_rows
```

Required support tables:

```text
chatgpt_intake_log
xlsx_import_log
file_scan_log
audit_log
schema_meta
```

Optional future expansion tables are allowed only if generated from `library_rows`:

```text
normalized_media
normalized_media_version
normalized_collections
normalized_tags
normalized_relations
normalized_sources
```

The first implementation must treat `library_rows` as the canonical table.

---

## 5. Identifier variables

```text
id = local SQLite autoincrement row id
media_uuid = stable intellectual-object identity
version_uuid = stable file/version identity
sha256 = local file content hash
import_batch = batch identity for scan/import sessions
```

Rules:

```text
One library row represents one physical or external-reference version.
Multiple rows may share the same media_uuid when they are versions of the same intellectual document.
Each row must have a unique version_uuid.
The app generates UUIDs locally if ChatGPT does not supply them.
The app must never trust ChatGPT for sha256, filesize, mimetype, filename, extension, or filesystem paths.
```

---

## 6. Main table column groups

```text
Identity
File facts
Description
kOA/UCKK classification
Public/non-public classification
Source and rights
Restriction and sensitivity
Lifecycle status
AI/local validation
Collections/tags/relations
Export policy
Audit fields
```

---

## 7. Canonical status values

```text
MEDIA_STATUS_VALUES = draft, submitted, active, restricted, superseded, archived, deleted_soft
```

---

## 8. Canonical validation values

```text
CANONICAL_VALIDATION_VALUES = unverified, human_reviewed, verified, contested, invalidated, archived
LOCAL_AI_VALIDATION_VALUES = ai_validated, ai_classified_needs_review, ai_uncertain, ai_rejected
```

Rule:

```text
AI may set local AI validation.
AI must not set canonical_validation_state to verified unless the human explicitly supplies that instruction.
Default canonical_validation_state = unverified.
```

---

## 9. Visibility and public state values

```text
VISIBILITY_VALUES = private, user, group, course, cohort, program, institution, public, restricted, restricted_integrity, restricted_cultural
PUBLIC_STATE_VALUES = public, non_public, private, restricted, confidential, unknown
ACCESS_LEVEL_VALUES = private, limited, internal, public, restricted, confidential, unknown
```

Rules:

```text
public_state answers whether the document is public in ordinary language.
visibility answers who can see/use it inside a structured system.
access_level answers how strict access should be in the local app.
```

---

## 10. kOA / UCKK classification values

```text
LIBRARY_SCOPE_VALUES = koa
UCKK_RELEVANCE_VALUES = uckk_core, uckk_related, uckk_reference, not_uckk, unknown
TARGET_SYSTEM_VALUES = none, uckkarchive, other
TARGET_EXPORT_ALLOWED_VALUES = 0, 1
EXPORT_DECISION_VALUES = yes, no, maybe, review_required
```

Rules:

```text
Médiathèque kOA is broader than UCKK.
UCKK is a classification target, not the app identity.
Non-UCKK records must be allowed.
Non-public records must be allowed.
Non-exportable records must be allowed.
```

---

## 11. Media type values

```text
MEDIA_TYPE_VALUES = document, pdf, image, audio, video, transcript, spreadsheet, presentation, source_package, external_reference, other
```

---

## 12. Source and rights values

```text
SOURCE_TYPE_VALUES = produced_by_uckk, submitted_to_uckk, imported, external_reference_only, licensed_external, public_domain, fair_use_reference, restricted_reference, unknown
SOURCE_OWNERSHIP_VALUES = uckk_created, uckk_commissioned, member_submitted, partner_submitted, external_reference, third_party_copyright, public_domain, open_license, unknown_source
OWNERSHIP_SCOPE_VALUES = uckk_owned, koa_owned, personal, third_party, public_domain, open_license, unknown
RIGHTS_STATUS_VALUES = owned, licensed, open_license, public_domain, fair_use_reference, third_party, unknown
```

Rules:

```text
Source describes origin.
Rights describe permission context.
Source and rights do not automatically grant public access.
Unknown rights require human_review_required = 1.
```

---

## 13. Restriction values

```text
RESTRICTION_STATE_VALUES = none, possible, restricted, confidential, cultural, integrity, privacy, copyright, unknown
AUDIENCE_SUITABILITY_VALUES = general, guided, mature, restricted, restricted_cultural, restricted_integrity, staff_only, unknown
```

Content flags may include:

```text
sexual_violence
violence
racism
colonial_violence
death
self_harm
substance_use
nudity
explicit_language
culturally_sensitive
sacred_content
ceremonial_content
restricted_knowledge
grief_or_mourning
requires_context
not_for_children
privacy_sensitive
copyright_uncertain
non_public
confidential
```

---

## 14. Relation types

```text
RELATION_TYPE_VALUES = belongs_to_collection, is_derivative_of, is_translation_of, is_excerpt_of, is_source_for, replaces, references, duplicates, references_external_work, contains_content_marker, related_to
```

Relation format in flat fields:

```text
relation_type:target_uuid
```

Multiple relations are separated by semicolons in XLSX.

---

## 15. JSON field convention

The SQLite table stores multi-value fields as JSON text.

```text
collections_json = JSON array of collection keys
tags_json = JSON array of tag keys
relations_json = JSON array of relation objects or compact strings
content_flags_json = JSON array of controlled or local flags
```

XLSX displays these as semicolon-separated strings.

---

## 16. ChatGPT intake rule

The GUI must provide a button:

```text
Copier template ChatGPT
```

The copied template must include:

```text
app identity
classification rules
allowed values
required JSON schema
instruction to output JSON only
instruction not to invent source/rights/public status
instruction to mark uncertainty for human review
```

The GUI must also provide:

```text
Coller réponse ChatGPT
Valider JSON
Prévisualiser entrée
Valider et intégrer
```

---

## 17. XLSX round-trip rule

```text
SQLite -> XLSX -> human edits -> import preview -> validated update -> SQLite
```

Rules:

```text
SQLite remains the source of truth.
Deleting an XLSX row must not delete a SQLite row.
version_uuid is the import key.
Protected technical fields cannot be overwritten from XLSX unless an explicit repair mode is used.
Every import must create a backup and an import log.
```

---

## 18. Export manifest rule

Canonical manifest filename:

```text
manifest.json
```

Manifest must include:

```text
app name
app component
export uuid
export timestamp
export actor
export reason
row count
media uuids
version uuids
file hashes
file sizes
mime types
visibility
public state
restricted flags
audience suitability
provenance
collections
tags
relations
validation state
export policy
```

---

## 19. AI writing rules

Every AI-generated implementation response must:

```text
Use the exact variable names from this file.
Avoid inventing alternate names.
Prefer SQLite, PS7, Streamlit or a small desktop GUI.
Keep the app simple from the user's perspective.
Preserve compatibility with future media-library export.
Treat non-UCKK and non-public records as first-class cases.
```
