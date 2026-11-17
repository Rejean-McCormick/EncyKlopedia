# 08 — Archive Workflows

**Path:** `docs/08_archive_workflows.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Archive item workflows for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines the final archive workflows for `mod_uckkarchive`.

The archive workflow layer governs how archive items are created, submitted, reviewed, validated, revised, restricted, contested, invalidated, archived, exported, and connected to media, provenance, Kristals, proofs, content advisories, external works, and Moodle contexts.

`mod_uckkarchive` is:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

The archive workflow does not replace Moodle gradebook, course enrolment, Assembly authority, challenge authority, integrity case authority, or institutional reporting authority.

---

## 2. Workflow ownership

`mod_uckkarchive` owns workflows for:

```text
archive item creation
archive item draft saving
archive item submission
archive item review
archive item validation
archive item revision
archive item restriction
archive item contestation
archive item invalidation
archive item archival
archive item export
archive-media linking
archive-provenance linking
archive-content advisory linking
archive-external work reference linking
```

`mod_uckkarchive` does not own workflows for:

```text
grading
transcripts
course enrolment
institutional registry state
challenge completion authority
Assembly decision authority
integrity case findings
sanctions
appeals
institutional reporting authority
```

The archive may preserve traces, evidence, references, or snapshots from external domains.

Preservation does not transfer authority.

---

## 3. Archive item identity

Each archive item has two identifiers:

```text
id = local Moodle database primary key
uuid = stable portable archive identity
```

The `id` is used internally by Moodle database operations.

The `uuid` is used for:

```text
export
restore
duplication
cross-site portability
manifest references
external package references
long-term archive identity
```

An archive item must not rely on a Moodle database `id` as its only durable identity.

---

## 4. Archive item status model

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
| `draft` | Item exists but is not formally submitted. |
| `submitted` | Item was submitted for review, validation, or preservation. |
| `under_review` | Item is actively being reviewed. |
| `validated` | Item has passed human validation. |
| `published` | Item is visible according to its visibility policy. |
| `restricted` | Item is preserved but access is restricted. |
| `contested` | Item remains preserved but is under dispute. |
| `invalidated` | Item is preserved as invalidated memory, not deleted silently. |
| `superseded` | Item remains preserved but is replaced by a newer item or revision. |
| `archived` | Item is preserved for long-term memory and normal editing is closed. |

---

## 5. Validation state model

Canonical validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Validation state is separate from visibility.

An item may be:

```text
validated but private
validated but restricted
published but later contested
archived but not public
invalidated but still preserved
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

## 6. Visibility model

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

Visibility controls who may see the item.

Visibility does not by itself grant permission to:

```text
download restricted files
view culturally restricted content
view integrity-restricted material
export records
revise records
validate records
delete records
```

All visibility decisions are enforced by policy classes and Moodle capabilities.

---

## 7. Core workflow map

Canonical archive item workflow:

```text
draft
  → submitted
  → under_review
  → validated
  → published
  → archived
```

Exceptional workflows:

```text
submitted → draft
under_review → submitted
under_review → contested
validated → contested
validated → superseded
validated → invalidated
published → contested
published → restricted
published → superseded
published → archived
restricted → archived
contested → human_reviewed
contested → invalidated
contested → validated
invalidated → archived
superseded → archived
```

Forbidden silent transitions:

```text
published → draft
validated → unverified
restricted_integrity → public
restricted_cultural → public
invalidated → verified
contested → published
archived → published
```

If an exceptional transition is allowed, it must create a revision record with an explicit reason and actor.

---

## 8. Draft workflow

Draft creation begins when a user creates or saves an archive item before formal submission.

Draft workflow:

```text
new request
  → create draft archive item
  → assign uuid
  → set status = draft
  → set validationstate = unverified
  → set default visibility
  → save metadata
  → save draft files through Moodle File API
  → create initial revision record
```

Draft requirements:

```text
draft items must have a uuid
draft items must have an owner or createdby user
draft items must have context
draft files must remain within Moodle File API
drafts must not be public
drafts must not be exported as official archive packages
```

Draft access:

```text
creator
users with edit authority
users with validation authority when submitted for review
```

Draft deletion may be allowed when the item has no institutional preservation dependency.

---

## 9. Submission workflow

Submission begins when a draft is formally submitted.

Submission workflow:

```text
draft
  → submitted
  → create revision
  → lock submitted fields when required
  → notify or expose to reviewers
  → make item eligible for review
```

Submission requirements:

```text
required title
required item type
required context
required provenance baseline
required visibility baseline
required createdby
required uuid
required status transition reason when configured
```

Submission does not equal validation.

Submission does not equal publication.

Submission does not create grades.

---

## 10. Review workflow

Review begins when a submitted item is taken into review.

Review workflow:

```text
submitted
  → under_review
  → provenance review
  → media link review
  → content advisory review
  → cultural protocol review where applicable
  → privacy review where applicable
  → validation decision
```

Review may produce:

```text
validation
revision request
restriction
content advisory marker
cultural protocol note
contestation
invalidation
archive note
```

Review requires human accountability.

AI may assist with summaries, suggestions, or candidate tags, but human review remains final.

---

## 11. Validation workflow

Validation confirms that an archive item is reliable enough for its intended archive role.

Validation workflow:

```text
under_review
  → human_reviewed
  → verified
  → validated
```

Validation must record:

```text
validator user id
validation time
validation state
validation reason
provenance state
visibility state
restriction state
content advisory state
revision id
```

Validation may also update:

```text
visibility
public summary
content advisory markers
media relations
provenance hash
retention class
redaction state
```

Validation uses capability:

```text
mod/uckkarchive:validateitem
```

Validation creates event:

```text
mod_uckkarchive\event\archive_item_validated
```

---

## 12. Revision workflow

Revision changes archive content, metadata, provenance, media links, validation state, visibility, or policy-relevant fields.

Revision workflow:

```text
load item
  → check context
  → check visibility
  → require reason
  → apply change
  → increment version number when meaningful
  → create uckkarchive_rev
  → update provenance hash when relevant
  → trigger revision event
```

Revision uses capability:

```text
mod/uckkarchive:reviseitem
```

There is no current archive item capability named:

```text
mod/uckkarchive:versionitem
```

Archive item versioning is controlled by:

```text
mod/uckkarchive:reviseitem
```

Revision creates event:

```text
mod_uckkarchive\event\archive_item_revised
```

---

## 13. Media linking workflow

Archive items may link to first-class media objects.

Media is not only an archive item attachment.

Media is represented by:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
```

Media linking workflow:

```text
select archive item
  → select media object
  → check archive access
  → check media access
  → create relation
  → create revision record
  → update provenance when relevant
  → refresh archive item view
```

Common relation types:

```text
belongs_to_item
is_proof_for
is_source_for
references
contains_content_marker
```

Media files remain in media file areas.

Archive item files remain in archive file areas.

The module must not duplicate files unnecessarily.

---

## 14. Proof workflow

Proofs are evidence records connected to archive items, media, challenges, validation, or integrity-related preservation.

Proof workflow:

```text
create proof
  → link proof to archive item
  → link proof to media when applicable
  → save proof files through Moodle File API
  → record provenance
  → set visibility/restriction
  → create revision
```

Proofs may be associated with:

```text
challenge evidence
portfolio evidence
validation evidence
integrity evidence
Assembly evidence
course work evidence
```

Proof preservation does not create gradebook authority.

Proof preservation does not create integrity case authority.

Proof files use:

```text
proof_files
```

Proof access is enforced through archive policy and restricted-access checks.

---

## 15. Kristal workflow

Kristals are archive-connected memory or knowledge objects.

Kristal workflow:

```text
create Kristal
  → link to archive item
  → link to media where applicable
  → link to provenance
  → validate when required
  → revise when updated
  → preserve as archive memory
```

Kristals may link to:

```text
archive items
media objects
proofs
content advisories
external works
collections
provenance records
```

Kristal files use:

```text
kristal_files
```

---

## 16. Content advisory workflow

Content advisories are first-class governance records.

They describe suitability, sensitivity, cultural protocol, and access conditions.

Content advisory workflow:

```text
identify content concern
  → choose content tag
  → create content marker
  → attach locator
  → link to media, archive item, media version, or external work
  → set audience suitability
  → set advisory severity
  → review marker
  → approve, contest, or retire marker
```

Content advisory tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

Content advisory does not automatically ban media.

It provides responsible warning, teaching context, suitability guidance, restriction, review, or cultural protocol.

---

## 17. Content marker workflow

Content markers link advisories to precise locations.

A marker may point to:

```text
media object
media version
archive item
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

Examples:

```text
Movie Maïna -> sexual_violence -> 01:12:30-01:15:10
Book The Body Keeps the Score -> sexual_violence -> page 42-45
PDF -> culturally_sensitive -> page 7
Audio -> grief_or_mourning -> 00:08:12-00:09:40
```

A content marker must include enough locator information to be useful without storing unauthorized copies of external content.

---

## 18. External work workflow

External works are works not produced by UCKK that may be referenced, taught, reviewed, tagged, or connected to archive/media records.

External work workflow:

```text
create external work record
  → record bibliographic/source metadata
  → record source ownership
  → add content markers
  → add advisory tags
  → link to archive item or media object when relevant
  → preserve reference without claiming ownership
```

External work table:

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

External/foreign media rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 19. Media source workflow

Media source records define origin and rights context.

Media source table:

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

Media source workflow:

```text
create or update media source
  → record source ownership
  → record rights/usage category
  → link media object or external work
  → update provenance
  → update export manifest eligibility
```

---

## 20. Cultural protocol workflow

Cultural protocol is part of the content advisory system.

Cultural protocol tags may include:

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

Cultural protocol workflow:

```text
identify cultural protocol concern
  → create content marker
  → attach cultural protocol tag
  → set restricted_cultural visibility when needed
  → require human review
  → record review decision
  → enforce access policy
```

Cultural protocol access requires policy checks beyond ordinary visibility.

AI cannot approve cultural protocol access.

---

## 21. Restriction workflow

Restriction limits access while preserving records.

Restriction workflow:

```text
identify restriction need
  → set visibility = restricted, restricted_integrity, or restricted_cultural
  → record reason
  → create revision
  → update policy metadata
  → update file access behavior
  → update export eligibility
```

Restriction reasons may include:

```text
privacy
integrity sensitivity
cultural protocol
minor safety
content advisory severity
copyright or external rights
unvalidated provenance
contested record
```

Restricted items remain preserved unless deletion or anonymisation is explicitly allowed.

---

## 22. Contestation workflow

Contestation records disagreement, uncertainty, objection, review challenge, or cultural/provenance concern.

Contestation workflow:

```text
validated or published item
  → contested
  → record contestation reason
  → preserve original state
  → create revision
  → notify/reveal to reviewers
  → review evidence
  → validate, restrict, supersede, invalidate, or archive
```

Contested records must not be silently overwritten.

Contestation may apply to:

```text
archive item
media metadata
media relation
content advisory marker
external work reference
provenance claim
validation decision
public summary
```

---

## 23. Invalidation workflow

Invalidation preserves the fact that something was rejected, superseded, false, unsafe, or unsuitable as originally stated.

Invalidation workflow:

```text
review contested or validated record
  → determine invalidation
  → record reason
  → preserve previous revision
  → set validationstate = invalidated
  → set status = invalidated
  → restrict or archive as needed
```

Invalidated records must not be silently deleted when they have institutional memory value.

Invalidated records may be hidden from ordinary browsing while preserved for audit, provenance, and review.

---

## 24. Supersession workflow

Supersession records that a newer or corrected record replaces an older one.

Supersession workflow:

```text
create or select replacement item
  → link previous item
  → set previous item status = superseded
  → create revision on both records
  → update relation/provenance
  → update export manifest behavior
```

Superseded records remain preserved.

Supersession does not erase the older record.

---

## 25. Archival workflow

Archival closes active workflow while preserving memory.

Archival workflow:

```text
validated, invalidated, superseded, restricted, or contested record
  → archived
  → lock ordinary editing
  → preserve provenance
  → preserve revision history
  → preserve content advisory markers
  → preserve media relations
  → preserve export eligibility policy
```

Archived does not mean public.

Archived does not mean unrestricted.

Archived does not mean deleted.

---

## 26. Export workflow

Archive exports are generated from archive/media-owned records.

Export workflow:

```text
select export scope
  → preview included records
  → apply visibility policy
  → apply restricted policy
  → apply content advisory policy
  → apply cultural protocol policy
  → apply redaction policy
  → create export package
  → create manifest.json
  → save export files through Moodle File API
  → trigger event
```

Export package file area:

```text
export_package
```

Export manifest file area:

```text
export_manifest
```

Export must include metadata needed for portability and interpretation.

Export must not bypass restrictions, content advisories, cultural protocol, redaction, privacy, or rights constraints.

---

## 27. Privacy workflow

Privacy workflow applies to all archive/media/content-advisory records containing user-linked data.

Privacy workflow includes:

```text
identify user-linked records
export user data
delete allowed draft data
anonymise where required
redact third-party sensitive content
preserve institutional memory where allowed
preserve restricted records where required
```

Privacy provider must cover:

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
content tags
content tag sets
content markers
content reviews
external works where user-linked
media source records where user-linked
files
```

---

## 28. Backup and restore workflow

Backup preserves module-owned archive/media/content-advisory state.

Backup includes:

```text
archive items
proofs
Kristals
provenance
revisions
exports
media objects
media versions
media relations
media tags
media collections
media collection items
content tags
content tag sets
content markers
content reviews
external works
media source records
files
```

Restore reconstructs module-owned records only.

Restore must not create:

```text
grades
transcripts
course enrolment authority
Assembly authority
challenge workflow authority
integrity case authority
institutional reporting authority
```

Restore must preserve:

```text
uuid identity
visibility
restriction state
content advisory state
cultural protocol state
validation state
provenance
revision history
relations
collections
export metadata
```

---

## 29. Event workflow

Archive workflows trigger Moodle events after successful state changes.

Canonical archive events:

```text
archive_viewed
archive_item_created
archive_item_validated
archive_item_revised
archive_item_exported
```

Related media/content events:

```text
media_created
media_updated
media_version_created
media_collection_created
media_exported
content_marker_created
content_marker_reviewed
external_work_created
```

Event rules:

```text
events audit successful state changes
events include context and object identifiers
events do not expose raw restricted content
events do not expose redacted details
events do not expose private cultural protocol notes
```

---

## 30. Service workflow rules

Every workflow exposed through AJAX or web service must use `classes/external`.

Every service must:

```text
require login
resolve context
validate parameters
check capabilities
call policy classes
call local domain classes
return permission-filtered data
avoid leaking restricted metadata
```

Services must not duplicate workflow policy.

Services must call:

```text
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

---

## 31. UI workflow rules

The UI may show:

```text
status
visibility
validation state
media links
content advisory badges
cultural protocol badges
review state
available actions
warnings
export eligibility
```

The UI must not decide:

```text
authority
validation
restriction
cultural protocol access
download access
export access
privacy access
redaction access
```

All UI actions must call server-side services.

---

## 32. Scheduled maintenance workflows

Scheduled tasks may handle:

```text
media derivative generation
media thumbnail generation
export package generation
expired export purge
media search rebuild
content marker index rebuild
pending item validation maintenance
```

Scheduled tasks must reuse local domain classes and policies.

Scheduled tasks must not bypass access, restriction, redaction, or content advisory rules for generated outputs.

---

## 33. Workflow capability map

Archive workflow capabilities:

| Workflow | Capability |
|---|---|
| View archive | `mod/uckkarchive:view` |
| Add archive item | `mod/uckkarchive:additem` |
| Validate archive item | `mod/uckkarchive:validateitem` |
| Revise archive item | `mod/uckkarchive:reviseitem` |
| View restricted item | `mod/uckkarchive:viewrestricted` |
| Export archive item | `mod/uckkarchive:export` |

Media workflow capabilities:

| Workflow | Capability |
|---|---|
| View media | `mod/uckkarchive:viewmedia` |
| Add media | `mod/uckkarchive:addmedia` |
| Edit media | `mod/uckkarchive:editmedia` |
| Delete media | `mod/uckkarchive:deletemedia` |
| Download media | `mod/uckkarchive:downloadmedia` |
| Add media version | `mod/uckkarchive:versionmedia` |
| Manage collections | `mod/uckkarchive:managemediacollections` |
| Export media | `mod/uckkarchive:exportmedia` |
| View restricted media | `mod/uckkarchive:viewrestrictedmedia` |

Content advisory workflow capabilities:

| Workflow | Capability |
|---|---|
| View advisories | `mod/uckkarchive:viewadvisories` |
| Manage advisories | `mod/uckkarchive:manageadvisories` |
| Review advisories | `mod/uckkarchive:reviewadvisories` |
| View culturally restricted material | `mod/uckkarchive:viewculturallyrestricted` |
| Manage external works | `mod/uckkarchive:manageexternalworks` |

Capabilities are gates, not complete authority.

Policy classes remain authoritative.

---

## 34. Required local classes

Archive workflows depend on:

```text
classes/local/archive_item.php
classes/local/archive_policy.php
classes/local/proof.php
classes/local/kristal.php
classes/local/provenance.php
classes/local/revision.php
```

Media workflows depend on:

```text
classes/local/media.php
classes/local/media_policy.php
classes/local/media_version.php
classes/local/media_collection.php
classes/local/media_relation.php
classes/local/media_tag.php
classes/local/media_file.php
```

Content advisory workflows depend on:

```text
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/content_marker.php
classes/local/content_review.php
classes/local/content_policy.php
classes/local/external_work.php
classes/local/media_source.php
```

Shared workflow infrastructure:

```text
classes/local/context_resolver.php
classes/local/file_area_registry.php
classes/local/manifest_builder.php
classes/local/metadata_validator.php
classes/local/uuid.php
```

---

## 35. Final workflow rule

```text
Archive workflows preserve memory.
Media workflows manage reusable media objects.
Content advisory workflows describe responsible access and suitability.
Provenance workflows explain origin.
Validation workflows record human trust.
Revision workflows preserve change.
Restriction workflows protect sensitive records.
Export workflows package only what policy allows.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
