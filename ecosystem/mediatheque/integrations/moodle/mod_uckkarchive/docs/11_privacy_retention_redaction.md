# 11 — Privacy, Retention, and Redaction

**Path:** `docs/11_privacy_retention_redaction.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Privacy, retention, deletion, anonymization, redaction, restricted access, content advisory privacy, cultural protocol privacy, external work references, File API data, and Moodle Privacy API responsibilities.

---

## 1. Purpose

This document defines the privacy, retention, and redaction architecture for `mod_uckkarchive`.

`mod_uckkarchive` is a self-contained Moodle activity module for:

```text
archive memory
media library management
content advisory governance
cultural protocol handling
external work references
provenance
validation
revision history
export packages
```

The module stores records that may contain personal data, educational data, evidence, cultural sensitivity metadata, restricted content, advisory notes, and external media references.

The module must preserve archive memory while still respecting privacy, retention, redaction, and deletion rules.

---

## 2. Core privacy decision

Canonical formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

Privacy behavior follows the same architecture.

`mod_uckkarchive` uses Moodle for:

```text
Privacy API
context ownership
user identity
capabilities
course module access
role-based access
File API storage
backup and restore boundaries
external service restrictions
events
scheduled tasks
```

`mod_uckkarchive` owns privacy behavior for the records it stores internally.

---

## 3. Privacy ownership boundary

`mod_uckkarchive` owns privacy handling for:

```text
archive records
archive items
media records
media versions
media files
media collections
media relations
media tags
proof records
Kristals
provenance records
revision records
validation state
restricted archive metadata
restricted media metadata
content advisory tags
cultural sensitivity tags
content tag sets
content markers
content reviews
external work references
media source records
audience suitability rules
export packages
export manifests
```

`mod_uckkarchive` does not own privacy behavior for records controlled by:

```text
Moodle gradebook
local_uckk
mod_uckkchallenge
mod_uckkassembly
tool_uckkintegrity
report_uckk
```

The archive may preserve snapshots or references from those systems.

Preservation does not transfer system authority.

Privacy export, redaction, deletion, or anonymization applies only to archive-owned records unless external data has been copied into archive-owned tables or files.

---

## 4. Moodle Privacy API contract

The plugin privacy provider is:

```text
classes/privacy/provider.php
```

The provider must declare metadata for all user-related data stored by `mod_uckkarchive`.

The provider must support Moodle privacy operations for:

```text
metadata declaration
contexts containing user data
export of user data
deletion of user data for a context
deletion of user data for a user in a context
deletion of all user data in a context
```

The privacy provider must cover:

```text
uckkarchive
uckkarchive_item
uckkarchive_proof
uckkarchive_kristal
uckkarchive_prov
uckkarchive_rev
uckkarchive_export
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

The privacy provider must also cover File API data stored in all plugin file areas.

---

## 5. Data categories

The module may store these privacy-relevant data categories:

```text
user identity references
creator identity
modifier identity
reviewer identity
validator identity
export actor identity
archive contributor identity
media submitter identity
proof submitter identity
content reviewer identity
provenance actor identity
timestamps
comments
notes
validation statements
review statements
content advisory statements
cultural protocol notes
file metadata
file contents
external work metadata
source ownership metadata
audience suitability metadata
restricted access metadata
redaction metadata
retention metadata
export metadata
```

The module must treat the following as sensitive:

```text
restricted archive records
restricted media records
restricted cultural protocol notes
integrity-sensitive records
proof records
personal testimony
personal educational work
personal portfolio material
validation comments
content review notes
content advisories involving trauma or violence
markers for sexual violence, self-harm, grief, racism, colonial violence, or cultural sensitivity
external work references tied to sensitive teaching or review context
```

---

## 6. Personal data fields

Any table with user references must be considered privacy-relevant.

Common user reference fields include:

```text
userid
createdby
modifiedby
submittedby
validatedby
reviewedby
exportedby
deletedby
actorid
sourceuserid
ownerid
```

Common timestamp fields include:

```text
timecreated
timemodified
timesubmitted
timevalidated
timereviewed
timeexported
timedeleted
```

Common privacy-relevant text fields include:

```text
title
name
description
summary
body
content
notes
reviewnotes
validationnotes
provenancenotes
redactionnotes
culturalnotes
advisorynotes
teachingnotes
sourcecitation
externalreference
```

All privacy provider logic must inspect both direct user fields and indirect user references embedded in structured metadata.

---

## 7. Archive privacy

Archive items may contain:

```text
personal submissions
course work
portfolio records
proof records
challenge evidence
assembly-related preserved material
integrity-related preserved material
public summaries
restricted notes
provenance history
validation history
revision history
export history
```

Archive privacy rule:

```text
Archive records must remain understandable over time without exposing more personal data than the requesting user is allowed to see.
```

Archive privacy export must include only records the requesting user has rights to receive through Moodle Privacy API rules and archive policy.

Archive deletion must respect retention rules, preservation duties, legal or cultural restrictions, and course context deletion.

---

## 8. Media privacy

Media objects may contain:

```text
uploaded files
original files
preview files
thumbnails
derivatives
captions
transcripts
attachments
metadata
source information
rights information
contributors
media versions
relations
collections
tags
content advisories
content markers
```

Media privacy rule:

```text
Media file existence is not access permission.
Access is resolved by context, capability, visibility, media status, content advisory rules, cultural protocol rules, and retention state.
```

Media privacy export must include media metadata and files only when the user has the right to receive them.

For privacy export, derivative files must not expose restricted source material if the user cannot access the original or relevant restricted metadata.

---

## 9. Content advisory privacy

Content advisories may reveal sensitive information about a work, a class, a learner, a community, a cultural protocol, or an institutional review.

The content advisory subsystem includes:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

Content advisory data may include:

```text
advisory tag keys
cultural sensitivity tags
cultural protocol tags
locator references
timecode ranges
page ranges
chapter ranges
scene references
review notes
suitability decisions
restriction decisions
review actor identity
review timestamps
contestation notes
```

Content advisory privacy rule:

```text
Content advisories are metadata, but they can still be sensitive.
They must be permission-filtered before display, export, search, backup preview, or API return.
```

Public users may see a simplified advisory label when appropriate.

Restricted users may see detailed markers, review notes, and cultural protocol notes only when policy allows.

---

## 10. Cultural protocol privacy

Cultural protocol data may be more sensitive than ordinary content advisory data.

Cultural protocol tags include:

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

Cultural protocol privacy rule:

```text
Cultural protocol data must be treated as restricted by default when marked restricted_cultural or when a policy rule requires review.
```

The module must support:

```text
restricted cultural visibility
staff-only notes
review-only notes
public-safe advisory summaries
export exclusion
metadata-only export
redacted export
contextual teaching notes
```

AI may suggest advisory or cultural tags.

AI must not approve cultural access, resolve contestations, or authorize restricted cultural viewing.

---

## 11. External work privacy

External works are represented by:

```text
uckkarchive_external_work
```

External works may include:

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

External work references may store:

```text
title
creator
publisher
year
edition
URL
citation
identifier
source notes
teaching notes
advisory markers
cultural protocol notes
rights notes
```

External work privacy rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, locators, teaching notes, and cultural protocol notes.
The archive must not imply ownership over third-party works.
```

External work metadata may be public, but local notes, teaching notes, review notes, cultural notes, and advisory decisions may be restricted.

---

## 12. Media source privacy

Media source records are represented by:

```text
uckkarchive_media_source
```

Media source values include:

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

Source ownership values include:

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

Media source privacy rule:

```text
Source describes origin and rights context.
Source does not grant access by itself.
Source does not override content advisory, cultural protocol, visibility, or retention policy.
```

Media source records may include personal data when the source is a user, partner, member, submitter, reviewer, or rights contact.

---

## 13. Visibility and restricted data

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

Restricted data must never be returned by:

```text
templates
output classes
external services
AMD calls
pluginfile URLs
exports
search results
event payloads
debug output
logs
backup previews
```

unless the active policy explicitly allows it.

---

## 14. Redaction model

The module must support multiple redaction levels.

Canonical redaction levels:

```text
none
minimal
standard
strict
metadata_only
fully_hidden
```

Redaction level meanings:

| Redaction level | Meaning |
|---|---|
| `none` | No redaction required for the current viewer/action. |
| `minimal` | Hide private notes and internal review details. |
| `standard` | Hide sensitive metadata, restricted notes, and personal identifiers not required for the action. |
| `strict` | Hide detailed content, locators, notes, actor identity, and restricted metadata. |
| `metadata_only` | Show only safe title/type/status-level metadata. |
| `fully_hidden` | Do not reveal that the record exists, unless policy requires a generic restricted notice. |

Redaction rule:

```text
Redaction happens before rendering, before service return, before export packaging, and before search indexing.
```

---

## 15. Redaction targets

Redaction may apply to:

```text
names
user identifiers
emails
profile links
free-text notes
validation notes
review notes
cultural protocol notes
content advisory notes
precise locators
timecodes
page ranges
external work notes
source ownership notes
restricted tags
file names
file contents
thumbnails
previews
transcripts
captions
derivatives
provenance details
revision details
export details
```

Redaction must preserve enough safe metadata to keep archive records understandable when policy permits metadata display.

---

## 16. Content advisory redaction

Content advisory redaction must support both safety and non-disclosure.

Example display modes:

```text
no_advisory_visible
summary_only
general_warning
tag_names_only
tags_with_locator
tags_with_review_summary
full_review_detail
```

Example public-safe display:

```text
Content advisory: mature themes.
```

Example guided-access display:

```text
Content advisory: sexual violence, page range available to authorized educators.
```

Example restricted display:

```text
Content advisory: sexual_violence, page 42-45, reviewed by authorized staff, approved for guided mature audience only.
```

Content advisory redaction rule:

```text
Precise locators and review notes are restricted unless the viewer has policy permission to see them.
```

---

## 17. Cultural protocol redaction

Cultural protocol redaction must avoid revealing restricted cultural knowledge through metadata.

For restricted cultural content, even the title, source, tag, marker, or locator may require redaction.

Cultural redaction modes:

```text
public_safe_notice
restricted_notice
metadata_only
protocol_summary
reviewer_only_detail
fully_hidden
```

Cultural protocol redaction rule:

```text
If revealing the advisory would reveal restricted knowledge, the advisory itself must be redacted.
```

Public-safe examples:

```text
This item has access conditions.
This item requires contextual guidance.
This item is not available for public export.
```

Avoid public exposure of:

```text
restricted ceremonial details
sacred content descriptions
community-specific restricted terms
elder review notes
non-public protocol rules
precise locators for restricted knowledge
```

---

## 18. File privacy

All files must be stored through Moodle File API.

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

File privacy rule:

```text
No plugin file may be served unless pluginfile policy confirms context, file area, item id, capability, visibility, media status, advisory policy, cultural protocol policy, retention state, and redaction rules.
```

Forbidden storage:

```text
No production archive/media files in unmanaged public folders.
No binary media files directly in custom database fields.
No direct public file URLs as authority.
```

---

## 19. Pluginfile privacy

`mod_uckkarchive_pluginfile()` in `lib.php` must route file access through a central policy layer.

The pluginfile handler must check:

```text
context validity
course module access
user login requirements
capability
file area registry
item ownership
media ownership
media version
visibility
restricted state
content advisory policy
cultural protocol policy
retention state
soft deletion state
redaction state
```

The pluginfile handler must not expose files based only on:

```text
context id
file area
item id
filename
stored_file existence
```

---

## 20. Retention model

Retention defines how long archive-owned records and files remain available.

Canonical retention outcomes:

```text
retain
retain_restricted
retain_metadata_only
redact
anonymize
soft_delete
delete_files_keep_record
delete_record_keep_audit
delete_all_allowed_data
```

Retention is decided by:

```text
course context
archive policy
media policy
content policy
validation state
restricted state
cultural protocol state
integrity-related state
export state
legal or institutional preservation requirement
user deletion request
course deletion request
```

Retention rule:

```text
The archive is a memory system.
Deletion is not always the correct outcome.
When preservation is required, use restriction, redaction, anonymization, or metadata-only retention.
```

---

## 21. Soft deletion

Canonical soft-deleted state:

```text
deleted_soft
```

Soft deletion means:

```text
not visible in ordinary UI
not searchable by ordinary users
not exportable by ordinary users
not downloadable by ordinary users
retained for policy, audit, restore, or retention purposes
available only to authorized roles when policy allows
```

Soft deletion must record:

```text
deleted flag
deletedby
timedeleted
delete reason
retention outcome
redaction level
```

Soft-deleted files must not be served through pluginfile unless policy explicitly allows administrative recovery.

---

## 22. Anonymization

Anonymization replaces identifying user data while preserving archive meaning where allowed.

Anonymization may apply to:

```text
createdby
modifiedby
submittedby
validatedby
reviewedby
exportedby
notes
comments
source identity
file metadata
provenance actor fields
review actor fields
```

Anonymization rule:

```text
Anonymized archive records must not retain direct identifiers for the anonymized user unless retention policy explicitly requires them.
```

Anonymized values must not create fake user identities.

Use neutral values such as:

```text
anonymized_user
removed_user
redacted_actor
```

---

## 23. Deletion

Deletion must be deliberate and policy-driven.

Deletion may involve:

```text
database record deletion
file deletion
metadata deletion
user reference anonymization
export package deletion
search index purge
cache purge
event/log non-expansion
soft deletion instead of hard deletion
```

Deletion rule:

```text
Hard deletion is allowed only when retention, audit, cultural protocol, integrity, and legal preservation rules permit it.
```

For user deletion requests, the privacy provider must choose the correct outcome for each record:

```text
delete
soft_delete
anonymize
redact
retain_restricted
retain_metadata_only
```

---

## 24. Export privacy

Archive/media exports are generated by `mod_uckkarchive`.

Institutional reporting exports are owned by `report_uckk`.

Archive export packages may contain:

```text
archive items
media metadata
media files
media versions
proofs
Kristals
provenance
revision history
validation state
content advisories
content markers
content reviews
external work references
export manifests
```

Export privacy rule:

```text
Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.
```

Every export package must include:

```text
manifest.json
```

The manifest must include redaction and restriction metadata when applicable.

The manifest must not expose restricted notes to unauthorized export recipients.

---

## 25. Export redaction

Export redaction must support:

```text
full export
restricted export
redacted export
metadata-only export
public export
teaching export
review export
integrity export
cultural protocol restricted export
```

Export redaction must filter:

```text
files
file names
media versions
content markers
precise locators
review notes
cultural notes
private provenance
revision comments
actor identity
restricted metadata
external work teaching notes
```

Export packages must not include hidden file areas unless policy allows.

---

## 26. Privacy export for a user

When Moodle requests a user data export, `classes/privacy/provider.php` must include user-related records from:

```text
archive items created by the user
archive items modified by the user
proofs submitted by the user
Kristals created or modified by the user
media submitted by the user
media versions created by the user
media collections created by the user
media relations created by the user
content markers created by the user
content reviews performed by the user
external work references created by the user
provenance records involving the user
revision records involving the user
export records created by the user
files uploaded by the user
```

Privacy export must respect access restrictions and Moodle Privacy API expectations.

If a record contains multiple users, export only the requesting user’s appropriate data unless policy allows broader disclosure.

---

## 27. Privacy deletion for a user

When Moodle requests deletion of data for a user, the provider must evaluate each record where the user appears.

Possible outcomes:

```text
delete if private draft and no preservation need
soft_delete if user-owned but audit retention is required
anonymize if archive meaning must remain
redact if sensitive notes include the user
retain_restricted if preservation is required
retain_metadata_only if only non-identifying record structure must remain
```

User deletion must not:

```text
break archive referential integrity
erase required validation history without replacement
erase required provenance without policy decision
expose other users' data
delete third-party records owned by other users
delete external works because one user referenced them
```

---

## 28. Course/context deletion

When a Moodle context is deleted, the plugin must process archive-owned data in that context.

Context deletion may result in:

```text
full deletion
soft deletion
archive retention
metadata-only retention
restricted institutional retention
export package purge
file purge
```

Context deletion rule:

```text
Context deletion removes ordinary course access.
It does not automatically erase preserved archive memory when retention policy requires preservation.
```

If retained after context deletion, the record must no longer appear in ordinary course UI.

---

## 29. Backup and restore privacy

Backup must include only archive-owned data intended for backup.

Restore must reconstruct archive-owned records only.

Backup/restore privacy rule:

```text
Backup and restore do not grant new access rights.
Restored records must still be governed by context, capabilities, visibility, restricted state, content advisory rules, cultural protocol rules, and redaction policy.
```

Backup must include enough metadata to restore:

```text
retention state
redaction level
restricted state
content advisory state
cultural protocol state
external work references
media source records
review states
```

Backup must not expose restricted content in backup logs, progress messages, or error messages.

---

## 30. Search and indexing privacy

Search and indexing must use redacted data.

Search indexes must not include:

```text
restricted notes
cultural protocol notes
private validation comments
private review notes
restricted advisory details
precise restricted locators
hidden external work teaching notes
restricted file contents
restricted transcripts
restricted captions
```

Search result rule:

```text
Search results must reveal only records and fields the viewer is allowed to see.
```

If a record is hidden by policy, search must not reveal its title, type, location, or existence unless policy allows a generic restricted notice.

---

## 31. Events and audit privacy

Events must audit successful state changes.

Event payloads must not expose:

```text
restricted content
raw file content
private notes
restricted cultural notes
redacted metadata
personal testimony
precise advisory locators
sensitive review text
```

Events may include:

```text
context id
object id
related user id where required
anonymous status flags
safe object type
safe action type
```

Event privacy rule:

```text
Events are for audit, not content transport.
```

---

## 32. External service privacy

External services must return policy-filtered data only.

External service classes must check:

```text
context
capability
visibility
ownership
media status
archive item status
validation state
restricted state
content advisory policy
cultural protocol policy
redaction level
retention state
```

External services must not return raw restricted data and rely on AMD, Mustache, or browser-side filtering.

Client-side code is not a privacy boundary.

---

## 33. UI privacy

Templates and output classes must receive pre-filtered data.

UI privacy rule:

```text
Templates render.
They do not authorize.
They do not redact.
They do not decide access.
```

Output classes may format data but must not override policy.

AMD modules may request data but must not decide whether data is allowed.

---

## 34. AI-assisted metadata privacy

AI may assist with:

```text
draft summaries
suggested tags
suggested content advisories
suggested content markers
suggested transcripts
suggested descriptions
suggested metadata normalization
```

AI must not:

```text
approve cultural protocol access
validate archive records
invalidate archive records
close contestations
override human review
decide privacy deletion
decide final redaction policy
```

AI-generated suggestions must be marked with provenance:

```text
ai_assisted
```

AI-generated content advisories or markers must remain unapproved until human review.

---

## 35. Content review privacy

Content reviews are represented by:

```text
uckkarchive_content_review
```

Content reviews may contain:

```text
reviewer identity
review timestamp
review decision
suitability decision
cultural protocol decision
restriction decision
private notes
public-safe summary
contestation state
```

Content review privacy rule:

```text
Review decisions may be visible.
Review notes are restricted unless policy allows.
```

The system must distinguish:

```text
public review summary
internal review notes
restricted cultural notes
staff-only notes
```

---

## 36. Tags and tag sets privacy

Content tags and tag sets may be public vocabularies or restricted vocabularies.

Tag sets are represented by:

```text
uckkarchive_content_tag_set
```

Tag set examples:

```text
general_advisories
cultural_protocols
classroom_suitability
integrity_sensitive
youth_access
```

Tag privacy rule:

```text
A tag key may be public, restricted, or culturally restricted.
The presence of a restricted tag on a record may itself be restricted.
```

Do not assume all tags can be shown to all users.

---

## 37. Reports and institutional exports boundary

`mod_uckkarchive` owns archive export packages.

`report_uckk` owns institutional reporting views and institutional report exports.

Privacy boundary rule:

```text
mod_uckkarchive does not become report_uckk.
report_uckk does not bypass mod_uckkarchive privacy policy when reading archive data.
```

When report systems consume archive data, they must receive redacted or permission-filtered data appropriate to the report context and actor.

---

## 38. Retention configuration

The module should support configurable retention settings for:

```text
draft archive items
submitted archive items
validated archive items
restricted archive items
media originals
media derivatives
media previews
media thumbnails
content reviews
content markers
external work references
export packages
export manifests
soft-deleted records
```

Retention configuration must not allow a lower-privileged user to disable required preservation, audit, privacy, cultural protocol, or integrity rules.

---

## 39. Scheduled retention tasks

Scheduled tasks may support:

```text
purge expired exports
purge expired temporary files
redact expired review notes
anonymize expired user references
remove orphaned derivatives
rebuild redacted search indexes
verify soft-deleted file inaccessibility
```

Task privacy rule:

```text
Scheduled tasks reuse classes/local policy logic.
Scheduled tasks do not bypass retention, redaction, cultural protocol, or privacy rules.
```

---

## 40. Required implementation files

Privacy implementation:

```text
classes/privacy/provider.php
```

Policy implementation:

```text
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

Retention and redaction helpers may be implemented in:

```text
classes/local/retention_policy.php
classes/local/redaction_policy.php
classes/local/metadata_validator.php
classes/local/file_area_registry.php
```

Content advisory implementation:

```text
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/content_marker.php
classes/local/content_review.php
classes/local/external_work.php
classes/local/media_source.php
```

Service implementation must respect privacy in:

```text
classes/external/*
```

File serving must respect privacy in:

```text
lib.php
```

Backup/restore must preserve privacy metadata in:

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

---

## 41. Required tests

Privacy and redaction tests must verify:

```text
privacy export includes correct user data
privacy deletion respects retention policy
restricted records are hidden from unauthorized users
pluginfile refuses unauthorized file access
media originals are not exposed through derivatives
content advisories are redacted by policy
cultural protocol notes are hidden by default
external work notes are permission-filtered
exports do not bypass privacy
backup/restore preserves restricted state
search does not reveal hidden records
events do not expose restricted content
AI-assisted suggestions require human review
```

Required test files include:

```text
tests/privacy_provider_test.php
tests/file_api_test.php
tests/export_test.php
tests/content_advisory_test.php
tests/external_work_test.php
tests/media_library_test.php
tests/services_test.php
```

---

## 42. Final privacy rule

```text
mod_uckkarchive preserves archive memory without treating preservation as unlimited disclosure.

Every archive item, media object, file, content marker, content review, external work reference, export, and manifest is governed by context, capability, visibility, retention, redaction, content advisory policy, cultural protocol policy, and Moodle Privacy API rules.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
