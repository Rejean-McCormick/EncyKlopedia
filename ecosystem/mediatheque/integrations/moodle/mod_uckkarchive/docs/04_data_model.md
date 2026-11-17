# 04 — Data Model

**Path:** `docs/04_data_model.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Database schema, object model, identifiers, relationships, lifecycle values, file-area references, privacy fields, and export identity for the self-contained UCKK Archive, Media Library, and Content Advisory system.

---

## 1. Purpose

This document defines the final data model for `mod_uckkarchive`.

`mod_uckkarchive` is a Moodle-native activity module with a self-contained internal data model for:

```text
archive memory
media library management
media versioning
media collections
media relations
content advisories
cultural sensitivity tags
external/foreign media references
proof records
Kristals
provenance
revision history
validation state
restricted metadata
export packages
export manifests
```

The module stores structured metadata in Moodle database tables and stores files through Moodle File API.

The module does not store binary media files directly in custom database fields.

---

## 2. Core data ownership

`mod_uckkarchive` owns the following data domains:

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
content advisory tags
content tag sets
content markers
content reviews
external works
media source records
```

`mod_uckkarchive` does not own:

```text
grades
gradebook records
transcripts
course enrolment authority
administrative registry records
challenge workflow authority
Assembly decision authority
integrity case authority
institutional report authority
```

Records from external domains may be referenced or preserved as archive/media evidence, but preservation does not transfer authority.

---

## 3. Identifier model

Every primary table uses a Moodle local integer primary key:

```text
id
```

Every portable domain object also has a stable UUID:

```text
uuid
```

Identifier rule:

```text
id = local Moodle database identity
uuid = portable object identity
```

Objects requiring UUIDs:

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

UUIDs support:

```text
backup
restore
export
import
duplication
cross-site portability
manifest generation
external references
media graph reconstruction
```

---

## 4. Table list

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

---

## 5. Shared field conventions

Most domain tables use these standard fields where applicable:

```text
id
uuid
archiveid
courseid
cmid
contextid
userid
createdby
modifiedby
timecreated
timemodified
status
visibility
metadata
```

Common meaning:

| Field | Meaning |
|---|---|
| `id` | Moodle local database primary key. |
| `uuid` | Stable portable object identity. |
| `archiveid` | Parent `uckkarchive` activity instance. |
| `courseid` | Moodle course ID. |
| `cmid` | Moodle course module ID. |
| `contextid` | Moodle context ID. |
| `userid` | Primary user associated with the record, when applicable. |
| `createdby` | User who created the record. |
| `modifiedby` | User who last modified the record. |
| `timecreated` | Creation timestamp. |
| `timemodified` | Last modification timestamp. |
| `status` | Lifecycle state of the object. |
| `visibility` | Visibility/access classification. |
| `metadata` | JSON metadata for extensible non-authority fields. |

Metadata is not a substitute for first-class fields when a value is used for access, lifecycle, privacy, backup, restore, export, or reporting.

---

## 6. Table: `uckkarchive`

Purpose:

```text
Activity instance and root archive/media library configuration.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable archive activity UUID. |
| `course` | int | Yes | Moodle course ID. |
| `name` | char | Yes | Activity name. |
| `intro` | text | No | Moodle intro field. |
| `introformat` | int | Yes | Moodle intro format. |
| `defaultvisibility` | char | Yes | Default visibility for new items/media. |
| `defaultmediastatus` | char | Yes | Default media lifecycle state. |
| `defaultvalidationstate` | char | Yes | Default validation state. |
| `enablemedia` | int | Yes | Whether media library features are enabled. |
| `enablecontentadvisories` | int | Yes | Whether content advisory features are enabled. |
| `enableexternalworks` | int | Yes | Whether external work references are enabled. |
| `enableexports` | int | Yes | Whether export features are enabled. |
| `enablepublicview` | int | Yes | Whether public visibility is allowed. |
| `enablerestrictedrecords` | int | Yes | Whether restricted records are allowed. |
| `configjson` | text | No | JSON configuration for module-level behavior. |
| `timecreated` | int | Yes | Creation time. |
| `timemodified` | int | Yes | Modified time. |

Rules:

```text
The activity instance is the root context for archive, media, content advisory, and export records.
The activity instance does not own grades or enrolments.
```

---

## 7. Table: `uckkarchive_item`

Purpose:

```text
Archive memory item, pedagogical item, evidence item, institutional memory item, or item-level record that may reference media.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable archive item UUID. |
| `archiveid` | int | Yes | Parent `uckkarchive`. |
| `courseid` | int | Yes | Moodle course ID. |
| `cmid` | int | Yes | Course module ID. |
| `contextid` | int | Yes | Moodle context ID. |
| `userid` | int | No | Primary associated user. |
| `itemtype` | char | Yes | Archive item type. |
| `title` | char | Yes | Item title. |
| `summary` | text | No | Short summary. |
| `content` | text | No | Rich content/editor content. |
| `contentformat` | int | Yes | Format for `content`. |
| `status` | char | Yes | Archive item status. |
| `visibility` | char | Yes | Visibility value. |
| `validationstate` | char | Yes | Validation state. |
| `versionno` | int | Yes | Current version number. |
| `currentrevisionid` | int | No | Current revision record. |
| `provenanceid` | int | No | Current provenance record. |
| `provenancehash` | char | No | Hash for provenance state. |
| `retentionclass` | char | Yes | Retention classification. |
| `redactionstate` | char | Yes | Redaction state. |
| `createdby` | int | Yes | Creator. |
| `modifiedby` | int | Yes | Last modifier. |
| `validatedby` | int | No | Validator. |
| `timevalidated` | int | No | Validation timestamp. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Canonical `itemtype` values:

```text
proof
decision_snapshot
minutes
challenge_result
course_work
portfolio_item
kristal_source
integrity_summary
public_summary
institutional_source
media_context
external_work_context
content_advisory_context
```

Rules:

```text
Archive items are not media objects.
Archive items may reference media objects through relation records.
Archive items may contain editor content and item files.
Archive items preserve meaning, context, validation, and institutional/pedagogical memory.
```

---

## 8. Table: `uckkarchive_proof`

Purpose:

```text
Proof/evidence record associated with an archive item, challenge, validation, portfolio, media, or restricted review.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable proof UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `itemid` | int | No | Related archive item. |
| `mediaid` | int | No | Related media object. |
| `courseid` | int | Yes | Course ID. |
| `cmid` | int | Yes | Course module ID. |
| `contextid` | int | Yes | Context ID. |
| `userid` | int | No | Submitter/owner. |
| `prooftype` | char | Yes | Proof type. |
| `title` | char | Yes | Proof title. |
| `description` | text | No | Proof description. |
| `status` | char | Yes | Lifecycle state. |
| `visibility` | char | Yes | Visibility state. |
| `validationstate` | char | Yes | Validation state. |
| `sourcecomponent` | char | No | Originating component. |
| `sourcearea` | char | No | Originating area. |
| `sourceid` | int | No | Originating record ID. |
| `retentionclass` | char | Yes | Retention classification. |
| `redactionstate` | char | Yes | Redaction state. |
| `createdby` | int | Yes | Creator. |
| `modifiedby` | int | Yes | Last modifier. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Rules:

```text
Proofs can link to archive items or media.
Proof records do not own grades or challenge workflow.
Restricted proofs require service-layer and file-layer checks.
```

---

## 9. Table: `uckkarchive_kristal`

Purpose:

```text
Kristal record preserved as archive/media knowledge, symbolic structure, or pedagogical memory object.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable Kristal UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `itemid` | int | No | Related archive item. |
| `mediaid` | int | No | Related media. |
| `title` | char | Yes | Kristal title. |
| `summary` | text | No | Kristal summary. |
| `kristaltype` | char | Yes | Kristal type. |
| `status` | char | Yes | Lifecycle state. |
| `visibility` | char | Yes | Visibility value. |
| `validationstate` | char | Yes | Validation state. |
| `provenanceid` | int | No | Provenance record. |
| `versionno` | int | Yes | Version number. |
| `createdby` | int | Yes | Creator. |
| `modifiedby` | int | Yes | Last modifier. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Rules:

```text
Kristals may reference media.
Kristals are archive-owned records.
Kristals do not own external authority domains.
```

---

## 10. Table: `uckkarchive_prov`

Purpose:

```text
Provenance record explaining origin, source, method, actor, context, and trust lineage.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable provenance UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `itemid` | int | No | Archive item. |
| `mediaid` | int | No | Media object. |
| `mediaversionid` | int | No | Media version. |
| `externalworkid` | int | No | External work. |
| `provenancetype` | char | Yes | Provenance value. |
| `sourcecomponent` | char | No | Source component. |
| `sourcearea` | char | No | Source area. |
| `sourceid` | char | No | Source identifier. |
| `sourcetitle` | char | No | Source title. |
| `sourceurl` | text | No | Source URL/reference. |
| `sourcehash` | char | No | Source hash. |
| `actorid` | int | No | Actor. |
| `statement` | text | No | Provenance statement. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Rules:

```text
Provenance explains origin.
Provenance does not grant authority.
Provenance may contain personal or sensitive data and must be privacy-aware.
```

---

## 11. Table: `uckkarchive_rev`

Purpose:

```text
Revision history for archive items, media metadata, validation changes, provenance changes, restriction changes, and content advisory changes.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable revision UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `itemid` | int | No | Archive item. |
| `mediaid` | int | No | Media object. |
| `mediaversionid` | int | No | Media version. |
| `contentmarkerid` | int | No | Content marker. |
| `revisiontype` | char | Yes | Revision type. |
| `versionno` | int | Yes | Version number. |
| `reason` | text | Yes | Reason for change. |
| `beforejson` | text | No | Safe previous-state JSON. |
| `afterjson` | text | No | Safe new-state JSON. |
| `createdby` | int | Yes | Actor. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |

Rules:

```text
No meaningful archive/media/advisory state change is silent.
Sensitive previous values must not be stored unredacted in revision JSON.
```

---

## 12. Table: `uckkarchive_export`

Purpose:

```text
Export request, export package, export manifest, and export status record.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable export UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `userid` | int | Yes | Export requester. |
| `exporttype` | char | Yes | Export type. |
| `scope` | char | Yes | Export scope. |
| `format` | char | Yes | Export format. |
| `status` | char | Yes | Export status. |
| `manifestjson` | text | No | Manifest JSON. |
| `includeditems` | text | No | JSON list of item UUIDs. |
| `includedmedia` | text | No | JSON list of media UUIDs. |
| `includedexternalworks` | text | No | JSON list of external work UUIDs. |
| `includedmarkers` | text | No | JSON list of content marker UUIDs. |
| `redactionmode` | char | Yes | Redaction/export filtering mode. |
| `expiresat` | int | No | Export expiry timestamp. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Rules:

```text
Exports must use manifest.json.
Exports must not bypass visibility, redaction, privacy, cultural protocol, or advisory policy.
```

---

## 13. Table: `uckkarchive_media`

Purpose:

```text
First-class media object managed by the self-contained media library.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable media UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `courseid` | int | Yes | Course ID. |
| `cmid` | int | Yes | Course module ID. |
| `contextid` | int | Yes | Context ID. |
| `sourceid` | int | No | Media source record. |
| `externalworkid` | int | No | External work reference. |
| `title` | char | Yes | Media title. |
| `description` | text | No | Media description. |
| `mediatype` | char | Yes | Media type. |
| `mimetype` | char | No | MIME type of primary/original file. |
| `status` | char | Yes | Media lifecycle state. |
| `visibility` | char | Yes | Visibility value. |
| `audiencesuitability` | char | Yes | Audience suitability. |
| `validationstate` | char | Yes | Validation state. |
| `currentversionid` | int | No | Current media version. |
| `originalversionid` | int | No | Original media version. |
| `durationseconds` | int | No | Audio/video duration. |
| `pagecount` | int | No | Document/page count. |
| `language` | char | No | Language code. |
| `license` | char | No | License/rights label. |
| `rightsstatement` | text | No | Rights statement. |
| `provenanceid` | int | No | Provenance record. |
| `retentionclass` | char | Yes | Retention classification. |
| `redactionstate` | char | Yes | Redaction state. |
| `createdby` | int | Yes | Creator. |
| `modifiedby` | int | Yes | Last modifier. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Canonical `mediatype` values:

```text
image
video
audio
document
pdf
text
transcript
caption
thumbnail
preview
derivative
archive_package
external_reference
other
```

Rules:

```text
Media is a first-class domain object.
Media is not merely a file attached to an archive item.
Media may reference external works without copying external files.
```

---

## 14. Table: `uckkarchive_media_version`

Purpose:

```text
Version record for media files, replacements, derivatives, previews, thumbnails, captions, transcripts, and metadata-significant media changes.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable media version UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `mediaid` | int | Yes | Parent media object. |
| `versionno` | int | Yes | Version number. |
| `versiontype` | char | Yes | Version type. |
| `filearea` | char | Yes | Moodle File API area. |
| `filename` | char | No | Stored/display filename. |
| `mimetype` | char | No | MIME type. |
| `filesize` | int | No | File size. |
| `contenthash` | char | No | Moodle/content hash. |
| `sha256` | char | No | Portable hash. |
| `durationseconds` | int | No | Duration. |
| `pagecount` | int | No | Page count. |
| `width` | int | No | Image/video width. |
| `height` | int | No | Image/video height. |
| `status` | char | Yes | Version status. |
| `iscurrent` | int | Yes | Whether this is the current version. |
| `createdby` | int | Yes | Creator. |
| `reason` | text | No | Version reason. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |

Canonical `versiontype` values:

```text
original
replacement
preview
thumbnail
derivative
caption
transcript
attachment
metadata_revision
```

Rules:

```text
Media files are not overwritten silently.
Meaningful media changes create media version records.
Generated derivatives are tracked separately from original files.
```

---

## 15. Table: `uckkarchive_media_relation`

Purpose:

```text
Graph relation between media, archive items, Kristals, collections, external works, content markers, and other media.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable relation UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `fromtype` | char | Yes | Source object type. |
| `fromid` | int | Yes | Source object ID. |
| `totype` | char | Yes | Target object type. |
| `toid` | int | Yes | Target object ID. |
| `relationtype` | char | Yes | Relation type. |
| `sortorder` | int | Yes | Ordering. |
| `createdby` | int | Yes | Creator. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |

Canonical `relationtype` values:

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

Rules:

```text
Relations describe meaning.
Relations do not copy files.
Relations do not transfer external authority.
```

---

## 16. Table: `uckkarchive_media_tag`

Purpose:

```text
General media tags for search, categorization, teaching use, and organization.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable tag UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `mediaid` | int | Yes | Media object. |
| `tagkey` | char | Yes | Machine tag key. |
| `taglabel` | char | Yes | Display label. |
| `tagtype` | char | Yes | Tag category. |
| `createdby` | int | Yes | Creator. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |

Rules:

```text
Media tags support discovery.
Content advisories use content advisory tables, not generic media tags.
```

---

## 17. Table: `uckkarchive_media_collection`

Purpose:

```text
Reusable media set, bundle, course pack, evidence pack, public set, restricted bundle, or pedagogical media library collection.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable collection UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `title` | char | Yes | Collection title. |
| `description` | text | No | Collection description. |
| `collectiontype` | char | Yes | Collection type. |
| `status` | char | Yes | Lifecycle state. |
| `visibility` | char | Yes | Visibility value. |
| `audiencesuitability` | char | Yes | Suitability. |
| `createdby` | int | Yes | Creator. |
| `modifiedby` | int | Yes | Last modifier. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Canonical `collectiontype` values:

```text
course_pack
kristal_source_pack
challenge_evidence_pack
assembly_record_pack
public_media_set
restricted_proof_bundle
content_advisory_set
external_work_set
```

---

## 18. Table: `uckkarchive_media_collection_item`

Purpose:

```text
Membership and ordering of media objects inside collections.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable membership UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `collectionid` | int | Yes | Parent collection. |
| `mediaid` | int | Yes | Media object. |
| `sortorder` | int | Yes | Sort order. |
| `role` | char | No | Role inside collection. |
| `createdby` | int | Yes | Creator. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |

Rules:

```text
A media object may belong to multiple collections.
Collections do not duplicate media files.
```

---

## 19. Table: `uckkarchive_content_tag`

Purpose:

```text
Reusable content advisory, cultural sensitivity, cultural protocol, suitability, or restriction tag.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable content tag UUID. |
| `archiveid` | int | No | Optional archive scope; null for global module tag. |
| `tagkey` | char | Yes | Machine key. |
| `taglabel` | char | Yes | Display label. |
| `tagtype` | char | Yes | Tag type. |
| `severity` | char | Yes | Severity. |
| `description` | text | No | Description. |
| `recommendedaction` | text | No | Teaching/access recommendation. |
| `requirescontext` | int | Yes | Whether context is required. |
| `requiresreview` | int | Yes | Whether human review is required. |
| `createdby` | int | Yes | Creator. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Canonical content tag examples:

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

Canonical `tagtype` values:

```text
content_advisory
cultural_protocol
audience_suitability
teaching_context
access_restriction
```

Canonical `severity` values:

```text
notice
moderate
strong
restricted
```

---

## 20. Table: `uckkarchive_content_tag_set`

Purpose:

```text
Reusable vocabulary or grouped tag set for advisory, cultural protocol, classroom suitability, integrity sensitivity, or youth access.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable tag set UUID. |
| `archiveid` | int | No | Optional archive scope. |
| `setkey` | char | Yes | Machine key. |
| `setlabel` | char | Yes | Display label. |
| `settype` | char | Yes | Set type. |
| `description` | text | No | Description. |
| `status` | char | Yes | Lifecycle state. |
| `createdby` | int | Yes | Creator. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Canonical tag set examples:

```text
general_advisories
cultural_protocols
classroom_suitability
integrity_sensitive
youth_access
```

Rules:

```text
A tag set groups advisory tags into reusable vocabularies.
Tag sets do not replace individual content tags or content markers.
```

---

## 21. Table: `uckkarchive_content_marker`

Purpose:

```text
Location-specific advisory or cultural protocol marker attached to internal media, archive items, media versions, external works, or manual references.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable content marker UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `tagid` | int | Yes | Content tag. |
| `tagsetid` | int | No | Tag set. |
| `mediaid` | int | No | Media object. |
| `mediaversionid` | int | No | Media version. |
| `itemid` | int | No | Archive item. |
| `externalworkid` | int | No | External work. |
| `locator_type` | char | Yes | Locator type. |
| `locator_start` | char | No | Locator start. |
| `locator_end` | char | No | Locator end. |
| `locator_label` | char | No | Human-readable locator. |
| `advisorytext` | text | No | Advisory note. |
| `audiencesuitability` | char | Yes | Audience suitability. |
| `reviewstate` | char | Yes | Review state. |
| `visibility` | char | Yes | Marker visibility. |
| `createdby` | int | Yes | Creator. |
| `reviewedby` | int | No | Reviewer. |
| `timereviewed` | int | No | Review timestamp. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

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

Rules:

```text
A content marker locates advisory meaning.
A content marker may point to an external work without copying external content.
A content marker does not ban media by itself.
```

---

## 22. Table: `uckkarchive_content_review`

Purpose:

```text
Human review record for content markers, cultural protocol notes, suitability, advisory status, and restriction decisions.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable review UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `markerid` | int | No | Content marker. |
| `tagid` | int | No | Content tag. |
| `mediaid` | int | No | Media object. |
| `externalworkid` | int | No | External work. |
| `reviewstate` | char | Yes | Review state. |
| `decision` | char | Yes | Review decision. |
| `reviewnote` | text | No | Review note. |
| `recommendedaction` | text | No | Access/teaching recommendation. |
| `reviewedby` | int | Yes | Reviewer. |
| `visibility` | char | Yes | Visibility. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Canonical review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Rules:

```text
AI may suggest advisory tags or markers.
Human review is required before advisory status becomes approved.
Cultural protocol review cannot be replaced by AI.
```

---

## 23. Table: `uckkarchive_external_work`

Purpose:

```text
Reference record for a work not produced by UCKK that may be taught, tagged, reviewed, cited, or linked to archive/media records.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable external work UUID. |
| `archiveid` | int | No | Optional parent archive. |
| `worktype` | char | Yes | External work type. |
| `title` | char | Yes | Work title. |
| `creator` | char | No | Author/director/creator. |
| `publisher` | char | No | Publisher/studio/source. |
| `publicationyear` | int | No | Year. |
| `identifier` | char | No | ISBN/DOI/URL/catalog ID. |
| `sourceurl` | text | No | URL/reference. |
| `rightsstatement` | text | No | Rights/copyright statement. |
| `sourceownership` | char | Yes | Ownership/source category. |
| `audiencesuitability` | char | Yes | Suitability. |
| `visibility` | char | Yes | Visibility. |
| `createdby` | int | Yes | Creator. |
| `modifiedby` | int | Yes | Last modifier. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Canonical `worktype` values:

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

Rules:

```text
External works may be referenced without being copied.
The archive must not imply ownership over third-party works.
Content markers can point to pages, timestamps, scenes, chapters, sections, or URL fragments of external works.
```

---

## 24. Table: `uckkarchive_media_source`

Purpose:

```text
Source/rights/origin record describing whether a media object is UCKK-created, submitted, imported, licensed, external, public domain, or reference-only.
```

Required fields:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `id` | int | Yes | Primary key. |
| `uuid` | char(36) | Yes | Portable media source UUID. |
| `archiveid` | int | Yes | Parent archive. |
| `mediaid` | int | No | Media object. |
| `externalworkid` | int | No | External work. |
| `sourcetype` | char | Yes | Media source value. |
| `sourceownership` | char | Yes | Ownership/source category. |
| `license` | char | No | License value. |
| `rightsstatement` | text | No | Rights statement. |
| `attribution` | text | No | Attribution. |
| `sourceurl` | text | No | Source URL/reference. |
| `createdby` | int | Yes | Creator. |
| `metadata` | text | No | JSON metadata. |
| `timecreated` | int | Yes | Creation timestamp. |
| `timemodified` | int | Yes | Modified timestamp. |

Canonical `sourcetype` values:

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

Canonical `sourceownership` values:

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

Rules:

```text
Media source records support rights, provenance, advisory, and export decisions.
Source records do not transfer ownership from external rights holders.
```

---

## 25. Status values

Archive item statuses:

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

Media statuses:

```text
draft
submitted
active
restricted
superseded
archived
deleted_soft
```

Export statuses:

```text
queued
processing
ready
failed
expired
purged
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

---

## 26. Visibility values

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

Rules:

```text
Visibility does not replace capability checks.
Restricted cultural visibility requires cultural protocol checks.
Restricted integrity visibility requires restricted integrity checks.
```

---

## 27. Validation states

Canonical validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Rules:

```text
Validation is human-final.
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot approve cultural protocol access.
AI cannot close contestations.
```

---

## 28. Audience suitability values

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

Rules:

```text
Audience suitability affects responsible access and teaching conditions.
Suitability is not the same as visibility.
Suitability can be refined by content markers.
```

---

## 29. Retention classes

Canonical retention classes:

```text
draft_short
course_operational
portfolio_user
proof_evidence
institutional_memory
restricted_integrity
restricted_cultural
export_generated
external_snapshot
```

Rules:

```text
Retention controls preservation/deletion behavior.
Retention does not automatically grant visibility.
```

---

## 30. Redaction states

Canonical redaction states:

```text
none
partial
full
anonymised
restricted
deleted
```

Rules:

```text
Redaction is persistent state.
Redaction must apply to services, UI, export, privacy export, backup, and restore.
```

---

## 31. File API mapping

Component:

```text
mod_uckkarchive
```

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

Content advisory file areas:

```text
content_review_files
external_work_reference_files
cultural_protocol_files
```

File area registry:

```text
classes/local/file_area_registry.php
```

Rules:

```text
All file areas are centralized in file_area_registry.
Pluginfile handling, services, privacy provider, backup, restore, and tests use the same registry.
```

---

## 32. Index and uniqueness requirements

Required unique keys:

```text
uckkarchive.uuid
uckkarchive_item.uuid
uckkarchive_proof.uuid
uckkarchive_kristal.uuid
uckkarchive_prov.uuid
uckkarchive_rev.uuid
uckkarchive_export.uuid
uckkarchive_media.uuid
uckkarchive_media_version.uuid
uckkarchive_media_relation.uuid
uckkarchive_media_tag.uuid
uckkarchive_media_collection.uuid
uckkarchive_media_collection_item.uuid
uckkarchive_content_tag.uuid
uckkarchive_content_tag_set.uuid
uckkarchive_content_marker.uuid
uckkarchive_content_review.uuid
uckkarchive_external_work.uuid
uckkarchive_media_source.uuid
```

Recommended functional indexes:

```text
archiveid
courseid
cmid
contextid
userid
status
visibility
validationstate
mediaid
itemid
externalworkid
tagid
tagsetid
collectionid
timecreated
timemodified
```

Recommended composite indexes:

```text
archiveid,status
archiveid,visibility
archiveid,validationstate
archiveid,mediaid
archiveid,itemid
archiveid,externalworkid
archiveid,tagid
archiveid,collectionid
mediaid,versionno
mediaid,iscurrent
collectionid,sortorder
tagid,reviewstate
externalworkid,locator_type
```

---

## 33. Metadata JSON rules

JSON metadata may store:

```text
display hints
non-authority UI preferences
import details
external IDs
non-critical source notes
search hints
format-specific media details
AI suggestion details
teaching context notes
```

JSON metadata must not be the only storage location for:

```text
capability decisions
visibility
status
validation state
media lifecycle state
content advisory review state
cultural restriction state
file area
UUID
primary relations
privacy deletion state
retention class
redaction state
export authority
```

---

## 34. Privacy data model rules

Tables that may contain personal data:

```text
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

Privacy provider must cover:

```text
user-linked records
creator/modifier/reviewer fields
uploaded files
media files
content review notes
restricted records
cultural protocol notes
export packages
manifest files
```

Rules:

```text
Privacy export must not expose third-party restricted data.
Cultural protocol notes may require redaction even when the user owns related content.
External work references must not imply ownership or authorization.
```

---

## 35. Backup and restore data model rules

Backup must include:

```text
archive instance
archive items
proofs
Kristals
provenance
revisions
exports
media
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
all active file areas
```

Restore must preserve:

```text
UUIDs
relations
collection membership
content marker locators
external work references
media source records
visibility
validation state
retention class
redaction state
restricted cultural state
restricted integrity state
export manifest metadata
```

Restore must not create authority in external systems.

---

## 36. Export manifest data model

Canonical manifest file:

```text
manifest.json
```

Manifest includes:

```text
plugin component
archive id
archive uuid
export id
export uuid
export timestamp
export actor
export reason
archive item uuids
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

Rules:

```text
Exports are portable and explainable.
Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.
```

---

## 37. Data model final rule

```text
mod_uckkarchive owns a self-contained archive, media library, and content advisory data model.

Archive records preserve meaning.
Media records manage reusable media objects.
Media versions preserve file history.
Collections organize media.
Relations describe graph meaning.
Content advisories describe responsible access, cultural protocol, and suitability.
External works allow foreign media to be referenced without claiming ownership.
Provenance explains origin.
Revisions preserve change.
Exports preserve portable memory.

All files remain in Moodle File API.
All authority checks remain server-side.
All final implementation must conform to this data model.
```
