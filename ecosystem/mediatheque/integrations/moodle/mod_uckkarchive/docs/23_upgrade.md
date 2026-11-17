# 23 — Upgrade

**Path:** `docs/23_upgrade.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Upgrade and migration contract for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines the final upgrade contract for `mod_uckkarchive`.

The upgrade process must move existing installations to the target architecture:

```text
mod_uckkarchive = self-contained archive + media library + content advisory system
```

Canonical formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

The upgrade process must preserve archive memory, media files, provenance, revisions, restricted state, privacy behavior, backup/restore compatibility, and export identity.

---

## 2. Upgrade owner

The upgrade owner is:

```text
db/upgrade.php
```

The target schema owner is:

```text
db/install.xml
```

Upgrade rules:

```text
db/install.xml defines the full current target schema.
db/upgrade.php migrates existing installs to the current target schema.
```

Upgrade must use Moodle XMLDB APIs.

Upgrade must not rely on unmanaged SQL that bypasses Moodle database portability.

Upgrade must be idempotent at each step through Moodle upgrade savepoints.

---

## 3. Upgrade principles

Every upgrade step must follow these rules:

```text
preserve existing archive records
preserve existing media and file references
preserve user ownership and timestamps where possible
preserve provenance
preserve revision history
preserve validation state
preserve visibility and restricted state
preserve backup/restore compatibility
preserve privacy provider behavior
avoid public exposure of restricted data
fail closed for unknown restricted or integrity-linked records
```

Upgrade must not:

```text
delete archive records silently
delete media files silently
make restricted records public
convert evidence files into unmanaged public files
create gradebook records
create administrative registry records
create live integrity procedure records
claim Assembly decision authority
claim institutional reporting authority
```

---

## 4. Version checkpoint pattern

`db/upgrade.php` must use Moodle version checkpoints.

Pattern:

```php
if ($oldversion < 2026052701) {
    // Apply schema/data migration.
    upgrade_mod_savepoint(true, 2026052701, 'uckkarchive');
}
```

Rules:

```text
Each checkpoint has one clear purpose.
Each checkpoint is safe to run only once.
Each checkpoint checks whether fields, tables, keys, indexes, and capabilities already exist.
Each checkpoint writes an upgrade savepoint after success.
```

---

## 5. Required target tables

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

Table rule:

```text
All target tables must exist after upgrade.
All newly created tables must include stable identifiers, timestamps, user references, and indexes required by services, privacy, backup, restore, and export.
```

---

## 6. UUID migration

Stable UUIDs are mandatory.

Identifier rule:

```text
id = local Moodle database primary key
uuid = stable portable object identity
```

UUIDs must exist for:

```text
archive items
proof records
Kristals
provenance records where exported or referenced
revision records where exported or referenced
export packages
media objects
media versions
media collections
media relations
content markers
content reviews
external works
media sources
```

UUID migration workflow:

```text
1. Add uuid fields where missing.
2. Backfill UUIDs for existing records.
3. Ensure UUIDs are unique.
4. Add indexes or unique keys where appropriate.
5. Preserve UUIDs in backup, restore, export, and manifests.
```

UUID rule:

```text
UUIDs must be generated once and then treated as stable.
Upgrade must not regenerate UUIDs for records that already have them.
```

---

## 7. Media schema upgrade

Media becomes first-class.

Upgrade must ensure these tables exist:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
uckkarchive_media_source
```

Media migration workflow:

```text
1. Create media tables if missing.
2. Add source, visibility, status, audience suitability, and current version fields.
3. Backfill media objects from existing archive-owned file references where applicable.
4. Create initial media version records for existing media files where applicable.
5. Store file hash, MIME type, size, filename, and file-area metadata where available.
6. Preserve archive item links through media relations.
7. Preserve file storage in Moodle File API.
8. Mark records with conservative visibility when prior visibility is unclear.
```

Media migration rule:

```text
Existing files must not be moved to unmanaged public folders.
Existing files must not be duplicated unnecessarily.
Existing files must remain served through Moodle File API.
```

---

## 8. Media lifecycle backfill

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

Backfill rule:

```text
Existing usable media should become active only when visibility and access are known.
Existing restricted or uncertain media should become restricted.
Existing removed media should become deleted_soft or archived according to retention policy.
```

Default mapping:

| Existing condition | Target media status |
|---|---|
| Normal visible file with valid archive context | `active` |
| File linked to restricted archive item | `restricted` |
| File linked to integrity-related record | `restricted` |
| File linked to culturally sensitive marker | `restricted` |
| File retained for evidence/history | `archived` |
| File marked removed but retained | `deleted_soft` |
| Unknown status | `restricted` |

Safety rule:

```text
Unknown status fails closed.
```

---

## 9. Visibility migration

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

Visibility migration workflow:

```text
1. Normalize legacy visibility values.
2. Convert institutional to institution.
3. Preserve public only when explicitly public.
4. Preserve restricted and integrity-related records as restricted_integrity where applicable.
5. Preserve cultural protocol restrictions as restricted_cultural where applicable.
6. Default unknown visibility to restricted.
```

Visibility rule:

```text
Upgrade must not make private, restricted, integrity-linked, or culturally restricted data public.
```

---

## 10. Capability upgrade

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

Removed capability:

```text
mod/uckkarchive:versionitem = not used
```

Capability migration rule:

```text
Do not create or preserve mod/uckkarchive:versionitem as a target capability.
Archive item revision uses mod/uckkarchive:reviseitem.
Media versioning uses mod/uckkarchive:versionmedia.
```

Role assignment rule:

```text
New powerful capabilities must not be granted broadly by upgrade unless explicitly safe.
Restricted, cultural, export, advisory review, and external work management capabilities should default conservatively.
```

---

## 11. File API upgrade

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

File API upgrade workflow:

```text
1. Ensure classes/local/file_area_registry.php lists all canonical file areas.
2. Normalize legacy file area names where needed.
3. Preserve existing files in Moodle File API.
4. Attach existing files to archive or media records through stable item ids.
5. Create media version records for media files where applicable.
6. Ensure pluginfile handling recognizes canonical areas.
7. Ensure privacy, backup, restore, and tests use the registry.
```

Forbidden storage:

```text
No production archive/media files in unmanaged public folders.
No binary media files directly in custom database fields.
No direct public file URLs as authority.
```

---

## 12. Content advisory schema upgrade

Content advisory and cultural protocol handling are first-class.

Required tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

Upgrade workflow:

```text
1. Create content advisory tables if missing.
2. Seed required tag sets.
3. Seed baseline advisory tags.
4. Add marker UUID support.
5. Add review state support.
6. Add audience suitability support.
7. Add cultural protocol flags.
8. Link markers to media, media versions, archive items, external works, or manual references.
```

Architecture rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 13. Content tag seed data

Baseline tag sets:

```text
general_advisories
cultural_protocols
classroom_suitability
integrity_sensitive
youth_access
```

Baseline content advisory tags:

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

Baseline cultural protocol tags:

```text
community_permission_required
elder_review_required
seasonal_or_contextual_access
not_for_public_export
```

Seed rule:

```text
Seed records must be inserted only if missing.
Existing edited records must not be overwritten by upgrade.
```

---

## 14. Content marker upgrade

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

Content marker migration workflow:

```text
1. Create marker table if missing.
2. Add locator fields.
3. Add target fields for media, media version, archive item, external work, or manual reference.
4. Add advisory tag linkage.
5. Add review state.
6. Add visibility and audience suitability fields.
7. Default uncertain sensitive markers to pending_review or restricted.
```

Marker rule:

```text
Content markers must not expose sensitive locator details to unauthorized users.
```

---

## 15. Content review upgrade

Canonical review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Content review migration workflow:

```text
1. Create review table if missing.
2. Add reviewer user reference.
3. Add review state.
4. Add rationale/note fields.
5. Add timestamps.
6. Add files through content_review_files where needed.
7. Ensure review records are included in privacy, backup, restore, and export manifests.
```

AI rule:

```text
AI may suggest tags or markers.
AI cannot approve content advisories.
AI cannot approve cultural protocol access.
Human review is required before advisory status becomes approved.
```

---

## 16. External work upgrade

External works are represented by:

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

Upgrade workflow:

```text
1. Create external work table if missing.
2. Add UUID, title, creator, year, source, URL, identifier, rights note, and citation fields.
3. Add visibility and audience suitability fields.
4. Add provenance and user references.
5. Link external works to content markers, media relations, archive items, or collections.
```

External work rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 17. Media source upgrade

Media source records are represented by:

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

Upgrade workflow:

```text
1. Create media source table if missing.
2. Add source type and ownership fields.
3. Backfill source records for existing media where possible.
4. Default unknown source to unknown_source.
5. Default rights uncertainty to restricted_reference where appropriate.
6. Link media records to media source records.
```

Source rule:

```text
Unknown source must not be treated as public domain.
```

---

## 18. Provenance upgrade

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

Provenance migration workflow:

```text
1. Ensure provenance table supports source component, source area, source id, UUID, actor, timestamp, and metadata.
2. Normalize provenance values.
3. Add missing provenance records where safe.
4. Preserve source references for imported or external records.
5. Add provenance links for media versions, external works, content markers, and reviews.
```

Provenance rule:

```text
Provenance explains origin.
Provenance does not grant authority by itself.
```

---

## 19. Validation upgrade

Canonical validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Validation migration workflow:

```text
1. Normalize validation state values.
2. Preserve contested and invalidated states.
3. Default unknown validation state to unverified.
4. Do not auto-verify archive records.
5. Do not auto-approve advisory review records.
6. Do not auto-approve cultural protocol access.
```

Validation rules:

```text
Validation is human-final.
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
AI cannot approve cultural protocol access.
```

---

## 20. Archive item status upgrade

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

Status migration workflow:

```text
1. Normalize old status values.
2. Preserve restricted, contested, invalidated, and archived states.
3. Map active published records only when access policy confirms visibility.
4. Default uncertain records to restricted or under_review.
```

Status rule:

```text
Unknown or sensitive state fails closed.
```

---

## 21. Media relation upgrade

Canonical media relation types:

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

Relation upgrade workflow:

```text
1. Create relation table if missing.
2. Backfill item-file links as belongs_to_item.
3. Backfill Kristal links as belongs_to_kristal.
4. Backfill collection links as belongs_to_collection.
5. Backfill derivative/thumbnail/source references where known.
6. Link external works through references_external_work.
7. Link markers through contains_content_marker where needed.
```

Relation rule:

```text
Relations describe graph meaning.
Relations do not transfer ownership to external plugins or external rights holders.
```

---

## 22. Collection upgrade

Collections are represented by:

```text
uckkarchive_media_collection
uckkarchive_media_collection_item
```

Collection upgrade workflow:

```text
1. Create collection tables if missing.
2. Generate UUIDs for existing logical bundles where applicable.
3. Preserve ordering.
4. Preserve visibility.
5. Preserve restricted state.
6. Link collection items by media id and UUID.
```

Collection examples:

```text
course pack
Kristal source pack
challenge evidence pack
assembly record pack
public media set
restricted proof bundle
external work study set
cultural protocol set
```

Collection rule:

```text
Collections group media.
Collections do not duplicate media files.
Collections do not override media-level restrictions.
```

---

## 23. Export upgrade

Export records are represented by:

```text
uckkarchive_export
```

Canonical export file areas:

```text
export_package
export_manifest
```

Canonical manifest filename:

```text
manifest.json
```

Export upgrade workflow:

```text
1. Ensure export table exists.
2. Add UUID, status, actor, reason, timestamp, redaction, visibility, and manifest metadata fields.
3. Preserve existing export package files.
4. Generate manifest records for future exports.
5. Do not retroactively expose restricted content through regenerated manifests.
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

## 24. Service upgrade

External service declarations belong in:

```text
db/services.php
```

Upgrade must ensure services exist for:

```text
archive workflows
media workflows
media collections
media versions
media relations
media tags
content tags
content tag sets
content markers
content reviews
external works
export preview
export generation
export status
```

Service rule:

```text
Services must check context, capability, visibility, status, content advisory rules, cultural protocol restrictions, redaction, and retention.
```

No service may expose restricted records through incomplete filtering.

---

## 25. Event upgrade

Observer registration belongs in:

```text
db/events.php
```

Event classes include:

```text
classes/event/archive_viewed.php
classes/event/archive_item_created.php
classes/event/archive_item_validated.php
classes/event/archive_item_revised.php
classes/event/archive_item_exported.php
classes/event/media_created.php
classes/event/media_updated.php
classes/event/media_version_created.php
classes/event/media_collection_created.php
classes/event/media_exported.php
classes/event/content_marker_created.php
classes/event/content_marker_reviewed.php
classes/event/external_work_created.php
```

Event rule:

```text
Events audit successful state changes.
Events must not expose restricted content, raw content, private cultural protocol notes, or redacted details.
```

---

## 26. Scheduled task upgrade

Task declarations belong in:

```text
db/tasks.php
```

Required task files:

```text
classes/task/generate_archive_exports.php
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
classes/task/validate_pending_items.php
```

Task upgrade workflow:

```text
1. Add db/tasks.php if missing.
2. Register scheduled tasks.
3. Ensure tasks reuse classes/local policy.
4. Ensure derivative and thumbnail tasks respect restricted and cultural states.
5. Ensure export purge respects retention.
```

Task rule:

```text
Scheduled tasks do not bypass policy checks for generated outputs.
```

---

## 27. Privacy provider upgrade

Privacy provider:

```text
classes/privacy/provider.php
```

Privacy provider must cover:

```text
archive items
media records
media versions
media files
media collections
media relations
media tags
content tags when user-created
content tag sets when user-created
content markers
content reviews
external works when user-created or user-linked
media sources
proofs
Kristals
provenance
revisions
exports
```

Privacy upgrade workflow:

```text
1. Add privacy coverage for new tables.
2. Add user data export logic.
3. Add deletion/anonymization/preservation logic.
4. Add redaction rules for restricted, cultural, integrity, third-party, and advisory data.
5. Add tests for new privacy surfaces.
```

Privacy rule:

```text
Privacy export is not a permission bypass.
Restricted third-party information and culturally restricted details must be filtered or redacted.
```

---

## 28. Backup and restore upgrade

Backup and restore files:

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

Backup/restore must include:

```text
archive records
media records
media versions
media files
media relations
media tags
media collections
media collection membership
media source records
external work records
content tags
content tag sets
content markers
content reviews
provenance
revisions
export manifests
restricted visibility
audience suitability
cultural protocol flags
```

Restore rule:

```text
Restore must not make restricted, culturally sensitive, or integrity-linked records public.
```

---

## 29. Language string upgrade

Language files:

```text
lang/en/uckkarchive.php
lang/fr/uckkarchive.php
```

Language strings must exist for:

```text
new capabilities
media library UI
media versions
media collections
media relations
media source
external works
content advisories
content tags
content tag sets
content markers
content reviews
audience suitability
cultural protocol
restricted integrity
restricted cultural
privacy provider
backup/restore
service errors
events
scheduled tasks
```

Language rule:

```text
Language files must not contain active strings for removed target capability mod/uckkarchive:versionitem.
English and French public UI strings must remain aligned.
```

---

## 30. Settings upgrade

Settings file:

```text
settings.php
```

Settings may include:

```text
enablemedialibrary
enablecontentadvisories
enableexternalworks
enableintegrityintegration
allowmediaexports
allowcollectionexports
defaultmediavisibility
defaultaudiencesuitability
defaultrestrictedhandling
defaultredaction
showadvisorybadges
```

Default values should be conservative:

```text
defaultmediavisibility = course or restricted according to site policy
defaultaudiencesuitability = guided when unknown
defaultrestrictedhandling = fail_closed
defaultredaction = enabled
enableintegrityintegration = disabled unless explicitly enabled
```

Settings rule:

```text
Settings cannot bypass context, capability, privacy, redaction, cultural protocol, content advisory, or retention policy.
```

---

## 31. Cache and search upgrade

Search/index maintenance task:

```text
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
```

Upgrade workflow:

```text
1. Mark media search index stale after schema changes.
2. Mark content marker index stale after advisory schema changes.
3. Queue rebuild tasks.
4. Rebuild only permission-filtered indexes.
5. Ensure restricted records are not leaked through facets, counts, snippets, previews, or thumbnails.
```

Search rule:

```text
Search results are permission-filtered.
Restricted records are not leaked through metadata.
```

---

## 32. Integrity integration upgrade

`tool_uckkintegrity` is optional.

Upgrade must preserve:

```text
ordinary archive operation without tool_uckkintegrity
ordinary media operation without tool_uckkintegrity
ordinary content advisory operation without tool_uckkintegrity
```

Integrity upgrade workflow:

```text
1. Add restricted_integrity visibility support.
2. Add integrity source provenance support.
3. Add integrity export file area support.
4. Add optional settings for integrity integration.
5. Ensure integrity-specific features fail closed when tool_uckkintegrity is absent.
```

Integrity rule:

```text
mod_uckkarchive may preserve integrity-related records.
mod_uckkarchive must not own integrity procedure authority.
```

---

## 33. Report integration upgrade

`report_uckk` owns institutional reporting.

Upgrade must preserve this boundary:

```text
mod_uckkarchive = archive-owned export packages
report_uckk = institutional reporting views and institutional report exports
```

Reporting rule:

```text
Upgrade must not convert archive export records into institutional report authority.
```

---

## 34. Assembly integration upgrade

`mod_uckkassembly` owns Assembly decision authority.

Upgrade may preserve:

```text
assembly snapshots
decision attachments
minutes files
proof bundles
archive summaries
media relations
```

Upgrade must not create:

```text
live Assembly decision records
Assembly voting authority
Assembly procedure state
```

Assembly rule:

```text
Preserved Assembly-related records are archive memory, not active Assembly authority.
```

---

## 35. Challenge integration upgrade

`mod_uckkchallenge` owns challenge workflow state.

Upgrade may preserve:

```text
challenge evidence
challenge media
challenge proof records
challenge summary snapshots
Kristal source packs
```

Upgrade must not create:

```text
live challenge workflow state
challenge grading authority
challenge decision authority
```

Challenge rule:

```text
Preserved challenge-related records are archive/media memory, not active challenge workflow authority.
```

---

## 36. Rollback and failure behavior

Moodle upgrade steps are not general-purpose rollback scripts.

Failure behavior:

```text
each step must be atomic where possible
each step must check existence before creating schema objects
each step must avoid destructive data changes
each step must leave restricted data protected if interrupted
each step must write savepoint only after success
```

Failure rule:

```text
If migration cannot determine safe visibility or authority, records must remain restricted.
```

---

## 37. Data integrity checks

After upgrade, checks must verify:

```text
all target tables exist
all required UUID fields exist
UUIDs are populated
UUIDs are unique where required
canonical file areas are recognized
capabilities are defined
removed capability is not target-defined
services are declared
tasks are declared
privacy provider covers new tables
backup/restore includes new tables
restricted records remain restricted
content advisory seed data exists
external work references are preserved
media source records exist where needed
```

Data integrity rule:

```text
Upgrade success means target behavior is reachable and protected, not merely that schema changes ran.
```

---

## 38. Test requirements

Upgrade tests must cover:

```text
fresh install target schema
upgrade from archive-only data
upgrade with existing files
upgrade with restricted records
upgrade with integrity-linked records
upgrade with external works
upgrade with content advisories
upgrade with collections and relations
upgrade with missing optional tool_uckkintegrity
upgrade does not create mod/uckkarchive:versionitem
upgrade does not make restricted data public
upgrade preserves Moodle File API files
upgrade preserves backup/restore behavior
upgrade preserves privacy provider behavior
```

Recommended test files:

```text
tests/upgrade_test.php
tests/media_library_test.php
tests/content_advisory_test.php
tests/external_work_test.php
tests/backup_restore_test.php
tests/privacy_provider_test.php
tests/services_test.php
```

Testing rule:

```text
Tests verify the final target behavior, not historical transitions.
```

---

## 39. Developer implementation checklist

Implementation must update:

```text
db/install.xml
db/upgrade.php
db/access.php
db/services.php
db/events.php
db/tasks.php
lib.php
settings.php
classes/privacy/provider.php
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
lang/en/uckkarchive.php
lang/fr/uckkarchive.php
tests/upgrade_test.php
```

Implementation must add or confirm:

```text
classes/local/file_area_registry.php
classes/local/uuid.php
classes/local/media.php
classes/local/media_version.php
classes/local/media_collection.php
classes/local/media_relation.php
classes/local/media_source.php
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/content_marker.php
classes/local/content_review.php
classes/local/content_policy.php
classes/local/external_work.php
```

Implementation rule:

```text
Upgrade code, install schema, services, privacy, backup/restore, and tests must describe the same target model.
```

---

## 40. Final upgrade rule

```text
The upgrade process converts mod_uckkarchive into the final self-contained archive, media library, and content advisory module.

It preserves archive memory, media files, source records, external works, content advisories, cultural protocol markers, provenance, revisions, exports, privacy behavior, backup/restore behavior, and restricted states.

It must not make restricted data public.
It must not create external domain authority.
It must not preserve removed capabilities as target behavior.
It must fail closed when safety, visibility, source, or authority is uncertain.

This document defines the final target behavior for implementation.
Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
```
