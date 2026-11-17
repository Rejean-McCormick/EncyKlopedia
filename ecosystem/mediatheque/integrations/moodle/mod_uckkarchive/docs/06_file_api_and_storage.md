# 06 — File API and Storage

**Path:** `docs/06_file_api_and_storage.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Moodle File API, file-area registry, archive files, media-library files, content advisory files, external work references, privacy, backup/restore, export, and pluginfile access rules.

---

## 1. Purpose

This document defines the final file storage architecture for `mod_uckkarchive`.

`mod_uckkarchive` is a Moodle-native activity module with a self-contained archive, media library, and content advisory system.

All production files owned by the module are stored through Moodle File API.

The module must not store production archive or media files in unmanaged public folders.

The module must not store binary media files directly in custom database fields.

The module must not use direct public file URLs as authority.

---

## 2. Core storage decision

Canonical storage formula:

```text
Moodle File API stores files.
mod_uckkarchive tables store identity, metadata, state, policy, relations, and provenance.
```

The plugin owns:

```text
archive file areas
media file areas
content advisory file areas
export package file areas
manifest file areas
provenance file areas
review file areas
```

Moodle owns the physical file storage mechanism.

`mod_uckkarchive` owns the meaning, policy, visibility, lifecycle, metadata, and access logic around those files.

---

## 3. Moodle component

Canonical File API component:

```text
mod_uckkarchive
```

Every module-owned file must use:

```text
component = mod_uckkarchive
```

No module-owned file may use another component as its storage authority.

External plugins may reference archive/media records through APIs, but the file remains owned by `mod_uckkarchive`.

---

## 4. Central file-area registry

The canonical file-area list is defined in:

```text
classes/local/file_area_registry.php
```

This registry is the single source of truth for file areas.

All of the following must use the registry:

```text
lib.php pluginfile handler
controllers
external services
forms
privacy provider
backup task
backup steps
restore task
restore steps
tests
export package builder
media file service
content advisory service
```

No controller, service, form, task, or template may invent a file-area name directly.

---

## 5. Canonical archive file areas

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

### Archive file-area meaning

| File area | Purpose |
|---|---|
| `intro` | Standard Moodle activity intro files. |
| `item_content` | Embedded files used inside archive item rich content. |
| `item_publicsummary` | Files attached to public or shareable summary content. |
| `item_files` | General archive item attachments. |
| `proof_files` | Evidence/proof attachments. |
| `decision_attachments` | Preserved Assembly decision attachments owned as archive copies or references. |
| `minutes_files` | Preserved minutes or institutional memory files. |
| `kristal_files` | Kristal-related attached files. |
| `portfolio_files` | Portfolio-linked archive files. |
| `integrity_exports` | Restricted integrity-related archive export files. |
| `provenance_files` | Source/provenance packages, references, or evidence files. |
| `validation_files` | Files used during validation or review. |
| `revision_files` | Files attached to revision history. |
| `export_package` | Generated archive/media export package. |
| `export_manifest` | Generated export manifest, usually `manifest.json`. |

---

## 6. Canonical media file areas

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

### Media file-area meaning

| File area | Purpose |
|---|---|
| `media_original` | Original uploaded or imported media file. |
| `media_preview` | Preview file optimized for display or teaching. |
| `media_thumbnail` | Thumbnail or poster image. |
| `media_derivative` | Generated or curated derivative file. |
| `media_caption` | Caption/subtitle files. |
| `media_transcript` | Transcript files. |
| `media_attachment` | Supporting files attached to a media object. |

Media file areas are linked to `uckkarchive_media` or `uckkarchive_media_version` records.

The original file must not be overwritten silently.

Media replacement creates a media version.

---

## 7. Canonical content advisory file areas

Content advisory file areas:

```text
content_review_files
external_work_reference_files
cultural_protocol_files
```

### Content advisory file-area meaning

| File area | Purpose |
|---|---|
| `content_review_files` | Files attached to advisory review decisions. |
| `external_work_reference_files` | Reference files or metadata packages for external works, when storage is permitted. |
| `cultural_protocol_files` | Files documenting cultural protocol, access conditions, or review notes. |

These areas support content advisories, cultural sensitivity tags, content markers, content reviews, external works, and audience suitability rules.

They do not automatically make restricted cultural or sensitive content visible.

---

## 8. File-area grouping

The registry must classify file areas into groups:

```text
activity_intro
archive_item
proof
kristal
portfolio
integrity
provenance
validation
revision
media
content_advisory
external_work
export
```

The group determines:

```text
allowed parent table
expected itemid meaning
privacy export behavior
backup/restore mapping
pluginfile policy
download policy
redaction behavior
retention behavior
```

---

## 9. Item ID rules

Every File API area must have a predictable `itemid`.

| File area group | Item ID points to |
|---|---|
| `activity_intro` | Moodle module context or activity instance, using Moodle conventions. |
| `archive_item` | `uckkarchive_item.id` |
| `proof` | `uckkarchive_proof.id` |
| `kristal` | `uckkarchive_kristal.id` |
| `portfolio` | `uckkarchive_item.id` or portfolio-specific archive item record. |
| `integrity` | `uckkarchive_export.id`, `uckkarchive_item.id`, or integrity-restricted archive-owned record. |
| `provenance` | `uckkarchive_prov.id` |
| `validation` | `uckkarchive_rev.id` or validation/review record. |
| `revision` | `uckkarchive_rev.id` |
| `media` | `uckkarchive_media.id` or `uckkarchive_media_version.id`, depending on area. |
| `content_advisory` | `uckkarchive_content_review.id` or `uckkarchive_content_marker.id`. |
| `external_work` | `uckkarchive_external_work.id` |
| `export` | `uckkarchive_export.id` |

Item ID rules must be enforced by `classes/local/file_area_registry.php`.

---

## 10. Media item ID rules

Media file areas use these target records:

| File area | Item ID |
|---|---|
| `media_original` | `uckkarchive_media_version.id` |
| `media_preview` | `uckkarchive_media_version.id` |
| `media_thumbnail` | `uckkarchive_media.id` |
| `media_derivative` | `uckkarchive_media_version.id` |
| `media_caption` | `uckkarchive_media_version.id` |
| `media_transcript` | `uckkarchive_media_version.id` |
| `media_attachment` | `uckkarchive_media.id` |

Rationale:

```text
originals, derivatives, captions, transcripts, and previews are version-specific
thumbnails and attachments may belong to the media object as a whole
```

A media version can have one original and multiple derivative/supporting files.

---

## 11. Content advisory item ID rules

Content advisory file areas use these target records:

| File area | Item ID |
|---|---|
| `content_review_files` | `uckkarchive_content_review.id` |
| `external_work_reference_files` | `uckkarchive_external_work.id` |
| `cultural_protocol_files` | `uckkarchive_content_review.id` or approved protocol record |

Content advisory files may contain sensitive context.

Access is controlled by content policy, cultural protocol policy, visibility, and capability.

---

## 12. External work storage decision

External or foreign media is not automatically copied into UCKK storage.

External works may be represented by:

```text
metadata
citation
external identifier
publisher/source information
URL
locator
content advisory tags
content markers
cultural protocol notes
teaching notes
review notes
```

The archive may store a file for an external work only when storage is permitted by rights, license, policy, or institutional decision.

When external content is not stored, the module may still store:

```text
work metadata
content markers
page references
timecode references
scene references
chapter references
advisory tags
review state
audience suitability
cultural protocol restrictions
```

External work records must not imply UCKK ownership of third-party media.

---

## 13. Content marker locator storage

Content markers may identify sensitive or culturally restricted content inside internal or external works.

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
film -> content marker -> 01:12:30-01:15:10
book -> content marker -> page 42-45
PDF -> content marker -> page 7
audio -> content marker -> 00:08:12-00:09:40
website -> content marker -> url_fragment #section-3
```

Locator metadata belongs in `uckkarchive_content_marker`.

Files supporting the review belong in `content_review_files` or `cultural_protocol_files`.

---

## 14. Draft file workflow

User uploads must use Moodle draft areas before being committed to permanent File API areas.

Workflow:

```text
upload to draft area
validate draft file
create or load target record
save file to canonical file area
store metadata and provenance
create revision/version record where required
trigger event
return filtered response
```

Draft files must not be treated as permanent records.

Draft files must not be exported.

Draft files must not be used as proof until committed to a canonical file area.

---

## 15. Media upload workflow

Media upload workflow:

```text
create uckkarchive_media record
create uckkarchive_media_version record
move original file from draft area to media_original
generate or queue thumbnail
generate or queue preview
extract or attach metadata
store provenance
apply initial visibility and suitability
apply content advisory defaults
trigger media_created
```

The module may queue derivative work using scheduled tasks.

Generated files must be stored in canonical media file areas.

Generated files must not overwrite originals.

---

## 16. Media version workflow

Media version workflow:

```text
load media object
check mod/uckkarchive:versionmedia
check media policy
create new uckkarchive_media_version
move uploaded file to media_original
queue derivative generation
record provenance
record relation to previous version
mark previous version as superseded where appropriate
trigger media_version_created
```

A new media version is required when:

```text
original file changes
caption file changes materially
transcript changes materially
preview/derivative changes materially
rights/license metadata changes materially
content advisory state changes materially
cultural protocol state changes materially
```

Minor display-only metadata changes may update the media record without creating a new file version, but must still be auditable when policy requires it.

---

## 17. Derivatives and generated files

Generated files include:

```text
preview files
thumbnails
transcoded derivatives
captions derived from transcripts
text extraction outputs
search index support files
```

Generated files must be reproducible or explicitly marked as curated.

Generated files must store:

```text
source media uuid
source version uuid
generator
generation time
hash
mime type
size
derivative type
```

Generated files must respect restrictions on the source media.

A restricted source cannot produce unrestricted derivatives.

---

## 18. Pluginfile handler

File serving is implemented through `lib.php` using the Moodle pluginfile callback.

The pluginfile handler must:

```text
require valid context
resolve archive instance
validate component
validate file area through file_area_registry
validate itemid
load parent record
check visibility
check capability
check media status
check archive item status
check content advisory policy
check cultural protocol policy
check restricted access policy
check retention/redaction policy
serve file only after all checks pass
```

The pluginfile handler must not:

```text
serve unknown file areas
serve files by direct URL alone
serve restricted files to ordinary users
serve deleted_soft media
serve redacted files without policy approval
serve external work references as if UCKK owned the content
```

---

## 19. Download authority

A file exists physically when Moodle File API stores it.

A file is downloadable only when policy permits it.

Download authority depends on:

```text
context
capability
ownership
visibility
media status
archive item status
validation state
restricted state
content advisory state
cultural protocol restrictions
audience suitability
retention state
redaction state
export policy
```

Direct file URL access is never sufficient authority.

---

## 20. Original media access

Original media files are higher-risk than previews or thumbnails.

Original media download requires:

```text
mod/uckkarchive:downloadmedia
context access
media access
media status access
version access
content advisory policy
cultural protocol policy
retention/redaction policy
```

Viewing a preview does not automatically grant access to the original.

Exporting a preview does not automatically grant access to the original.

---

## 21. Restricted media

Restricted media includes:

```text
restricted
restricted_integrity
restricted_cultural
staff_only
redacted
deleted_soft
archived with limited access
```

Restricted media must not be served through ordinary media browsing.

Restricted media must not appear in public search results.

Restricted media must not be exported unless export policy permits it.

Restricted cultural media requires cultural protocol checks.

Restricted integrity media requires integrity-specific checks.

---

## 22. Content advisory access effects

A content advisory does not automatically ban a file.

A content advisory can require:

```text
notice before viewing
guided access
mature audience access
staff review
cultural protocol check
restricted access
contextual teaching note
exclusion from public export
exclusion from youth-facing views
```

Content advisory policy belongs in:

```text
classes/local/content_policy.php
```

Content advisory policy is consulted by:

```text
media browsing
media download
archive item view
export package generation
search results
course integration views
public summary rendering
```

---

## 23. Cultural protocol files

Cultural protocol files may describe:

```text
community permission rules
elder review notes
seasonal/contextual restrictions
sacred or ceremonial content rules
restricted knowledge rules
public export prohibitions
teaching context requirements
```

These files are sensitive by default.

They require:

```text
mod/uckkarchive:viewculturallyrestricted
```

or stricter policy rules.

Cultural protocol notes must not be exposed in public output unless explicitly approved.

---

## 24. Privacy API storage obligations

The privacy provider must declare and handle all module-owned file areas.

Privacy provider path:

```text
classes/privacy/provider.php
```

The provider must cover:

```text
archive files
media files
media version files
content advisory files
external work reference files
cultural protocol files
export packages
export manifests
provenance files
validation files
revision files
```

Privacy export must not expose third-party restricted data, cultural protocol notes, or redacted material unless policy allows it.

Deletion and anonymisation must preserve institutional memory where policy requires preservation.

---

## 25. Backup storage obligations

Backup must include archive, media, content advisory, and external work file areas.

Backup files:

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
```

Backup must include:

```text
archive item files
proof files
media originals
media versions
media thumbnails
media previews
media derivatives
media captions
media transcripts
media attachments
content review files
external work reference files
cultural protocol files
export packages
export manifests
provenance files
validation files
revision files
```

Backup must preserve file-area names exactly as defined by `file_area_registry`.

---

## 26. Restore storage obligations

Restore must recreate file ownership only after records and mappings exist.

Restore files:

```text
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

Restore must remap:

```text
archive item ids
proof ids
Kristal ids
provenance ids
revision ids
export ids
media ids
media version ids
media relation ids
media collection ids
content tag ids
content marker ids
content review ids
external work ids
```

Restore must not:

```text
make restricted files public
drop cultural protocol restrictions
drop content advisory metadata
drop redaction state
regenerate exports as new authoritative packages
create gradebook records
create integrity case authority
create Assembly decision authority
```

---

## 27. Export package storage

Export package files use:

```text
export_package
export_manifest
```

Canonical manifest filename:

```text
manifest.json
```

Export packages may include:

```text
archive records
media records
media versions
selected files
content markers
content tags
content reviews
external work metadata
relations
collections
provenance
redaction information
validation state
```

Export packages must not include restricted files unless export policy permits them.

Export package generation must use:

```text
classes/local/export_package.php
classes/local/manifest_builder.php
```

---

## 28. Manifest file hashes

Every exported file entry must include:

```text
file area
itemid
filename
filepath
contenthash
sha256 or stronger hash where available
mime type
file size
source uuid
source version uuid where applicable
redaction state
restriction state
```

The manifest must allow an exported package to be audited without direct database access.

---

## 29. Search indexing files

Search indexes or derived search metadata must not be stored as uncontrolled public files.

Media search behavior belongs in:

```text
classes/local/media_search.php
```

Content marker indexing belongs in scheduled task support:

```text
classes/task/rebuild_content_marker_index.php
```

Search indexes must respect:

```text
visibility
content advisory policy
cultural protocol restrictions
restricted integrity policy
redaction state
deleted_soft state
```

---

## 30. Scheduled file tasks

Scheduled tasks that may create, update, or remove files:

```text
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
```

Task rules:

```text
tasks reuse policy classes
tasks do not bypass restrictions
tasks preserve source file integrity
tasks do not overwrite originals
tasks log generated outputs
tasks remove expired generated files according to retention policy
```

---

## 31. Retention and deletion

Deletion states:

```text
active
archived
deleted_soft
purged
```

Soft-deleted media must not be downloadable.

Soft-deleted media may remain in Moodle File API until retention policy permits purge.

Purging must remove:

```text
files
derivatives
thumbnails
captions
transcripts
attachments
generated export copies
orphaned draft-derived files
```

Purging must not remove evidence required for institutional, legal, cultural protocol, or integrity retention.

---

## 32. Redaction

Redaction may apply to:

```text
archive item files
media previews
media transcripts
captions
content advisory notes
cultural protocol notes
external work references
export packages
manifest metadata
```

Redacted files must either:

```text
be replaced by redacted derivatives
be withheld from output
be excluded from export
be marked in the manifest
```

The original restricted file may remain preserved if retention policy requires it.

---

## 33. Public summaries

Public summary file area:

```text
item_publicsummary
```

Public summary files are not automatically public.

They are public only when:

```text
parent item is public
summary is approved
file is not restricted
content advisory policy permits public display
cultural protocol policy permits public display
redaction policy permits public display
```

The name `item_publicsummary` is the canonical File API area for public summaries.

---

## 34. File metadata

The module stores file-related metadata in domain tables, not by relying only on Moodle file records.

Required metadata may include:

```text
uuid
source uuid
version uuid
file role
media type
mime type
duration
page count
width
height
size
hash
rights/license
source ownership
audience suitability
visibility
restriction state
redaction state
provenance
createdby
modifiedby
timecreated
timemodified
metadata json
```

Moodle File API stores the file.

Module tables store semantic meaning.

---

## 35. Rights and source ownership

Media source records define ownership and source context.

Canonical media source values:

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

Rights metadata affects:

```text
viewing
download
reuse
export
public display
teaching context
derivative generation
```

---

## 36. File validation

Before permanent storage, uploads must be validated for:

```text
file size
mime type
extension
malware scan where Moodle/site supports it
allowed file types
context
capability
file area
itemid
rights/source metadata
content advisory defaults
cultural protocol defaults
```

Invalid files remain in draft state or are rejected.

---

## 37. Forbidden file behavior

The plugin must not:

```text
store production files in public/media
store production files in public/uckk_media
store production files in public/assets
store binary media in custom DB fields
serve files without context checks
serve files without policy checks
treat URL possession as authorization
make derivatives less restricted than originals
drop content advisories during export
drop cultural protocol restrictions during backup/restore
silently overwrite originals
silently delete preserved evidence
```

---

## 38. Required tests

Tests must cover:

```text
file_area_registry contains all canonical areas
pluginfile rejects unknown file areas
pluginfile rejects wrong context
pluginfile rejects wrong itemid
pluginfile enforces media status
pluginfile enforces content advisory restrictions
pluginfile enforces cultural protocol restrictions
media_original stores version-specific files
media_thumbnail stores media-level files
draft files promote to correct file areas
backup includes archive file areas
backup includes media file areas
backup includes content advisory file areas
restore remaps media file areas
restore preserves restricted state
privacy provider declares all file areas
export package uses export_package
export manifest uses export_manifest
restricted exports exclude unauthorized files
```

---

## 39. Implementation files

Files that implement this specification:

```text
lib.php
classes/local/file_area_registry.php
classes/local/media_file.php
classes/local/media_policy.php
classes/local/content_policy.php
classes/local/export_package.php
classes/local/manifest_builder.php
classes/privacy/provider.php
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
tests/file_api_test.php
tests/privacy_provider_test.php
tests/backup_restore_test.php
tests/export_test.php
```

---

## 40. Final rule

This document defines the final target behavior for file storage.

```text
Moodle File API stores the bytes.
mod_uckkarchive owns the meaning, lifecycle, policy, provenance, advisory context, cultural protocol, and export behavior.
```

Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
