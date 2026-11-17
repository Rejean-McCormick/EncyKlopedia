# 17 — Integration with Challenges

**Path:** `docs/17_integration_with_challenges.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Related component:** `mod_uckkchallenge`  
**Status:** Final target specification  
**Scope:** Integration contract between the UCKK Archive/Media Library module and the UCKK Challenge module.

---

## 1. Purpose

This document defines how `mod_uckkarchive` integrates with challenge activity data.

`mod_uckkarchive` is a self-contained Moodle activity module for archive memory, media library management, and content advisory governance.

`mod_uckkchallenge` owns challenge workflow.

The archive may preserve challenge-related records, media, proofs, review artifacts, provenance, content advisories, and export packages.

The archive does not become the challenge workflow authority.

Canonical boundary:

```text
mod_uckkchallenge = challenge workflow authority
mod_uckkarchive   = archive/media preservation authority
```

---

## 2. Core integration decision

Challenge integration is reference-based and preservation-based.

`mod_uckkarchive` may store:

```text
challenge references
challenge evidence snapshots
challenge submission snapshots
challenge review summaries
challenge proof records
challenge-related media
challenge-related content markers
challenge-related provenance
challenge-related export packages
```

`mod_uckkarchive` must not own:

```text
challenge activity setup
challenge workflow state
challenge grading
challenge submission authority
challenge attempt lifecycle
challenge completion rules
challenge evaluator assignment
challenge internal review workflow
```

Preservation does not transfer authority.

---

## 3. Ownership boundary

### 3.1 Owned by `mod_uckkchallenge`

`mod_uckkchallenge` owns:

```text
challenge definition
challenge instructions
challenge workflow state
challenge attempt/submission state
challenge participant state
challenge review workflow
challenge evaluator assignment
challenge scoring logic
challenge completion logic
challenge grading bridge
challenge-specific deadlines
challenge-specific rules
```

### 3.2 Owned by `mod_uckkarchive`

`mod_uckkarchive` owns:

```text
archive items created from challenges
challenge-related media records
challenge-related media versions
challenge-related media collections
challenge evidence proof records
challenge preservation provenance
challenge archive revisions
challenge content advisories
challenge cultural protocol markers
challenge export packages
challenge export manifests
```

### 3.3 Owned by Moodle gradebook

Moodle gradebook owns:

```text
grades
grade items
gradebook aggregation
grade history
final grade display
```

`mod_uckkarchive` does not own grades.

---

## 4. Integration model

The integration uses stable references.

Archive records may reference challenge records by:

```text
sourcecomponent = mod_uckkchallenge
sourcearea
sourceid
sourceuuid
sourcetype
sourceurl
snapshot time
```

Challenge references must be treated as pointers to external authority.

The archive stores its own preservation record and provenance around the reference.

---

## 5. Challenge-to-archive preservation

A challenge may generate or contribute to archive material.

Examples:

```text
validated challenge response
learner artifact
evaluator feedback snapshot
challenge proof bundle
challenge media submission
challenge reflection
challenge completion evidence
challenge discussion evidence
challenge appeal evidence
challenge public showcase item
```

These may become archive-owned records when preserved.

Archive preservation creates an archive identity.

It does not replace the challenge identity.

---

## 6. Archive item types for challenges

Challenge-related archive items may use item types such as:

```text
challenge_submission_snapshot
challenge_review_snapshot
challenge_evidence
challenge_reflection
challenge_media
challenge_proof
challenge_public_summary
challenge_portfolio_item
challenge_export_bundle
```

Each preserved item must include enough metadata to explain:

```text
which challenge it came from
which user or group submitted it
which course context applied
which moment was preserved
who preserved it
why it was preserved
what version was preserved
what visibility applies
what restrictions apply
```

---

## 7. Media integration

Challenge-related media is managed as first-class archive media.

The media object belongs to `uckkarchive_media`.

The original challenge submission remains owned by `mod_uckkchallenge`.

The preserved media record may include:

```text
media uuid
source component
source id
source version
source ownership
license metadata
rights metadata
content advisory markers
cultural protocol markers
media versions
derivatives
thumbnails
captions
transcripts
relations
collections
```

Media files are stored through Moodle File API under `mod_uckkarchive` when preserved into the archive.

The archive must not rely on unmanaged public folders.

---

## 8. Media source values

Challenge-related media may use source values such as:

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

For challenge submissions, the common source values are:

```text
submitted_to_uckk
member_submitted
partner_submitted
external_reference
unknown_source
```

Source metadata must not imply ownership where ownership is uncertain.

---

## 9. Media relations for challenges

Challenge-related media may use relation types such as:

```text
belongs_to_item
belongs_to_collection
is_proof_for
is_source_for
is_derivative_of
is_translation_of
is_excerpt_of
references_external_work
contains_content_marker
```

Challenge-specific relation examples:

```text
media belongs_to_item challenge_submission_snapshot
media is_proof_for challenge_completion_evidence
media is_source_for challenge_public_summary
media is_excerpt_of external_work
media contains_content_marker sexual_violence
```

Relations describe archive graph meaning.

Relations do not transfer challenge workflow authority to the archive.

---

## 10. Content advisories in challenge integration

Challenge artifacts may contain content that requires advisories, cultural protocol, or audience suitability review.

`mod_uckkarchive` owns the advisory record once the material is preserved in the archive.

Required advisory tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_media_source
```

Content advisories may apply to:

```text
challenge submission media
challenge written response
challenge proof file
challenge reflection
challenge evaluator note
external work referenced by a challenge
media excerpt used in challenge work
public showcase item
```

A content advisory does not ban the challenge artifact.

It defines conditions for responsible access, teaching, warning, review, restriction, or contextualization.

---

## 11. Cultural protocol in challenge integration

Challenge-related archive records may carry cultural protocol restrictions.

Cultural protocol restrictions may affect:

```text
who can view a challenge artifact
who can view the media original
who can view thumbnails or previews
who can review cultural notes
whether the item can be exported
whether the item can appear in a public showcase
whether advisory details must be redacted
whether elder or community review metadata is required
```

Cultural protocol access requires explicit policy checks.

It is not granted automatically by teacher, manager, or administrator status.

---

## 12. External works in challenge integration

Challenges may reference works not produced by UCKK.

Examples:

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
```

External works are stored in:

```text
uckkarchive_external_work
```

Challenge artifacts may link to external works through content markers, media source records, and archive relations.

The archive may store:

```text
external work metadata
locator references
content advisory markers
teaching notes
cultural protocol notes
review state
rights notes
source references
```

The archive must not imply ownership of third-party works.

The archive must not copy external media unless rights and policy allow it.

---

## 13. Locator model

Challenge-related content markers may use locators.

Locator types:

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
Challenge references a film scene -> sexual_violence -> 01:12:30-01:15:10
Challenge references a book excerpt -> trauma -> page 42-45
Challenge PDF submission -> culturally_sensitive -> page 7
Challenge audio reflection -> grief_or_mourning -> 00:08:12-00:09:40
```

Locator records must be precise enough to support review, warning, and teaching context.

---

## 14. Provenance requirements

Every challenge-related archive object must preserve provenance.

Required provenance fields include:

```text
source component
source area
source id
source uuid when available
source type
source title
source course id
source cm id
source user id when applicable
source group id when applicable
snapshot timestamp
preserved by userid
preservation reason
import method
file hashes when files are copied
visibility at preservation time
validation state at preservation time
```

Provenance explains origin.

Provenance does not grant authority.

---

## 15. Validation model

Challenge validation and archive validation are separate.

`mod_uckkchallenge` may determine challenge workflow status.

`mod_uckkarchive` may determine archive preservation status.

Archive validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Archive validation is human-final.

AI cannot validate archive records.

AI cannot invalidate archive records.

AI cannot close contestations.

AI cannot approve cultural protocol access.

---

## 16. Revision model

Challenge records may change after a snapshot is preserved.

The archive must preserve its own revision history.

Archive revisions may record:

```text
metadata correction
visibility change
content advisory update
cultural protocol update
media version update
provenance correction
source challenge reference update
redaction update
export correction
```

Archive item revisions use:

```text
mod/uckkarchive:reviseitem
```

Media versioning uses:

```text
mod/uckkarchive:versionmedia
```

The module does not use:

```text
mod/uckkarchive:versionitem
```

---

## 17. Permissions

Challenge integration uses both challenge authority and archive authority.

When viewing preserved archive records, `mod_uckkarchive` policy applies.

When operating on live challenge workflow, `mod_uckkchallenge` policy applies.

Archive capabilities involved:

```text
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Media capabilities involved:

```text
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:editmedia
mod/uckkarchive:downloadmedia
mod/uckkarchive:versionmedia
mod/uckkarchive:managemediacollections
mod/uckkarchive:exportmedia
mod/uckkarchive:viewrestrictedmedia
```

Content advisory capabilities involved:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:manageexternalworks
```

---

## 18. Policy checks

Challenge-related archive access must check:

```text
course module context
archive capability
archive record visibility
media visibility
restricted state
cultural protocol state
content advisory state
audience suitability
validation state
retention state
redaction state
source ownership
export rights
```

Policy classes:

```text
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

Controllers, AMD modules, templates, and forms must not duplicate policy decisions.

---

## 19. Services

Challenge integration may require archive services such as:

```text
classes/external/add_item.php
classes/external/get_archive_item.php
classes/external/get_archive_items.php
classes/external/update_provenance.php
classes/external/validate_item.php
classes/external/revise_item.php
classes/external/add_media.php
classes/external/get_media_item.php
classes/external/add_media_version.php
classes/external/add_media_relation.php
classes/external/add_media_to_collection.php
classes/external/get_content_markers.php
classes/external/add_content_marker.php
classes/external/review_content_marker.php
classes/external/add_external_work.php
classes/external/export_items.php
classes/external/export_media.php
```

Services must never return restricted challenge-derived archive data for client-side hiding.

Filtering happens server-side.

---

## 20. Events

Challenge-related archive events may include:

```text
archive_item_created
archive_item_revised
archive_item_validated
archive_item_exported
media_created
media_updated
media_version_created
media_collection_created
media_exported
content_marker_created
content_marker_reviewed
external_work_created
```

Events audit archive state changes.

Events do not expose restricted content, raw media, private cultural protocol notes, or redacted data.

---

## 21. Backup and restore

Archive backup must preserve challenge-related archive records as archive-owned data.

Backup may preserve:

```text
archive item records
challenge source references
media records
media versions
media relations
media collections
proof records
provenance records
content markers
content reviews
external work metadata
export manifests
```

Restore must not recreate live challenge workflow state.

Restore must not create challenge attempts.

Restore must not create grades.

Restore may restore source references as references.

If the original challenge does not exist after restore, preserved archive records remain valid archive records with historical provenance.

---

## 22. Privacy and retention

Challenge-derived archive records may contain personal data.

Privacy handling must include:

```text
submitter data
reviewer data
preserver data
media contributor data
proof contributor data
content reviewer data
external work curator data
restricted notes
cultural protocol notes
source references
```

Privacy deletion must respect:

```text
user rights
institutional preservation duties
challenge evidence requirements
restricted cultural protocol rules
integrity restrictions when applicable
redaction policy
retention policy
```

A privacy request does not automatically delete institutional archive memory.

Policy determines export, redaction, anonymization, or retention.

---

## 23. Reporting boundary

`mod_uckkarchive` may provide archive-level exports.

`report_uckk` owns institutional reporting.

Challenge-derived archive exports may include:

```text
selected challenge evidence package
validated challenge archive bundle
media proof bundle
content advisory manifest
public showcase export
restricted review package
```

Institutional reports, dashboards, cross-course metrics, and administrative reporting belong to `report_uckk`.

---

## 24. Grade boundary

Challenge artifacts may be related to assessment.

`mod_uckkarchive` must not own grade data.

The archive may preserve:

```text
non-authoritative grade snapshot when explicitly exported
review evidence
proof of completion
public summary
portfolio artifact
feedback snapshot
```

The authoritative grade remains in Moodle gradebook.

---

## 25. UI integration

Archive UI may show challenge-related context.

Examples:

```text
source challenge title
source course
source participant
source group
snapshot timestamp
challenge evidence badge
content advisory badge
cultural protocol badge
media count
proof count
validation state
export status
```

UI must not expose:

```text
restricted challenge details without policy approval
restricted media thumbnails without policy approval
restricted advisory details without policy approval
private reviewer notes
redacted details
```

---

## 26. Search integration

Search and listing must be permission-filtered.

Challenge-related archive records must not leak restricted data through:

```text
title
snippet
media thumbnail
media preview
tag
collection
content advisory label
source challenge reference
external work reference
count
facet
autocomplete
```

Redacted placeholders may be used only when policy allows.

---

## 27. Export manifest

Challenge-related exports must include manifest metadata.

Manifest fields may include:

```text
plugin component
archive id
export id
export timestamp
export actor
export reason
source component = mod_uckkchallenge
source challenge id
source challenge uuid
archive item ids
media uuids
media version uuids
external work uuids
content marker uuids
content tag keys
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
redaction level
validation state
revision history
```

Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.

---

## 28. Failure behavior

If `mod_uckkchallenge` is missing, disabled, or the referenced challenge record is unavailable:

```text
preserved archive records remain accessible according to archive policy
source reference is shown as unavailable when policy allows
archive provenance remains intact
live challenge workflow actions are unavailable
restore does not attempt to recreate the challenge workflow
exports may include historical source metadata when permitted
```

The archive must fail closed for restricted or uncertain access.

---

## 29. Implementation touchpoints

Relevant archive files:

```text
classes/local/archive_item.php
classes/local/archive_policy.php
classes/local/proof.php
classes/local/provenance.php
classes/local/revision.php
classes/local/export_package.php
```

Relevant media files:

```text
classes/local/media.php
classes/local/media_policy.php
classes/local/media_relation.php
classes/local/media_collection.php
classes/local/media_version.php
classes/local/media_source.php
```

Relevant content advisory files:

```text
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/content_marker.php
classes/local/content_review.php
classes/local/content_policy.php
classes/local/external_work.php
```

Relevant integration files:

```text
classes/local/context_resolver.php
classes/local/manifest_builder.php
classes/local/metadata_validator.php
classes/local/uuid.php
db/install.xml
db/upgrade.php
db/services.php
db/access.php
classes/privacy/provider.php
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

---

## 30. Tests

Challenge integration tests must cover:

```text
creating archive items from challenge references
preserving challenge source metadata
adding media to challenge archive items
adding content markers to challenge media
linking external works to challenge records
permission-filtering restricted challenge archive records
cultural protocol restriction behavior
media download restrictions
archive export manifest generation
backup and restore of challenge-derived archive records
restore when source challenge is absent
privacy export/redaction of challenge-derived records
```

Required test files:

```text
tests/archive_test.php
tests/media_library_test.php
tests/content_advisory_test.php
tests/export_test.php
tests/backup_restore_test.php
tests/privacy_provider_test.php
tests/services_test.php
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

---

## 31. Final integration rule

```text
mod_uckkchallenge owns live challenge workflow.
mod_uckkarchive owns preserved challenge archive memory.

The archive may preserve challenge evidence, media, content advisories,
external work references, provenance, validation state, revisions, restricted
metadata, and export packages.

The archive does not own challenge attempts, challenge workflow state,
challenge grading, evaluator assignment, or Moodle gradebook authority.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
