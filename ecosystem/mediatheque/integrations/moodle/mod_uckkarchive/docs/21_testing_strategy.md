# 21 — Testing Strategy

**Path:** `docs/21_testing_strategy.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Test strategy for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines the final testing strategy for `mod_uckkarchive`.

`mod_uckkarchive` is a Moodle-native activity module with a self-contained archive, media library, and content advisory system.

The test suite must prove that the module behaves correctly as:

```text
archive memory engine
media library engine
content advisory governance engine
Moodle activity module
File API consumer
Privacy API provider
Backup/restore participant
External services provider
UI-rendered Moodle module
```

Testing must verify final target behavior.

Testing must not depend on historical gap documents, acceptance checklists, or release notes.

---

## 2. Core testing principle

Canonical rule:

```text
Tests verify implemented behavior against final-state specifications.
Tests do not document historical transitions.
Tests do not preserve obsolete architecture.
```

All tests must align with:

```text
docs/_alignment_variables.md
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
docs/22_installation.md
docs/23_upgrade.md
docs/24_release_spec.md
```

---

## 3. Required test files

Canonical test files:

```text
tests/archive_test.php
tests/backup_restore_test.php
tests/content_advisory_test.php
tests/export_test.php
tests/external_work_test.php
tests/file_api_test.php
tests/lib_test.php
tests/media_library_test.php
tests/privacy_provider_test.php
tests/services_test.php
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

Optional future expansion may split large files by subsystem, but these files define the required baseline.

---

## 4. Testing layers

The test suite must cover these layers:

```text
unit/domain tests
database tests
File API tests
policy tests
external service tests
privacy provider tests
backup/restore tests
export/manifest tests
event/audit tests
scheduled task tests
renderer/output tests
Behat UI tests
upgrade tests
```

Each layer tests a different responsibility.

No layer should duplicate all behavior from another layer.

---

## 5. Archive tests

File:

```text
tests/archive_test.php
```

Archive tests must cover:

```text
activity instance creation
archive item creation
archive item draft state
archive item submitted state
archive item validated state
archive item restricted state
archive item contested state
archive item invalidated state
archive item archived state
archive item visibility filtering
archive item revision
archive item provenance
archive item proof linkage
archive item Kristal linkage
archive item export eligibility
archive item redaction eligibility
```

Archive tests must verify canonical statuses:

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

Archive tests must verify canonical validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Archive tests must verify that:

```text
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
AI cannot approve cultural protocol access.
```

---

## 6. Media library tests

File:

```text
tests/media_library_test.php
```

Media library tests must cover:

```text
media object creation
media uuid generation
media source metadata
media version creation
media version inheritance
media original file registration
media preview file registration
media thumbnail file registration
media derivative file registration
media caption file registration
media transcript file registration
media attachment file registration
media visibility filtering
media lifecycle transitions
media soft deletion
media relation creation
media collection creation
media collection membership
media tag assignment
media search indexing behavior
media export eligibility
restricted media behavior
culturally restricted media behavior
```

Media tests must verify canonical media states:

```text
draft
submitted
active
restricted
superseded
archived
deleted_soft
```

Media tests must verify that file existence does not equal media availability.

Media status, visibility, policy, and retention must control usability.

---

## 7. Content advisory tests

File:

```text
tests/content_advisory_test.php
```

Content advisory tests must cover:

```text
content tag creation
content tag set creation
content marker creation
content marker locator validation
content marker review
content review state transitions
content advisory visibility
audience suitability behavior
cultural protocol behavior
restricted cultural access
advisory acknowledgement behavior
content marker relation to media
content marker relation to media version
content marker relation to archive item
content marker relation to external work
content marker redaction behavior
```

Content advisory tests must verify required tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_media_source
```

Content advisory tests must verify canonical review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Content advisory tests must verify canonical severity values:

```text
notice
moderate
strong
restricted
```

Content advisory tests must verify that a content advisory does not automatically ban media.

It must define conditions for responsible access, warning, review, restriction, teaching, or contextualization.

---

## 8. External work tests

File:

```text
tests/external_work_test.php
```

External work tests must cover:

```text
external work creation
external work metadata validation
external work type validation
external source ownership validation
external rights metadata
external locator metadata
external work advisory markers
foreign media reference behavior
reference-only external media
licensed external media
public domain external media
fair-use reference behavior
restricted reference behavior
export of external work metadata
redaction of restricted external work notes
```

External work tests must verify supported external work types:

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

External work tests must verify that the archive does not imply ownership over third-party works.

---

## 9. File API tests

File:

```text
tests/file_api_test.php
```

File API tests must cover:

```text
pluginfile access
context resolution
file area registry
item file access
proof file access
Kristal file access
provenance file access
validation file access
revision file access
export package access
export manifest access
media original access
media preview access
media thumbnail access
media derivative access
media caption access
media transcript access
media attachment access
content review file access
external work reference file access
cultural protocol file access
restricted file denial
redacted file denial
deleted_soft media file denial
```

Canonical component:

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

File API tests must verify:

```text
No production archive/media files are served from unmanaged public folders.
No binary media files are stored directly in custom database fields.
File URL possession is not authority.
```

---

## 10. Permission and policy tests

Permission tests may live in:

```text
tests/archive_test.php
tests/media_library_test.php
tests/content_advisory_test.php
tests/services_test.php
tests/file_api_test.php
```

Policy tests must verify that Moodle capabilities are gates, not final authority.

Policy classes:

```text
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

Policy tests must cover:

```text
view archive
add archive item
revise archive item
validate archive item
export archive item
view media
add media
edit media
delete media
download media
version media
export media
manage media collections
view advisories
manage advisories
review advisories
view culturally restricted material
manage external works
```

Policy tests must verify that templates, AMD, forms, and controllers do not authorize access.

Server-side policy must filter before rendering or service return.

---

## 11. Capability tests

Capability tests must verify canonical archive capabilities:

```text
mod/uckkarchive:addinstance
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Capability tests must verify canonical media capabilities:

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

Capability tests must verify canonical content advisory capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:manageexternalworks
```

Capability tests must verify that the module does not use:

```text
mod/uckkarchive:versionitem
```

---

## 12. External service tests

File:

```text
tests/services_test.php
```

Service tests must cover:

```text
parameter validation
context resolution
login requirement
capability checks
policy checks
record existence
record visibility
return value filtering
warning generation
exception behavior
state-changing service events
restricted data denial
redacted data denial
```

Service tests must cover archive services, media services, content advisory services, external work services, and export services.

Services must not return restricted data for client-side hiding.

Filtering must happen server-side.

---

## 13. Privacy provider tests

File:

```text
tests/privacy_provider_test.php
```

Privacy tests must cover:

```text
archive item user data
proof user data
Kristal user data
provenance user data
revision user data
export user data
media object user data
media version user data
media source user data
media collection user data
media relation user data
media tag user data
content tag user data
content marker user data
content review user data
external work curator data
restricted metadata
cultural protocol notes
content advisory notes
file references
```

Privacy tests must verify:

```text
privacy export
privacy deletion
privacy redaction
retention-aware deletion
restricted data handling
third-party data handling
institutional preservation behavior
```

A privacy request must not automatically bypass archive, media, content, retention, or cultural protocol policy.

---

## 14. Backup and restore tests

File:

```text
tests/backup_restore_test.php
```

Backup/restore tests must verify preservation of:

```text
archive records
archive items
proof records
Kristals
provenance records
revision records
export records
media records
media versions
media relations
media tags
media collections
media collection membership
content tags
content tag sets
content markers
content reviews
external works
media source records
file areas
visibility
restricted flags
cultural protocol flags
audience suitability
validation state
redaction state
retention class
UUIDs
source references
export manifests
```

Restore tests must verify:

```text
ID mapping
file restoration
media relation restoration
collection restoration
external work restoration
content marker restoration
restricted state preservation
cultural protocol preservation
privacy-sensitive data preservation according to policy
```

Restore must not create:

```text
grades
challenge attempts
Assembly decisions
integrity cases
institutional reports
external authority records
```

---

## 15. Export and manifest tests

File:

```text
tests/export_test.php
```

Export tests must cover:

```text
archive item export
selected archive export
media export
media collection export
restricted export denial
redacted export
content advisory manifest inclusion
external work metadata export
file hash generation
manifest generation
export package creation
export package access
export retention
export status services
```

Canonical manifest filename:

```text
manifest.json
```

Manifest tests must verify inclusion of:

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

Exports must not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.

---

## 16. Event and audit tests

Event tests must cover events such as:

```text
archive_viewed
archive_item_created
archive_item_validated
archive_item_revised
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

Event tests must verify:

```text
correct context
correct object id
correct related user id when applicable
correct other data when applicable
no raw restricted content in event payload
no private cultural protocol notes in event payload
no redacted data in event payload
```

Events audit successful state changes.

Events must not leak sensitive content.

---

## 17. Scheduled task tests

Scheduled task tests may live in subsystem test files.

Tasks to test:

```text
classes/task/generate_archive_exports.php
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
classes/task/validate_pending_items.php
```

Task tests must verify:

```text
task registration
task execution
idempotency where required
policy-safe output
failure handling
restricted data handling
file creation through Moodle File API
no bypass of domain policy
```

Scheduled tasks reuse `classes/local` domain logic.

---

## 18. Renderer and output tests

Renderer/output tests must verify renderable payloads for:

```text
archive item card
archive view
Kristal card
media card
media collection
media library
media version list
content advisory panel
external work card
provenance panel
validation panel
```

Output tests must verify:

```text
permission-filtered fields
redacted fields
restricted badges
content advisory badges
cultural protocol badges
download flags
export flags
review flags
no hidden raw restricted payload
```

Output classes format permission-filtered data.

Output classes do not authorize access.

---

## 19. Behat UI tests

Required Behat files:

```text
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

### 19.1 Archive Behat coverage

Archive UI tests must cover:

```text
teacher creates archive activity
participant views archive activity
participant submits archive item
mentor revises archive item
archivist validates archive item
restricted archive item is hidden from unauthorized user
validated archive item appears to authorized user
archive item export action is visible only when allowed
```

### 19.2 Media Behat coverage

Media UI tests must cover:

```text
authorized user opens media library
authorized user adds media
authorized user edits media metadata
authorized user adds media version
authorized user creates media collection
authorized user adds media to collection
unauthorized user cannot download media original
restricted media thumbnail is hidden or redacted
deleted_soft media is not shown as active
```

### 19.3 Content advisory Behat coverage

Content advisory UI tests must cover:

```text
authorized user creates content marker
authorized user adds advisory tag
authorized reviewer reviews advisory
content advisory badge appears where permitted
cultural protocol badge appears where permitted
unauthorized user cannot view culturally restricted details
external work is referenced without implying ownership
advisory acknowledgement appears where required
```

Behat tests must focus on user-visible behavior.

Policy depth belongs in PHPUnit tests.

---

## 20. Upgrade tests

Upgrade tests must verify schema migration in:

```text
db/upgrade.php
```

Upgrade tests must cover:

```text
new archive fields
new media tables
new media version tables
new media relation tables
new media tag tables
new media collection tables
new content advisory tables
new external work tables
new source fields
new uuid fields
new visibility values
new file area normalization
capability additions
removed versionitem capability absence
```

Upgrade must preserve existing archive data.

Upgrade must not create invalid permissions.

Upgrade must not expose restricted data.

---

## 21. Installation tests

Installation tests must verify:

```text
db/install.xml creates all required tables
db/access.php defines all required capabilities
db/services.php defines all required services
db/events.php registers required observers
db/tasks.php registers required tasks
version.php has correct component metadata
tool_uckkintegrity is not a hard dependency
local_uckk dependency is handled according to plugin architecture
```

Installation must not require raw public folders for media storage.

---

## 22. Integration tests

Integration tests must verify boundaries with:

```text
Moodle course context
Moodle gradebook
local_uckk
mod_uckkchallenge
mod_uckkassembly
tool_uckkintegrity
report_uckk
```

Boundary tests must verify:

```text
archive can reference external domains
archive does not own external authority
archive does not create grades
archive does not create challenge workflow state
archive does not create Assembly decisions
archive does not create integrity cases
archive does not create institutional reports
```

Optional integrations must fail closed when absent.

---

## 23. Search and listing tests

Search/listing tests must verify:

```text
archive search filtering
media search filtering
content marker search filtering
external work search filtering
collection listing filtering
tag facet filtering
advisory facet filtering
restricted count protection
autocomplete protection
thumbnail protection
preview protection
snippet protection
```

Search must not leak restricted records through:

```text
title
snippet
thumbnail
preview
caption
transcript
tag
collection membership
content advisory marker
external work reference
count
facet
autocomplete
```

---

## 24. Redaction tests

Redaction tests must verify:

```text
restricted archive fields redacted
restricted media metadata redacted
restricted thumbnails hidden or replaced
restricted previews hidden or replaced
cultural protocol notes redacted
private review notes redacted
external work restricted notes redacted
manifest redaction
privacy export redaction
service response redaction
UI payload redaction
```

Redaction must be enforced server-side.

---

## 25. Negative tests

The suite must include negative tests for:

```text
unauthenticated access
missing capability
wrong course context
wrong archive instance
wrong media id
wrong media uuid
restricted record without permission
culturally restricted record without permission
download without download capability
export without export capability
review without review capability
invalid locator
invalid source ownership
invalid visibility value
invalid media state transition
invalid validation transition
invalid relation type
invalid file area
deleted_soft media access
```

Negative tests are required for trust.

---

## 26. Test data builders

The module should use test data helpers for:

```text
archive instance
archive item
proof
Kristal
provenance record
revision record
media object
media version
media relation
media tag
media collection
media collection item
content tag
content tag set
content marker
content review
external work
media source
export package
```

Builders must create valid objects by default.

Invalid test objects should be explicit.

---

## 27. Fixture principles

Fixtures must be:

```text
minimal
explicit
policy-aware
context-aware
repeatable
isolated
```

Fixtures must avoid:

```text
global state pollution
hardcoded unrelated users
unmanaged files
public folder media
hidden dependencies on optional plugins
```

---

## 28. Performance and scale tests

The test suite should include reasonable scale checks for:

```text
archive item listing
media listing
media search
content marker search
collection membership
export manifest generation
backup structure generation
privacy metadata export
```

Scale tests should verify that permission filtering remains correct under larger datasets.

---

## 29. Security tests

Security tests must cover:

```text
capability enforcement
context isolation
file access enforcement
external service access
restricted data filtering
redaction
content advisory restriction
cultural protocol restriction
export restriction
CSRF/session behavior where applicable
input validation
parameter validation
```

Security tests must verify that client-side hiding is never the only protection.

---

## 30. Test ownership map

| Area | Primary test file |
|---|---|
| Archive domain | `tests/archive_test.php` |
| Media domain | `tests/media_library_test.php` |
| Content advisories | `tests/content_advisory_test.php` |
| External works | `tests/external_work_test.php` |
| File API | `tests/file_api_test.php` |
| Services | `tests/services_test.php` |
| Privacy | `tests/privacy_provider_test.php` |
| Backup/restore | `tests/backup_restore_test.php` |
| Exports/manifests | `tests/export_test.php` |
| Moodle callbacks | `tests/lib_test.php` |
| Archive UI | `tests/behat/uckkarchive.feature` |
| Media UI | `tests/behat/uckkarchive_media.feature` |
| Content advisory UI | `tests/behat/uckkarchive_content_advisory.feature` |

---

## 31. Required test assertions

Every relevant test should assert:

```text
record exists
record belongs to correct context
record uses correct component
record has correct status
record has correct visibility
record has correct uuid
record has correct provenance
record is permission-filtered
record is redacted when required
record is exported only when permitted
record is restored correctly
record does not leak restricted data
```

---

## 32. Final testing rule

```text
The test suite must prove that mod_uckkarchive works as a self-contained
archive, media library, and content advisory system inside Moodle.

It must prove that the module owns archive/media/content records while using
Moodle for context, users, roles, capabilities, File API, Privacy API,
Backup/Restore API, events, services, settings, rendering, and scheduled tasks.

It must prove that restricted, culturally sensitive, external, redacted,
private, and retention-controlled records remain protected across UI, services,
files, exports, backup, restore, privacy, and search.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
