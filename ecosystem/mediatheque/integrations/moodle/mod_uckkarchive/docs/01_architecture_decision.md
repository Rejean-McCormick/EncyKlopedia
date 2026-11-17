# 01 — Architecture Decision

**Path:** `docs/01_architecture_decision.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Architecture decision for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Core decision

`mod_uckkarchive` is a Moodle-native activity module with a self-contained internal archive, media library, and content advisory system.

Canonical formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

The module is installed, configured, secured, rendered, backed up, restored, and governed through Moodle APIs.

Inside that Moodle boundary, the module owns its own archive, media library, content advisory, cultural protocol, external work, provenance, validation, versioning, and export domain.

---

## 2. Module definition

Canonical module definition:

```text
mod_uckkarchive = self-contained Moodle activity module for archive memory, media library management, and content advisory governance.
```

The module is not only a file attachment feature.

The module is not only an archive item list.

The module is not only a didactic resource activity.

The module is the UCKK archive/media/content-advisory memory layer.

---

## 3. Internal ownership

`mod_uckkarchive` owns internally:

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
audience suitability rules
export packages
export manifests
```

The module owns three internal engines:

```text
archive engine
media library engine
content advisory engine
```

The archive engine manages institutional, pedagogical, evidential, validation, revision, and provenance memory.

The media library engine manages media objects, versions, files, collections, tags, relations, derivatives, transcripts, captions, thumbnails, previews, and export identity.

The content advisory engine manages advisories, cultural sensitivity tags, cultural protocol notes, content markers, locators, suitability rules, review state, and external work references.

---

## 4. Moodle ownership boundary

`mod_uckkarchive` uses Moodle for:

```text
plugin lifecycle
course module context
course visibility
users
roles
capabilities
groups
File API
Privacy API
Backup API
Restore API
External Services API
events
settings
language strings
rendering
scheduled tasks
```

`mod_uckkarchive` must not bypass Moodle’s context, capability, privacy, backup/restore, file, event, task, rendering, or service systems.

Moodle remains the host platform.

`mod_uckkarchive` remains the self-contained domain module inside Moodle.

---

## 5. External domain boundaries

`mod_uckkarchive` must not own external UCKK or Moodle authority domains.

Canonical ownership boundaries:

```text
GRADE_OWNER = Moodle gradebook
REGISTRY_OWNER = local_uckk
CHALLENGE_OWNER = mod_uckkchallenge
ASSEMBLY_OWNER = mod_uckkassembly
INTEGRITY_OWNER = tool_uckkintegrity
REPORT_OWNER = report_uckk
ARCHIVE_OWNER = mod_uckkarchive
```

Boundary rules:

```text
mod_uckkarchive does not own grades.
mod_uckkarchive does not own transcripts.
mod_uckkarchive does not own enrolment authority.
mod_uckkarchive does not own administrative registry records.
mod_uckkarchive does not own challenge workflow state.
mod_uckkarchive does not own Assembly decision authority.
mod_uckkarchive does not own integrity case authority.
mod_uckkarchive does not own institutional reporting authority.
```

The archive may preserve records, evidence, media, attachments, summaries, content advisories, cultural protocol notes, external work references, or exported snapshots from those domains.

Preservation does not transfer authority.

---

## 6. Integrity integration decision

`tool_uckkintegrity` is an optional integration.

Ordinary archive, media-library, and content-advisory operation must not require `tool_uckkintegrity`.

Integrity-specific archive features must be hidden, disabled, or fail closed when `tool_uckkintegrity` is absent.

The archive may preserve integrity-related evidence, media, restricted records, content markers, provenance, and export packages.

The archive does not own integrity case procedure, findings, sanctions, appeals, or closure.

---

## 7. Archive decision

Archive items are first-class memory objects.

Canonical archive table:

```text
uckkarchive_item
```

Archive items represent preserved UCKK memory such as:

```text
proof
decision snapshot
minutes
challenge result
course work
portfolio item
Kristal source
integrity summary
public summary
institutional source
pedagogical source
```

Archive items may link to media objects, content advisories, content markers, external works, Kristals, proofs, collections, provenance records, revision records, and export manifests.

Archive items are not grades.

Archive items are not administrative records.

Archive items are not final Assembly authority.

Archive items are not integrity case authority.

---

## 8. Media-library decision

Media is a first-class domain object in the target architecture.

Canonical decision:

```text
media object = uckkarchive_media
media version = uckkarchive_media_version
media collection = uckkarchive_media_collection
media relation = uckkarchive_media_relation
media tag = uckkarchive_media_tag
```

Media is not merely a subtype of `uckkarchive_item`.

Media is not stored as a public folder.

Media is not stored directly as binary data in custom database fields.

Media files are stored through Moodle File API.

Media metadata, identity, versions, relations, collections, tags, lifecycle state, file references, source records, and advisory links are stored in archive-owned tables.

---

## 9. Content advisory decision

Content advisories are first-class domain objects.

The content advisory system manages:

```text
content advisories
cultural sensitivity tags
cultural protocol tags
content tag sets
content markers
content reviews
external works
foreign media references
media source records
audience suitability rules
review states
```

Canonical rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

The system must support content that is not suitable for everyone.

Examples:

```text
film with sexual violence at a timecode range
book with sexual violence at a page range
PDF with culturally sensitive content on a page
audio with grief or mourning content at a timestamp
external work with colonial violence in a chapter
```

The system uses the term `content advisory` internally.

The user-facing UI may use:

```text
content advisory
content warning
trigger warning
cultural advisory
cultural protocol
audience suitability
```

The database/system name must not use `trigger` alone, because it can be confused with database triggers.

---

## 10. External work decision

External and foreign media are first-class reference targets.

Canonical table:

```text
uckkarchive_external_work
```

External works represent works not produced by UCKK that may be referenced, taught, reviewed, tagged, or connected to archive/media records.

External work types include:

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

External work rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 11. Media source decision

Every media object must be able to describe its source.

Canonical table:

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

Source rules:

```text
Source describes origin and rights context.
Source does not grant access by itself.
Source does not override content advisory, cultural protocol, visibility, or retention policy.
```

---

## 12. Archive and media relationship

Archive items and media objects are separate but connected.

A media object can be linked to one or more archive items.

An archive item can reference one or more media objects.

The relationship is represented through the media relation and archive relation model, not through duplicated files.

Canonical media relation examples:

```text
belongs_to_item
belongs_to_kristal
belongs_to_collection
is_derivative_of
is_translation_of
is_excerpt_of
is_proof_for
is_source_for
replaces
references
duplicates
references_external_work
contains_content_marker
```

Relations describe meaning.

Relations do not transfer ownership to external plugins or external rights holders.

---

## 13. Database decision

Required archive tables:

```text
uckkarchive
uckkarchive_item
uckkarchive_proof
uckkarchive_kristal
uckkarchive_prov
uckkarchive_rev
uckkarchive_export
```

Required media library tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
```

Required content advisory and external-work tables:

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

UUID rule:

```text
Archive objects, media objects, content markers, external works, and export packages use UUIDs for export, restore, duplication, and cross-site portability.
```

---

## 14. File storage decision

All files are stored through Moodle File API.

Component:

```text
mod_uckkarchive
```

Canonical archive file areas:

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

Canonical media file areas:

```text
media_original
media_preview
media_thumbnail
media_derivative
media_caption
media_transcript
media_attachment
```

Canonical content advisory file areas:

```text
content_review_files
external_work_reference_files
cultural_protocol_files
```

File-area rule:

```text
classes/local/file_area_registry.php is the central file-area registry.
All controllers, services, pluginfile handling, privacy provider, backup, restore, and tests use the registry.
```

Forbidden storage:

```text
No production archive/media files in unmanaged public folders.
No binary media files directly in custom database fields.
No direct public file URLs as authority.
```

---

## 15. Capability decision

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

Capability rules:

```text
Capabilities are gates, not full authority.
Policy classes enforce context, ownership, visibility, status, validation state, restricted state, content advisory rules, cultural protocol rules, retention, and redaction.
```

Removed capability:

```text
mod/uckkarchive:versionitem = not used
```

Versioning permissions:

```text
archive item revision = mod/uckkarchive:reviseitem
media versioning = mod/uckkarchive:versionmedia
```

---

## 16. Policy architecture decision

Policy must be centralized.

Archive policy belongs in:

```text
classes/local/archive_policy.php
```

Media policy belongs in:

```text
classes/local/media_policy.php
```

Content advisory policy belongs in:

```text
classes/local/content_policy.php
```

Policy classes enforce:

```text
context access
capability gates
ownership
visibility
media status
archive item status
validation state
restricted state
download authority
export authority
privacy policy
retention policy
redaction policy
content advisory policy
cultural protocol policy
audience suitability rules
workflow rules
```

Controllers, AMD modules, templates, output classes, and forms must not duplicate policy decisions.

---

## 17. Media lifecycle decision

Canonical media states:

```text
draft
submitted
active
restricted
superseded
archived
deleted_soft
```

Media lifecycle rule:

```text
File existence is not media availability.
Media status controls usability.
Visibility controls access.
Policy controls download and export.
Content advisories describe suitability, cultural protocol, and access conditions.
Retention controls deletion.
```

---

## 18. Archive lifecycle decision

Canonical archive item statuses:

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

Canonical validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Validation rule:

```text
Validation is human-final.
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
AI cannot approve cultural protocol access.
```

---

## 19. Visibility decision

Canonical visibility values:

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

Compatibility rule:

```text
institutional must normalize to institution.
```

Visibility rule:

```text
Visibility controls who may see the record.
Capability controls whether the user may attempt the action.
Policy resolves final access.
```

---

## 20. Content advisory vocabulary decision

Content advisory tag examples:

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
```

Cultural protocol tag examples:

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

Audience suitability values:

```text
general
guided
mature
restricted
restricted_cultural
restricted_integrity
staff_only
```

Content advisory severity values:

```text
notice
moderate
strong
restricted
```

Content advisory review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Content tag set rule:

```text
uckkarchive_content_tag_set groups advisory tags into reusable vocabularies.
Examples: general_advisories, cultural_protocols, classroom_suitability, integrity_sensitive, youth_access.
```

Content review rule:

```text
uckkarchive_content_review records human review of content markers, advisory tags, cultural protocol notes, suitability, and restriction decisions.
AI may suggest tags or markers, but human review is required before advisory status becomes approved.
```

---

## 21. Content marker and locator decision

Canonical content marker table:

```text
uckkarchive_content_marker
```

Content marker purpose:

```text
Link a content advisory or cultural protocol tag to a precise location inside an internal media object, archive item, media version, external work, or manual reference.
```

Canonical locator types:

```text
timecode
timecode_range
page
page_range
chapter
chapter_range
section
section_range
paragraph
paragraph_range
scene
track
timestamp
url_fragment
manual_reference
```

Canonical locator examples:

```text
Movie Maïna -> sexual_violence -> 01:12:30-01:15:10
Book The Body Keeps the Score -> sexual_violence -> page 42-45
PDF -> culturally_sensitive -> page 7
Audio -> grief_or_mourning -> 00:08:12-00:09:40
Website -> colonial_violence -> url_fragment #section-3
```

Content marker rule:

```text
A content marker can point to internal media, archive items, media versions, external works, or manual references.
A content marker must include enough locator information to be useful without storing unauthorized copies of external content.
```

---

## 22. Provenance decision

Every meaningful archive, media, content marker, content review, and external work reference must preserve provenance.

Canonical provenance values:

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

Provenance rule:

```text
Provenance explains origin.
Provenance does not grant authority by itself.
```

Media and archive provenance must support:

```text
source description
source component
source identifier
creation actor
modification actor
validation actor
review actor
file hash
manifest reference
import metadata
AI-assistance flag
external work reference
content review reference
```

---

## 23. Export decision

Exports are portable and explainable.

Every archive/media export package contains a manifest.

Canonical manifest filename:

```text
manifest.json
```

Manifest includes:

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

Export rule:

```text
Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.
```

---

## 24. Documentation decision

The documentation set describes the final target behavior.

Documentation must not keep a historical gap register.

Documentation must not include process-only acceptance checklists.

Documentation must not describe the old media-as-attachment model as an active option.

The architecture documents are written so AI can generate code from them in separate conversations while remaining aligned through shared variables.

---

## 25. Final architecture rule

```text
mod_uckkarchive is a self-contained archive, media-library, and content-advisory Moodle activity module.

It owns archive records, media records, media versions, collections, relations,
tags, content advisories, cultural protocol notes, external work references,
proofs, Kristals, provenance, revisions, validation state, restricted metadata,
export packages, and export manifests.

It uses Moodle for plugin lifecycle, contexts, users, capabilities, File API,
Privacy API, Backup/Restore API, events, settings, language, rendering,
scheduled tasks, and external services.

The module is modular enough to troubleshoot independently and to duplicate
for future archive/media/content-advisory use cases without becoming detached
from Moodle.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
