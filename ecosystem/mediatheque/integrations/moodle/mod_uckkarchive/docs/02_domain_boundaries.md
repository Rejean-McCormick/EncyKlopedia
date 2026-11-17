# 02 — Domain Boundaries

**Path:** `docs/02_domain_boundaries.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Domain ownership boundaries for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle module.

---

## 1. Purpose

This document defines the domain boundaries of `mod_uckkarchive`.

`mod_uckkarchive` is responsible for archive memory, media-library management, content advisories, cultural sensitivity markers, external work references, provenance, revision history, validation state, restricted archive metadata, and archive/media exports.

This document defines what the module owns, what it may reference, and what it must not become.

---

## 2. Core boundary rule

Canonical formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

`mod_uckkarchive` owns its internal archive, media, and content advisory domains.

It does not own external Moodle or UCKK authority domains.

Preservation does not transfer authority.

Reference does not transfer authority.

Export does not transfer authority.

---

## 3. Domain ownership map

```text
GRADE_OWNER = Moodle gradebook
REGISTRY_OWNER = local_uckk
CHALLENGE_OWNER = mod_uckkchallenge
ASSEMBLY_OWNER = mod_uckkassembly
INTEGRITY_OWNER = tool_uckkintegrity
REPORT_OWNER = report_uckk
ARCHIVE_OWNER = mod_uckkarchive
```

Ownership rule:

```text
The plugin that owns a workflow remains the authority for that workflow.
mod_uckkarchive may preserve evidence, media, summaries, exports, provenance, and snapshots from other workflows.
mod_uckkarchive must not become the workflow authority for those external domains.
```

---

## 4. What `mod_uckkarchive` owns

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
audience suitability rules
export packages
export manifests
```

`mod_uckkarchive` owns the following internal engines:

```text
archive engine
media library engine
content advisory engine
provenance engine
revision engine
validation engine
export engine
```

---

## 5. What `mod_uckkarchive` does not own

`mod_uckkarchive` does not own:

```text
grades
gradebook records
official transcripts
course enrolment authority
site-wide user identity authority
global UCKK registry records
challenge workflow state
Assembly decision authority
integrity case procedure state
institutional reporting authority
external work copyright ownership
external work publication rights
```

The module may preserve or reference records from these domains, but it does not become their authority.

---

## 6. Moodle platform boundary

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

Moodle platform boundary rule:

```text
mod_uckkarchive must not bypass Moodle contexts.
mod_uckkarchive must not bypass Moodle capabilities.
mod_uckkarchive must not bypass Moodle File API.
mod_uckkarchive must not bypass Moodle Privacy API.
mod_uckkarchive must not bypass Moodle Backup/Restore API.
mod_uckkarchive must not bypass Moodle External Services API.
```

---

## 7. Gradebook boundary

Moodle gradebook owns:

```text
grades
grade items
grade history
final marks
assessment scores
official transcript-relevant results
```

`mod_uckkarchive` may own:

```text
proof records
media evidence
archive evidence
portfolio evidence
validation notes
exported evidence packages
```

Boundary rule:

```text
Archive evidence is not a grade.
Validation is not a grade.
Media completion is not a grade unless Moodle gradebook receives a grade through proper Moodle APIs.
```

`mod_uckkarchive` must not write arbitrary gradebook records as archive state.

---

## 8. Registry boundary

`local_uckk` owns:

```text
UCKK registry records
institutional configuration
program structures
global UCKK profiles
cross-plugin identity mapping
shared UCKK configuration
```

`mod_uckkarchive` may reference:

```text
program ids
course ids
cohort ids
institutional labels
registry-derived display metadata
```

Boundary rule:

```text
Registry data may contextualize archive records.
Registry data remains owned by local_uckk.
```

---

## 9. Course boundary

Moodle course and course module context own:

```text
course membership
course visibility
course roles
course groups
course module visibility
completion framework
```

`mod_uckkarchive` owns:

```text
archive activity instance
archive item records
media library records inside the activity context
content advisories linked to archive/media records
proof records
Kristals
provenance
revision history
validation state
exports
```

Boundary rule:

```text
Course context controls where the module lives.
The archive/media module controls its internal records.
```

---

## 10. Challenge boundary

`mod_uckkchallenge` owns:

```text
challenge workflow
challenge state
challenge rules
challenge submissions
challenge evaluation process
challenge result authority
```

`mod_uckkarchive` may preserve:

```text
challenge evidence
challenge media
challenge proof packages
challenge provenance
challenge snapshots
challenge-related content advisories
challenge-related export packages
```

Boundary rule:

```text
Archive proof is not the challenge workflow.
Archive preservation does not decide challenge outcome.
```

---

## 11. Assembly boundary

`mod_uckkassembly` owns:

```text
motions
deliberations
votes
minutes workflow
decision workflow
Assembly authority
final Assembly decisions
```

`mod_uckkarchive` may preserve:

```text
Assembly minutes snapshots
decision snapshots
attachments
minority reports
supporting media
public decision packages
restricted decision records
content advisories for Assembly materials
export packages
```

Boundary rule:

```text
The archive preserves Assembly memory.
The Assembly remains the decision authority.
```

---

## 12. Integrity boundary

`tool_uckkintegrity` owns:

```text
integrity case workflow
case participants
findings
sanctions
appeals
closure
restricted procedure state
```

`tool_uckkintegrity` is an optional integration.

Ordinary archive, media, and content advisory operation must not require `tool_uckkintegrity`.

`mod_uckkarchive` may preserve:

```text
integrity evidence
restricted proof files
restricted media
case-linked archive records
integrity export packages
restricted content advisories
provenance records
redacted summaries
```

Boundary rule:

```text
The archive may preserve integrity evidence.
The archive does not decide integrity cases.
Integrity-specific archive features must be hidden, disabled, or fail closed when tool_uckkintegrity is absent.
```

---

## 13. Reporting boundary

`report_uckk` owns:

```text
institutional dashboards
institutional reports
cross-course reports
cross-plugin reports
cohort reports
program reports
administrative reporting exports
```

`mod_uckkarchive` owns:

```text
archive export packages
media export packages
collection export packages
manifest.json files
archive/media provenance bundles
permission-filtered archive export payloads
```

Boundary rule:

```text
Archive exports preserve archive/media records.
Reports present institutional views.
Archive export is not institutional reporting authority.
```

---

## 14. External work boundary

`mod_uckkarchive` may reference external works.

External works include:

```text
film
book
article
podcast
website
external video
external image
public archive item
third-party PDF
other
```

Canonical external work table:

```text
uckkarchive_external_work
```

External/foreign media boundary rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
The archive must not store unauthorized copies of external works.
```

---

## 15. Media source boundary

Canonical media source table:

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

Media source boundary rule:

```text
Media source describes origin and rights context.
Media source does not grant access by itself.
Media source does not override policy, visibility, retention, redaction, or cultural protocol rules.
```

---

## 16. Content advisory boundary

`mod_uckkarchive` owns a content advisory subsystem.

Canonical subsystem name:

```text
content advisories, cultural sensitivity tags, content markers, external works, reviews, and audience suitability rules
```

Required tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_media_source
```

Content advisory boundary rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

A content advisory may affect:

```text
display warnings
teaching context
audience suitability
access prompts
restricted visibility
cultural protocol review
export filtering
review workflow
redaction decisions
```

A content advisory must not silently delete or hide records without policy.

---

## 17. Cultural protocol boundary

Cultural protocol data may include:

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

Cultural protocol boundary rule:

```text
Cultural protocol rules are access and context rules.
They do not become external ownership authority.
They must be enforced through module policy before display, download, export, or reuse.
```

---

## 18. Content marker boundary

Canonical content marker table:

```text
uckkarchive_content_marker
```

A content marker may point to:

```text
archive item
media object
media version
external work
manual reference
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

Content marker boundary rule:

```text
A content marker locates advisory meaning.
A content marker does not copy external content.
A content marker does not transfer external rights.
```

---

## 19. Content review boundary

Canonical content review table:

```text
uckkarchive_content_review
```

Content review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Content review boundary rule:

```text
AI may suggest tags or markers.
Human review is required before advisory status becomes approved.
AI cannot approve cultural protocol access.
AI cannot remove cultural restrictions.
```

---

## 20. Content tag set boundary

Canonical content tag set table:

```text
uckkarchive_content_tag_set
```

Content tag sets group reusable vocabularies.

Examples:

```text
general_advisories
cultural_protocols
classroom_suitability
integrity_sensitive
youth_access
```

Content tag set boundary rule:

```text
Tag sets organize advisory vocabulary.
Tag sets do not decide access alone.
Access decisions belong to policy classes.
```

---

## 21. AI assistance boundary

AI may assist with:

```text
metadata suggestions
content advisory suggestions
content marker suggestions
summary drafts
classification drafts
transcript drafts
caption drafts
search enhancement
```

AI must not:

```text
validate archive records
invalidate archive records
approve content reviews
approve cultural protocol access
remove cultural restrictions
decide grade outcomes
decide integrity outcomes
decide Assembly outcomes
override human review
```

AI boundary rule:

```text
AI assistance is provenance.
AI assistance is not authority.
```

---

## 22. File API boundary

All files belong to Moodle File API.

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

File API boundary rule:

```text
File areas are declared centrally in classes/local/file_area_registry.php.
All controllers, services, pluginfile handling, privacy provider, backup, restore, and tests use the registry.
No production archive/media files live in unmanaged public folders.
```

---

## 23. Privacy boundary

`mod_uckkarchive` owns privacy responsibilities for personal data stored in its own tables and file areas.

Privacy scope includes:

```text
archive items
proofs
Kristals
provenance
revisions
exports
media objects
media versions
media collections
media relations
media tags
content advisories
content markers
content reviews
external work references
media source records
user-linked files
restricted metadata
```

Privacy boundary rule:

```text
Privacy API behavior belongs to mod_uckkarchive for records stored by mod_uckkarchive.
External authority records remain outside the archive privacy surface unless copied into archive-owned records.
```

---

## 24. Backup and restore boundary

Backup includes module-owned records.

Restore reconstructs module-owned records.

Backup/restore scope includes:

```text
activity instance
archive items
proofs
Kristals
provenance
revisions
exports
media objects
media versions
media files
media collections
media relations
media tags
content tags
content tag sets
content markers
content reviews
external works
media source records
file areas
manifest records
```

Backup/restore boundary rule:

```text
Restore must not create grades.
Restore must not create external workflow authority.
Restore must not turn external work references into owned media.
Restore must not make restricted or culturally restricted records public.
```

---

## 25. Export boundary

`mod_uckkarchive` owns archive/media export packages.

Canonical manifest filename:

```text
manifest.json
```

Exports may include:

```text
archive records
media records
media versions
file hashes
media files when permitted
collections
relations
tags
content advisories
content markers
content reviews
external work metadata
provenance
revision history
validation state
redaction state
restricted flags
```

Export boundary rule:

```text
Exports are portable and explainable.
Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.
```

---

## 26. Capability boundary

Capabilities are gates.

Canonical archive capabilities:

```text
mod/uckkarchive:addinstance
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Canonical media capabilities:

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

Canonical content advisory capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:manageexternalworks
```

Capability boundary rule:

```text
Capabilities do not replace policy.
Policy classes enforce context, ownership, visibility, status, validation state, restricted state, content advisory rules, cultural protocol rules, retention, and redaction.
```

Removed capability:

```text
mod/uckkarchive:versionitem = not used
```

---

## 27. Policy class boundary

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
content advisory rules
cultural protocol rules
download authority
export authority
privacy policy
retention policy
redaction policy
workflow rules
```

Policy boundary rule:

```text
Controllers coordinate.
Services expose contracts.
Forms collect input.
Output classes format data.
Templates render.
AMD modules provide UI behavior.
Policy classes decide authority.
```

---

## 28. Database boundary

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

Database boundary rule:

```text
The database stores module-owned records.
The database does not store binary media content directly in custom fields.
The database does not duplicate external workflow authority.
```

---

## 29. Duplication and portability boundary

The module is designed to be self-contained enough to be duplicated for other archive/media use cases.

Portable identity relies on:

```text
uuid
manifest.json
file hashes
media version UUIDs
external work UUIDs
content marker UUIDs
collection UUIDs
provenance records
```

Duplication boundary rule:

```text
Duplication copies archive/media module records.
Duplication must not copy external authority as if it were owned by the archive.
```

---

## 30. Final boundary rule

```text
mod_uckkarchive owns archive memory, media library objects, content advisories,
cultural protocol metadata, external work references, provenance, revisions,
validation state, restricted metadata, and export packages.

It uses Moodle for context, users, roles, capabilities, files, privacy, backup,
restore, services, events, settings, language, rendering, and scheduled tasks.

It does not own grades, transcripts, enrolments, registry authority, challenge
workflow, Assembly authority, integrity case authority, institutional reporting
authority, or external copyright ownership.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
