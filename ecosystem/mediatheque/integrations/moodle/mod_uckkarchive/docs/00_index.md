# 00 — Documentation Index

**Path:** `docs/00_index.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Index and navigation map for the clean `mod_uckkarchive` documentation set.

---

## 1. Purpose

This document is the canonical index for the `mod_uckkarchive` documentation set.

The documentation defines the final target behavior for a self-contained Moodle activity module that provides:

```text
archive memory
media library management
public Médiathèque façade
public Médiathèque explorer
content advisory governance
cultural sensitivity tagging
external/foreign media references
exportable archive/media packages
```

The documentation is used to guide code generation, implementation review, testing, backup/restore design, privacy coverage, service design, UI construction, and packaging.

---

## 2. Documentation mode

The documentation set uses this mode:

```text
DOC_MODE = final_state_specification
DOC_STYLE = descriptive
DOC_TARGET = build-ready module specification
```

Rules:

```text
Documentation describes the final target behavior.
Documentation does not preserve historical debate.
Documentation does not keep a gap register.
Documentation does not use acceptance-checklist process documents.
Documentation does not use release-notes process documents.
Documentation does not describe required features as future optional features.
```

---

## 3. Canonical architecture formula

`mod_uckkarchive` follows this architecture formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

Canonical module definition:

```text
mod_uckkarchive = self-contained Moodle activity module for archive memory, media library management, and content advisory governance.
```

The module is installed and governed as a Moodle module.

The module owns its internal archive/media/content-advisory domain.

---

## 4. Canonical paths

Source documentation path:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive\docs
```

Active Moodle documentation path:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive\docs
```

Source plugin path:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive
```

Active Moodle plugin path:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
```

Canonical Moodle plugin path:

```text
mod/uckkarchive
```

Component:

```text
mod_uckkarchive
```

---

## 5. Required alignment file

Every documentation-generation conversation must start from:

```text
docs/_alignment_variables.md
```

This file defines shared variables for:

```text
plugin identity
canonical paths
active documentation set
architecture formula
database tables
capabilities
file areas
media lifecycle
public Médiathèque façade
public Médiathèque explorer
archive lifecycle
validation states
visibility values
provenance values
media relation types
content advisory subsystem
external works
foreign media references
export manifests
required code files
writing rules
```

Rule:

```text
If another document conflicts with docs/_alignment_variables.md, update the document to match the alignment variables.
```

---

## 6. Active documentation set

Generate and maintain these documents only:

```text
docs/_alignment_variables.md
docs/00_index.md
docs/01_architecture_decision.md
docs/02_domain_boundaries.md
docs/03_file_architecture.md
docs/04_data_model.md
docs/05_media_library.md
docs/06_file_api_and_storage.md
docs/07_permissions_and_roles.md
docs/08_archive_workflows.md
docs/09_media_workflows.md
docs/10_provenance_versioning_validation.md
docs/11_privacy_retention_redaction.md
docs/12_backup_restore.md
docs/13_services_and_ajax_api.md
docs/14_events_and_audit.md
docs/15_ui_templates_and_amd.md
docs/16_integration_with_courses.md
docs/17_integration_with_challenges.md
docs/18_integration_with_assemblies.md
docs/19_integration_with_integrity.md
docs/20_reporting_and_exports.md
docs/21_testing_strategy.md
docs/22_installation.md
docs/23_upgrade.md
docs/24_release_spec.md
docs/25_mediatheque_public_explorer.md
```

---

## 7. Generation order

Use this order when generating documents in separate conversations:

```text
1. docs/_alignment_variables.md
2. docs/00_index.md
3. docs/01_architecture_decision.md
4. docs/02_domain_boundaries.md
5. docs/03_file_architecture.md
6. docs/04_data_model.md
7. docs/05_media_library.md
8. docs/06_file_api_and_storage.md
9. docs/07_permissions_and_roles.md
10. docs/08_archive_workflows.md
11. docs/09_media_workflows.md
12. docs/10_provenance_versioning_validation.md
13. docs/11_privacy_retention_redaction.md
14. docs/12_backup_restore.md
15. docs/13_services_and_ajax_api.md
16. docs/14_events_and_audit.md
17. docs/15_ui_templates_and_amd.md
18. docs/16_integration_with_courses.md
19. docs/17_integration_with_challenges.md
20. docs/18_integration_with_assemblies.md
21. docs/19_integration_with_integrity.md
22. docs/20_reporting_and_exports.md
23. docs/21_testing_strategy.md
24. docs/22_installation.md
25. docs/23_upgrade.md
26. docs/24_release_spec.md
27. docs/25_mediatheque_public_explorer.md
```

---

## 8. Documents not generated

The clean documentation set does not generate these files:

```text
docs/05_media_database_division.md
docs/09_didactic_material_workflows.md
docs/24_acceptance_checklist.md
docs/25_known_gaps_and_corrections.md
docs/26_release_notes.md
docs/27_file_architecture_manifest.md
```

Replacement mapping:

```text
media_database_division -> docs/05_media_library.md
didactic_material_workflows -> docs/08_archive_workflows.md and docs/09_media_workflows.md
acceptance_checklist -> docs/24_release_spec.md
known_gaps_and_corrections -> not replaced
25_mediatheque_public_explorer -> active public Médiathèque specification
release_notes -> docs/24_release_spec.md
file_architecture_manifest -> docs/03_file_architecture.md
```

---

## 9. Document summaries

### `docs/_alignment_variables.md`

Defines the canonical variables used by every document.

This file is the cross-document contract.

All other documentation must align with it.

---

### `docs/00_index.md`

Defines the active documentation set, generation order, module formula, navigation map, and cross-document consistency rules.

This file is the documentation entry point.

---

### `docs/01_architecture_decision.md`

Defines the core architecture decision:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

It establishes module ownership, Moodle boundary, external plugin boundaries, media as a first-class domain object, content advisory governance, and non-negotiable architecture rules.

---

### `docs/02_domain_boundaries.md`

Defines ownership boundaries between `mod_uckkarchive` and other Moodle/UCKK systems.

It defines what the archive may preserve, reference, display, summarize, export, or link without becoming the authority for external workflows.

---

### `docs/03_file_architecture.md`

Defines the plugin file and folder architecture.

It covers:

```text
root PHP files
AMD files
backup/restore files
classes/local
classes/external
classes/output
classes/event
classes/form
classes/task
db files
lang files
templates
tests
pix assets
```

---

### `docs/04_data_model.md`

Defines the database schema and entity relationships.

It covers archive tables, media tables, content advisory tables, external work tables, UUID rules, status fields, visibility fields, indexes, constraints, and migration expectations.

---

### `docs/05_media_library.md`

Defines the internal media-library engine.

It covers media objects, media versions, media collections, media relations, media tags, media source records, derivatives, thumbnails, captions, transcripts, external/foreign media references, and media lifecycle.

---

### `docs/06_file_api_and_storage.md`

Defines Moodle File API usage.

It covers archive file areas, media file areas, content advisory file areas, pluginfile handling, restricted access, derivative files, export files, backup/restore file handling, privacy file handling, and forbidden storage patterns.

---

### `docs/07_permissions_and_roles.md`

Defines capabilities, role defaults, access rules, policy classes, restricted access, media download permissions, advisory review permissions, cultural protocol permissions, and export permissions.

---

### `docs/08_archive_workflows.md`

Defines archive workflows.

It covers item creation, submission, validation, revision, contestation, restriction, publication, archive item/media linking, proof workflows, Kristal workflows, and export preparation.

---

### `docs/09_media_workflows.md`

Defines media workflows.

It covers media creation, upload, source classification, versioning, collection membership, tagging, relation mapping, derivative generation, transcript/caption management, external work linking, and content advisory marker creation.

---

### `docs/10_provenance_versioning_validation.md`

Defines provenance, versioning, validation, contestability, archive revision rules, media version rules, content review rules, human-final validation, and provenance portability.

---

### `docs/11_privacy_retention_redaction.md`

Defines privacy, retention, redaction, restricted records, export redaction, advisory redaction, cultural protocol redaction, user data export, and deletion behavior.

---

### `docs/12_backup_restore.md`

Defines backup and restore behavior.

It covers archive records, media records, media files, media versions, collections, relations, content advisories, content markers, content reviews, external works, export manifests, ID mapping, and file restoration.

---

### `docs/13_services_and_ajax_api.md`

Defines external service and AJAX API architecture.

It covers archive services, media services, content advisory services, external work services, export services, parameter validation, return structures, capability gates, and policy enforcement.

---

### `docs/14_events_and_audit.md`

Defines event and audit behavior.

It covers archive events, media events, content marker events, external work events, export events, privacy-safe event payloads, and audit trace rules.

---

### `docs/15_ui_templates_and_amd.md`

Defines UI architecture.

It covers page layouts, Mustache templates, renderables, AMD modules, archive cards, media cards, content advisory panels, external work cards, validation panels, provenance panels, and client/server responsibility boundaries.

---

### `docs/16_integration_with_courses.md`

Defines integration with Moodle courses.

It covers course-module context, course visibility, groups, activity completion, course navigation, course content usage, and course-level archive/media access.

---

### `docs/17_integration_with_challenges.md`

Defines integration with `mod_uckkchallenge`.

It covers preserving challenge evidence, linking challenge outputs, archiving challenge-related media, and maintaining challenge workflow boundaries.

---

### `docs/18_integration_with_assemblies.md`

Defines integration with `mod_uckkassembly`.

It covers preserving assembly minutes, decisions, attachments, media, summaries, and provenance while keeping assembly decision authority outside the archive.

---

### `docs/19_integration_with_integrity.md`

Defines optional integration with `tool_uckkintegrity`.

It covers restricted integrity-related archive records, integrity exports, integrity evidence preservation, content warnings, cultural restrictions, and fail-closed behavior when the tool is absent.

---

### `docs/20_reporting_and_exports.md`

Defines reporting and export boundaries.

It covers archive-owned export packages, media export packages, collection exports, manifest format, content advisory export behavior, external work references, and separation from `report_uckk`.

---

### `docs/21_testing_strategy.md`

Defines testing strategy.

It covers unit tests, advanced tests, privacy tests, backup/restore tests, service tests, file API tests, media library tests, content advisory tests, external work tests, Behat tests, and regression rules.

---

### `docs/22_installation.md`

Defines installation behavior.

It covers Moodle installation, plugin version, database install, capabilities, tasks, services, language strings, file areas, settings, and initial configuration.

---

### `docs/23_upgrade.md`

Defines upgrade behavior.

It covers schema upgrades, media table introduction, content advisory table introduction, file-area normalization, capability migration, data migration, backup compatibility, and upgrade safety.

---

### `docs/24_release_spec.md`

Defines release-state package expectations.

It covers the final package shape, required files, excluded files, clean distribution rules, code-generation completion criteria, and packaging constraints.

This document is a release specification, not a release note and not an acceptance checklist.

---

### `docs/25_mediatheque_public_explorer.md`

Defines the public Médiathèque page and public Médiathèque Explorer.

It covers the relationship between `local_uckk` and `mod_uckkarchive`, the public search façade, the `mod_uckkarchive_search_mediatheque` AJAX contract, public DTOs, filters, cards, targeted passages, visibility rules, cultural-protocol boundaries, content-advisory display, reusable media-library assets, and anti-duplication rules.

This document is the public-surface contract for exposing a policy-filtered subset of the existing media library. It does not create a second media engine.

---

## 10. Canonical internal ownership list

`mod_uckkarchive` owns:

```text
archive records
archive items
media records
media versions
media files
media collections
media collection membership
media relations
media tags
proof records
Kristals
provenance records
revision history
validation state
restricted archive metadata
restricted media metadata
content advisory tags
cultural sensitivity tags
content tag sets
content markers
content reviews
external works
foreign media references
media source records
public Médiathèque search façade
public Médiathèque repository/service
public media DTO filtering
audience suitability rules
export packages
export manifests
```

---

## 11. Canonical external ownership boundaries

`mod_uckkarchive` does not own:

```text
grades
transcripts
course enrolment authority
administrative registry records
challenge workflow state
Assembly decision authority
integrity case authority
institutional reporting authority
public page shell ownership
public navigation shell ownership
```

External ownership map:

```text
Moodle gradebook = grades
local_uckk = shared UCKK registry, institutional configuration, public page shell, and public navigation shell
mod_uckkchallenge = challenge workflow
mod_uckkassembly = assembly workflow and decisions
tool_uckkintegrity = integrity procedures and case records
report_uckk = institutional reporting views and institutional report exports
mod_uckkarchive = archive/media/content-advisory memory layer
```

---

## 12. Canonical database table list

Archive tables:

```text
uckkarchive
uckkarchive_item
uckkarchive_proof
uckkarchive_kristal
uckkarchive_prov
uckkarchive_rev
uckkarchive_export
```

Media tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
```

Content advisory and external-work tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_media_source
```

Identifier rule:

```text
id = local Moodle database primary key
uuid = stable portable object identity
```

---

## 13. Canonical capability list

Archive capabilities:

```text
mod/uckkarchive:addinstance
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Media capabilities:

```text
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:editmedia
mod/uckkarchive:deletemedia
mod/uckkarchive:downloadmedia
mod/uckkarchive:versionmedia
mod/uckkarchive:managemediacollections
mod/uckkarchive:exportmedia
mod/uckkarchive:viewrestrictedmedia
```

Content advisory capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:manageexternalworks
```

Removed capability:

```text
mod/uckkarchive:versionitem = not used
```

---

## 14. Canonical File API areas

Archive file areas:

```text
intro
item_content
item_publicsummary
item_files
proof_files
decision_attachments
minutes_files
kristal_files
portfolio_files
integrity_exports
provenance_files
validation_files
revision_files
export_package
export_manifest
```

Media file areas:

```text
media_original
media_preview
media_thumbnail
media_derivative
media_caption
media_transcript
media_attachment
```

Content advisory file areas:

```text
content_review_files
external_work_reference_files
cultural_protocol_files
```

---

## 15. Canonical status and classification values

Media states:

```text
draft
submitted
active
restricted
superseded
archived
deleted_soft
```

Archive item statuses:

```text
draft
submitted
under_review
validated
published
restricted
contested
invalidated
superseded
archived
```

Validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Visibility values:

```text
private
user
group
course
cohort
program
institution
public
restricted
restricted_integrity
restricted_cultural
```

Provenance values:

```text
human
ai_assisted
imported
system
archive
assembly
challenge
integrity
media
external_work
content_review
```

---

## 16. Content advisory index

The content advisory subsystem covers:

```text
content advisories
content warnings
cultural advisories
cultural protocols
audience suitability
content markers
tag sets
reviews
external works
foreign media references
```

Canonical advisory tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_media_source
```

Architecture rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 17. External works index

External works are works not produced by UCKK but referenced, taught, reviewed, tagged, or connected to archive/media records.

External work examples:

```text
film
book
article
podcast
website
external_video
external_image
public_archive_item
third_party_pdf
other
```

External/foreign media rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 18. Export manifest index

Canonical manifest filename:

```text
manifest.json
```

The manifest includes:

```text
plugin component
archive id
export id
export timestamp
export actor
export reason
archive item ids
media uuids
media version uuids
external work uuids
content marker uuids
content tag keys
content tag set keys
content review state
file hashes
file sizes
mime types
visibility
restricted flags
audience suitability
cultural protocol flags
provenance
relations
collections
tags
redaction level
validation state
revision history
```

---

## 19. Cross-document consistency rules

Every document must use the same:

```text
component name
plugin path
architecture formula
database table names
capability names
file areas
media states
archive item statuses
validation states
visibility values
provenance values
content advisory terminology
external work terminology
export manifest terminology
public Médiathèque terminology
public Médiathèque Explorer terminology
local_uckk public shell boundary
mod_uckkarchive public data/policy boundary
```

Every document must avoid:

```text
known gaps
known corrections
acceptance checklist
release notes
old architecture debate
media as only generic item attachment
content advisories as only a JSON field
duplicating the media-library engine for the public Médiathèque
creating separate Médiathèque card/detail/marker templates when existing media templates suffice
placing media access decisions in local_uckk, AMD, or Mustache
versionitem capability
hard dependency on tool_uckkintegrity
```

---

## 20. Implementation-use rule

This documentation set is written for implementation.

Each document must be usable by an AI coding conversation as a source of truth for generating:

```text
PHP classes
Moodle callbacks
database schema
upgrade steps
external services
public service façades
events
forms
output classes
templates
AMD modules
public controllers
privacy provider
backup/restore steps
tests
language strings
package structure
```

---

## 21. Final rule

```text
This documentation set defines the final target behavior for implementation. Code, tests, services, UI, public Médiathèque surfaces, backup/restore, privacy, content advisory governance, and packaging must conform to these specifications.
```
- [27 — Médiathèques autonomes et bridges inter-Univers-Cités](27_media_library_partition_and_bridges.md)
