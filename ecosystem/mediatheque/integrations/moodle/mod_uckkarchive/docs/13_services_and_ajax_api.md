# 13 — Services and AJAX API

**Path:** `docs/13_services_and_ajax_api.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** External services, AJAX APIs, service-layer rules, request/response contracts, and server-side authority for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines the final service and AJAX API architecture for `mod_uckkarchive`.

The module is:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

The service layer exposes controlled Moodle external functions for:

```text
archive items
media objects
media versions
media collections
media relations
media tags
content advisories
content tag sets
content markers
content reviews
external works
proofs
Kristals
provenance panels
validation panels
restricted views
exports
rendered cards and panels
```

Services are not simple data access endpoints.

Services are authority gates.

---

## 2. Service architecture rule

Every external service must:

```text
resolve Moodle context
validate parameters
require login when needed
check sesskey where required
check capability gates
apply archive/media/content policy
filter output by visibility and restriction
apply privacy and redaction rules
validate lifecycle state
avoid leaking restricted metadata
return stable structured payloads
emit events only after successful state changes
```

No AJAX or external function may bypass:

```text
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
classes/local/context_resolver.php
classes/local/file_area_registry.php
```

---

## 3. Moodle service registration

External service functions are declared in:

```text
db/services.php
```

Service implementation classes are stored in:

```text
classes/external/
```

The service declaration must define:

```text
classname
methodname
classpath
description
type
ajax
capabilities where appropriate
```

AJAX-enabled functions use:

```text
'ajax' => true
```

Service classes must follow Moodle external API conventions:

```text
external_function_parameters
execute
execute_returns
```

---

## 4. Naming convention

Service class filenames use lower_snake_case:

```text
classes/external/get_archive.php
classes/external/add_media.php
classes/external/review_content_marker.php
```

Class names use the Moodle component namespace:

```php
mod_uckkarchive\external\get_archive
mod_uckkarchive\external\add_media
mod_uckkarchive\external\review_content_marker
```

Function naming rule:

```text
get_* = read
search_* = filtered read
add_* = create
update_* = update
delete_* = soft delete or controlled removal
remove_* = relation or membership removal
review_* = human review action
export_* = export creation/request
```

---

## 5. Context resolution

All services must resolve context through:

```text
classes/local/context_resolver.php
```

Supported resolution inputs:

```text
cmid
courseid
archiveid
itemid
mediaid
mediauuid
collectionid
externalworkid
contentmarkerid
```

Resolution must produce, as applicable:

```text
context_module
course
cm
uckkarchive instance
archive item
media object
media version
media collection
content marker
external work
```

Context rule:

```text
Services must not manually reconstruct context resolution in each endpoint.
```

---

## 6. Common request fields

Most services accept one or more of:

```text
cmid
courseid
archiveid
itemid
itemuuid
mediaid
mediauuid
versionid
versionuuid
collectionid
collectionuuid
contentmarkerid
contentmarkeruuid
externalworkid
externalworkuuid
page
perpage
sort
direction
filters
include
```

Pagination defaults:

```text
page = 0
perpage = 20
maximum_perpage = 100
```

Sorting defaults:

```text
sort = timemodified
direction = desc
```

---

## 7. Common response fields

Read/list services return:

```text
status
warnings
data
pagination
permissions
```

Create/update services return:

```text
status
warnings
record
permissions
events
```

Rendered-card services return:

```text
status
warnings
html
data
permissions
```

Export services return:

```text
status
warnings
exportid
exportuuid
state
downloadurl
manifest
```

Error responses must use Moodle exceptions where appropriate:

```text
required_capability_exception
invalid_parameter_exception
moodle_exception
invalid_response_exception
```

---

## 8. Permission payload rule

Service responses may include permission summaries for UI convenience.

Example:

```json
{
  "permissions": {
    "canview": true,
    "canedit": false,
    "candelete": false,
    "canexport": true,
    "canviewrestricted": false,
    "canreviewadvisories": false
  }
}
```

Permission summaries are not authority.

The server must re-check policy on every action.

---

## 9. Archive service files

```text
classes/external/get_archive.php
classes/external/get_archive_items.php
classes/external/get_archive_item.php
classes/external/get_archive_item_card.php
classes/external/get_proofs.php
classes/external/get_provenance_panel.php
classes/external/get_kristal.php
classes/external/get_revisions.php
classes/external/get_restricted_item.php
classes/external/save_item_draft.php
classes/external/add_item.php
classes/external/add_proof.php
classes/external/update_provenance.php
classes/external/validate_item.php
classes/external/revise_item.php
classes/external/create_kristal.php
classes/external/update_kristal.php
```

Archive services must enforce:

```text
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Archive service policy source:

```text
classes/local/archive_policy.php
```

---

## 10. `get_archive`

Path:

```text
classes/external/get_archive.php
```

Purpose:

```text
Return the main archive activity state for the current user.
```

Parameters:

```text
cmid
include
```

Allowed include values:

```text
summary
counts
permissions
recent_items
collections_summary
advisory_summary
export_summary
```

Returns:

```text
archive
counts
recentitems
permissions
warnings
```

Rules:

```text
Only permission-visible summary data is returned.
Restricted counts may be rounded, hidden, or omitted depending on policy.
```

---

## 11. `get_archive_items`

Path:

```text
classes/external/get_archive_items.php
```

Purpose:

```text
Return a filtered, permission-aware list of archive items.
```

Parameters:

```text
cmid
filters
page
perpage
sort
direction
```

Supported filters:

```text
status
validationstate
visibility
type
ownerid
tag
hasmedia
hasadvisory
hasrestricted
provenance
timemodifiedfrom
timemodifiedto
```

Returns:

```text
items
pagination
permissions
warnings
```

Rules:

```text
Restricted items are excluded unless the user has authority.
Fields inside visible items are redacted when needed.
```

---

## 12. `get_archive_item`

Path:

```text
classes/external/get_archive_item.php
```

Purpose:

```text
Return one archive item with permission-filtered metadata.
```

Parameters:

```text
cmid
itemid
itemuuid
include
```

Allowed include values:

```text
files
proofs
media
provenance
revisions
validation
advisories
collections
permissions
```

Returns:

```text
item
files
proofs
media
provenance
revisions
validation
advisories
permissions
warnings
```

Rules:

```text
The service must not return restricted file URLs, restricted notes, private review data, or cultural protocol details without authority.
```

---

## 13. `get_archive_item_card`

Path:

```text
classes/external/get_archive_item_card.php
```

Purpose:

```text
Return rendered HTML and matching structured data for one archive item card.
```

Parameters:

```text
cmid
itemid
itemuuid
```

Returns:

```text
html
item
permissions
warnings
```

Rendering source:

```text
classes/output/archive_item_card.php
templates/archive_item_card.mustache
```

Rules:

```text
The card must be generated from permission-filtered data only.
```

---

## 14. `save_item_draft`

Path:

```text
classes/external/save_item_draft.php
```

Purpose:

```text
Create or update a draft archive item.
```

Parameters:

```text
cmid
itemid
title
summary
content
type
visibility
metadata
```

Returns:

```text
item
permissions
warnings
```

Rules:

```text
Drafts are visible only according to ownership and role policy.
Draft save does not validate the item.
```

---

## 15. `add_item`

Path:

```text
classes/external/add_item.php
```

Purpose:

```text
Create a non-draft archive item or submit a draft archive item.
```

Parameters:

```text
cmid
title
summary
content
type
visibility
metadata
mediauuids
contentmarkeruuids
```

Returns:

```text
item
permissions
warnings
```

Events:

```text
classes/event/archive_item_created.php
```

Rules:

```text
Creation must assign UUID, provenance, status, visibility, owner, and context.
```

---

## 16. `validate_item`

Path:

```text
classes/external/validate_item.php
```

Purpose:

```text
Apply a human validation decision to an archive item.
```

Parameters:

```text
cmid
itemid
validationstate
validationnote
visibility
restrictionstate
```

Allowed validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Returns:

```text
item
validation
permissions
warnings
```

Events:

```text
classes/event/archive_item_validated.php
```

Rules:

```text
Validation is human-final.
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
```

---

## 17. `revise_item`

Path:

```text
classes/external/revise_item.php
```

Purpose:

```text
Create an archive item revision.
```

Parameters:

```text
cmid
itemid
revisiontitle
revisionnote
fields
```

Returns:

```text
item
revision
permissions
warnings
```

Capability:

```text
mod/uckkarchive:reviseitem
```

Rules:

```text
The module does not use mod/uckkarchive:versionitem.
Archive item revision authority is mod/uckkarchive:reviseitem.
```

---

## 18. Media service files

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

Media services must enforce:

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

Media service policy source:

```text
classes/local/media_policy.php
```

---

## 19. `get_media`

Path:

```text
classes/external/get_media.php
```

Purpose:

```text
Return a filtered, permission-aware media library list.
```

Parameters:

```text
cmid
filters
page
perpage
sort
direction
include
```

Supported filters:

```text
mediatype
status
visibility
source
ownerid
tag
contenttag
collectionid
hasadvisory
hasrestricted
hastranscript
hascaption
hasthumbnail
createdfrom
createdto
modifiedfrom
modifiedto
```

Returns:

```text
media
pagination
permissions
warnings
```

Rules:

```text
Media objects are returned only if viewable.
Restricted fields are redacted before response construction.
```

---

## 20. `search_media`

Path:

```text
classes/external/search_media.php
```

Purpose:

```text
Search media metadata, tags, collections, sources, and approved content advisory metadata.
```

Parameters:

```text
cmid
query
filters
page
perpage
```

Returns:

```text
results
pagination
permissions
warnings
```

Rules:

```text
Search must not reveal the existence of restricted media to unauthorized users.
Search indexing must respect content policy and visibility.
```

---

## 21. `get_media_item`

Path:

```text
classes/external/get_media_item.php
```

Purpose:

```text
Return one media object with versions, files, source, advisories, and relations when authorized.
```

Parameters:

```text
cmid
mediaid
mediauuid
include
```

Allowed include values:

```text
versions
files
relations
collections
tags
source
advisories
reviews
permissions
```

Returns:

```text
media
versions
files
relations
collections
tags
source
advisories
permissions
warnings
```

Rules:

```text
Original file download URLs require download authority.
Preview and thumbnail URLs require view authority.
Restricted media requires restricted media authority.
Culturally restricted fields require cultural protocol authority.
```

---

## 22. `get_media_card`

Path:

```text
classes/external/get_media_card.php
```

Purpose:

```text
Return rendered HTML and structured data for one media card.
```

Parameters:

```text
cmid
mediaid
mediauuid
```

Returns:

```text
html
media
permissions
warnings
```

Rendering source:

```text
classes/output/media_card.php
templates/media_card.mustache
```

Rules:

```text
The card may show advisory badges only if the advisory policy allows them.
The card must not show hidden cultural notes to unauthorized users.
```

---

## 23. `add_media`

Path:

```text
classes/external/add_media.php
```

Purpose:

```text
Create a media object and initial media version.
```

Parameters:

```text
cmid
title
description
mediatype
visibility
source
metadata
draftitemid
```

Returns:

```text
media
version
permissions
warnings
```

Events:

```text
classes/event/media_created.php
classes/event/media_version_created.php
```

Rules:

```text
The service creates a stable media UUID.
The service creates a stable media version UUID.
The uploaded file is stored in the appropriate Moodle File API area.
```

---

## 24. `update_media`

Path:

```text
classes/external/update_media.php
```

Purpose:

```text
Update media metadata, lifecycle state, source classification, or visibility.
```

Parameters:

```text
cmid
mediaid
mediauuid
fields
```

Returns:

```text
media
permissions
warnings
```

Events:

```text
classes/event/media_updated.php
```

Rules:

```text
Metadata update does not overwrite original files.
File changes require media versioning.
```

---

## 25. `delete_media`

Path:

```text
classes/external/delete_media.php
```

Purpose:

```text
Soft-delete or controlled-remove a media object.
```

Parameters:

```text
cmid
mediaid
mediauuid
reason
```

Returns:

```text
media
state
warnings
```

Rules:

```text
Default deletion is deleted_soft.
Retention, provenance, export history, validation links, and content advisories must be preserved according to policy.
```

---

## 26. `add_media_version`

Path:

```text
classes/external/add_media_version.php
```

Purpose:

```text
Create a new version for an existing media object.
```

Parameters:

```text
cmid
mediaid
mediauuid
versionnote
draftitemid
metadata
```

Returns:

```text
media
version
permissions
warnings
```

Capability:

```text
mod/uckkarchive:versionmedia
```

Events:

```text
classes/event/media_version_created.php
```

Rules:

```text
Media files are not silently overwritten.
Replacement or correction creates a version record.
```

---

## 27. Media relation services

Files:

```text
classes/external/get_media_relations.php
classes/external/add_media_relation.php
classes/external/remove_media_relation.php
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

Rules:

```text
Relations describe graph meaning.
Relations do not transfer ownership.
Relations must not create unauthorized visibility.
```

---

## 28. Media collection services

Files:

```text
classes/external/get_media_collections.php
classes/external/get_media_collection.php
classes/external/add_media_collection.php
classes/external/update_media_collection.php
classes/external/add_media_to_collection.php
classes/external/remove_media_from_collection.php
```

Collection service rules:

```text
Collections group media objects without duplicating files.
Collection visibility cannot make restricted media public.
Collection export requires export authority for each included object.
```

---

## 29. Media tag services

Files:

```text
classes/external/tag_media.php
classes/external/untag_media.php
```

Rules:

```text
Media tags describe media organization.
Content advisory tags describe suitability, cultural sensitivity, and warning conditions.
Do not merge media tags and content advisory tags into one authority model.
```

---

## 30. Content advisory service files

```text
classes/external/get_content_tags.php
classes/external/get_content_tag_sets.php
classes/external/get_content_markers.php
classes/external/add_content_marker.php
classes/external/update_content_marker.php
classes/external/delete_content_marker.php
classes/external/review_content_marker.php
```

Content advisory services must enforce:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
```

Content policy source:

```text
classes/local/content_policy.php
```

---

## 31. `get_content_tags`

Path:

```text
classes/external/get_content_tags.php
```

Purpose:

```text
Return available content advisory and cultural protocol tags.
```

Parameters:

```text
cmid
tagset
includeinactive
```

Returns:

```text
tags
tagsets
permissions
warnings
```

Rules:

```text
Culturally restricted tag definitions may be hidden or summarized depending on policy.
```

---

## 32. `get_content_tag_sets`

Path:

```text
classes/external/get_content_tag_sets.php
```

Purpose:

```text
Return reusable advisory vocabularies.
```

Canonical tag set examples:

```text
general_advisories
cultural_protocols
classroom_suitability
integrity_sensitive
youth_access
```

Returns:

```text
tagsets
permissions
warnings
```

Rules:

```text
Tag sets support controlled vocabularies.
They do not replace review policy.
```

---

## 33. `get_content_markers`

Path:

```text
classes/external/get_content_markers.php
```

Purpose:

```text
Return content advisory markers for media, archive items, media versions, or external works.
```

Parameters:

```text
cmid
mediaid
mediauuid
itemid
itemuuid
externalworkid
externalworkuuid
filters
```

Returns:

```text
markers
permissions
warnings
```

Supported locator types:

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
Markers must be filtered by review state, audience suitability, visibility, and cultural protocol policy.
```

---

## 34. `add_content_marker`

Path:

```text
classes/external/add_content_marker.php
```

Purpose:

```text
Add a content advisory marker to an internal media object, archive item, media version, or external work.
```

Parameters:

```text
cmid
targettype
targetid
targetuuid
tagkeys
locator_type
locator_start
locator_end
description
severity
audience_suitability
cultural_protocol
review_required
```

Returns:

```text
marker
permissions
warnings
```

Events:

```text
classes/event/content_marker_created.php
```

Rules:

```text
AI may suggest a marker.
Human review is required before advisory status becomes approved.
```

---

## 35. `update_content_marker`

Path:

```text
classes/external/update_content_marker.php
```

Purpose:

```text
Update marker tags, locator, severity, suitability, or description.
```

Parameters:

```text
cmid
contentmarkerid
contentmarkeruuid
fields
```

Returns:

```text
marker
permissions
warnings
```

Rules:

```text
Changing a reviewed marker may return it to pending_review depending on policy.
```

---

## 36. `delete_content_marker`

Path:

```text
classes/external/delete_content_marker.php
```

Purpose:

```text
Retire or soft-delete a content marker.
```

Parameters:

```text
cmid
contentmarkerid
contentmarkeruuid
reason
```

Returns:

```text
marker
state
warnings
```

Rules:

```text
The system preserves review and provenance history.
```

---

## 37. `review_content_marker`

Path:

```text
classes/external/review_content_marker.php
```

Purpose:

```text
Record human review of a content marker, advisory tag, suitability value, or cultural protocol note.
```

Parameters:

```text
cmid
contentmarkerid
contentmarkeruuid
reviewstate
reviewnote
audience_suitability
restriction
```

Allowed review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Returns:

```text
marker
review
permissions
warnings
```

Events:

```text
classes/event/content_marker_reviewed.php
```

Rules:

```text
AI cannot approve cultural protocol access.
AI cannot mark culturally restricted content as safe.
AI cannot close contestations.
```

---

## 38. External work service files

```text
classes/external/get_external_works.php
classes/external/get_external_work.php
classes/external/add_external_work.php
classes/external/update_external_work.php
```

External work services must enforce:

```text
mod/uckkarchive:manageexternalworks
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
```

External work policy source:

```text
classes/local/external_work.php
classes/local/content_policy.php
```

---

## 39. `get_external_works`

Path:

```text
classes/external/get_external_works.php
```

Purpose:

```text
Return a filtered list of referenced external or foreign works.
```

Parameters:

```text
cmid
query
filters
page
perpage
sort
direction
```

Supported work types:

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

Returns:

```text
externalworks
pagination
permissions
warnings
```

Rules:

```text
The archive may reference foreign media without copying it.
The response must not imply UCKK ownership of third-party works.
```

---

## 40. `get_external_work`

Path:

```text
classes/external/get_external_work.php
```

Purpose:

```text
Return one external work reference with permission-filtered metadata and advisory markers.
```

Parameters:

```text
cmid
externalworkid
externalworkuuid
include
```

Allowed include values:

```text
markers
reviews
relations
permissions
```

Returns:

```text
externalwork
markers
relations
permissions
warnings
```

Rules:

```text
External work services may return metadata, teaching notes, locators, and content advisories.
They must not store or expose unauthorized copies of third-party content.
```

---

## 41. `add_external_work`

Path:

```text
classes/external/add_external_work.php
```

Purpose:

```text
Create an external work reference.
```

Parameters:

```text
cmid
title
worktype
creator
publisher
publicationdate
identifier
url
citation
source_ownership
rights_note
metadata
```

Returns:

```text
externalwork
permissions
warnings
```

Events:

```text
classes/event/external_work_created.php
```

Rules:

```text
External work creation stores reference metadata and source classification.
It does not import third-party content unless a separate authorized media object is created.
```

---

## 42. Export service files

```text
classes/external/get_export_preview.php
classes/external/export_items.php
classes/external/export_media.php
classes/external/export_collection.php
classes/external/get_export_status.php
```

Export service policy sources:

```text
classes/local/export_package.php
classes/local/manifest_builder.php
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

Export services must enforce:

```text
mod/uckkarchive:export
mod/uckkarchive:exportmedia
mod/uckkarchive:viewrestricted
mod/uckkarchive:viewrestrictedmedia
mod/uckkarchive:viewculturallyrestricted
```

---

## 43. `get_export_preview`

Path:

```text
classes/external/get_export_preview.php
```

Purpose:

```text
Return a permission-aware preview of what an export would include.
```

Parameters:

```text
cmid
targettype
targetids
options
```

Target types:

```text
archive_items
media_items
media_collection
full_archive
content_advisory_package
external_work_reference_package
```

Returns:

```text
included
excluded
redacted
warnings
permissions
```

Rules:

```text
Preview must show excluded/redacted counts without leaking restricted details.
```

---

## 44. `export_items`

Path:

```text
classes/external/export_items.php
```

Purpose:

```text
Create an export package for archive items.
```

Parameters:

```text
cmid
itemids
format
options
reason
```

Returns:

```text
exportid
exportuuid
state
manifest
downloadurl
warnings
```

Rules:

```text
Export includes manifest.json.
Export respects validation, visibility, restricted state, retention, redaction, content advisories, and cultural protocol rules.
```

---

## 45. `export_media`

Path:

```text
classes/external/export_media.php
```

Purpose:

```text
Create an export package for selected media objects.
```

Parameters:

```text
cmid
mediaids
format
options
reason
```

Returns:

```text
exportid
exportuuid
state
manifest
downloadurl
warnings
```

Rules:

```text
Original files require download/export authority.
Restricted media requires restricted media authority.
Culturally restricted media requires cultural access authority.
External references may export metadata and locators without exporting third-party content.
```

---

## 46. `export_collection`

Path:

```text
classes/external/export_collection.php
```

Purpose:

```text
Create an export package for a media collection.
```

Parameters:

```text
cmid
collectionid
collectionuuid
format
options
reason
```

Returns:

```text
exportid
exportuuid
state
manifest
downloadurl
warnings
```

Rules:

```text
Collection export checks every included media object individually.
Collection membership does not grant export authority.
```

---

## 47. `get_export_status`

Path:

```text
classes/external/get_export_status.php
```

Purpose:

```text
Return the current status of an export package.
```

Parameters:

```text
cmid
exportid
exportuuid
```

Returns:

```text
exportid
exportuuid
state
progress
downloadurl
manifest
warnings
```

Allowed states:

```text
queued
running
ready
failed
expired
purged
```

Rules:

```text
Download URL is returned only if the user still has authority to access the export.
```

---

## 48. Rendered panel services

Rendered panel services return HTML generated through output classes and Mustache templates.

Required panel/card services:

```text
classes/external/get_archive_item_card.php
classes/external/get_media_card.php
classes/external/get_provenance_panel.php
classes/external/get_restricted_item.php
```

Optional rendered payloads may be added for:

```text
content_advisory_panel
external_work_card
media_version_list
media_relation_list
validation_panel
```

Rendered service rule:

```text
Rendered services must return HTML only from already-filtered data.
```

---

## 49. File URL and download rules

Services may return file metadata:

```text
filename
mimetype
filesize
timecreated
timemodified
contenthash where allowed
filearea
itemid
```

Services may return file URLs only when permitted.

Rules:

```text
Preview URLs require view authority.
Thumbnail URLs require view authority.
Original download URLs require download authority.
Export package URLs require export/download authority.
Restricted file URLs require restricted authority.
Culturally restricted file URLs require cultural protocol authority.
```

File delivery remains controlled by:

```text
mod_uckkarchive_pluginfile()
```

in:

```text
lib.php
```

---

## 50. Content advisory examples

A content marker for a film:

```json
{
  "targettype": "external_work",
  "worktype": "film",
  "title": "Maïna",
  "tagkeys": ["sexual_violence"],
  "locator_type": "timecode_range",
  "locator_start": "01:12:30",
  "locator_end": "01:15:10",
  "severity": "strong",
  "audience_suitability": "mature",
  "reviewstate": "approved"
}
```

A content marker for a book:

```json
{
  "targettype": "external_work",
  "worktype": "book",
  "title": "The Body Keeps the Score",
  "tagkeys": ["sexual_violence", "requires_context"],
  "locator_type": "page_range",
  "locator_start": "42",
  "locator_end": "45",
  "severity": "strong",
  "audience_suitability": "guided",
  "reviewstate": "approved"
}
```

Rules:

```text
The marker records advisory metadata and locator information.
It does not copy external content.
It does not ban the work.
It supports responsible teaching, access, review, restriction, and contextualization.
```

---

## 51. AJAX front-end integration

AMD modules call Moodle external services through Moodle’s core AJAX API.

AMD files:

```text
amd/src/archive.js
amd/src/content_advisory.js
amd/src/export.js
amd/src/external_work.js
amd/src/kristal.js
amd/src/media.js
amd/src/media_collection.js
```

AJAX rule:

```text
AMD modules send requests.
External services decide.
```

AMD modules must not:

```text
grant access
infer hidden permissions
construct restricted URLs
approve validation
approve content advisory review
approve cultural protocol access
decide export authority
```

---

## 52. Security rules

Every service must protect against:

```text
context confusion
ID guessing
UUID guessing
capability bypass
hidden metadata leakage
restricted file URL leakage
culturally restricted note leakage
cross-course access
cross-module access
unvalidated draft publication
unauthorized export
unauthorized external work modification
unauthorized content advisory review
```

Security rule:

```text
The service layer must treat all input as untrusted.
```

---

## 53. Privacy and redaction rules

Services must apply privacy and redaction rules before response construction.

Redactable fields include:

```text
private notes
review notes
cultural protocol notes
restricted metadata
source identifiers
user identifiers
file hashes
external work rights notes
integrity-sensitive references
download URLs
export URLs
```

Privacy rule:

```text
If the user cannot view a field, the field must be omitted, redacted, or summarized before output.
```

---

## 54. Events from services

Services that create or change state emit events after successful transaction completion.

Event classes:

```text
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
No event is emitted for failed or unauthorized service calls.
```

---

## 55. Transactions

State-changing services should use database transactions when writing related records.

Examples:

```text
media object + first version + file reference
archive item + provenance + media relations
content marker + review state + provenance
export record + manifest + package file
collection + collection items
```

Transaction rule:

```text
Partial state must not be committed when a required related write fails.
```

---

## 56. Caching

Read services may use caching only when safe.

Cache-sensitive data:

```text
permissions
visibility
restricted state
content advisory review state
cultural protocol access
file URLs
export URLs
```

Caching rule:

```text
Do not cache permission-filtered responses across users unless the cache key includes all relevant access dimensions.
```

---

## 57. Validation

Parameter validation must include:

```text
type checks
required fields
allowed enum values
context existence
record existence
record belongs to context
UUID format
JSON metadata shape
file area validity
locator type validity
tag key validity
visibility validity
status validity
review state validity
```

Validation source helpers:

```text
classes/local/metadata_validator.php
classes/local/uuid.php
classes/local/file_area_registry.php
```

---

## 58. Stable identifiers

Services may accept local IDs or UUIDs where appropriate.

Rules:

```text
Local ids are used for Moodle runtime convenience.
UUIDs are used for portability, restore, duplication, and export identity.
Responses should include UUIDs for archive, media, version, content marker, external work, collection, and export records.
```

---

## 59. Versioning rules

Archive item revision:

```text
mod/uckkarchive:reviseitem
```

Media versioning:

```text
mod/uckkarchive:versionmedia
```

Removed capability:

```text
mod/uckkarchive:versionitem
```

Rules:

```text
Do not define or require mod/uckkarchive:versionitem.
Do not silently overwrite media files.
Do not silently overwrite validation history.
```

---

## 60. Final service rule

```text
External services are the controlled API surface of mod_uckkarchive.

They expose archive, media, content advisory, external work, validation, provenance,
revision, and export behavior through Moodle-native external functions.

They must resolve context, validate input, check capabilities, apply policy,
filter output, protect restricted data, emit events only after successful changes,
and return stable structured payloads suitable for AMD and server-rendered UI.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
