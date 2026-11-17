# 07 — Permissions and Roles

**Path:** `docs/07_permissions_and_roles.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Capabilities, roles, access rules, restricted access, media permissions, content advisory permissions, and server-side policy enforcement for the self-contained UCKK Archive and Media Library Moodle activity module.

---

## 1. Purpose

This document defines the final permission and role model for `mod_uckkarchive`.

`mod_uckkarchive` is a Moodle-native activity module with a self-contained archive, media library, and content advisory system.

The module uses Moodle capabilities as access gates.

The module uses internal policy classes as authority enforcement.

Canonical rule:

```text
Capabilities are gates.
Policy classes make final access decisions.
Templates, AMD, forms, and controllers do not authorize access.
```

---

## 2. Permission architecture

`mod_uckkarchive` has three permission layers:

```text
Moodle capability layer
module policy layer
record state layer
```

### 2.1 Moodle capability layer

Moodle capabilities answer:

```text
Can this user attempt this kind of action in this context?
```

Examples:

```text
Can view archive activity?
Can add media?
Can validate archive item?
Can download media?
Can review content advisories?
```

### 2.2 Module policy layer

Policy classes answer:

```text
Can this specific user perform this specific action on this specific record right now?
```

Policy classes include:

```text
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

### 2.3 Record state layer

Record state affects permissions.

Examples:

```text
draft
submitted
active
validated
published
restricted
restricted_integrity
restricted_cultural
contested
archived
deleted_soft
```

A capability does not override record state.

---

## 3. Canonical policy classes

Permission logic must be centralized.

```text
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

### 3.1 Archive policy

`classes/local/archive_policy.php` controls:

```text
archive activity access
archive item visibility
archive item editing
archive item validation
archive item revision
archive item restriction
archive item export
proof visibility
Kristal visibility
provenance panel visibility
revision history visibility
```

### 3.2 Media policy

`classes/local/media_policy.php` controls:

```text
media visibility
media creation
media metadata editing
media deletion
media download
media original-file access
media derivative access
media preview access
media thumbnail access
media versioning
media export
media collection access
restricted media access
```

### 3.3 Content policy

`classes/local/content_policy.php` controls:

```text
content advisory visibility
content advisory management
content marker creation
content marker review
content tag set management
cultural protocol visibility
culturally restricted access
external work management
audience suitability enforcement
content review authority
```

---

## 4. Canonical archive capabilities

Archive capabilities:

```text
mod/uckkarchive:addinstance
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

| Capability | Purpose |
|---|---|
| `mod/uckkarchive:addinstance` | Add a UCKK Archive activity to a Moodle course. |
| `mod/uckkarchive:view` | View the activity and non-restricted archive records. |
| `mod/uckkarchive:additem` | Add archive items, proofs, draft records, and archive submissions. |
| `mod/uckkarchive:validateitem` | Validate, reject, contest, restrict, or mark archive review state. |
| `mod/uckkarchive:reviseitem` | Revise archive item content, metadata, provenance, visibility, or version state. |
| `mod/uckkarchive:viewrestricted` | View archive records restricted by privacy, integrity, or elevated review rules. |
| `mod/uckkarchive:export` | Generate archive exports according to export policy. |

Archive versioning uses:

```text
mod/uckkarchive:reviseitem
```

The module does not use:

```text
mod/uckkarchive:versionitem
```

---

## 5. Canonical media capabilities

Media capabilities:

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

| Capability | Purpose |
|---|---|
| `mod/uckkarchive:viewmedia` | View media library records visible to the user. |
| `mod/uckkarchive:addmedia` | Add new media objects and initial media files. |
| `mod/uckkarchive:editmedia` | Edit media metadata, tags, source data, advisory visibility, and descriptive fields. |
| `mod/uckkarchive:deletemedia` | Soft-delete or retire media according to policy. |
| `mod/uckkarchive:downloadmedia` | Download media files when media policy permits it. |
| `mod/uckkarchive:versionmedia` | Add new media versions, replacements, derivatives, captions, transcripts, or corrected files. |
| `mod/uckkarchive:managemediacollections` | Create and manage media collections and collection membership. |
| `mod/uckkarchive:exportmedia` | Export media records, versions, collections, manifests, and allowed files. |
| `mod/uckkarchive:viewrestrictedmedia` | View restricted media, culturally restricted media, or elevated-access media when policy permits it. |

Media versioning uses:

```text
mod/uckkarchive:versionmedia
```

---

## 6. Canonical content advisory capabilities

Content advisory capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:manageexternalworks
```

| Capability | Purpose |
|---|---|
| `mod/uckkarchive:viewadvisories` | View content advisories, content warnings, cultural notes, and audience suitability notes visible to the user. |
| `mod/uckkarchive:manageadvisories` | Create and edit advisory tags, tag sets, content markers, and advisory metadata. |
| `mod/uckkarchive:reviewadvisories` | Review, approve, contest, retire, or confirm content markers and advisory classifications. |
| `mod/uckkarchive:viewculturallyrestricted` | View culturally restricted content, markers, protocol notes, or restricted advisory details when policy permits it. |
| `mod/uckkarchive:manageexternalworks` | Add and edit external works, foreign media references, source metadata, and locator metadata. |

Content advisory rule:

```text
A content advisory does not ban media.
It defines conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 7. Capability categories

Capabilities are grouped into these domains:

```text
activity administration
archive viewing
archive creation
archive validation
archive revision
restricted archive access
archive export
media viewing
media creation
media editing
media deletion
media download
media versioning
media collection management
media export
restricted media access
content advisory visibility
content advisory management
content advisory review
cultural restriction access
external work management
```

---

## 8. Default Moodle archetypes

Capabilities should map to Moodle archetypes conservatively.

### 8.1 Student / participant

Typical participant permissions:

```text
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:viewadvisories
```

Participant access remains subject to policy.

A participant may not automatically download originals, view restricted media, review advisories, validate archive items, or export packages.

### 8.2 Teacher / mentor

Typical teacher or mentor permissions:

```text
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:editmedia
mod/uckkarchive:downloadmedia
mod/uckkarchive:versionmedia
mod/uckkarchive:managemediacollections
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
```

Teacher/mentor authority does not automatically include culturally restricted access or integrity-restricted access.

### 8.3 Editing teacher / manager

Typical manager permissions:

```text
mod/uckkarchive:addinstance
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:editmedia
mod/uckkarchive:deletemedia
mod/uckkarchive:downloadmedia
mod/uckkarchive:versionmedia
mod/uckkarchive:managemediacollections
mod/uckkarchive:exportmedia
mod/uckkarchive:viewrestrictedmedia
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:manageexternalworks
```

Culturally restricted access should still be separately controlled.

### 8.4 Administrator

Administrators may configure the module and assign roles.

Administrative capability does not mean the UI should expose every restricted cultural detail by default.

Policy classes may still require explicit access context, audit, or protocol confirmation for sensitive content.

---

## 9. Functional roles

The module supports functional roles through Moodle role assignments and capability combinations.

Functional role names are descriptive.

They do not replace Moodle roles.

### 9.1 Viewer

Can view public, course, or permitted archive/media records.

Typical capabilities:

```text
mod/uckkarchive:view
mod/uckkarchive:viewmedia
mod/uckkarchive:viewadvisories
```

### 9.2 Contributor

Can add archive items and media.

Typical capabilities:

```text
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:viewadvisories
```

### 9.3 Mentor

Can revise items, curate collections, edit metadata, and manage ordinary content advisories.

Typical capabilities:

```text
mod/uckkarchive:reviseitem
mod/uckkarchive:editmedia
mod/uckkarchive:downloadmedia
mod/uckkarchive:versionmedia
mod/uckkarchive:managemediacollections
mod/uckkarchive:manageadvisories
```

### 9.4 Archivist

Can validate records, manage provenance, curate archive memory, export allowed packages, and review records.

Typical capabilities:

```text
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:export
mod/uckkarchive:editmedia
mod/uckkarchive:versionmedia
mod/uckkarchive:exportmedia
mod/uckkarchive:reviewadvisories
```

### 9.5 Media librarian

Can manage media objects, media versions, media collections, media relations, tags, thumbnails, derivatives, captions, transcripts, and media exports.

Typical capabilities:

```text
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:editmedia
mod/uckkarchive:deletemedia
mod/uckkarchive:downloadmedia
mod/uckkarchive:versionmedia
mod/uckkarchive:managemediacollections
mod/uckkarchive:exportmedia
mod/uckkarchive:manageadvisories
```

### 9.6 Content reviewer

Can review content advisories, content markers, cultural notes, and suitability levels.

Typical capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
```

### 9.7 Cultural protocol reviewer

Can view and review culturally restricted markers, protocols, and advisory notes.

Typical capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
```

This role should be assigned deliberately.

It should not be bundled automatically into ordinary teacher or manager roles.

### 9.8 External work curator

Can create and update external works, source records, foreign media references, and locator metadata.

Typical capabilities:

```text
mod/uckkarchive:manageexternalworks
mod/uckkarchive:manageadvisories
mod/uckkarchive:viewadvisories
```

### 9.9 Integrity reviewer

Can view integrity-restricted archive/media records only when integrity-specific policy allows it.

Typical capabilities:

```text
mod/uckkarchive:viewrestricted
mod/uckkarchive:viewrestrictedmedia
mod/uckkarchive:viewadvisories
```

Integrity-specific archive features require `tool_uckkintegrity` when case-linked functionality is active.

Ordinary archive and media access must not require `tool_uckkintegrity`.

---

## 10. Access decision inputs

Every policy decision may use:

```text
user id
course id
course module id
context id
Moodle capability
record owner
record creator
record modifier
record validator
record reviewer
archive id
archive item id
media id
media uuid
media version id
external work id
content marker id
status
visibility
validation state
media state
content review state
audience suitability
restricted flag
cultural protocol flag
redaction state
retention class
relation type
collection membership
source ownership
export purpose
```

No single field is sufficient by itself.

---

## 11. Visibility values

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

Restricted visibility requires additional policy checks.

Restricted visibility is not only a display label.

---

## 12. Archive access rules

### 12.1 View archive item

To view an archive item, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:view
archive item visibility check
archive item status check
restricted policy check
privacy/redaction policy check
```

### 12.2 Add archive item

To add an archive item, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:additem
archive instance availability check
input validation
file-area policy
```

### 12.3 Revise archive item

To revise an archive item, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:reviseitem
archive item visibility check
revision policy
provenance policy
restricted policy if applicable
```

### 12.4 Validate archive item

To validate an archive item, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:validateitem
validation policy
provenance policy
status transition policy
restricted policy if applicable
```

### 12.5 Export archive item

To export archive items, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:export
export scope policy
visibility policy
restricted policy
redaction policy
retention policy
manifest policy
```

---

## 13. Media access rules

### 13.1 View media

To view a media object, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:viewmedia
media visibility check
media lifecycle state check
content advisory policy
restricted media policy
privacy/redaction policy
```

### 13.2 Add media

To add media, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:addmedia
media source policy
file-area policy
metadata validation
content advisory default policy
```

### 13.3 Edit media

To edit media metadata, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:editmedia
media ownership or role policy
media lifecycle state policy
restricted media policy if applicable
content advisory policy if changing advisory fields
```

### 13.4 Delete media

To delete media, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:deletemedia
media lifecycle policy
retention policy
relation policy
export history policy
restricted media policy
```

Deletion is soft deletion unless policy allows purge.

### 13.5 Download media

To download media, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:downloadmedia
media visibility check
file-area access check
content advisory acknowledgement if required
cultural protocol check if required
restricted media policy
retention/redaction policy
```

### 13.6 Version media

To add a media version, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:versionmedia
media lifecycle policy
file-area policy
version policy
provenance policy
content advisory inheritance policy
```

### 13.7 Export media

To export media, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:exportmedia
media export policy
file-area policy
content advisory policy
cultural protocol policy
redaction policy
manifest policy
```

---

## 14. Content advisory access rules

### 14.1 View advisories

To view content advisories, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:viewadvisories
content marker visibility check
content review state check
cultural protocol visibility check
```

### 14.2 Manage advisories

To create or edit advisory tags, tag sets, or markers, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:manageadvisories
content policy
tag set policy
marker locator validation
source reference policy
```

### 14.3 Review advisories

To review, approve, contest, retire, or confirm content markers, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:reviewadvisories
review policy
cultural protocol policy when applicable
human-review requirement
audit requirement
```

### 14.4 View culturally restricted material

To view culturally restricted advisory details, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:viewculturallyrestricted
cultural protocol policy
audience suitability policy
record visibility policy
restricted media policy if linked to media
redaction policy
```

### 14.5 Manage external works

To manage external works or foreign media references, the user must pass:

```text
login/session check
course module context check
mod/uckkarchive:manageexternalworks
source ownership policy
external rights metadata validation
content advisory policy
locator policy
```

---

## 15. Content advisory acknowledgement

Some media or archive records may require acknowledgement before viewing or downloading.

Acknowledgement may be required for:

```text
strong content advisory
restricted content advisory
restricted cultural protocol
mature audience suitability
guided access suitability
integrity-sensitive material
```

Acknowledgement records must not replace permission checks.

Acknowledgement means:

```text
the user has been warned or contextualized
```

Acknowledgement does not mean:

```text
the user has unrestricted access
the user may export the material
the user may bypass cultural protocol
the user may redistribute the material
```

---

## 16. External work permissions

External works represent media or works not produced by UCKK.

External work records may be visible even when the external media file is not stored by the module.

Policy must distinguish:

```text
view external work metadata
view advisory markers
view teaching notes
view cultural protocol notes
view restricted review notes
download local files
export reference metadata
export copied media files
```

External work permissions must respect:

```text
source ownership
license metadata
rights metadata
audience suitability
content advisories
cultural protocol restrictions
redaction rules
```

---

## 17. Restricted access model

Restricted access categories:

```text
restricted
restricted_integrity
restricted_cultural
restricted_media
restricted_external_work
```

Restricted records require:

```text
ordinary capability
plus restricted capability
plus policy approval
```

Examples:

```text
mod/uckkarchive:viewrestricted
mod/uckkarchive:viewrestrictedmedia
mod/uckkarchive:viewculturallyrestricted
```

Restricted access must be audited.

Restricted access must not be inferred only from Moodle manager status.

---

## 18. Cultural protocol model

Culturally restricted access is independent from ordinary restricted access.

A user may have `viewrestricted` but not `viewculturallyrestricted`.

A user may have `viewmedia` but not `viewculturallyrestricted`.

Cultural protocol restrictions apply to:

```text
media objects
media versions
content markers
external works
archive items
proofs
collections
exports
manifest details
review notes
```

Cultural protocol policy may require:

```text
specific role assignment
explicit capability
human review
community permission metadata
elder review metadata
seasonal/contextual access conditions
redaction of protocol details
export exclusion
```

---

## 19. Audience suitability model

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

Audience suitability affects:

```text
viewing
download
teaching context
export
search/listing
preview display
thumbnail display
collection inclusion
```

Audience suitability is advisory unless policy marks it restrictive.

---

## 20. Export permission model

Archive/media/content exports must check:

```text
archive export capability
media export capability
restricted archive access
restricted media access
cultural protocol access
content advisory policy
redaction policy
retention policy
external work rights metadata
manifest policy
```

Export can include:

```text
archive item metadata
media metadata
media files
media versions
collections
relations
tags
content markers
content tag sets
content reviews
external work metadata
manifest.json
```

Export must not include:

```text
restricted media files without authority
restricted cultural notes without authority
third-party copyrighted files when only reference metadata is permitted
redacted data
private reviewer notes not permitted by policy
integrity case procedure records owned by tool_uckkintegrity
grades or transcripts
```

---

## 21. Search and listing permissions

Search results must be permission-filtered before rendering.

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

Restricted records may appear as redacted placeholders only when policy allows.

---

## 22. File download permissions

File downloads pass through the `pluginfile` handler in `lib.php`.

The handler must check:

```text
component = mod_uckkarchive
file area
context
item id
record existence
record visibility
record status
Moodle capability
archive/media/content policy
restricted status
redaction status
retention status
```

File URL possession is not authority.

---

## 23. Service permissions

Every external service must define and enforce:

```text
parameters
context resolution
login requirement
capability checks
record lookup
policy checks
return filtering
warnings
exceptions
audit event if state changes
```

Services must not return raw restricted data to be hidden client-side.

Filtering happens server-side before response construction.

---

## 24. UI permissions

UI components may show or hide actions based on permission-filtered data.

UI components must not decide access.

Templates and AMD modules may use flags such as:

```text
canview
canedit
canvalidate
canrevise
candownload
canexport
canreviewadvisory
canviewrestricted
canviewcultural
```

Those flags come from server-side policy.

---

## 25. Backup and restore permissions

Backup/restore preserves records and permissions metadata.

Restore must preserve:

```text
visibility
restricted flags
cultural protocol flags
content advisory tags
content markers
review states
redaction state
retention class
relations
collections
source ownership
```

Restore must not make restricted data public.

Restore must not grant new authority.

---

## 26. Privacy permissions

Privacy export and deletion must respect:

```text
user data ownership
third-party data
restricted cultural protocol notes
integrity-sensitive material
external work metadata
media files
review notes
redaction state
retention class
institutional preservation rules
```

A privacy export request is not a permission bypass.

---

## 27. Role preset guidance

The plugin may provide role preset documentation.

Role presets must not be hard-coded as authority.

Suggested presets:

```text
viewer
contributor
mentor
archivist
media_librarian
content_reviewer
cultural_protocol_reviewer
external_work_curator
integrity_reviewer
```

Moodle site administrators decide actual role assignments.

---

## 28. Denial behavior

When access is denied, the module should avoid leaking sensitive information.

Possible denial responses:

```text
not found
access denied
restricted
requires review
requires cultural permission
requires content advisory acknowledgement
not exportable
redacted
```

The exact response depends on policy.

Restricted records should not reveal more than policy permits.

---

## 29. Audit behavior

The module should audit successful state-changing operations.

Audited actions include:

```text
archive item created
archive item revised
archive item validated
archive item exported
media created
media updated
media deleted_soft
media version created
media downloaded when restricted
media exported
media collection created
content marker created
content marker reviewed
external work created
restricted record viewed when audit policy requires it
```

Audit events must not expose restricted content or redacted details.

---

## 30. Implementation files

Permission definitions:

```text
db/access.php
```

Service declarations:

```text
db/services.php
```

Policy classes:

```text
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
```

File access:

```text
lib.php
classes/local/file_area_registry.php
classes/local/media_file.php
```

Privacy:

```text
classes/privacy/provider.php
```

Backup/restore:

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

Tests:

```text
tests/archive_test.php
tests/media_library_test.php
tests/content_advisory_test.php
tests/file_api_test.php
tests/privacy_provider_test.php
tests/services_test.php
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

---

## 31. Final permission rule

```text
Moodle capabilities open the gate.
Archive, media, and content policies decide the actual access.
Record state, visibility, validation, restriction, redaction, retention,
cultural protocol, and content advisory rules remain enforceable at all times.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
