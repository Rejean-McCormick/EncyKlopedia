# 14 — Events and Audit

**Path:** `docs/14_events_and_audit.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Moodle events, event classes, audit behavior, observer behavior, revision records, privacy-safe logging, content advisory audit, cultural protocol audit, media audit, and export audit.

---

## 1. Purpose

This document defines the final event and audit architecture for `mod_uckkarchive`.

`mod_uckkarchive` is a self-contained Moodle activity module for:

```text
archive memory
media library management
content advisories
cultural sensitivity tags
external/foreign media references
provenance
validation
revision history
export packages
```

Events and audit records must make important actions traceable without exposing restricted content.

---

## 2. Core audit decision

`mod_uckkarchive` uses two complementary audit layers:

```text
Moodle Events API = activity log, user action log, system event stream
uckkarchive_rev = domain revision history for meaningful state changes
```

Moodle events answer:

```text
who did something
where it happened
when it happened
what kind of action happened
which object was affected
```

Revision records answer:

```text
what changed
why it changed
which domain state changed
which version is current
which record supersedes another
how provenance, validation, restriction, or advisory state evolved
```

Both layers are required.

---

## 3. Event architecture rule

Events audit successful actions.

Events do not authorize actions.

Events do not validate actions.

Events do not reveal restricted content.

Canonical rule:

```text
Authorization happens before events.
Domain state changes happen before events.
Events record the result.
```

An event must not be triggered for a failed permission check unless Moodle core security logging requires a separate safe event.

---

## 4. Required event files

Required event classes:

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

Required event registration file:

```text
db/events.php
```

Required observer file:

```text
classes/observer.php
```

Events must follow Moodle namespacing:

```text
\mod_uckkarchive\event\event_name
```

---

## 5. Event class naming

Event class names use lowercase words separated by underscores.

Examples:

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

Each class path must match the class name:

```text
classes/event/media_created.php
```

Class:

```php
namespace mod_uckkarchive\event;

class media_created extends \core\event\base {
}
```

---

## 6. Moodle event base requirements

Every event class must define:

```text
init()
get_name()
get_description()
get_url()
get_objectid_mapping()
get_other_mapping()
```

Where appropriate, event classes also define:

```text
validate_data()
```

Each event must set:

```text
context
objectid
userid
relateduserid when applicable
courseid when applicable
other when needed
```

The event `other` payload must be minimal and privacy-safe.

---

## 7. Event privacy rule

Events must not include:

```text
raw media content
file contents
full archive item content
private notes
cultural protocol notes
restricted advisory notes
restricted integrity details
unredacted personal data
unredacted proof details
full manifest JSON
private source URLs
confidential review text
```

Events may include:

```text
record id
record uuid
record type
status key
visibility key
validation state key
media type key
version number
export type
collection id
marker id
external work id
safe tag key
safe relation type
```

Rule:

```text
Events identify actions.
Events do not carry sensitive payloads.
```

---

## 8. Audit authority layers

Audit behavior is divided across these layers:

| Layer | Role |
|---|---|
| Moodle Events API | Records action occurrence in Moodle logs. |
| `uckkarchive_rev` | Records domain-level change history. |
| `uckkarchive_prov` | Records source, origin, actor, and provenance. |
| `uckkarchive_export` | Records export request, status, manifest, and expiry. |
| `uckkarchive_content_review` | Records human review of content advisories and cultural protocol markers. |
| Moodle File API | Stores files and supports file access logging through Moodle. |
| Moodle Privacy API | Exports/deletes/anonymises user-linked data according to policy. |

No layer replaces the others.

---

## 9. Archive events

### `archive_viewed`

Path:

```text
classes/event/archive_viewed.php
```

Triggered when a user views the main activity/archive page.

Required payload:

```text
contextid
courseid
objectid = uckkarchive.id
userid
other.archiveuuid
```

Must not include:

```text
item content
restricted item count details
private user-specific notes
```

### `archive_item_created`

Path:

```text
classes/event/archive_item_created.php
```

Triggered when an archive item is created.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_item.id
userid
other.archiveid
other.archiveuuid
other.itemuuid
other.itemtype
other.status
other.visibility
other.validationstate
```

Associated revision:

```text
uckkarchive_rev.revisiontype = item_created
```

### `archive_item_validated`

Path:

```text
classes/event/archive_item_validated.php
```

Triggered when a human validation action changes validation state.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_item.id
userid = validator
relateduserid = item owner when applicable
other.itemuuid
other.previousvalidationstate
other.newvalidationstate
other.visibility
```

Associated revision:

```text
uckkarchive_rev.revisiontype = item_validation_changed
```

Validation rule:

```text
Validation is human-final.
AI cannot trigger final validation events as the validating authority.
```

### `archive_item_revised`

Path:

```text
classes/event/archive_item_revised.php
```

Triggered when an archive item receives a new revision.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_item.id
userid
other.itemuuid
other.revisionuuid
other.revisiontype
other.versionno
```

Associated revision:

```text
uckkarchive_rev.revisiontype = item_revised
```

### `archive_item_exported`

Path:

```text
classes/event/archive_item_exported.php
```

Triggered when an archive item is included in an export package.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_export.id
userid
other.exportuuid
other.itemuuid
other.exporttype
other.redactionmode
```

Must not include:

```text
manifestjson
file paths
restricted content
```

---

## 10. Media events

### `media_created`

Path:

```text
classes/event/media_created.php
```

Triggered when a first-class media object is created.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_media.id
userid
other.mediauuid
other.mediatype
other.status
other.visibility
other.audiencesuitability
```

Associated revision:

```text
uckkarchive_rev.revisiontype = media_created
```

### `media_updated`

Path:

```text
classes/event/media_updated.php
```

Triggered when media metadata, status, visibility, suitability, rights, source, or restriction state changes.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_media.id
userid
other.mediauuid
other.revisionuuid
other.status
other.visibility
other.audiencesuitability
```

Associated revision:

```text
uckkarchive_rev.revisiontype = media_updated
```

### `media_version_created`

Path:

```text
classes/event/media_version_created.php
```

Triggered when a media version is created.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_media_version.id
userid
other.mediaid
other.mediauuid
other.mediaversionuuid
other.versionno
other.versiontype
other.filearea
```

Associated revision:

```text
uckkarchive_rev.revisiontype = media_version_created
```

Must not include:

```text
file content
direct file URL
contenthash if restricted
private derivative generation details
```

### `media_collection_created`

Path:

```text
classes/event/media_collection_created.php
```

Triggered when a media collection is created.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_media_collection.id
userid
other.collectionuuid
other.collectiontype
other.status
other.visibility
other.audiencesuitability
```

Associated revision:

```text
uckkarchive_rev.revisiontype = media_collection_created
```

### `media_exported`

Path:

```text
classes/event/media_exported.php
```

Triggered when one or more media objects are included in an export.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_export.id
userid
other.exportuuid
other.mediauuid
other.exporttype
other.redactionmode
```

For multi-media exports, the event may include count values but must not include a full media list when the list is sensitive.

Safe count fields:

```text
other.mediacount
other.collectioncount
other.markercount
other.externalworkcount
```

---

## 11. Content advisory events

### `content_marker_created`

Path:

```text
classes/event/content_marker_created.php
```

Triggered when a content advisory or cultural protocol marker is created.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_content_marker.id
userid
other.markeruuid
other.tagkey
other.locator_type
other.reviewstate
other.visibility
other.audiencesuitability
```

May include one target reference:

```text
other.mediauuid
other.itemuuid
other.externalworkuuid
```

Must not include:

```text
advisorytext when restricted
cultural protocol note
review note
full locator text if it exposes sensitive content
external source private URL
```

Associated revision:

```text
uckkarchive_rev.revisiontype = content_marker_created
```

### `content_marker_reviewed`

Path:

```text
classes/event/content_marker_reviewed.php
```

Triggered when a human reviewer changes advisory/cultural review state.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_content_review.id
userid = reviewer
other.markeruuid
other.reviewuuid
other.previousreviewstate
other.newreviewstate
other.decision
other.visibility
other.audiencesuitability
```

Associated records:

```text
uckkarchive_content_review
uckkarchive_rev.revisiontype = content_marker_reviewed
```

Review rule:

```text
AI may suggest tags or markers.
Human review is required before advisory status becomes approved.
Cultural protocol review cannot be replaced by AI.
```

---

## 12. External work events

### `external_work_created`

Path:

```text
classes/event/external_work_created.php
```

Triggered when an external/foreign work reference is created.

Required payload:

```text
contextid
courseid
objectid = uckkarchive_external_work.id
userid
other.externalworkuuid
other.worktype
other.sourceownership
other.visibility
other.audiencesuitability
```

Must not imply ownership over third-party work.

Must not include:

```text
full copyrighted content
private acquisition notes
restricted source URL
confidential review notes
```

Associated revision:

```text
uckkarchive_rev.revisiontype = external_work_created
```

---

## 13. Event-to-table mapping

| Event | Primary table | Revision table? | Additional audit table |
|---|---|---:|---|
| `archive_viewed` | `uckkarchive` | No | Moodle log only |
| `archive_item_created` | `uckkarchive_item` | Yes | `uckkarchive_prov` when applicable |
| `archive_item_validated` | `uckkarchive_item` | Yes | `uckkarchive_prov` when applicable |
| `archive_item_revised` | `uckkarchive_item` | Yes | — |
| `archive_item_exported` | `uckkarchive_export` | Yes | export manifest |
| `media_created` | `uckkarchive_media` | Yes | `uckkarchive_media_source` when applicable |
| `media_updated` | `uckkarchive_media` | Yes | — |
| `media_version_created` | `uckkarchive_media_version` | Yes | Moodle File API |
| `media_collection_created` | `uckkarchive_media_collection` | Yes | — |
| `media_exported` | `uckkarchive_export` | Yes | export manifest |
| `content_marker_created` | `uckkarchive_content_marker` | Yes | — |
| `content_marker_reviewed` | `uckkarchive_content_review` | Yes | `uckkarchive_content_review` |
| `external_work_created` | `uckkarchive_external_work` | Yes | `uckkarchive_media_source` when applicable |

---

## 14. Event trigger points

Events are triggered by server-side code only.

Allowed trigger locations:

```text
classes/local/*
classes/external/*
root controllers after successful state change
scheduled tasks after successful state change
restore code only when restore creates meaningful domain records and Moodle event policy allows it
```

Forbidden trigger locations:

```text
templates
AMD JavaScript
CSS
language files
client-side-only handlers
```

Rule:

```text
Client-side UI may request an action.
Server-side code performs the action.
Server-side code triggers the event.
```

---

## 15. External service event behavior

External services must trigger the same events as page controllers when they produce the same successful state change.

Examples:

```text
classes/external/add_media.php -> media_created
classes/external/update_media.php -> media_updated
classes/external/add_media_version.php -> media_version_created
classes/external/add_content_marker.php -> content_marker_created
classes/external/review_content_marker.php -> content_marker_reviewed
classes/external/add_external_work.php -> external_work_created
classes/external/export_media.php -> media_exported
classes/external/export_items.php -> archive_item_exported
```

Rule:

```text
The audit trail must not depend on whether the action came from UI, AJAX, service, task, or controller.
```

---

## 16. Observer architecture

Observer registration lives in:

```text
db/events.php
```

Observer methods live in:

```text
classes/observer.php
```

Observer methods may:

```text
schedule derivative generation
schedule thumbnail generation
schedule export processing
schedule search index rebuild
invalidate render caches
enqueue notification tasks
update safe aggregate counters
```

Observer methods must not:

```text
grant access
validate records
override policy
reveal restricted data
perform long blocking work
copy restricted content to public areas
create external authority records
```

Observer rule:

```text
Observers react to events.
Observers do not become the authority layer.
```

---

## 17. Scheduled task interaction

Events may cause scheduled work.

Relevant tasks:

```text
classes/task/generate_archive_exports.php
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
classes/task/validate_pending_items.php
```

Task audit rule:

```text
Scheduled tasks must produce audit records when they create or modify domain state.
Scheduled tasks must not produce duplicate audit records when they only rebuild derived caches.
```

Examples:

| Task action | Event required? |
|---|---:|
| Generate thumbnail version | Yes, `media_version_created` |
| Generate preview derivative | Yes, `media_version_created` |
| Rebuild search index only | No |
| Purge expired export package | Yes, if export state changes to `purged` |
| Mark export failed | Yes, export revision/event if implemented |
| Rebuild content marker index only | No |

---

## 18. Revision audit model

Revision records are stored in:

```text
uckkarchive_rev
```

Revision records are required for meaningful changes to:

```text
archive item content
archive item status
archive item visibility
validation state
restricted state
media metadata
media status
media visibility
media source
media version
collection membership
content marker
content advisory review state
cultural protocol state
external work metadata
export status
redaction state
retention class
```

Revision records must include:

```text
archiveid
target object reference
revisiontype
versionno when applicable
reason
actor
timestamp
safe before/after summary when appropriate
```

Revision records must not store unredacted sensitive data in `beforejson` or `afterjson`.

---

## 19. Provenance audit model

Provenance records are stored in:

```text
uckkarchive_prov
```

Provenance records are required when an object is:

```text
created from human input
imported
generated by system
AI-assisted
copied from another archive
linked to external work
derived from media
associated with Assembly material
associated with challenge material
associated with integrity material
```

Provenance events and revision events may reference provenance IDs but must not duplicate the full provenance statement when it is sensitive.

---

## 20. Content advisory audit model

Content advisory audit must track:

```text
who created the marker
who reviewed the marker
which tag was applied
which tag set was used
which work/media/item/location was marked
which review state was assigned
which suitability value was assigned
whether cultural restriction applies
whether access requires context or review
```

Content advisory audit must not expose:

```text
restricted cultural notes
confidential review notes
unredacted trauma descriptions
private teaching notes
private URLs
full copyrighted excerpts
```

Rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 21. Cultural protocol audit model

Cultural protocol audit applies to tags and markers such as:

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

Cultural protocol events must be especially minimal.

Allowed event payload:

```text
marker id
marker uuid
tag key
review state
visibility
audience suitability
object id
context id
```

Forbidden event payload:

```text
private protocol explanation
names of community authorities unless already public and authorized
restricted knowledge detail
ceremonial detail
sacred content description
```

---

## 22. External/foreign media audit model

External/foreign media audit applies to:

```text
films
books
articles
podcasts
websites
external videos
external images
public archive items
third-party PDFs
other external works
```

Audit must record:

```text
external work creation
external work metadata updates
media source creation
media source updates
content markers attached to external works
review decisions for external works
exports that include external work references
```

Audit must not imply:

```text
UCKK owns the external work
UCKK has copied the external work
UCKK has permission beyond recorded rights/source fields
```

---

## 23. Export audit model

Exports are audited through:

```text
uckkarchive_export
Moodle event classes
uckkarchive_rev
manifest.json
```

Export audit must record:

```text
export requester
export type
export scope
export redaction mode
export status
export timestamp
included archive item UUIDs
included media UUIDs
included media version UUIDs
included external work UUIDs
included content marker UUIDs
manifest hash when available
expiry timestamp
purge timestamp when applicable
```

Export events must not include full manifest JSON.

Export package files use Moodle File API areas:

```text
export_package
export_manifest
```

---

## 24. File access audit

File access is governed through:

```text
mod_uckkarchive_pluginfile()
classes/local/file_area_registry.php
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

File access checks must consider:

```text
context
capability
file area
itemid
mediaid
media version id
content marker restrictions
visibility
media status
archive item status
validation state
redaction state
retention state
audience suitability
restricted cultural state
restricted integrity state
```

File access events should not expose raw file details when files are restricted.

---

## 25. Event payload patterns

### Safe `other` payload pattern for archive items

```php
[
    'archiveid' => $archiveid,
    'archiveuuid' => $archiveuuid,
    'itemuuid' => $itemuuid,
    'itemtype' => $itemtype,
    'status' => $status,
    'visibility' => $visibility,
    'validationstate' => $validationstate,
]
```

### Safe `other` payload pattern for media

```php
[
    'archiveid' => $archiveid,
    'mediauuid' => $mediauuid,
    'mediatype' => $mediatype,
    'status' => $status,
    'visibility' => $visibility,
    'audiencesuitability' => $audiencesuitability,
]
```

### Safe `other` payload pattern for media versions

```php
[
    'archiveid' => $archiveid,
    'mediauuid' => $mediauuid,
    'mediaversionuuid' => $mediaversionuuid,
    'versionno' => $versionno,
    'versiontype' => $versiontype,
    'filearea' => $filearea,
]
```

### Safe `other` payload pattern for content markers

```php
[
    'archiveid' => $archiveid,
    'markeruuid' => $markeruuid,
    'tagkey' => $tagkey,
    'locator_type' => $locatortype,
    'reviewstate' => $reviewstate,
    'visibility' => $visibility,
    'audiencesuitability' => $audiencesuitability,
]
```

### Safe `other` payload pattern for external works

```php
[
    'archiveid' => $archiveid,
    'externalworkuuid' => $externalworkuuid,
    'worktype' => $worktype,
    'sourceownership' => $sourceownership,
    'visibility' => $visibility,
    'audiencesuitability' => $audiencesuitability,
]
```

---

## 26. Redaction and restricted audit

When an object is restricted, redacted, culturally restricted, or integrity restricted, the event still records that an action happened.

The event must not reveal restricted detail.

Safe restricted values:

```text
restricted = true
restrictedtype = restricted_cultural
restrictedtype = restricted_integrity
redactionstate = partial
redactionstate = full
```

Unsafe restricted values:

```text
full explanation of the restricted material
sensitive evidence content
private cultural protocol details
trauma description
confidential notes
hidden external source
```

---

## 27. Event URLs

`get_url()` should point to the safest relevant UI page.

Examples:

| Event | URL target |
|---|---|
| `archive_viewed` | `view.php?id={cmid}` |
| `archive_item_created` | `item.php?id={cmid}&itemid={itemid}` |
| `archive_item_validated` | `validate.php?id={cmid}&itemid={itemid}` |
| `archive_item_revised` | `item.php?id={cmid}&itemid={itemid}` |
| `archive_item_exported` | `export.php?id={cmid}&exportid={exportid}` |
| `media_created` | `media.php?id={cmid}&mediaid={mediaid}` |
| `media_updated` | `media.php?id={cmid}&mediaid={mediaid}` |
| `media_version_created` | `media.php?id={cmid}&mediaid={mediaid}` |
| `media_collection_created` | `media.php?id={cmid}&collectionid={collectionid}` |
| `media_exported` | `export.php?id={cmid}&exportid={exportid}` |

URL access must still be checked by the destination controller.

---

## 28. Object mapping

Each event class must define restore mappings.

Examples:

```text
archive_item_created -> uckkarchive_item
archive_item_validated -> uckkarchive_item
archive_item_revised -> uckkarchive_item
archive_item_exported -> uckkarchive_export
media_created -> uckkarchive_media
media_updated -> uckkarchive_media
media_version_created -> uckkarchive_media_version
media_collection_created -> uckkarchive_media_collection
media_exported -> uckkarchive_export
content_marker_created -> uckkarchive_content_marker
content_marker_reviewed -> uckkarchive_content_review
external_work_created -> uckkarchive_external_work
```

`get_objectid_mapping()` must return the matching table name where Moodle supports mapping.

`get_other_mapping()` must map IDs stored in `other` only when they are local database IDs.

UUIDs in `other` do not require Moodle restore ID mapping.

---

## 29. Backup and restore interaction

Backup and restore must preserve:

```text
events only through Moodle log policy where applicable
domain revision records
provenance records
content review records
export records
media version records
relation records
external work records
```

Restore must not replay events as if users performed new actions unless Moodle restore behavior explicitly requires new restore-time events.

Restore must preserve data audit.

Restore must not create false human validation events.

Restore must not create false content review events.

---

## 30. Privacy API interaction

Privacy provider must account for user links in:

```text
events through Moodle log system
uckkarchive_rev.createdby
uckkarchive_prov.actorid
uckkarchive_export.userid
uckkarchive_content_review.reviewedby
createdby fields
modifiedby fields
validatedby fields
reviewedby fields
```

Privacy export must distinguish:

```text
user-authored content
user action metadata
system logs
third-party external work metadata
restricted cultural protocol data
restricted integrity data
```

Privacy deletion/anonymisation must not destroy institutional audit records when retention requires preservation, but must redact/anonymise personal fields according to policy.

---

## 31. Language strings

Each event requires English and French language strings in:

```text
lang/en/uckkarchive.php
lang/fr/uckkarchive.php
```

Required string keys follow this pattern:

```text
eventarchiveviewed
eventarchiveitemcreated
eventarchiveitemvalidated
eventarchiveitemrevised
eventarchiveitemexported
eventmediacreated
eventmediaupdated
eventmediaversioncreated
eventmediacollectioncreated
eventmediaexported
eventcontentmarkercreated
eventcontentmarkerreviewed
eventexternalworkcreated
```

Language strings must not expose sensitive details.

---

## 32. Event testing

Tests must cover:

```text
event class creation
required payload fields
safe payload behavior
context assignment
objectid assignment
URL generation
object mapping
event trigger on successful action
no event trigger on failed permission check
revision record creation
content review event behavior
restricted/cultural payload redaction
external work event behavior
export event behavior
```

Required test files:

```text
tests/archive_test.php
tests/media_library_test.php
tests/content_advisory_test.php
tests/external_work_test.php
tests/export_test.php
tests/privacy_provider_test.php
tests/services_test.php
```

Required Behat files:

```text
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

---

## 33. Event implementation checklist for code generation

Every event class must include:

```text
namespace mod_uckkarchive\event
defined('MOODLE_INTERNAL') || die()
class extends \core\event\base
protected function init()
public static function get_name()
public function get_description()
public function get_url()
public static function get_objectid_mapping()
public static function get_other_mapping()
protected function validate_data()
```

Every trigger call must provide:

```text
context
objectid
userid
courseid when applicable
relateduserid when applicable
other safe payload
```

Every trigger call must occur after:

```text
capability check
policy check
database write
file write when applicable
revision record creation when applicable
```

---

## 34. Forbidden event behavior

The implementation must not:

```text
trigger events from templates
trigger events from AMD JavaScript
trigger events before state changes succeed
store full content in event other payload
store raw file content in event other payload
store private cultural protocol notes in event other payload
store private review notes in event other payload
store full manifest JSON in event other payload
use events as permission checks
use observers as authority layers
create false validation events during restore
create false review events during restore
```

---

## 35. Final event and audit rule

```text
mod_uckkarchive events make actions visible to Moodle.
mod_uckkarchive revisions make domain change history durable.
mod_uckkarchive provenance explains origin.
mod_uckkarchive content reviews preserve human advisory decisions.
mod_uckkarchive export records preserve package history.

Events identify safe facts about successful actions.
Events do not reveal restricted content.
Events do not replace policy.
Events do not replace revisions.
Events do not replace provenance.
Events do not transfer authority to or from external plugins.

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
```
