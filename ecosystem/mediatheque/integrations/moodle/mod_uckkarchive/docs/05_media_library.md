# 05 — Media Library

**Path:** `docs/05_media_library.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Self-contained media library subsystem inside the UCKK Archive Moodle activity module.

---

## 1. Purpose

This document defines the final media-library architecture for `mod_uckkarchive`.

The media library is a first-class subsystem of the module.

It is not a public folder.

It is not only a set of file attachments.

It is not a generic archive item subtype.

It is a managed media domain with its own records, versions, relations, collections, tags, source metadata, content advisories, cultural protocol markers, export identity, and Moodle File API storage.

Canonical formula:

```text
mod_uckkarchive = archive engine + media library engine + content advisory system + Moodle adapter layer
```

---

## 2. Core decision

Media is a first-class object.

Canonical media object:

```text
uckkarchive_media
```

Canonical media version object:

```text
uckkarchive_media_version
```

Canonical media collection object:

```text
uckkarchive_media_collection
```

Canonical media relation object:

```text
uckkarchive_media_relation
```

Canonical media tag object:

```text
uckkarchive_media_tag
```

The module stores actual media files through Moodle File API.

The module stores media identity, metadata, versioning, collections, relations, tags, content markers, provenance, visibility, suitability, and source information in module-owned tables.

---

## 3. Media library responsibilities

The media library owns:

```text
media records
media versions
media file identity
media metadata
media lifecycle state
media visibility
media source information
media ownership metadata
media collections
media collection membership
media relations
media tags
media content advisories
media cultural protocol markers
media review state
media export identity
media restore identity
media privacy surface
```

The media library does not own:

```text
grades
transcripts
course enrolments
Assembly decision authority
integrity case authority
institutional report authority
external copyright ownership
third-party work ownership
```

The media library may reference external works without claiming ownership over those works.

---

## 4. Moodle integration boundary

The media library uses Moodle for:

```text
course module context
users
roles
groups
capabilities
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

The media library must not bypass Moodle’s context, capability, file, privacy, backup, restore, service, or event systems.

---

## 5. Required media tables

The media library requires these tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
uckkarchive_media_source
```

The content advisory subsystem extends media management with:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
```

These tables are part of the current target architecture.

They are not optional.

---

## 6. `uckkarchive_media`

`uckkarchive_media` is the canonical table for media objects.

A media object represents the managed intellectual/media entity.

It is not the same as a single file.

A media object may have:

```text
one original file
many versions
many derivatives
many thumbnails
many captions
many transcripts
many attachments
many relations
many content markers
many collection memberships
```

Recommended fields:

```text
id
uuid
archiveid
courseid
cmid
contextid
ownerid
createdby
modifiedby
sourceid
title
subtitle
description
mediatype
mimetype
status
visibility
audiencesuitability
licensekey
rightsstatement
language
duration
pagecount
hashoriginal
currentversionid
provenanceid
metadata
timecreated
timemodified
```

Canonical `mediatype` values:

```text
image
video
audio
document
pdf
transcript
caption
thumbnail
preview
derivative
source_package
external_reference
other
```

---

## 7. `uckkarchive_media_version`

`uckkarchive_media_version` stores version history for media objects.

A media version represents a meaningful media state.

Media must not be silently overwritten.

A new version is created when:

```text
the original file is replaced
a corrected file is uploaded
metadata affecting meaning is changed
a transcript is corrected
captions are corrected
a derivative is generated or replaced
rights/license metadata changes
visibility changes in a way that affects access
content advisories are materially changed
cultural protocol state changes
```

Recommended fields:

```text
id
uuid
mediaid
versionno
versionlabel
filearea
fileitemid
filename
mimetype
filesize
contenthash
status
createdby
reason
changesummary
metadata
timecreated
```

Media versioning permission:

```text
mod/uckkarchive:versionmedia
```

---

## 8. `uckkarchive_media_collection`

`uckkarchive_media_collection` stores reusable groups of media.

A collection is not a folder in the filesystem.

A collection is an ordered or structured media grouping.

Examples:

```text
course pack
Kristal source pack
challenge evidence pack
assembly record pack
public media set
restricted proof bundle
cultural protocol set
external work study set
```

Recommended fields:

```text
id
uuid
archiveid
courseid
contextid
ownerid
title
description
collectiontype
visibility
audiencesuitability
createdby
modifiedby
metadata
timecreated
timemodified
```

Canonical `collectiontype` values:

```text
course_pack
kristal_pack
challenge_pack
assembly_pack
proof_bundle
public_set
restricted_set
cultural_protocol_set
external_work_set
custom
```

---

## 9. `uckkarchive_media_collection_item`

`uckkarchive_media_collection_item` stores membership of media objects in collections.

Recommended fields:

```text
id
collectionid
mediaid
sortorder
role
addedby
metadata
timecreated
```

Canonical membership roles:

```text
primary
supporting
source
derivative
preview
required
optional
restricted
contextual
```

A media object may belong to multiple collections.

A collection does not own the media object.

---

## 10. `uckkarchive_media_relation`

`uckkarchive_media_relation` stores graph relationships between media objects, archive items, Kristals, collections, external works, and proof records.

Canonical relation types:

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

Recommended fields:

```text
id
uuid
sourcetype
sourceid
targettype
targetid
relationtype
direction
createdby
metadata
timecreated
```

Relation rules:

```text
Relations describe meaning.
Relations do not transfer ownership.
Relations do not grant access automatically.
Relations must be filtered by policy before display or export.
```

---

## 11. `uckkarchive_media_tag`

`uckkarchive_media_tag` stores media classification tags.

Media tags are general descriptive tags.

Content advisory tags are stored separately in `uckkarchive_content_tag`.

Recommended fields:

```text
id
mediaid
tagkey
tagtype
createdby
metadata
timecreated
```

Canonical `tagtype` values:

```text
topic
discipline
format
language
pedagogical
technical
source
rights
custom
```

Tag rule:

```text
Media tags describe media.
Content advisory tags describe suitability, sensitivity, or protocol conditions.
```

---

## 12. `uckkarchive_media_source`

`uckkarchive_media_source` records source and ownership classification for media.

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

Canonical source ownership values:

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

Recommended fields:

```text
id
uuid
mediaid
externalworkid
sourcekind
ownershipkind
sourcecomponent
sourceurl
sourcetitle
sourceauthor
licensekey
rightsstatement
citation
createdby
metadata
timecreated
timemodified
```

Source rule:

```text
The module may preserve source metadata.
The module must not imply ownership over third-party media.
The module may reference foreign media without copying it.
```

---

## 13. External works

External works are represented by:

```text
uckkarchive_external_work
```

External works are media or cultural objects not produced by UCKK.

Examples:

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

Recommended fields:

```text
id
uuid
worktype
title
subtitle
creator
publisher
publicationyear
identifier
url
citation
language
country
rightsstatement
licensekey
metadata
timecreated
timemodified
```

External work rules:

```text
An external work can be referenced without copying the work.
A content marker can point to a precise location in an external work.
The module can store teaching notes, advisories, cultural protocols, citations, and locators for external works.
The module must not claim ownership over external works.
```

---

## 14. Content advisories

The media library includes content advisories as a first-class subsystem.

Canonical content advisory tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

A content advisory does not ban media.

It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.

User-facing terms may include:

```text
content advisory
content warning
trigger warning
cultural advisory
cultural protocol
audience suitability
```

System-level terminology should prefer:

```text
content advisory
content marker
content tag
content review
cultural protocol
```

Avoid using `trigger` alone as a database/system name because it can be confused with database triggers.

---

## 15. Content advisory tags

`uckkarchive_content_tag` defines reusable advisory and cultural protocol tags.

Examples:

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

Cultural protocol examples:

```text
community_permission_required
elder_review_required
seasonal_or_contextual_access
not_for_public_export
not_for_children
requires_context
restricted_knowledge
sacred_content
ceremonial_content
```

Recommended fields:

```text
id
uuid
tagkey
label
description
category
severitydefault
iscultural
isrestricted
requiresreview
createdby
metadata
timecreated
timemodified
```

Canonical advisory severity values:

```text
notice
moderate
strong
restricted
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

Recommended fields:

```text
id
uuid
setkey
name
description
visibility
createdby
metadata
timecreated
timemodified
```

Content tag set rule:

```text
Tag sets define advisory vocabularies.
Tag sets do not assign advisories to media by themselves.
Assignments happen through content markers.
```

---

## 17. Content markers

`uckkarchive_content_marker` links a content advisory tag to a precise location in media, archive material, or external work.

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
Website -> colonial_violence -> url_fragment #section-3
```

Recommended fields:

```text
id
uuid
tagid
targettype
targetid
externalworkid
mediaid
mediaversionid
archiveitemid
locatortype
locatorstart
locatorend
locatorlabel
audiencesuitability
severity
reviewstate
visibility
createdby
metadata
timecreated
timemodified
```

Content marker rule:

```text
A content marker can point to internal media, media versions, archive items, external works, or manual references.
A marker must include enough locator information to be useful without storing unauthorized copies of external content.
```

---

## 18. Content reviews

`uckkarchive_content_review` records human review of advisory markers, cultural protocol notes, suitability, and restriction decisions.

Canonical review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Recommended fields:

```text
id
uuid
markerid
reviewstate
reviewedby
reviewnote
decision
audiencesuitability
visibility
requirescontext
requirespermission
createdby
metadata
timecreated
timemodified
```

Content review rule:

```text
AI may suggest tags or markers.
Human review is required before advisory state becomes approved.
Cultural protocol access cannot be approved by AI.
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
Audience suitability informs responsible access.
It does not automatically hide media unless policy maps it to access restrictions.
```

Policy may use suitability to:

```text
show advisory banners
require confirmation
require context notes
restrict export
restrict public display
require elevated capability
hide media from unsuitable audiences
```

---

## 20. Media lifecycle

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

Lifecycle meaning:

| State | Meaning |
|---|---|
| `draft` | Media exists but is not ready for general use. |
| `submitted` | Media has been submitted for review or inclusion. |
| `active` | Media is usable according to visibility and policy. |
| `restricted` | Media is usable only under restricted access rules. |
| `superseded` | Media has been replaced by a newer media object or version. |
| `archived` | Media is preserved but not active for ordinary use. |
| `deleted_soft` | Media is hidden/retained only for audit, recovery, or retention policy. |

Lifecycle rule:

```text
File existence is not media availability.
Media status controls usability.
Visibility controls access.
Policy controls download and export.
Retention controls deletion.
Content advisories describe suitability, cultural protocol, and access conditions.
```

---

## 21. Media visibility

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

Visibility rule:

```text
Visibility defines audience scope.
Capabilities and policy still decide actual access.
Restricted cultural material requires cultural protocol checks.
Restricted integrity material requires integrity-specific checks.
```

---

## 22. Media file areas

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

File-area meanings:

| File area | Purpose |
|---|---|
| `media_original` | Original uploaded or preserved media file. |
| `media_preview` | Preview file for display. |
| `media_thumbnail` | Generated or uploaded thumbnail. |
| `media_derivative` | Generated derivative such as compressed video, converted image, or alternate format. |
| `media_caption` | Caption file such as VTT/SRT. |
| `media_transcript` | Transcript file. |
| `media_attachment` | Supporting attachment. |
| `content_review_files` | Files used during content advisory or cultural review. |
| `external_work_reference_files` | Reference files or permitted metadata files for external works. |
| `cultural_protocol_files` | Cultural protocol notes or permission files. |

File-area rule:

```text
All file areas are declared centrally in classes/local/file_area_registry.php.
```

---

## 23. Media policy

Media access policy belongs in:

```text
classes/local/media_policy.php
```

Content advisory policy belongs in:

```text
classes/local/content_policy.php
```

Policy methods include:

```text
can_view_media
can_download_original
can_view_derivative
can_view_thumbnail
can_view_transcript
can_edit_metadata
can_add_version
can_export_media
can_view_restricted_media
can_view_culturally_restricted
can_manage_content_markers
can_review_content_marker
can_reference_external_work
```

Policy rule:

```text
Controllers, templates, AMD modules, and output classes must not make final access decisions.
```

---

## 24. Media services

Required media services:

```text
classes/external/get_media.php
classes/external/get_media_item.php
classes/external/get_media_card.php
classes/external/search_media.php
classes/external/add_media.php
classes/external/update_media.php
classes/external/delete_media.php
classes/external/add_media_version.php
classes/external/get_media_versions.php
classes/external/get_media_relations.php
classes/external/add_media_relation.php
classes/external/remove_media_relation.php
classes/external/get_media_collections.php
classes/external/get_media_collection.php
classes/external/add_media_collection.php
classes/external/update_media_collection.php
classes/external/add_media_to_collection.php
classes/external/remove_media_from_collection.php
classes/external/tag_media.php
classes/external/untag_media.php
```

Required content advisory and external work services:

```text
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
External services check context, capability, visibility, media lifecycle, content advisory policy, cultural protocol rules, restricted state, retention, and redaction.
```

---

## 25. Media UI

Required media UI controllers:

```text
media.php
```

Required media templates:

```text
templates/media_card.mustache
templates/media_collection.mustache
templates/media_library.mustache
templates/media_relation_list.mustache
templates/media_upload.mustache
templates/media_version_list.mustache
templates/content_advisory_panel.mustache
templates/external_work_card.mustache
```

Required media AMD files:

```text
amd/src/media.js
amd/src/media_collection.js
amd/src/content_advisory.js
amd/src/external_work.js
```

UI rule:

```text
The UI displays policy-filtered data.
The UI may show advisory banners, locator markers, context notes, and restricted-state labels.
The UI must not expose restricted metadata or hidden cultural protocol notes to unauthorized users.
```

---

## 26. Media events

Required media events:

```text
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
Events audit state changes.
Events must not expose raw media content, restricted notes, hidden cultural protocol notes, or redacted data.
```

---

## 27. Media tasks

Required scheduled tasks:

```text
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
```

Task responsibilities:

```text
generate previews
generate thumbnails
generate derivatives
maintain media search data
maintain content marker index
avoid bypassing policy
```

---

## 28. Media export

Media exports are generated by the archive export subsystem.

Media export includes:

```text
media metadata
media UUIDs
media versions
file hashes
file sizes
mime types
relations
collections
tags
content markers
content reviews
external work references
audience suitability
cultural protocol flags
visibility
redaction state
provenance
manifest.json
```

Media export rule:

```text
Export does not bypass permissions.
Export does not bypass content advisory policy.
Export does not bypass cultural protocol restrictions.
Export does not imply ownership over external works.
```

---

## 29. Media backup and restore

Backup must preserve:

```text
media records
media versions
media collections
media collection membership
media relations
media tags
media source records
content tags
content tag sets
content markers
content reviews
external works
media files
content review files
external work reference files
cultural protocol files
```

Restore must preserve:

```text
UUIDs
relations
collections
markers
review states
visibility
audience suitability
restricted state
provenance
file hashes
file areas
```

Restore rule:

```text
Restore reconstructs module-owned media library state.
Restore does not create external ownership authority.
Restore does not make restricted media public.
```

---

## 30. Media privacy

Privacy provider must cover:

```text
media created by user
media modified by user
media uploaded by user
media versions created by user
media collections created by user
media relations created by user
media tags created by user
content markers created by user
content reviews performed by user
external works created by user
media source records created by user
files uploaded by user
review notes containing personal data
metadata containing personal data
```

Privacy rule:

```text
Privacy export is not a permission bypass.
Restricted third-party data must be redacted or filtered.
Cultural protocol notes must not be exposed to unauthorized users.
```

---

## 31. Media search

Media search should support:

```text
title
description
mediatype
mimetype
status
visibility
collection
tag
content advisory tag
audience suitability
source kind
external work
language
rights/license
provenance
creator
date
```

Search rule:

```text
Search results must be permission-filtered.
Restricted media must not appear to unauthorized users.
Restricted content advisory details must not leak through search snippets.
```

---

## 32. Required tests

Required test areas:

```text
media creation
media update
media deletion soft state
media version creation
media collection creation
media collection membership
media relation graph
media tags
media source records
external works
content advisory tags
content tag sets
content markers
content reviews
media file areas
restricted media access
culturally restricted access
media export
media backup
media restore
media privacy
media search filtering
```

Required test files:

```text
tests/media_library_test.php
tests/content_advisory_test.php
tests/external_work_test.php
tests/file_api_test.php
tests/privacy_provider_test.php
tests/backup_restore_test.php
tests/export_test.php
tests/services_test.php
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

---

## 33. Final rule

The media library is self-contained inside `mod_uckkarchive`.

It owns media objects, media versions, collections, relations, tags, source records, external work references, content advisories, cultural protocol markers, review states, and export identity.

It uses Moodle File API for storage and Moodle APIs for lifecycle, access, privacy, backup, restore, events, services, and rendering.

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
