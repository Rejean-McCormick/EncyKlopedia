# 20 — Reporting and Exports

**Path:** `docs/20_reporting_and_exports.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Related plugin:** `report_uckk`  
**Status:** Final target specification  
**Scope:** Archive-owned exports, media-library exports, content advisory export behavior, external work references, export manifests, reporting boundaries, redaction, portability, and separation from institutional reporting.

---

## 1. Purpose

This document defines the reporting and export contract for `mod_uckkarchive`.

`mod_uckkarchive` is a self-contained Moodle activity module for:

```text
archive memory
media library management
content advisory governance
cultural sensitivity tagging
external/foreign media references
exportable archive/media packages
```

This document defines what `mod_uckkarchive` may export, what it must not export, how exports are represented, how export manifests are built, and how reporting boundaries are preserved.

---

## 2. Core architecture rule

Canonical architecture formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

Export architecture follows the same rule.

`mod_uckkarchive` uses Moodle for:

```text
context
users
roles
capabilities
File API
Privacy API
Backup API
Restore API
events
scheduled tasks
external services
```

Inside that Moodle boundary, `mod_uckkarchive` owns archive/media/content-advisory export packages.

---

## 3. Reporting boundary decision

`mod_uckkarchive` owns archive/media export packages.

`report_uckk` owns institutional reports.

Canonical boundary:

```text
mod_uckkarchive = archive-owned export packages
report_uckk     = institutional reporting views and institutional report exports
```

`mod_uckkarchive` may export selected archive/media records that it owns.

`report_uckk` may aggregate, filter, display, and export cross-plugin institutional reporting views.

The archive module does not become the institutional reporting authority.

---

## 4. External ownership map

Canonical ownership boundaries:

```text
Moodle gradebook = grades
local_uckk = shared UCKK registry and institutional configuration
mod_uckkchallenge = challenge workflow
mod_uckkassembly = assembly workflow and decisions
tool_uckkintegrity = integrity procedures and case records
report_uckk = institutional reporting views and institutional report exports
mod_uckkarchive = archive/media/content-advisory memory layer
```

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
```

Preserved evidence does not transfer authority.

Referenced external works do not become UCKK-owned works.

---

## 5. Archive export ownership

`mod_uckkarchive` may own and generate exports for:

```text
archive item exports
selected item exports
validated item exports
public item exports
restricted item exports when authorized
proof bundles
Kristal bundles
provenance bundles
revision bundles
media bundles
media collection bundles
content advisory bundles
external work reference bundles
export manifests
archive export package files
```

These exports are archive-owned packages.

They are not institutional reports.

---

## 6. Institutional reporting boundary

`report_uckk` owns:

```text
institutional dashboards
cross-course reports
cross-plugin reports
cohort reports
program reports
administrative reports
grade reports
activity reports across plugins
institutional export views
institutional reporting permissions
```

`mod_uckkarchive` may provide archive data to `report_uckk` through safe APIs or database views when designed.

`mod_uckkarchive` must not duplicate `report_uckk` as a reporting dashboard.

---

## 7. Export package types

Canonical archive/media export package types:

```text
archive_item_export
archive_selection_export
archive_collection_export
media_item_export
media_selection_export
media_collection_export
proof_bundle_export
kristal_bundle_export
provenance_export
revision_export
content_advisory_export
external_work_reference_export
restricted_archive_export
restricted_integrity_export
```

Export package type rule:

```text
Export type describes the package purpose.
Export type does not bypass permission, redaction, visibility, cultural protocol, or retention policy.
```

---

## 8. Required export tables

Primary export table:

```text
uckkarchive_export
```

Export records may reference:

```text
uckkarchive_item
uckkarchive_proof
uckkarchive_kristal
uckkarchive_prov
uckkarchive_rev
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_media_source
```

Export record rule:

```text
The export record stores the export request, policy result, manifest reference, file reference, actor, timestamps, status, and redaction level.
```

---

## 9. Export package lifecycle

Canonical export package statuses:

```text
requested
queued
generating
ready
failed
expired
revoked
deleted_soft
```

Status meaning:

| Status | Meaning |
|---|---|
| `requested` | Export request has been submitted. |
| `queued` | Export is waiting for scheduled task or worker processing. |
| `generating` | Export package is being generated. |
| `ready` | Export package is available under policy. |
| `failed` | Export generation failed and error metadata is available to authorized users. |
| `expired` | Export package is no longer downloadable under retention policy. |
| `revoked` | Export access was explicitly withdrawn. |
| `deleted_soft` | Export package is hidden and retained only as policy requires. |

Lifecycle rule:

```text
Export readiness is not export authority.
A ready package still requires permission checks before download.
```

---

## 10. Export file areas

Canonical export file areas:

```text
export_package
export_manifest
```

Export file areas belong to:

```text
component = mod_uckkarchive
```

File-area rule:

```text
Export package files and manifest files are stored through Moodle File API.
No production export package is stored in unmanaged public folders.
```

Export package files may include:

```text
ZIP files
JSON files
CSV files
PDF summary files
HTML index files
manifest files
redacted media copies
allowed original media copies
allowed derivative media copies
allowed transcript/caption files
reference-only external work records
```

---

## 11. Export manifest

Every export package must include a manifest.

Canonical manifest filename:

```text
manifest.json
```

The manifest is the authoritative description of the package contents.

Manifest includes:

```text
plugin component
plugin version
archive id
export id
export uuid
export type
export timestamp
export actor
export reason
course id
course module id
context id
archive item ids
archive item uuids
media uuids
media version uuids
media collection uuids
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

Manifest rule:

```text
Exports are portable and explainable.
Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.
```

---

## 12. Manifest redaction

The manifest must be redaction-aware.

Manifest fields may be:

```text
included
summarized
redacted
omitted
reference_only
```

Restricted manifest data includes:

```text
private reviewer notes
private cultural protocol notes
integrity details
restricted media metadata
restricted archive metadata
sensitive content advisory notes
third-party rights notes not safe to share
personal data not authorized for export
```

Manifest redaction rule:

```text
A manifest may explain that redaction occurred without exposing the redacted content.
```

---

## 13. Export capability model

Archive export capability:

```text
mod/uckkarchive:export
```

Media export capability:

```text
mod/uckkarchive:exportmedia
```

Restricted archive access capability:

```text
mod/uckkarchive:viewrestricted
```

Restricted media access capability:

```text
mod/uckkarchive:viewrestrictedmedia
```

Content advisory view capability:

```text
mod/uckkarchive:viewadvisories
```

Content advisory management capability:

```text
mod/uckkarchive:manageadvisories
```

Culturally restricted view capability:

```text
mod/uckkarchive:viewculturallyrestricted
```

Capability rule:

```text
Capabilities are gates, not full authority.
Policy classes still enforce context, ownership, visibility, status, validation state, restricted state, content advisory rules, cultural protocol rules, retention, and redaction.
```

---

## 14. Export policy classes

Archive export policy belongs in:

```text
classes/local/archive_policy.php
```

Media export policy belongs in:

```text
classes/local/media_policy.php
```

Content advisory export policy belongs in:

```text
classes/local/content_policy.php
```

Manifest construction belongs in:

```text
classes/local/manifest_builder.php
```

Export package creation belongs in:

```text
classes/local/export_package.php
```

Policy classes decide:

```text
whether export is allowed
which records are included
which files are included
which media versions are included
which advisories are included
which cultural protocol fields are redacted
which external works are reference-only
which fields are redacted
which manifest entries are included
which package format is allowed
whether package download is allowed
```

---

## 15. Archive item export

Archive item export may include:

```text
archive item metadata
archive item public summary
archive item body/content
status
visibility
validation state
provenance
revision history
linked proofs
linked Kristals
linked media references
content advisory summaries
export-safe content markers
export-safe review state
allowed files
manifest entry
```

Archive item export must not include:

```text
restricted metadata without authority
private review notes without authority
unredacted cultural protocol notes without authority
integrity case details without authority
unauthorized media files
unauthorized external work copies
```

---

## 16. Media export

Media export may include:

```text
media metadata
media source metadata
media version metadata
allowed original files
allowed derivative files
allowed preview files
allowed thumbnails
allowed captions
allowed transcripts
media relations
media tags
media collection membership
content advisory markers
content review state
external work references
manifest entry
```

Media export must respect:

```text
media status
media visibility
media source classification
download authority
export authority
cultural protocol restrictions
third-party rights metadata
redaction policy
```

Media export rule:

```text
A user who can view a media card is not automatically allowed to export the original media file.
```

---

## 17. Media collection export

Media collection export may include:

```text
collection metadata
collection membership
collection order
media object references
media version references
allowed files
media relations
content advisory summaries
content marker references
external work references
manifest entry
```

Collection export rule:

```text
Collection membership does not override media item policy.
Each media item remains independently permission-filtered.
```

---

## 18. Content advisory export

Content advisory export may include:

```text
content tag keys
content tag display names
content tag set keys
content marker locators
severity
audience suitability
review state
public teaching context
redacted review notes
cultural protocol flags
manifest entries
```

Content advisory export must not expose:

```text
private reviewer notes
private cultural protocol notes
restricted knowledge
community permission notes without authority
integrity-sensitive notes without authority
unapproved AI-suggested markers as approved records
```

Architecture rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 19. Cultural protocol export

Cultural protocol data must be exported only when policy allows.

Cultural protocol-related tags may include:

```text
culturally_sensitive
sacred_content
ceremonial_content
restricted_knowledge
community_permission_required
elder_review_required
seasonal_or_contextual_access
not_for_public_export
not_for_children
requires_context
```

Cultural protocol export decisions may be:

```text
include
include_summary_only
include_flag_only
redact_private_notes
omit
block_export
```

Cultural protocol export rule:

```text
AI cannot approve cultural protocol access.
AI cannot remove cultural restrictions.
AI cannot downgrade cultural sensitivity.
```

---

## 20. External work export

External works use:

```text
uckkarchive_external_work
```

External work export may include:

```text
title
creator
publisher
publication year
work type
language
edition
identifier
citation text
rights status
reference URL
content advisory markers
teaching notes when allowed
manifest entry
```

External work export must not include unauthorized copies of third-party works.

External/foreign media rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

External work package mode:

```text
reference_only
metadata_only
citation_only
included_if_licensed
redacted
omitted
```

---

## 21. Media source export

Media source records use:

```text
uckkarchive_media_source
```

Media source values:

```text
produced_by_uckk
submitted_to_uckk
imported
external_reference_only
licensed_external
public_domain
fair_use_reference
restricted_reference
```

Source ownership values:

```text
uckk_created
uckk_commissioned
member_submitted
partner_submitted
external_reference
third_party_copyright
public_domain
open_license
unknown_source
```

Media source export rule:

```text
Source classification must be exported when it affects reuse, rights, trust, teaching context, download, or export policy.
```

---

## 22. Restricted integrity export

`tool_uckkintegrity` is optional.

Ordinary archive/media/content-advisory exports must not require `tool_uckkintegrity`.

Integrity-specific export behavior must be hidden, disabled, or fail closed when `tool_uckkintegrity` is absent.

Restricted integrity exports may include:

```text
restricted archive item metadata
proof references
media references
content advisory flags
redacted summaries
manifest references
integrity export files when authorized
```

Restricted integrity exports must not include:

```text
integrity case authority
integrity sanctions
appeals authority
procedure ownership
unredacted case records without explicit authority
```

Integrity boundary rule:

```text
The archive may preserve integrity-related evidence and restricted summaries.
The archive does not own integrity case procedure or decision authority.
```

---

## 23. Export previews

Export preview services must show what will be included before generation.

Export preview may show:

```text
number of archive items
number of media objects
number of media files
number of media versions
number of content markers
number of external works
number of redacted records
number of omitted records
estimated package size
selected format
warnings
policy blocks
```

Export preview must not reveal restricted data that the user cannot view.

Preview rule:

```text
A preview is permission-filtered and policy-filtered.
A preview is not a promise that generation will succeed.
```

---

## 24. Export formats

Supported export formats may include:

```text
zip
json
csv
html
pdf_summary
manifest_only
```

Format rule:

```text
Format availability depends on export type, policy, files, media rights, content advisories, and redaction level.
```

CSV exports are appropriate for structured metadata.

ZIP exports are appropriate for file packages.

JSON exports are appropriate for portable structured records.

PDF summary exports are appropriate for human-readable summaries.

HTML exports are appropriate for browsable packages when policy allows.

Manifest-only exports are appropriate for restricted reference packages.

---

## 25. Export redaction levels

Canonical export redaction levels:

```text
none
standard
restricted
cultural
integrity
public
manifest_only
```

Redaction level meaning:

| Level | Meaning |
|---|---|
| `none` | No redaction beyond normal permission filtering. |
| `standard` | Private notes and unsafe metadata are redacted. |
| `restricted` | Restricted records are summarized or omitted unless authorized. |
| `cultural` | Cultural protocol details are redacted or omitted according to policy. |
| `integrity` | Integrity-sensitive details are redacted or omitted according to policy. |
| `public` | Export contains only public-safe data. |
| `manifest_only` | Export contains metadata/reference manifest only. |

Redaction rule:

```text
Redaction is part of export construction, not a post-processing decoration.
```

---

## 26. Export statuses and failure handling

Export failures must be explainable to authorized users.

Failure reasons may include:

```text
permission_denied
policy_blocked
restricted_content
cultural_protocol_block
missing_file
file_area_error
manifest_error
storage_error
task_error
invalid_selection
external_work_rights_block
privacy_redaction_block
```

Failure handling rule:

```text
Failure messages must be useful for troubleshooting without leaking restricted data.
```

---

## 27. Scheduled export tasks

Scheduled export task:

```text
classes/task/generate_archive_exports.php
```

Related cleanup task:

```text
classes/task/purge_expired_exports.php
```

Optional supporting tasks:

```text
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/rebuild_content_marker_index.php
classes/task/rebuild_media_search.php
```

Task rule:

```text
Scheduled tasks reuse classes/local domain logic.
Scheduled tasks do not bypass policy checks for generated outputs.
```

---

## 28. Export services

Required export-related external services:

```text
classes/external/get_export_preview.php
classes/external/export_items.php
classes/external/export_media.php
classes/external/export_collection.php
classes/external/get_export_status.php
```

Content advisory and external work services may support export preparation:

```text
classes/external/get_content_markers.php
classes/external/get_content_tags.php
classes/external/get_content_tag_sets.php
classes/external/get_external_works.php
classes/external/get_external_work.php
```

Service rule:

```text
Export services must validate parameters, resolve context, check capabilities, apply policy, filter restricted data, and return only authorized information.
```

---

## 29. Export UI

Export UI may include:

```text
export form
export preview
selected item summary
selected media summary
redaction summary
content advisory warning summary
cultural protocol warning summary
external work reference summary
format selector
export status panel
download button
failure message panel
```

Relevant form:

```text
classes/form/export_form.php
```

Relevant output classes:

```text
classes/output/content_advisory_panel.php
classes/output/media_card.php
classes/output/media_collection.php
classes/output/provenance_panel.php
```

Relevant template areas:

```text
templates/content_advisory_panel.mustache
templates/media_card.mustache
templates/media_collection.mustache
templates/provenance_panel.mustache
```

Relevant AMD module:

```text
amd/src/export.js
```

UI rule:

```text
The UI displays policy-filtered export information.
The UI does not decide export authority.
```

---

## 30. Export event model

Export-related events include:

```text
classes/event/archive_item_exported.php
classes/event/media_exported.php
```

Export events should record:

```text
context id
export id
export uuid
export type
actor user id
object id when applicable
object uuid when applicable
created time
```

Export events must not expose:

```text
raw file content
private notes
restricted metadata
private cultural protocol notes
integrity-sensitive details
redacted data
```

Event rule:

```text
Events audit successful state changes.
Events are not export manifests.
```

---

## 31. Privacy and exports

Exports may contain personal data.

Privacy-sensitive export data includes:

```text
archive item authorship
media submitter metadata
reviewer metadata
validator metadata
revision actors
content marker creators
content reviewers
external work notes
restricted notes
private review notes
cultural protocol notes
export actor metadata
export manifest metadata
```

Privacy rule:

```text
A user may receive their own personal data through Moodle Privacy API.
A user must not receive restricted cultural, integrity, third-party, or other user data merely because it is stored near their record.
```

Privacy provider must account for export records and export files.

---

## 32. Backup and restore of exports

Backup may include export metadata when appropriate.

Backup may include export files when policy and backup settings allow.

Restore must preserve or reconstruct:

```text
export records
export status where appropriate
manifest references
file references
redaction metadata
actor references where possible
archive item mappings
media mappings
content marker mappings
external work mappings
```

Restore rule:

```text
Restored export packages must not become more accessible than they were before backup.
```

---

## 33. Retention and expiry

Export packages must support retention rules.

Retention controls:

```text
how long export files remain downloadable
when export package files expire
when manifests remain as audit records
when files are purged
when metadata is retained
when soft-deleted exports are hidden
```

Retention rule:

```text
Export files may expire before export metadata is deleted.
```

Expired exports must not be downloadable.

Revoked exports must not be downloadable.

Soft-deleted exports must not appear in normal export lists.

---

## 34. Report plugin integration

`mod_uckkarchive` may expose safe data for `report_uckk`.

Safe integration may include:

```text
summary counts
archive item counts
media counts
validation state counts
content advisory counts
restricted record counts
export counts
redaction counts
course-level summary data
program-level summary data when authorized
```

`report_uckk` may use this data for institutional dashboards.

Integration rule:

```text
report_uckk may report on archive data.
report_uckk does not own archive records.
mod_uckkarchive does not become report_uckk.
```

---

## 35. Reporting-safe fields

Reporting-safe fields may include:

```text
archive id
course id
context id
item count
media count
validated count
restricted count
content marker count
external work count
export count
last activity time
status counts
validation counts
media type counts
redaction counts
```

Reporting-safe fields must not include:

```text
raw restricted content
private notes
cultural protocol private details
integrity case details
unauthorized personal data
unredacted external work notes
```

Reporting rule:

```text
Aggregated reporting must still respect privacy, cultural protocol, and institutional authority boundaries.
```

---

## 36. Export package structure

A ZIP export package should use a predictable structure.

Recommended package layout:

```text
manifest.json
README.txt
items/
media/
media/originals/
media/derivatives/
media/previews/
media/thumbnails/
media/captions/
media/transcripts/
proofs/
kristals/
provenance/
revisions/
content_advisories/
external_works/
redactions/
```

Package layout rule:

```text
Package structure must match the manifest.
The manifest is the authoritative index.
```

---

## 37. External work locator examples

External work exports may include locators without including the external work itself.

Examples:

```text
Movie Maïna -> sexual_violence -> 01:12:30-01:15:10
Book The Body Keeps the Score -> sexual_violence -> page 42-45
PDF -> culturally_sensitive -> page 7
Audio -> grief_or_mourning -> 00:08:12-00:09:40
Website -> colonial_violence -> url_fragment #section-3
```

Locator rule:

```text
Locators make advisories useful without requiring unauthorized storage or export of third-party content.
```

---

## 38. Export manifest object model

Each manifest object should include:

```text
object_type
object_id
object_uuid
included
redaction_state
visibility
restricted_flags
source_classification
validation_state
provenance_state
file_entries
relations
content_advisories
external_references
```

Each file entry should include:

```text
file_area
item_id
filename
mime_type
size
content_hash
included
redaction_state
source_media_uuid
source_media_version_uuid
```

Each content advisory entry should include:

```text
content_marker_uuid
tag_key
tag_set_key
locator_type
locator_start
locator_end
severity
audience_suitability
review_state
cultural_protocol_flag
included
redaction_state
```

---

## 39. Export security rules

Export generation must enforce:

```text
context validation
capability validation
sesskey validation for web actions
parameter validation
record ownership checks
media status checks
visibility checks
download checks
export checks
content advisory checks
cultural protocol checks
retention checks
redaction checks
```

Export download must re-check:

```text
context
capability
export ownership or authority
export status
expiry
revocation
file availability
policy state
```

Security rule:

```text
Export authorization is checked at request time, generation time, and download time.
```

---

## 40. Testing requirements

Testing must cover:

```text
archive item export
media item export
media collection export
content advisory export
external work reference export
restricted export
redacted export
manifest generation
manifest redaction
export preview filtering
export service permissions
export file-area storage
export download authorization
expired export blocking
revoked export blocking
backup/restore of export metadata
privacy coverage for export records
reporting boundary with report_uckk
```

Required tests include:

```text
tests/export_test.php
tests/media_library_test.php
tests/content_advisory_test.php
tests/external_work_test.php
tests/privacy_provider_test.php
tests/services_test.php
tests/backup_restore_test.php
```

Testing rule:

```text
Tests verify final target behavior.
Tests must not depend on historical gap documents.
Tests must not require mod/uckkarchive:versionitem.
```

---

## 41. Non-negotiable export rules

```text
mod_uckkarchive owns archive/media export packages.
report_uckk owns institutional reports.
Exports are permission-filtered.
Exports are policy-filtered.
Exports are redaction-aware.
Exports are manifest-backed.
Exports are File API-backed.
Exports do not bypass visibility.
Exports do not bypass cultural protocol restrictions.
Exports do not bypass content advisory policy.
Exports do not imply ownership over external works.
Exports do not include unauthorized third-party content.
Exports do not expose private review notes.
Exports do not expose restricted integrity details without authority.
A ready export still requires authorization before download.
```

---

## 42. Final rule

```text
This document defines the final target behavior for reporting boundaries, archive/media exports, content advisory exports, external work references, manifests, redaction, retention, and package portability. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
```
