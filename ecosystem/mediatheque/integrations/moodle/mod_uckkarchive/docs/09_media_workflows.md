# 09 — Media Workflows

**Path:** `docs/09_media_workflows.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Media library workflows for the self-contained UCKK Archive and Media Library Moodle activity module.

---

## 1. Purpose

This document defines the final target media workflows for `mod_uckkarchive`.

`mod_uckkarchive` is a Moodle-native activity module with a self-contained archive, media library, and content advisory system.

Media is a first-class domain object.

Media is not only an archive item attachment.

Media is not stored in unmanaged public folders.

Media is not stored directly as binary data in custom database fields.

Media files are stored through Moodle File API.

Media identity, metadata, versions, collections, relations, content advisories, cultural protocol markers, source records, and export identity are stored in `mod_uckkarchive` tables.

---

## 2. Core workflow rule

Canonical formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

Media workflows must use Moodle for:

```text
course module context
users
roles
capabilities
File API
Privacy API
Backup API
Restore API
External Services API
events
settings
language strings
scheduled tasks
```

Media workflows are owned internally by:

```text
classes/local/media.php
classes/local/media_file.php
classes/local/media_policy.php
classes/local/media_version.php
classes/local/media_collection.php
classes/local/media_relation.php
classes/local/media_tag.php
classes/local/media_search.php
classes/local/media_source.php
classes/local/content_marker.php
classes/local/content_policy.php
classes/local/content_review.php
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/external_work.php
```

Controllers, templates, and AMD modules do not own media policy.

---

## 3. Media object model

Every managed media object is represented by:

```text
uckkarchive_media
```

Every media object has:

```text
id
uuid
archiveid
courseid
cmid
contextid
title
description
mediatype
mimetype
status
visibility
audiencesuitability
sourceid
currentversionid
createdby
modifiedby
timecreated
timemodified
metadata
```

Identifier rule:

```text
id = local Moodle database primary key
uuid = stable portable object identity
```

UUIDs are required for:

```text
backup
restore
export
import
duplication
cross-site portability
external manifest references
media relation graphs
```

---

## 4. Media lifecycle

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
| `draft` | Media record exists but is not submitted for use. |
| `submitted` | Media was submitted and awaits review, metadata completion, or validation. |
| `active` | Media is usable according to visibility and policy. |
| `restricted` | Media exists but requires additional capability, cultural protocol, integrity access, or guided context. |
| `superseded` | Media remains preserved but is no longer the current version or preferred item. |
| `archived` | Media is retained for memory, evidence, or historical reasons. |
| `deleted_soft` | Media is removed from normal use but preserved for retention, audit, or recovery policy. |

Lifecycle rule:

```text
File existence is not media availability.
Media status controls usability.
Visibility controls access.
Policy controls download and export.
Content advisories describe suitability, cultural protocol, and access conditions.
Retention controls deletion.
```

---

## 5. Media creation workflow

Media creation begins through:

```text
media.php
classes/form/media_form.php
classes/external/add_media.php
classes/local/media.php
classes/local/media_file.php
```

Creation workflow:

```text
1. User opens media library or archive item media panel.
2. User selects add/upload/reference media.
3. Moodle context and capability are checked.
4. Media form collects metadata and file/reference information.
5. File is uploaded to Moodle draft area or external work reference is recorded.
6. Service validates input.
7. Media policy checks permission and workflow state.
8. Media UUID is generated.
9. uckkarchive_media record is created.
10. Initial uckkarchive_media_version record is created when a file is stored.
11. File is promoted to the correct Moodle File API area.
12. Provenance is recorded.
13. Content advisory defaults are applied.
14. Event media_created is triggered.
15. Permission-filtered media card is returned.
```

Required capability:

```text
mod/uckkarchive:addmedia
```

Required policy checks:

```text
context access
course module visibility
media library availability
upload permission
source permission
file type permission
size limit
visibility selection
cultural protocol constraints
privacy constraints
```

---

## 6. Media source workflow

Every media object has a source classification.

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

Media source data is stored in:

```text
uckkarchive_media_source
classes/local/media_source.php
```

Source workflow:

```text
1. User selects media source type.
2. User records creator, owner, license, URL, citation, or origin statement.
3. Media source policy validates the source category.
4. External works are linked when media references a non-UCKK work.
5. Provenance is recorded.
6. Source metadata is included in backup, restore, privacy export, and export manifest.
```

Source rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 7. External work workflow

Works not produced by UCKK are represented by:

```text
uckkarchive_external_work
classes/local/external_work.php
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

External work workflow:

```text
1. User selects create or link external work.
2. User enters title, creator, year, publisher/source, URL/identifier, rights note, and citation.
3. External work UUID is generated.
4. Work metadata is stored without copying protected content unless permitted.
5. Content markers can be attached to the external work.
6. External work can be related to internal media, archive items, collections, or course contexts.
7. Event external_work_created is triggered.
```

External work services:

```text
classes/external/get_external_works.php
classes/external/get_external_work.php
classes/external/add_external_work.php
classes/external/update_external_work.php
```

Required capability:

```text
mod/uckkarchive:manageexternalworks
```

---

## 8. Media file workflow

Media files are stored through Moodle File API.

Component:

```text
mod_uckkarchive
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

File-area ownership:

| File area | Purpose |
|---|---|
| `media_original` | Original uploaded or preserved file. |
| `media_preview` | Preview-optimized representation. |
| `media_thumbnail` | Thumbnail image or preview still. |
| `media_derivative` | Generated derivative, compressed version, resized image, or converted format. |
| `media_caption` | Caption file. |
| `media_transcript` | Transcript file. |
| `media_attachment` | Related supporting file. |

File workflow:

```text
1. User uploads file to Moodle draft area.
2. Service validates media type, size, source metadata, and context.
3. Media policy checks upload authority.
4. File is saved to the canonical media file area.
5. Hash, size, MIME type, and file metadata are stored in media version metadata.
6. Media version becomes current version unless policy prevents activation.
7. Derivative and thumbnail tasks are queued when applicable.
```

Forbidden storage:

```text
No production archive/media files in unmanaged public folders.
No binary media files directly in custom database fields.
No direct public file URLs as authority.
```

---

## 9. Media version workflow

Media versioning is first-class.

Media versions are stored in:

```text
uckkarchive_media_version
classes/local/media_version.php
```

Media versioning uses:

```text
mod/uckkarchive:versionmedia
```

Version workflow:

```text
1. User requests add media version.
2. Service checks context and mod/uckkarchive:versionmedia.
3. Existing media object is loaded.
4. Media policy checks edit/version authority.
5. New file or metadata revision is submitted.
6. New media version UUID is generated.
7. File is stored in the correct File API area.
8. Hash, MIME type, size, duration/page count, and technical metadata are recorded.
9. Previous current version remains preserved.
10. Current version pointer is updated when policy allows.
11. Provenance and revision records are created.
12. Event media_version_created is triggered.
```

Versioning rule:

```text
Media files are not silently overwritten.
Every replacement, derivative, transcript, caption, or major metadata correction creates a version or derivative record.
```

---

## 10. Derivative and thumbnail workflow

Media derivatives and thumbnails are generated through scheduled tasks:

```text
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
```

Derivative workflow:

```text
1. Media version is created or updated.
2. Task queue marks derivative generation required.
3. Scheduled task loads media and current version.
4. Media policy checks that derivative generation is permitted.
5. Derivative file is generated.
6. Generated file is stored in media_derivative or media_preview.
7. Thumbnail is stored in media_thumbnail.
8. Metadata records derivative relation to the source version.
9. Event or audit record is created when relevant.
```

Derivative relation type:

```text
is_derivative_of
```

Derivative rule:

```text
The original file remains preserved.
Derivatives and thumbnails never replace the original.
```

---

## 11. Caption and transcript workflow

Caption and transcript files are stored as media-related files.

File areas:

```text
media_caption
media_transcript
```

Workflow:

```text
1. User adds caption or transcript file to a media object or version.
2. Service checks edit or version authority.
3. File is validated.
4. Caption/transcript language and format are recorded.
5. File is stored through Moodle File API.
6. Media version or media metadata is updated.
7. Provenance is recorded.
8. Content advisories may reference transcript/page/time locators.
```

Rules:

```text
Captions and transcripts may have their own visibility and restriction metadata.
Transcript text can contain sensitive content and must follow privacy and content advisory rules.
```

---

## 12. Media collection workflow

Media collections are first-class.

Collections are stored in:

```text
uckkarchive_media_collection
uckkarchive_media_collection_item
classes/local/media_collection.php
```

Collection workflow:

```text
1. User creates media collection.
2. Service checks mod/uckkarchive:managemediacollections.
3. Collection UUID is generated.
4. Collection title, description, visibility, purpose, and metadata are stored.
5. Media items are added to the collection.
6. Ordering and grouping metadata are stored.
7. Event media_collection_created is triggered.
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

## 13. Media relation workflow

Media relations are stored in:

```text
uckkarchive_media_relation
classes/local/media_relation.php
```

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

Relation workflow:

```text
1. User or system creates a relation between media, archive item, Kristal, collection, external work, or content marker.
2. Service checks relation authority.
3. Relation type is validated.
4. Source and target object existence is verified.
5. Relation is stored with UUID and metadata.
6. Provenance is recorded.
7. Relation graph becomes available to media search and export manifest.
```

Relation rule:

```text
Relations describe graph meaning.
Relations do not transfer ownership to external plugins or external rights holders.
```

---

## 14. Media tagging workflow

Media tags are stored in:

```text
uckkarchive_media_tag
classes/local/media_tag.php
```

Media tag workflow:

```text
1. User adds tag to media object.
2. Service checks edit authority.
3. Tag key is normalized.
4. Tag type is validated.
5. Tag is stored with source and provenance.
6. Search index is updated.
```

Media tags are used for:

```text
topic
format
course use
collection use
language
region
pedagogical theme
source category
review state
```

Content advisory tags are not stored as ordinary media tags.

Content advisory tags belong to:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

---

## 15. Content advisory workflow

Content advisories describe suitability, cultural protocol, and access conditions.

Required tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

Required local classes:

```text
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/content_marker.php
classes/local/content_review.php
classes/local/content_policy.php
```

User-facing labels:

```text
content advisory
content warning
cultural advisory
cultural protocol
audience suitability
trigger warning
```

Architecture rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 16. Content tag workflow

Content tags define reusable advisory and cultural protocol vocabulary.

Content tags are stored in:

```text
uckkarchive_content_tag
```

Content tag examples:

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

Content tag workflow:

```text
1. Authorized user creates or edits content tag.
2. Tag key, label, description, severity, category, and cultural protocol flag are stored.
3. Tag can be assigned to a tag set.
4. Tag becomes available for content markers and reviews.
```

Required capability:

```text
mod/uckkarchive:manageadvisories
```

---

## 17. Content tag set workflow

Tag sets group advisory tags into reusable vocabularies.

Tag sets are stored in:

```text
uckkarchive_content_tag_set
```

Examples:

```text
general_advisories
cultural_protocols
classroom_suitability
integrity_sensitive
youth_access
```

Tag set workflow:

```text
1. Authorized user creates tag set.
2. Tags are added to the set.
3. Tag set is assigned purpose and visibility.
4. Tag set becomes available for course, collection, media, or archive context.
```

Rule:

```text
Tag sets organize vocabulary.
Tag sets do not themselves restrict access unless content policy uses them to evaluate access conditions.
```

---

## 18. Content marker workflow

Content markers link an advisory tag to a location inside media, archive material, or an external work.

Content markers are stored in:

```text
uckkarchive_content_marker
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

Content marker examples:

```text
Movie Maïna -> sexual_violence -> 01:12:30-01:15:10
Book The Body Keeps the Score -> sexual_violence -> page 42-45
PDF -> culturally_sensitive -> page 7
Audio -> grief_or_mourning -> 00:08:12-00:09:40
Website -> colonial_violence -> url_fragment #section-3
```

Content marker workflow:

```text
1. User opens media, archive item, or external work advisory panel.
2. User selects advisory tag.
3. User selects locator type.
4. User enters locator value or range.
5. User enters note, teaching context, or cultural protocol context.
6. Marker is saved as draft or pending review.
7. Review workflow approves, contests, retires, or restricts marker.
```

Required services:

```text
classes/external/get_content_markers.php
classes/external/add_content_marker.php
classes/external/update_content_marker.php
classes/external/delete_content_marker.php
classes/external/review_content_marker.php
```

---

## 19. Content review workflow

Content review records human judgment over markers, advisories, cultural protocols, and suitability.

Content reviews are stored in:

```text
uckkarchive_content_review
```

Review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Review workflow:

```text
1. Marker is submitted for review.
2. Reviewer opens advisory panel.
3. Reviewer checks source, locator, advisory tag, note, and cultural protocol.
4. Reviewer sets review state.
5. Reviewer may set audience suitability or restricted cultural visibility.
6. Review record is saved with actor, timestamp, state, and rationale.
7. Event content_marker_reviewed is triggered.
```

AI rule:

```text
AI may suggest tags or markers.
AI cannot approve content advisories.
AI cannot approve cultural protocol access.
Human review is required before advisory status becomes approved.
```

---

## 20. Cultural protocol workflow

Cultural protocol handling uses content advisory infrastructure.

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

Cultural protocol workflow:

```text
1. User or reviewer identifies culturally sensitive content.
2. Content marker is created.
3. Cultural protocol tag is applied.
4. Marker is reviewed by authorized reviewer.
5. Visibility may be set to restricted_cultural.
6. Access policy enforces view/download/export restrictions.
7. Advisory panel explains access conditions to authorized users.
```

Required capability for restricted cultural material:

```text
mod/uckkarchive:viewculturallyrestricted
```

Cultural protocol rule:

```text
Restricted cultural material must not become public through search, export, backup preview, course display, media thumbnails, or derivative generation.
```

---

## 21. Audience suitability workflow

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

Suitability workflow:

```text
1. Media or content marker is assigned suitability level.
2. Policy checks whether current user can view the media, advisory, derivative, thumbnail, download, or export.
3. UI displays advisory when appropriate.
4. Restricted suitability prevents ordinary access.
5. Export manifest includes suitability values.
```

Rule:

```text
Audience suitability is descriptive and policy-relevant.
It does not replace Moodle capabilities.
```

---

## 22. Media search workflow

Search is handled by:

```text
classes/local/media_search.php
classes/task/rebuild_media_search.php
```

Searchable dimensions:

```text
title
description
media type
MIME type
source type
creator
license
tags
collections
relations
status
visibility
audience suitability
content advisory tags
external work metadata
provenance
```

Search rule:

```text
Search results are permission-filtered.
Restricted records are not leaked through counts, facets, thumbnails, previews, or snippets.
```

---

## 23. Media display workflow

Media display is handled by:

```text
media.php
classes/output/media_library.php
classes/output/media_card.php
classes/output/media_collection.php
classes/output/media_version_list.php
templates/media_library.mustache
templates/media_card.mustache
templates/media_collection.mustache
templates/media_version_list.mustache
templates/content_advisory_panel.mustache
```

Display workflow:

```text
1. Controller resolves course, module, archive, context, and page state.
2. Policy filters accessible media.
3. Output classes format media data.
4. Advisory panel data is attached when applicable.
5. Templates render filtered data.
6. AMD modules enhance interaction.
```

Display rule:

```text
Templates receive pre-filtered render data.
Templates do not decide authority.
Thumbnails, previews, advisories, tags, and snippets must be filtered before rendering.
```

---

## 24. Media download workflow

Download is handled through:

```text
lib.php
uckkarchive_pluginfile()
classes/local/media_policy.php
classes/local/media_file.php
```

Download workflow:

```text
1. User requests media file.
2. Moodle pluginfile handler resolves context, file area, item id, and file.
3. Media object or version is loaded.
4. Media policy checks view/download authority.
5. Restricted, cultural, integrity, retention, and redaction rules are applied.
6. File is served only if all checks pass.
```

Download capabilities:

```text
mod/uckkarchive:downloadmedia
mod/uckkarchive:viewrestrictedmedia
mod/uckkarchive:viewculturallyrestricted
```

Download rule:

```text
A direct file URL is never sufficient authority.
```

---

## 25. Media export workflow

Media can be exported as:

```text
single media export
media collection export
archive item with related media export
external work reference export
content advisory package export
```

Export services:

```text
classes/external/export_media.php
classes/external/export_collection.php
classes/external/export_items.php
classes/external/get_export_preview.php
classes/external/get_export_status.php
```

Export workflow:

```text
1. User requests export preview.
2. Service checks export capability and context.
3. Export preview identifies included media, versions, files, relations, collections, advisories, reviews, and external work metadata.
4. Policy removes unauthorized restricted content.
5. User confirms export.
6. Export package is generated.
7. manifest.json is created.
8. Files are stored through Moodle File API.
9. Export event is triggered.
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

## 26. Media deletion workflow

Deletion is policy-controlled.

Deletion states:

```text
deleted_soft
archived
retained
purged
```

Deletion workflow:

```text
1. User requests delete media.
2. Service checks mod/uckkarchive:deletemedia.
3. Media policy checks retention, provenance, evidence, collection, and export constraints.
4. Media is soft-deleted when preservation is required.
5. Files are retained or purged according to retention policy.
6. Relations, collections, advisories, and reviews are preserved or anonymized according to policy.
7. Event media_updated or deletion audit event is recorded.
```

Deletion rule:

```text
Validated, exported, culturally restricted, integrity-linked, or evidence-linked media must not be silently purged.
```

---

## 27. Privacy workflow

Media privacy is handled by:

```text
classes/privacy/provider.php
```

Privacy provider covers:

```text
media objects
media versions
media files
media collections
media relations
media tags
content tags when user-created
content markers
content reviews
external works when user-created or user-linked
media sources
proofs
provenance
revisions
exports
```

Privacy workflow:

```text
1. Privacy API asks for user-linked data.
2. Provider locates media records and related data.
3. Provider exports personal data belonging to the user.
4. Provider redacts third-party or restricted data.
5. Provider deletes, anonymizes, or preserves records according to retention rules.
```

Privacy rule:

```text
Privacy export is not a permission bypass.
Restricted third-party information and culturally restricted details must be filtered or redacted.
```

---

## 28. Backup and restore workflow

Backup/restore includes:

```text
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
export manifest metadata
```

Restore workflow:

```text
1. Restore recreates archive instance.
2. Restore maps users, courses, contexts, archive ids, media ids, and UUID references.
3. Media objects are restored.
4. Media versions are restored.
5. Files are restored to canonical File API areas.
6. Collections and relations are restored.
7. Content markers and reviews are restored.
8. External work references are restored.
9. Visibility and restricted states remain preserved.
```

Restore rule:

```text
Restore must not make restricted, culturally sensitive, or integrity-linked media public.
```

---

## 29. Event workflow

Media events:

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

Event workflow:

```text
1. State-changing service completes successfully.
2. Event is triggered with context and object identifiers.
3. Event does not expose restricted content.
4. Observers may update search, reports, or audit views.
```

Event rule:

```text
Events audit successful state changes.
Events do not expose restricted content, raw content, private cultural protocol notes, or redacted details.
```

---

## 30. UI workflow

Media UI consists of:

```text
media library view
media card
media upload form
media version list
media collection view
media relation list
content advisory panel
external work card
provenance panel
```

AMD modules:

```text
amd/src/media.js
amd/src/media_collection.js
amd/src/content_advisory.js
amd/src/external_work.js
```

UI workflow:

```text
1. Server renders initial permission-filtered data.
2. AMD enhances browsing, filtering, editing, upload, advisory panels, and collection interactions.
3. AJAX services return permission-filtered updates.
4. UI displays warnings, restrictions, and advisory labels.
5. UI never exposes hidden or restricted records by client-side filtering alone.
```

UI rule:

```text
Server-side policy is authoritative.
Client-side UI is never the security boundary.
```

---

## 31. Course and archive item linking workflow

Media can be linked to:

```text
course context
archive item
proof record
Kristal
collection
external work
content marker
```

Link workflow:

```text
1. User selects media to attach or relate.
2. Relation type is selected.
3. Service checks authority on both source and target.
4. Relation is stored.
5. Both media and archive item views can display the relationship according to policy.
```

Canonical relation:

```text
belongs_to_item
```

Rule:

```text
Linking media to an archive item does not duplicate the media file.
```

---

## 32. Restricted media workflow

Restricted media includes:

```text
restricted_integrity
restricted_cultural
staff_only
private
```

Restricted workflow:

```text
1. Media or content marker receives restricted status or suitability.
2. Policy checks restrict view, thumbnail, preview, download, export, and search visibility.
3. UI displays restricted markers only to authorized users.
4. Export excludes or redacts restricted material unless user has authority.
```

Required capabilities:

```text
mod/uckkarchive:viewrestrictedmedia
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:viewrestricted
```

Restricted rule:

```text
Restricted media must not leak through thumbnails, previews, search facets, export manifests, backup previews, or advisory summaries.
```

---

## 33. Final media workflow rule

```text
Media is managed as a first-class object.

Media files live in Moodle File API.
Media identity, versions, collections, relations, source records, content advisories, cultural protocol markers, reviews, and export identity live in mod_uckkarchive tables.

Media workflow is controlled by server-side policy.
Content advisories describe responsible access.
Cultural protocol rules protect sensitive knowledge.
External works can be referenced without being owned.

This document defines the final target behavior for implementation.
Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
```
