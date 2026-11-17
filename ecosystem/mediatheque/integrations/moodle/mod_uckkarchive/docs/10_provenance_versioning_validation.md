# 10 — Provenance, Versioning and Validation

**Path:** `docs/10_provenance_versioning_validation.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Provenance, archive revisions, media versions, content advisory reviews, validation states, contestability, trust rules, and auditability for the self-contained UCKK Archive module.

---

## 1. Purpose

This document defines how `mod_uckkarchive` records, verifies, revises, validates, contests, invalidates, preserves, and exports archive/media memory.

The module is a self-contained Moodle activity module for:

```text
archive memory
media library management
content advisory governance
cultural sensitivity tagging
external/foreign media references
exportable archive/media packages
```

This document applies to:

```text
archive items
proof records
Kristals
media objects
media versions
media collections
media relations
media tags
content advisory tags
content tag sets
content markers
content reviews
external works
foreign media references
media source records
provenance records
revision records
validation state
restricted records
export packages
export manifests
```

---

## 2. Core rule

Canonical architecture formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

Provenance, versioning, validation, and review are internal authority functions of `mod_uckkarchive`.

The module uses Moodle for:

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
external services
scheduled tasks
```

The module owns its own:

```text
archive provenance
media provenance
media versions
archive revisions
content advisory reviews
cultural protocol review records
validation state
contestability metadata
export manifests
```

---

## 3. Canonical ownership

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

## 4. Required tables

Archive tables involved in provenance, versioning, and validation:

```text
uckkarchive_item
uckkarchive_proof
uckkarchive_kristal
uckkarchive_prov
uckkarchive_rev
uckkarchive_export
```

Media tables involved in provenance and versioning:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
```

Content advisory and external-work tables involved in review and suitability:

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

## 5. Provenance model

Provenance explains where a record, media object, marker, review, or exported package came from.

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

A record with valid provenance is not automatically validated.

A record with AI-assisted provenance is not automatically rejected.

A record imported from another system is not automatically trusted.

Human review and validation rules decide trust state.

---

## 6. Provenance records

`uckkarchive_prov` stores structured provenance for archive-owned records.

It must support provenance for:

```text
archive items
proofs
Kristals
media objects
media versions
content markers
content reviews
external works
export packages
```

A provenance record should support:

```text
uuid
context id
course id
course module id
archive id
target table
target id
target uuid
source type
source component
source identifier
source title
source URL or reference
source description
actor user id
created time
modified time
import time
AI-assistance flag
human review flag
file hash
manifest reference
notes
metadata JSON
```

Sensitive provenance notes must be permission-filtered.

Provenance records must not expose private cultural protocol details to users who do not have authority to view them.

---

## 7. Archive item lifecycle

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

Status meaning:

| Status | Meaning |
|---|---|
| `draft` | Editable record not submitted for review. |
| `submitted` | Submitted for review or validation. |
| `under_review` | Currently being reviewed by an authorized human reviewer. |
| `validated` | Human reviewer has validated the record. |
| `published` | Record is visible according to its visibility policy. |
| `restricted` | Record exists but has restricted access. |
| `contested` | Record is challenged, disputed, or awaiting clarification. |
| `invalidated` | Record is preserved but marked invalid or no longer reliable. |
| `superseded` | Record has been replaced by a newer record or revision. |
| `archived` | Record is retained for memory, audit, or preservation. |

Status rule:

```text
Archive status controls workflow state.
Visibility controls who can see it.
Validation state controls trust.
Policy controls actions.
```

---

## 8. Media lifecycle

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

Status meaning:

| Status | Meaning |
|---|---|
| `draft` | Media metadata or file is being prepared. |
| `submitted` | Media is submitted for review, tagging, or validation. |
| `active` | Media is available according to policy and visibility. |
| `restricted` | Media exists but access is restricted. |
| `superseded` | Media has been replaced by a newer version or object. |
| `archived` | Media is retained for preservation or audit. |
| `deleted_soft` | Media is hidden from normal use but retained according to retention rules. |

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

## 9. Validation states

Canonical validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Validation meaning:

| State | Meaning |
|---|---|
| `unverified` | No human validation has occurred. |
| `human_reviewed` | A reviewer has examined the record but has not fully verified it. |
| `verified` | A reviewer has validated the record as reliable for its stated use. |
| `contested` | The record is disputed or under challenge. |
| `invalidated` | The record is preserved but marked unreliable or incorrect. |
| `archived` | The record is preserved for memory, history, or audit. |

Validation rules:

```text
Validation is human-final.
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
AI cannot approve cultural protocol access.
```

AI may assist with:

```text
suggesting tags
suggesting summaries
suggesting locator candidates
suggesting duplicate detection
suggesting metadata normalization
suggesting provenance classification
```

AI output must remain:

```text
ai_assisted
unverified
human-review required
```

until reviewed by an authorized human.

---

## 10. Revision model for archive items

Archive item revision uses:

```text
uckkarchive_rev
```

Archive revision permission:

```text
mod/uckkarchive:reviseitem
```

Removed capability:

```text
mod/uckkarchive:versionitem = not used
```

An archive revision must be created when a meaningful change occurs to:

```text
title
description
public summary
visibility
validation state
status
provenance
restricted metadata
source reference
linked proof
linked Kristal
linked media
content advisory relationship
export-relevant metadata
```

An archive revision should record:

```text
uuid
archive item id
archive item uuid
revision number
previous revision id
actor user id
change reason
change summary
changed fields
old values where safe
new values where safe
created time
validation state before change
validation state after change
status before change
status after change
visibility before change
visibility after change
metadata JSON
```

Restricted old/new values must be redacted when viewed by users without authority.

---

## 11. Media versioning model

Media versioning uses:

```text
uckkarchive_media_version
```

Media version permission:

```text
mod/uckkarchive:versionmedia
```

A media version must be created when there is a meaningful change to:

```text
original file
replacement file
preview file
derivative file
thumbnail
caption
transcript
technical metadata
file hash
source classification
license/rights metadata
access restriction
cultural protocol restriction
content advisory state
```

A media version should record:

```text
uuid
media id
media uuid
version number
previous version id
actor user id
change reason
change summary
file area
file item id
filename
mime type
file size
content hash
source type
rights metadata
created time
metadata JSON
```

Media versioning rule:

```text
Media files are not silently overwritten.
Meaningful replacement creates a new media version.
Derived files remain linked to their source version.
```

---

## 12. Media source records

Media source classification uses:

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

Media source records must clarify:

```text
whether UCKK produced the media
whether the media was submitted to UCKK
whether the media was imported
whether the media is only referenced
whether UCKK may store a copy
whether UCKK may export a copy
whether UCKK may show previews
whether teaching use requires context
whether access is culturally restricted
```

External/foreign media rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 13. External work records

External works use:

```text
uckkarchive_external_work
```

External work types:

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

External work records should support:

```text
uuid
title
creator
publisher
publication year
work type
language
edition
ISBN or identifier
URL or catalog reference
rights status
source ownership
description
citation text
metadata JSON
created time
modified time
```

External work records may be linked to:

```text
archive items
media objects
content markers
content reviews
media source records
export manifests
```

External work records may store references and advisory metadata without storing the full external work.

---

## 14. Content advisory model

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

Canonical content advisory tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

Architecture rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

Content advisories may apply to:

```text
archive item
media object
media version
media collection
external work
specific timecode
specific page
specific chapter
specific paragraph
specific scene
manual reference
```

---

## 15. Content tags

`uckkarchive_content_tag` defines reusable advisory and cultural protocol tags.

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

Content tag fields should support:

```text
id
uuid
tag key
display name
description
tag type
severity default
audience default
cultural protocol flag
restricted flag
active flag
sort order
created time
modified time
```

---

## 16. Content tag sets

`uckkarchive_content_tag_set` groups advisory tags into reusable vocabularies.

Examples:

```text
general_advisories
cultural_protocols
classroom_suitability
integrity_sensitive
youth_access
```

A tag set should support:

```text
uuid
key
display name
description
scope
active flag
created time
modified time
metadata JSON
```

Content tag set rule:

```text
Content tag sets organize vocabularies.
They do not replace policy.
They do not override cultural protocol review.
```

---

## 17. Content markers and locators

`uckkarchive_content_marker` links a content advisory or cultural protocol tag to a precise location inside an internal media object, archive item, media version, or external work.

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

Content marker examples:

```text
Movie Maïna -> sexual_violence -> 01:12:30-01:15:10
Book The Body Keeps the Score -> sexual_violence -> page 42-45
PDF -> culturally_sensitive -> page 7
Audio -> grief_or_mourning -> 00:08:12-00:09:40
Website -> colonial_violence -> url_fragment #section-3
```

A content marker should support:

```text
uuid
context id
archive id
target type
target id
target uuid
external work id
external work uuid
media id
media uuid
media version id
media version uuid
tag id
tag uuid
tag set id
tag set uuid
locator type
locator start
locator end
locator label
severity
audience suitability
review state
restricted flag
cultural protocol flag
created by
reviewed by
created time
reviewed time
notes
redacted notes
metadata JSON
```

Content marker rule:

```text
A content marker can point to internal media, archive items, media versions, external works, or manual references.
A content marker must include enough locator information to be useful without storing unauthorized copies of external content.
```

---

## 18. Content reviews

`uckkarchive_content_review` records human review of content markers, advisory tags, cultural protocol notes, suitability, and restriction decisions.

Content advisory review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Content review should support:

```text
uuid
content marker id
content marker uuid
reviewer user id
review type
review state
review decision
audience suitability
severity
cultural protocol decision
restriction decision
redaction decision
export decision
teaching context note
private reviewer note
created time
modified time
reviewed time
metadata JSON
```

Content review rule:

```text
AI may suggest tags or markers, but human review is required before advisory status becomes approved.
```

Cultural review rule:

```text
Cultural protocol decisions require authorized human review.
AI cannot approve cultural access.
AI cannot remove cultural restrictions.
AI cannot downgrade cultural sensitivity.
```

---

## 19. Audience suitability

Canonical audience suitability values:

```text
general
guided
mature
restricted
restricted_cultural
restricted_integrity
staff_only
```

Suitability rule:

```text
Audience suitability is advisory and policy-relevant.
It does not automatically grant access.
It informs warnings, teaching context, filtering, exports, and restrictions.
```

---

## 20. Content advisory severity

Canonical severity values:

```text
notice
moderate
strong
restricted
```

Severity rule:

```text
Severity guides presentation and review priority.
Restricted severity requires policy evaluation before access or export.
```

---

## 21. Visibility and restrictions

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
Visibility defines the intended audience.
Restrictions define access constraints.
Policy decides whether the current user can act.
```

Content advisory restrictions may affect:

```text
viewing
download
preview
export
thumbnail display
public summary display
classroom use
youth access
external sharing
manifest disclosure
```

---

## 22. Contestability

Archive items, media metadata, content markers, and content reviews must be contestable when policy allows.

Contestable targets include:

```text
archive item validation
archive item status
media source classification
media version metadata
content tag assignment
content marker locator
audience suitability
cultural protocol classification
external work citation
provenance statement
export redaction decision
```

Contestation should record:

```text
target type
target id
target uuid
contesting user id
reason
evidence
status
reviewer
decision
created time
resolved time
metadata JSON
```

Contested records remain preserved.

Contested records must display safe warning state to authorized viewers.

---

## 23. Invalidation

Invalidation marks a record as unreliable, incorrect, or unsuitable for its previous use.

Invalidation does not automatically delete the record.

Invalidation applies to:

```text
archive item
proof
Kristal
media metadata
media version metadata
content marker
content review
external work reference
provenance record
```

Invalidation must record:

```text
actor
reason
time
target
previous state
new state
related revision
related provenance
notes
```

Invalidation rule:

```text
Invalidated records are preserved unless retention policy requires deletion.
Invalidated records must not be silently used as verified records.
```

---

## 24. Export trust model

Export packages must include enough provenance, validation, revision, media version, content advisory, and external work metadata to make the package explainable.

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
Exports are portable and explainable.
Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.
```

---

## 25. Hashing and file integrity

Media versions and export packages must preserve file integrity metadata.

File integrity metadata should include:

```text
filename
mime type
file size
content hash
file area
item id
media uuid
media version uuid
created time
source classification
```

Hashing rule:

```text
Hashes support integrity and audit.
Hashes do not grant access.
Hashes do not replace provenance.
```

---

## 26. Policy classes

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
content advisory rules
cultural protocol rules
privacy policy
retention policy
redaction policy
workflow rules
```

No controller, AMD module, template, output class, or form may replace policy classes.

---

## 27. Capabilities

Archive capabilities involved in provenance, revision, validation, and export:

```text
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Media capabilities involved in provenance and media versioning:

```text
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:editmedia
mod/uckkarchive:downloadmedia
mod/uckkarchive:versionmedia
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

Capability rule:

```text
Capabilities are gates, not full authority.
Policy classes still enforce context, ownership, visibility, status, validation state, restricted state, content advisory rules, cultural protocol rules, retention, and redaction.
```

---

## 28. Events

Events must audit successful state changes.

Relevant event classes include:

```text
classes/event/archive_item_created.php
classes/event/archive_item_validated.php
classes/event/archive_item_revised.php
classes/event/archive_item_exported.php
classes/event/media_created.php
classes/event/media_updated.php
classes/event/media_version_created.php
classes/event/media_exported.php
classes/event/content_marker_created.php
classes/event/content_marker_reviewed.php
classes/event/external_work_created.php
```

Events must include safe identifiers:

```text
context id
object id
object uuid when appropriate
related user id when safe
action type
created time
```

Events must not expose:

```text
restricted content
raw media content
private reviewer notes
private cultural protocol notes
redacted metadata
unauthorized external work details
```

---

## 29. External services

External service files related to provenance, versioning, and validation include:

```text
classes/external/update_provenance.php
classes/external/validate_item.php
classes/external/revise_item.php
classes/external/add_media_version.php
classes/external/get_media_versions.php
classes/external/get_content_tags.php
classes/external/get_content_tag_sets.php
classes/external/get_content_markers.php
classes/external/add_content_marker.php
classes/external/update_content_marker.php
classes/external/delete_content_marker.php
classes/external/review_content_marker.php
classes/external/get_external_works.php
classes/external/get_external_work.php
classes/external/add_external_work.php
classes/external/update_external_work.php
```

Service rule:

```text
External services must check context, capability, visibility, status, review state, cultural protocol restrictions, redaction rules, and policy class decisions.
```

Services must never trust client-provided validation, review, or restriction state without server-side policy evaluation.

---

## 30. Privacy and redaction

Provenance, revisions, validation records, media versions, content markers, and content reviews may contain personal or sensitive information.

Privacy coverage must include:

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
export manifests
```

Redaction must apply to:

```text
private notes
restricted metadata
cultural protocol details
integrity-related details
sensitive content advisory notes
external work notes that cannot be shared
old revision values not visible to the current user
```

Privacy rule:

```text
A user may receive their own personal data through Moodle Privacy API.
A user must not receive restricted cultural, integrity, or third-party information merely because it is stored near their record.
```

---

## 31. Backup and restore

Backup must preserve:

```text
provenance records
archive revisions
media versions
content tags
content tag sets
content markers
content reviews
external works
media source records
validation state
contestability metadata
export manifests when included
```

Restore must remap:

```text
context ids
course ids
course module ids
archive ids
archive item ids
media ids
media version ids
content marker ids
external work ids
user ids where possible
file item ids
```

Restore rule:

```text
Restore reconstructs archive-owned memory.
Restore does not create grades, challenge workflow authority, Assembly decision authority, integrity case authority, or institutional reporting authority.
```

---

## 32. Import behavior

Imported records must preserve source provenance.

Imported records begin as:

```text
unverified
```

unless a trusted human validation record is imported and accepted under policy.

Imported media must include source classification.

Imported content markers must include review state.

Imported external works must not imply UCKK ownership.

Import rule:

```text
Import can preserve prior claims.
Import does not automatically validate prior claims.
```

---

## 33. External/foreign media examples

The module must support advisory metadata for external or foreign works without requiring UCKK to store the full work.

Examples:

```text
Movie Maïna -> sexual_violence -> 01:12:30-01:15:10
Book The Body Keeps the Score -> sexual_violence -> page 42-45
PDF -> culturally_sensitive -> page 7
Audio -> grief_or_mourning -> 00:08:12-00:09:40
Website -> colonial_violence -> url_fragment #section-3
```

External reference rule:

```text
The archive may store locator, advisory, review, citation, and teaching-context metadata for an external work.
The archive must not store or export unauthorized copies of external works.
```

---

## 34. Required local classes

Required local authority classes include:

```text
classes/local/archive_policy.php
classes/local/content_marker.php
classes/local/content_policy.php
classes/local/content_review.php
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/external_work.php
classes/local/media_policy.php
classes/local/media_source.php
classes/local/media_version.php
classes/local/provenance.php
classes/local/revision.php
classes/local/uuid.php
```

Implementation rule:

```text
Business rules belong in classes/local.
Controllers coordinate.
Services validate API contracts and call policy/domain classes.
Templates render pre-filtered data.
AMD modules never authorize access.
```

---

## 35. Tests

Testing must cover:

```text
provenance creation
archive revision creation
media version creation
validation transitions
contestation transitions
invalidation behavior
content tag creation
content tag set behavior
content marker locator behavior
content review workflow
external work references
media source classification
restricted visibility
cultural protocol restriction
export manifest provenance
privacy redaction
backup/restore remapping
service permission checks
```

Required tests include:

```text
tests/archive_test.php
tests/content_advisory_test.php
tests/external_work_test.php
tests/media_library_test.php
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

## 36. Non-negotiable rules

```text
Validation is human-final.
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
AI cannot approve cultural protocol access.
Media files are not silently overwritten.
Meaningful media replacement creates a media version.
Meaningful archive item change creates an archive revision.
Content advisories are first-class records, not only JSON metadata.
External works can be referenced without being copied.
External work reference does not imply UCKK ownership.
Provenance explains origin but does not grant authority.
Exports must remain portable, explainable, permission-filtered, and redaction-aware.
```

---

## 37. Final rule

```text
This document defines the final target behavior for provenance, versioning, validation, content advisory review, external work references, and trust governance. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
```
