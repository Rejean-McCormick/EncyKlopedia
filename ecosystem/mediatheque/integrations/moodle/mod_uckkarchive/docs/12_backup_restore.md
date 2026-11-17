# 12 — Backup and Restore

**Path:** `docs/12_backup_restore.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Backup and restore contract for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines the backup and restore behavior for `mod_uckkarchive`.

`mod_uckkarchive` is a Moodle-native activity module with a self-contained internal archive, media library, and content advisory system.

Canonical formula:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

Backup and restore must preserve module-owned records, files, metadata, relations, provenance, revision history, validation state, content advisories, cultural protocol metadata, external work references, and export manifests.

Backup and restore must not turn `mod_uckkarchive` into the owner of external workflow domains.

---

## 2. Core backup decision

`mod_uckkarchive` backup must preserve:

```text
activity instance
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
content tag sets
content markers
content reviews
external works
foreign media references
media source records
audience suitability rules
export package metadata
export manifests
Moodle File API file areas
```

Restore must reconstruct the same module-owned state in the restored activity context.

Restore must not create or claim ownership over external authority records.

---

## 3. Domain boundary rule

Canonical ownership map:

```text
GRADE_OWNER = Moodle gradebook
REGISTRY_OWNER = local_uckk
CHALLENGE_OWNER = mod_uckkchallenge
ASSEMBLY_OWNER = mod_uckkassembly
INTEGRITY_OWNER = tool_uckkintegrity
REPORT_OWNER = report_uckk
ARCHIVE_OWNER = mod_uckkarchive
```

Backup/restore boundary rules:

```text
Restore must not create grades.
Restore must not create official transcripts.
Restore must not create enrolments.
Restore must not create global registry authority.
Restore must not create challenge workflow authority.
Restore must not create Assembly decision authority.
Restore must not create integrity case authority.
Restore must not create institutional reporting authority.
Restore must not claim copyright ownership over external works.
```

The archive may restore references, preserved snapshots, evidence, media, content advisories, and provenance from external domains.

Restoring a reference does not restore external authority.

---

## 4. Required backup and restore files

Canonical backup/restore files:

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

File responsibilities:

| File | Responsibility |
|---|---|
| `backup_uckkarchive_activity_task.class.php` | Defines the Moodle backup task, encoded content links, file areas, and backup step registration. |
| `backup_uckkarchive_stepslib.php` | Defines the backup structure for module-owned records. |
| `restore_uckkarchive_activity_task.class.php` | Defines the Moodle restore task, decode rules, file areas, and restore step registration. |
| `restore_uckkarchive_stepslib.php` | Restores module-owned records, maps IDs, restores files, and reconnects relations. |

Implementation rule:

```text
Backup/restore code must use Moodle backup and restore APIs.
It must not use raw filesystem copies.
It must not bypass Moodle File API.
```

---

## 5. Backup root structure

The backup XML structure must begin with the activity instance:

```text
uckkarchive
```

The activity root contains child structures for:

```text
items
proofs
kristals
provenance_records
revisions
exports
media
media_versions
media_relations
media_tags
media_collections
media_collection_items
content_tags
content_tag_sets
content_markers
content_reviews
external_works
media_sources
```

The backup structure must be deterministic.

Records should be ordered by stable identifiers where possible:

```text
id
uuid
timecreated
sortorder
```

---

## 6. Activity instance backup

Required table:

```text
uckkarchive
```

The activity instance backup preserves:

```text
id
course
name
intro
introformat
configuration fields
default visibility
default archive policy
default media policy
default advisory policy
completion configuration
timecreated
timemodified
```

Restore rule:

```text
The restored uckkarchive record receives a new local id.
The restored activity keeps a stable uuid when appropriate.
Course and course module references are remapped by Moodle restore.
```

---

## 7. Archive item backup

Required table:

```text
uckkarchive_item
```

Archive item backup preserves:

```text
id
uuid
uckkarchiveid
userid
title
description
descriptionformat
type
status
visibility
validationstate
provenance
sourcecomponent
sourceid
sortorder
metadata
timecreated
timemodified
```

Archive item restore must:

```text
map uckkarchiveid to the restored activity id
map userid through Moodle user mapping when available
preserve uuid unless restore policy explicitly regenerates it
preserve status
preserve validation state
preserve visibility
preserve provenance
preserve metadata
```

Restore must not convert archive items into grades, official decisions, or external workflow records.

---

## 8. Proof backup

Required table:

```text
uckkarchive_proof
```

Proof backup preserves:

```text
id
uuid
uckkarchiveid
itemid
userid
type
status
visibility
validationstate
description
descriptionformat
metadata
timecreated
timemodified
```

Proof restore must:

```text
map uckkarchiveid
map itemid
map userid
restore proof file areas
preserve restricted flags
preserve validation state
preserve provenance
```

Proof records remain archive evidence.

They do not become gradebook records, integrity findings, or Assembly decisions.

---

## 9. Kristal backup

Required table:

```text
uckkarchive_kristal
```

Kristal backup preserves:

```text
id
uuid
uckkarchiveid
itemid
userid
title
summary
summaryformat
status
visibility
validationstate
metadata
timecreated
timemodified
```

Kristal restore must:

```text
map uckkarchiveid
map itemid when linked
map userid
restore Kristal file areas
preserve visibility
preserve validation state
preserve provenance
```

Kristals remain archive-owned learning/memory objects.

---

## 10. Provenance backup

Required table:

```text
uckkarchive_prov
```

Provenance backup preserves:

```text
id
uuid
uckkarchiveid
targettype
targetid
targetuuid
provenancetype
sourcecomponent
sourceid
sourceuuid
actorid
description
descriptionformat
hashvalue
metadata
timecreated
```

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

Provenance restore must:

```text
map target ids when target objects are restored
map actorid through Moodle user mapping when available
preserve targetuuid
preserve sourcecomponent
preserve sourceid/sourceuuid as reference metadata
preserve hash values
preserve metadata
```

Provenance rule:

```text
Provenance explains origin.
Provenance does not grant authority by itself.
```

---

## 11. Revision backup

Required table:

```text
uckkarchive_rev
```

Revision backup preserves:

```text
id
uuid
uckkarchiveid
targettype
targetid
targetuuid
revisionnumber
userid
summary
summaryformat
changedata
metadata
timecreated
```

Revision restore must:

```text
map target ids
map userid
preserve revision numbers
preserve changedata
preserve targetuuid
```

Archive revision permission uses:

```text
mod/uckkarchive:reviseitem
```

The removed capability must not be restored or referenced:

```text
mod/uckkarchive:versionitem
```

---

## 12. Export metadata backup

Required table:

```text
uckkarchive_export
```

Export metadata backup preserves:

```text
id
uuid
uckkarchiveid
userid
exporttype
status
visibility
redactionlevel
manifestjson
metadata
timecreated
timemodified
```

Export package files are restored only through Moodle File API file areas.

Export restore must:

```text
map uckkarchiveid
map userid
restore export metadata
restore export_manifest file area when included
restore export_package file area when included and allowed
preserve manifest references
preserve redaction level
preserve restricted flags
```

Restore must not make restricted exports public.

---

## 13. Media object backup

Required table:

```text
uckkarchive_media
```

Media backup preserves:

```text
id
uuid
uckkarchiveid
userid
title
description
descriptionformat
mediatype
mimetype
status
visibility
audiencesuitability
sourceid
currentversionid
metadata
timecreated
timemodified
```

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

Restore must:

```text
map uckkarchiveid
map userid
map sourceid
map currentversionid after media versions are restored
preserve uuid
preserve status
preserve visibility
preserve audience suitability
preserve metadata
```

Media restore must not assume file availability means media availability.

Media status remains authoritative.

---

## 14. Media version backup

Required table:

```text
uckkarchive_media_version
```

Media version backup preserves:

```text
id
uuid
mediaid
versionnumber
userid
status
mimetype
filesize
contenthash
filearea
filename
description
descriptionformat
metadata
timecreated
```

Media version restore must:

```text
map mediaid
map userid
preserve uuid
preserve versionnumber
preserve contenthash
restore related File API files
preserve filearea and filename references
```

Media versioning permission uses:

```text
mod/uckkarchive:versionmedia
```

Media versions must remain connected to their parent media object.

---

## 15. Media relation backup

Required table:

```text
uckkarchive_media_relation
```

Media relation backup preserves:

```text
id
uuid
uckkarchiveid
frommediaid
tomediaid
fromuuid
touuid
relationtype
targettype
targetid
targetuuid
metadata
timecreated
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

Restore must:

```text
map frommediaid
map tomediaid
map targetid when target is restored
preserve fromuuid
preserve touuid
preserve targetuuid
preserve relationtype
```

Relation rule:

```text
Relations describe media graph meaning.
Relations do not transfer ownership to external plugins or external rights holders.
```

---

## 16. Media tag backup

Required table:

```text
uckkarchive_media_tag
```

Media tag backup preserves:

```text
id
uuid
mediaid
tagkey
tagvalue
tagtype
userid
metadata
timecreated
```

Restore must:

```text
map mediaid
map userid
preserve tagkey
preserve tagvalue
preserve tagtype
preserve metadata
```

Media tags are descriptive.

Content advisories and cultural protocol tags belong to the content advisory subsystem when they affect suitability, restriction, teaching context, or review state.

---

## 17. Media collection backup

Required tables:

```text
uckkarchive_media_collection
uckkarchive_media_collection_item
```

Collection backup preserves:

```text
id
uuid
uckkarchiveid
userid
title
description
descriptionformat
visibility
status
metadata
timecreated
timemodified
```

Collection item backup preserves:

```text
id
collectionid
mediaid
sortorder
metadata
timecreated
```

Restore must:

```text
map uckkarchiveid
map userid
map collectionid
map mediaid
preserve uuid
preserve sortorder
preserve visibility
preserve status
```

Collections remain archive/media-library structures.

They do not become Moodle course sections or external library records.

---

## 18. Content tag backup

Required table:

```text
uckkarchive_content_tag
```

Content tag backup preserves:

```text
id
uuid
tagkey
name
description
descriptionformat
tagtype
severity
audiencesuitability
status
metadata
timecreated
timemodified
```

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

Restore must:

```text
preserve tagkey
preserve severity
preserve audience suitability
preserve cultural protocol metadata
preserve status
```

Content advisory rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 19. Content tag set backup

Required table:

```text
uckkarchive_content_tag_set
```

Content tag set backup preserves:

```text
id
uuid
setkey
name
description
descriptionformat
status
metadata
timecreated
timemodified
```

Examples:

```text
general_advisories
cultural_protocols
classroom_suitability
integrity_sensitive
youth_access
```

Restore must:

```text
preserve setkey
preserve status
preserve metadata
reconnect included tags when membership is represented
```

Tag set rule:

```text
Tag sets organize advisory vocabulary.
Tag sets do not decide access alone.
Access decisions belong to policy classes.
```

---

## 20. Content marker backup

Required table:

```text
uckkarchive_content_marker
```

Content marker backup preserves:

```text
id
uuid
uckkarchiveid
tagid
taguuid
targettype
targetid
targetuuid
externalworkid
externalworkuuid
locator_type
locator_start
locator_end
locator_label
description
descriptionformat
severity
audiencesuitability
reviewstate
metadata
timecreated
timemodified
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

Restore must:

```text
map uckkarchiveid
map tagid
map targetid when target is restored
map externalworkid when external work is restored
preserve taguuid
preserve targetuuid
preserve externalworkuuid
preserve locator fields
preserve severity
preserve audience suitability
preserve review state
```

Content marker rule:

```text
A content marker locates advisory meaning.
A content marker does not copy external content.
A content marker does not transfer external rights.
```

---

## 21. Content review backup

Required table:

```text
uckkarchive_content_review
```

Content review backup preserves:

```text
id
uuid
markerid
markeruuid
reviewerid
reviewstate
reviewnote
reviewnoteformat
decision
metadata
timecreated
timemodified
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

Restore must:

```text
map markerid
map reviewerid through Moodle user mapping when available
preserve markeruuid
preserve reviewstate
preserve decision
preserve review notes according to privacy/redaction policy
restore review file areas when included
```

Review rule:

```text
AI may suggest tags or markers.
Human review is required before advisory status becomes approved.
AI cannot approve cultural protocol access.
AI cannot remove cultural restrictions.
```

---

## 22. External work backup

Required table:

```text
uckkarchive_external_work
```

External work backup preserves:

```text
id
uuid
worktype
title
creator
publisher
publicationdate
identifier
identifier_type
url
citation
citationformat
rightsstatement
sourceownership
metadata
timecreated
timemodified
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

Restore must:

```text
preserve uuid
preserve citation metadata
preserve rights metadata
preserve source ownership
preserve URL/reference fields
restore reference files only when allowed
```

External work rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
The archive must not store unauthorized copies of external works.
```

---

## 23. Media source backup

Required table:

```text
uckkarchive_media_source
```

Media source backup preserves:

```text
id
uuid
mediaid
externalworkid
sourcetype
sourceownership
license
rightsstatement
attribution
url
metadata
timecreated
timemodified
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

Restore must:

```text
map mediaid
map externalworkid
preserve source type
preserve source ownership
preserve license and rights metadata
```

Media source rule:

```text
Media source describes origin and rights context.
Media source does not grant access by itself.
Media source does not override policy, visibility, retention, redaction, or cultural protocol rules.
```

---

## 24. File API backup

All files must be backed up and restored through Moodle File API.

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

File backup rule:

```text
File areas are declared centrally in classes/local/file_area_registry.php.
Backup and restore must use the same registry.
No production archive/media files are backed up from unmanaged public folders.
```

---

## 25. File restore behavior

File restore must:

```text
restore files into the restored module context
map item ids where Moodle File API itemids are tied to restored records
preserve filenames
preserve content hashes
preserve author metadata where permitted
preserve license metadata where permitted
preserve timecreated and timemodified where supported
```

File restore must not:

```text
make restricted files public
make culturally restricted files public
restore unauthorized external work copies
write files outside Moodle File API
create direct public URLs as authority
```

File existence does not grant access.

Access remains controlled by policy classes.

---

## 26. User mapping

Backup may include user-related fields such as:

```text
userid
actorid
reviewerid
creatorid
modifierid
```

Restore must map users through Moodle restore user mapping.

If a user cannot be mapped, restore must preserve record integrity using safe fallback behavior:

```text
use restored mapped user when available
use current restoring user only where Moodle restore policy allows
use null or system marker when allowed by schema and policy
preserve original user metadata only when privacy policy allows
```

User mapping must not reveal private user data beyond Moodle restore policy.

---

## 27. Context mapping

Restore must remap:

```text
course id
course module id
context id
activity instance id
archive item ids
media ids
media version ids
collection ids
content tag ids
content marker ids
content review ids
external work ids
file item ids
```

Context mapping rule:

```text
Local database ids change during restore.
UUIDs remain stable unless restore policy explicitly regenerates them.
Relations must be reconnected using mapped ids and preserved UUIDs.
```

---

## 28. UUID behavior

UUIDs provide stable portable identity.

UUIDs are required for:

```text
archive items
proofs
Kristals
provenance records
revisions
exports
media objects
media versions
media collections
media relations
content tags
content tag sets
content markers
content reviews
external works
media sources
export packages
```

Restore UUID policy:

```text
Default restore preserves UUIDs for portability.
Duplicate-into-same-context restore may regenerate UUIDs if collision prevention requires it.
Any UUID regeneration must update all internal relations and manifest references.
```

---

## 29. Restricted records

Restricted records include:

```text
restricted archive items
restricted media
restricted integrity records
restricted cultural records
staff-only review notes
redacted export packages
content markers with restricted suitability
external work references with restricted access
```

Restore rule:

```text
Restricted status must survive backup and restore.
Restore must never downgrade restricted visibility to public.
Restore must never bypass cultural protocol restrictions.
Restore must never expose restricted review notes to unauthorized roles.
```

---

## 30. Cultural protocol restore

Cultural protocol metadata may include:

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

Restore must preserve:

```text
cultural protocol tags
cultural protocol file areas
cultural review state
audience suitability
restriction flags
export restrictions
```

Cultural protocol restore rule:

```text
Restored cultural protocol restrictions remain active.
Restore must not transform cultural protocol notes into public metadata.
```

---

## 31. Content advisory restore

Content advisories may affect:

```text
display warnings
teaching context
audience suitability
access prompts
restricted visibility
cultural protocol review
export filtering
review workflow
redaction decisions
```

Restore must preserve:

```text
content tag keys
content tag sets
content markers
locators
severity
audience suitability
review state
review decisions
review notes
external work references
```

Content advisory restore rule:

```text
A restored advisory remains advisory metadata.
It does not ban media by itself.
It must still be interpreted by content_policy.php.
```

---

## 32. External work restore

External work records are references.

Restore must preserve:

```text
citation
identifier
URL
rights statement
source ownership
locator references
advisory markers
teaching metadata
```

Restore must not:

```text
copy external media unless the original backup lawfully contained a permitted file
imply UCKK ownership
turn an external reference into UCKK-created media
erase source ownership
```

External work restore rule:

```text
External works remain external after restore.
```

---

## 33. Encoded links

Backup task must define encoded link handling for internal module URLs.

Internal links may include:

```text
view.php?id=$cmid
item.php?id=$cmid&itemid=$itemid
media.php?id=$cmid&mediaid=$mediaid
validate.php?id=$cmid&itemid=$itemid
export.php?id=$cmid&exportid=$exportid
```

Restore must decode internal links to point to restored course-module and record IDs.

Encoded link restore must:

```text
map course module id
map archive item id
map media id
map export id
preserve external URLs as external URLs
not rewrite external work references into local files
```

---

## 34. Manifest restore

Canonical manifest filename:

```text
manifest.json
```

Export manifests may include:

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

Restore must preserve manifest files and metadata when included in the backup.

Restore must not treat a manifest as an authority override.

---

## 35. Privacy interaction

Backup and restore must respect Moodle privacy expectations.

Privacy-sensitive data may include:

```text
user-created archive items
proof records
private media
restricted metadata
review notes
content reviews
cultural protocol notes
provenance actor data
revision actor data
export actor data
file author metadata
```

Privacy restore rule:

```text
Restored data remains subject to mod_uckkarchive privacy provider behavior.
Backup/restore does not bypass privacy export, deletion, retention, or redaction policy.
```

---

## 36. Redaction behavior

Backup may include redacted and unredacted records depending on Moodle backup context and permissions.

Restore must preserve:

```text
redaction level
restricted flags
visibility
review state
audience suitability
cultural protocol flags
export restrictions
```

Restore must not:

```text
reconstruct redacted fields from export summaries
make redacted metadata visible
erase redaction state
convert restricted records into ordinary public records
```

Redaction rule:

```text
Redaction state is data.
It must be restored as part of the archive record.
```

---

## 37. Optional integration behavior

Optional integrations include:

```text
tool_uckkintegrity
mod_uckkchallenge
mod_uckkassembly
report_uckk
local_uckk
```

Restore behavior:

```text
If optional plugins are present, restored references may be resolvable.
If optional plugins are absent, restored references remain preserved metadata.
Ordinary archive/media/content-advisory operation must continue.
Integrity-specific features must be hidden, disabled, or fail closed when tool_uckkintegrity is absent.
```

Restore must not require optional plugins for core archive/media restore.

---

## 38. Restore order

Recommended restore order:

```text
1. uckkarchive activity instance
2. archive items
3. proofs
4. Kristals
5. media sources that do not depend on media
6. external works
7. media objects
8. media versions
9. media collections
10. media collection items
11. media tags
12. media relations
13. content tags
14. content tag sets
15. content markers
16. content reviews
17. provenance records
18. revision records
19. export metadata
20. File API files
21. encoded links
22. post-restore relation repair
23. post-restore current-version repair
```

Ordering rule:

```text
Records that provide identities must be restored before records that reference them.
Post-restore repair must reconnect relations that require mapped ids.
```

---

## 39. Post-restore repair

Post-restore repair must verify:

```text
current media version references
media relation endpoints
collection membership
content marker targets
content review marker links
external work links
media source links
archive item links
proof links
Kristal links
provenance target links
revision target links
export manifest references
File API itemids
```

Post-restore repair must not invent missing external authority records.

---

## 40. Failure handling

Restore should fail safely.

Safe failure behavior:

```text
do not expose restricted data
do not publish culturally restricted data
do not create public file links
do not discard provenance silently
do not discard content advisories silently
do not discard external work rights metadata silently
do not convert broken references into owned records
```

When restore cannot resolve a relation, it should preserve:

```text
targetuuid
sourcecomponent
sourceid
external identifier
metadata
human-readable reference
```

---

## 41. Scheduled task interaction

Backup/restore may affect scheduled tasks.

Relevant task files:

```text
classes/task/generate_archive_exports.php
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
classes/task/validate_pending_items.php
```

Restore rule:

```text
Restore may mark search indexes, thumbnails, derivatives, and advisory indexes for rebuild.
Restore must not run privileged generation that bypasses policy.
```

---

## 42. Events and audit interaction

Restore may create Moodle restore logs.

Restore must not emit normal user action events as if users manually created every restored record.

Audit-sensitive restored data includes:

```text
archive provenance
media provenance
content reviews
validation state
restricted records
export metadata
```

Audit rule:

```text
Restore metadata must distinguish restored records from newly created user actions.
```

---

## 43. Testing requirements

Required backup/restore tests:

```text
tests/backup_restore_test.php
tests/file_api_test.php
tests/media_library_test.php
tests/content_advisory_test.php
tests/external_work_test.php
tests/privacy_provider_test.php
```

Test coverage must verify:

```text
activity instance backup and restore
archive item backup and restore
media object backup and restore
media version backup and restore
media collection backup and restore
media relation backup and restore
content tag backup and restore
content tag set backup and restore
content marker backup and restore
content review backup and restore
external work backup and restore
media source backup and restore
File API file restore
restricted visibility preservation
cultural protocol restriction preservation
UUID preservation
ID remapping
manifest preservation
optional integration absence behavior
```

Testing rule:

```text
Tests verify final target behavior, not historical transitions.
```

---

## 44. Non-goals

Backup/restore must not:

```text
backup raw public folder files as archive authority
restore unauthorized third-party media copies
create grades
create transcripts
create enrolments
create global registry authority
create challenge workflow state
create Assembly decision authority
create integrity case authority
create institutional report authority
bypass Moodle File API
bypass Moodle Privacy API
bypass Moodle capabilities
bypass policy classes
```

---

## 45. Final backup/restore rule

```text
mod_uckkarchive backup and restore preserve archive memory, media library
objects, content advisories, cultural protocol metadata, external work references,
media source records, provenance, revisions, validation state, restricted
metadata, File API files, and export manifests.

Restore reconstructs module-owned state in the restored Moodle activity context.

Restore does not create grades, transcripts, enrolments, registry authority,
challenge workflow authority, Assembly decision authority, integrity case
authority, institutional reporting authority, or third-party ownership rights.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
