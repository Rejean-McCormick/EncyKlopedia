# 16 — Integration with Courses

**Path:** `docs/16_integration_with_courses.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Course-level integration for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines how `mod_uckkarchive` integrates with Moodle courses.

`mod_uckkarchive` is a Moodle activity module. It exists inside a Moodle course as a course module instance.

The module provides a self-contained archive, media library, and content advisory system while respecting Moodle’s course, context, visibility, role, group, completion, backup, restore, and privacy systems.

Canonical formula:

```text
Moodle course owns the course context.
mod_uckkarchive owns archive/media/content-advisory records inside its activity context.
Moodle gradebook owns grades.
```

---

## 2. Course integration decision

`mod_uckkarchive` integrates with courses as a normal Moodle activity module installed at:

```text
mod/uckkarchive
```

Each activity instance is stored in:

```text
uckkarchive
```

Each instance belongs to a Moodle course through Moodle’s standard course module system.

The module must not create its own independent course system.

The module must not bypass Moodle course visibility, role assignment, group restrictions, or activity availability.

---

## 3. Course-level responsibilities

Moodle course responsibilities:

```text
course identity
course sections
course visibility
course enrolments
course roles
groups and groupings
activity availability
activity completion shell
gradebook ownership
course backup container
course restore container
course navigation
```

`mod_uckkarchive` responsibilities inside the course:

```text
archive records
media records
media versions
media collections
media relations
media tags
content advisory tags
content markers
content reviews
external work references
proof records
Kristals
provenance
revision history
validation state
restricted metadata
export packages
export manifests
```

---

## 4. Course module context

All instance-level access checks must resolve the Moodle context:

```text
context_module
```

The context is resolved from:

```text
course id
course module id
activity instance id
```

The central context resolver belongs in:

```text
classes/local/context_resolver.php
```

Context resolver responsibilities:

```text
load course
load course module
load uckkarchive instance
validate component
validate module type
return context_module
return course record
return cm record
return archive instance record
```

Controllers and services must not duplicate context resolution logic.

---

## 5. Required Moodle callbacks

Course integration depends on Moodle module callbacks in:

```text
lib.php
```

Required callback categories:

```text
add instance
update instance
delete instance
course module info
navigation
activity completion
file serving
backup support
restore support
view logging
user outline where needed
```

The implementation must follow Moodle module conventions for `mod_uckkarchive`.

---

## 6. Activity instance record

The `uckkarchive` table stores the activity instance.

The activity instance must include fields for:

```text
id
course
name
intro
introformat
archive mode
default visibility
default media visibility
default audience suitability
default advisory behavior
allow media library
allow external work references
allow content advisories
allow exports
enable group mode behavior
completion settings
timecreated
timemodified
```

The `course` field links the activity instance to the Moodle course.

The activity instance does not own enrolments.

---

## 7. Activity modes

The module may support course-facing modes such as:

```text
archive
media_library
archive_and_media
restricted_archive
teaching_collection
evidence_archive
portfolio_archive
```

Mode behavior controls defaults only.

Mode behavior must not bypass capability checks.

Mode behavior must not bypass content advisory policy.

Mode behavior must not bypass cultural protocol restrictions.

---

## 8. Course section display

`mod_uckkarchive` appears in Moodle course sections like any other activity.

The activity page is served by:

```text
view.php
```

Course-level listing is served by:

```text
index.php
```

Archive item pages are served by:

```text
item.php
```

Media library page is served by:

```text
media.php
```

Export page is served by:

```text
export.php
```

Validation page is served by:

```text
validate.php
```

The controller must resolve the course module context before loading activity-owned records.

---

## 9. Course visibility

Moodle controls whether the activity is visible in the course.

`mod_uckkarchive` controls visibility of records inside the activity.

Two visibility layers apply:

```text
Moodle activity visibility
archive/media record visibility
```

The activity must be visible to the user before activity records are shown.

A visible activity does not automatically make all archive/media records visible.

A hidden activity blocks ordinary access even when an internal archive/media item has public visibility.

---

## 10. Internal visibility values

Internal visibility values:

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

Course integration primarily uses:

```text
user
group
course
restricted
restricted_cultural
restricted_integrity
```

The value `institutional` must normalize to:

```text
institution
```

---

## 11. Course visibility rule

Course-level visibility rule:

```text
User access requires Moodle course/module access first.
Then mod_uckkarchive policy decides internal archive/media/content access.
```

Order of evaluation:

```text
course exists
course module exists
module is mod_uckkarchive
user can access course
user can access activity
activity availability permits access
capability permits access
archive/media/content policy permits access
```

---

## 12. Enrolment boundary

`mod_uckkarchive` does not own enrolments.

The module must not:

```text
enrol users
unenrol users
create cohorts
assign course roles
alter course membership
```

The module may read enrolment-derived access through Moodle APIs.

The module may use Moodle capabilities assigned through course/module contexts.

---

## 13. Role and capability integration

Course integration uses Moodle role assignments and capabilities.

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

Content advisory capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:manageexternalworks
```

Capability checks must use the resolved `context_module` unless a broader context is explicitly required by Moodle.

---

## 14. Add instance capability

Adding an archive activity to a course requires:

```text
mod/uckkarchive:addinstance
```

This capability is checked by Moodle when adding the activity to a course.

Creating an activity instance does not automatically grant permission to validate, export, download originals, manage cultural protocols, or view restricted media.

---

## 15. View capability

Viewing the activity shell requires:

```text
mod/uckkarchive:view
```

Viewing internal media records may also require:

```text
mod/uckkarchive:viewmedia
```

Viewing restricted media may require:

```text
mod/uckkarchive:viewrestrictedmedia
```

Viewing culturally restricted records may require:

```text
mod/uckkarchive:viewculturallyrestricted
```

Viewing the activity page does not imply full internal access.

---

## 16. Groups and groupings

The module must respect Moodle group mode where the activity/course uses groups.

Relevant group behaviors:

```text
no groups
separate groups
visible groups
grouping restriction
```

Group-aware archive/media rules apply to records with visibility:

```text
group
```

Group-aware filtering must apply to:

```text
archive item list
media library list
collections
proof records
Kristal records
content markers
external work teaching notes
exports
search results
AJAX service responses
```

Group filtering must happen server-side.

AMD modules may request group filters, but they must not enforce group authority.

---

## 17. Group ownership

Archive and media records may store:

```text
groupid
```

Group ownership means the record belongs to a group context inside the activity.

Group ownership does not create a Moodle group.

Group ownership does not override Moodle group mode.

When group mode is separate groups, users must not see records belonging only to other groups unless they have the required Moodle permission to access all groups.

---

## 18. Course collections

Media collections may be course-facing.

Examples:

```text
course media pack
week module collection
teaching collection
challenge evidence collection
Kristal source collection
public summary collection
restricted staff collection
cultural protocol collection
```

Course-facing collections belong to `uckkarchive_media_collection`.

A collection can include media from the same activity instance.

Cross-activity reuse must be explicit and policy controlled.

---

## 19. Course archive items

Course archive items may represent:

```text
course work
learning artifact
portfolio item
challenge evidence
proof
minutes
decision snapshot
Kristal source
public summary
restricted integrity summary
external work teaching note
```

Course archive items belong to `uckkarchive_item`.

Course archive items may link to media records, external works, content markers, and content advisories.

---

## 20. Course media library

The media library is an internal module-owned subsystem.

Course users may access media library features only when policy permits.

Course media library features may include:

```text
browse media
upload media
view media card
view media preview
download original
create media version
create collection
tag media
link media to archive item
review content advisories
reference external works
```

Each feature requires capability and policy checks.

---

## 21. Course content advisories

Content advisories support responsible teaching and viewing inside courses.

Content advisories can apply to:

```text
archive items
media objects
media versions
external works
content markers
collections
public summaries
exports
```

Course-facing advisory behavior may include:

```text
show notice before viewing
show cultural protocol note
hide item from youth-facing view
require guided access
restrict public export
require staff review
require cultural access permission
```

Content advisory logic belongs in:

```text
classes/local/content_policy.php
```

---

## 22. External works in courses

The module may reference external or foreign works used in teaching.

External works are stored in:

```text
uckkarchive_external_work
```

The module may store:

```text
title
creator
publisher
source type
citation
URL
external identifier
rights/license metadata
content markers
advisory tags
review notes
teaching notes
audience suitability
cultural protocol restrictions
```

The module must not imply UCKK ownership over third-party works.

The module may store an external work file only when storage is permitted by policy, rights, or license.

---

## 23. Course examples

Course examples:

```text
A film shown in class has content markers with timecodes.
A book used in a reading week has page-range advisories.
A student-submitted media item has restricted cultural review notes.
A teacher creates a course media pack for guided access.
A staff member exports a validated proof bundle.
A public summary excludes culturally restricted media.
```

These examples must be implemented through archive/media/content policy, not through template-only hiding.

---

## 24. Completion integration

The module may support Moodle activity completion.

Completion may be based on:

```text
viewing the activity
viewing required archive item
submitting archive item
uploading media
creating proof
reviewing advisory notice
teacher validation
manual completion
```

Completion logic belongs in:

```text
classes/completion/custom_completion.php
```

Completion must not require:

```text
viewing restricted content without permission
downloading original restricted media
viewing culturally restricted material
reviewing integrity records without authority
```

Completion conditions must respect access rules.

---

## 25. Gradebook boundary

`mod_uckkarchive` does not own grades.

The module must not become the gradebook authority.

The Moodle gradebook owns:

```text
grade items
grade values
final grades
grade aggregation
grade export
grade history
```

`mod_uckkarchive` may preserve:

```text
graded artifact snapshot
submission evidence
teacher feedback archive
validation notes
course work media
proof of completion
exported archive package
```

Preserving grade-related evidence does not make the archive the gradebook.

---

## 26. Grade-related evidence

If archive records reference graded work, they must store archive-owned metadata only.

Allowed archive metadata:

```text
source activity reference
source course id
source user id
source timestamp
submitted file copy where permitted
provenance
validation state
teacher note copy where permitted
export manifest reference
```

Forbidden behavior:

```text
recalculate grade
modify grade
override gradebook
replace Moodle assignment records
own grade appeals
```

---

## 27. Course navigation

Course navigation may expose:

```text
activity view
archive item list
media library
collections
exports
validation tools
restricted tools
content advisory tools
external works
```

Navigation entries must be capability-filtered.

Restricted tools must not appear to users without authority.

Navigation visibility is not authorization.

The controller and service layer must still enforce access.

---

## 28. Course search

Course search may include archive and media records when policy permits.

Search results must respect:

```text
course/module access
visibility
group mode
media status
archive item status
content advisory policy
cultural protocol restrictions
restricted integrity policy
redaction state
deleted_soft state
```

Search must not leak restricted titles, private notes, cultural protocol notes, or third-party restricted metadata.

---

## 29. Course backup

Course backup includes `mod_uckkarchive` activity instances and module-owned records.

Backup must preserve:

```text
activity instance
archive items
media records
media versions
media collections
media relations
media tags
content advisory tags
content tag sets
content markers
content reviews
external works
media source records
proof records
Kristals
provenance
revisions
validation state
exports
files
manifests
```

Backup must not create or own:

```text
grades
enrolments
institutional registry authority
challenge workflow authority
assembly decision authority
integrity case authority
reporting authority
```

---

## 30. Course restore

Course restore must restore the activity inside the target course.

Restore must remap:

```text
course id
course module id
activity instance id
user ids
group ids
archive item ids
media ids
media version ids
collection ids
relation ids
content marker ids
content review ids
external work ids
file itemids
```

Restore must preserve:

```text
visibility
restricted state
cultural protocol restrictions
content advisories
redaction state
validation state
provenance
revision history
export manifest history
```

Restore must not make restricted course records public.

---

## 31. Course reset

If Moodle course reset support is implemented, the module must provide explicit reset behavior.

Possible reset options:

```text
remove student draft archive items
remove student media drafts
remove course-generated exports
keep validated archive records
keep staff media library
keep external work references
keep content advisory vocabulary
keep cultural protocol records
```

Course reset must not silently delete preserved evidence.

Course reset must not delete culturally restricted records without explicit authority.

Course reset must respect retention policy.

---

## 32. Calendar integration

Calendar integration is optional and must remain limited.

The module may create or expose dates such as:

```text
archive submission due date
validation deadline
review deadline
collection release date
media availability date
```

Calendar events must not expose restricted titles, cultural protocol notes, or private advisory details to unauthorized users.

The archive is not the course calendar authority.

---

## 33. Availability dates

The module may support availability dates for archive/media records.

Availability may include:

```text
available from
available until
review window
export window
collection release window
restricted staff window
```

Availability dates do not replace Moodle activity availability.

The most restrictive applicable rule wins.

---

## 34. User data in courses

Course users may contribute:

```text
archive items
media uploads
proof records
comments where implemented
content advisory suggestions
external work references
review notes where permitted
```

User-linked data must be handled through:

```text
classes/privacy/provider.php
```

Privacy behavior must respect both Moodle course context and archive/media preservation rules.

---

## 35. Teacher workflows

Teachers may use course integration to:

```text
create archive activity
create course archive item
upload teaching media
create media collection
reference external work
add content advisory marker
review content advisory suggestion
publish course-facing media pack
validate archive item
export course archive package
```

Teacher authority depends on capabilities and policy.

Teacher role alone is not hardcoded authority.

---

## 36. Student workflows

Students may use course integration to:

```text
view allowed archive items
view allowed media
submit archive item
upload media where permitted
view advisory notices
submit content advisory suggestion where permitted
access guided collections
view feedback or validation status where permitted
```

Students must not access restricted staff records, restricted cultural records, private review notes, or integrity-restricted media unless explicit policy permits it.

---

## 37. Staff and reviewer workflows

Staff/reviewers may:

```text
validate archive items
review media metadata
review content advisories
manage cultural protocol notes
manage restricted records
create export packages
review external work references
manage collections
```

Reviewer permissions are capability-based.

The module must support review workflows without relying on hardcoded user IDs.

---

## 38. Public-facing course material

Some archive/media material may be public-facing.

Public-facing output must pass all checks:

```text
activity permits access
record visibility is public
record status permits display
content advisory policy permits display
cultural protocol policy permits display
redaction policy permits display
rights/license permits display
export/public summary policy permits display
```

Public-facing course material must not expose internal notes, private provenance details, cultural protocol notes, or restricted file URLs.

---

## 39. Public summaries

Course archive items may include public summaries.

Public summaries use file area:

```text
item_publicsummary
```

Public summaries must be separately approved.

Public summaries may differ from internal archive records.

Public summaries must not automatically include original restricted media.

---

## 40. Activity deletion

Deleting a course module instance triggers module deletion behavior.

Deletion must respect:

```text
Moodle deletion lifecycle
privacy obligations
retention obligations
institutional memory rules
cultural protocol restrictions
export retention rules
```

The module must not leave orphaned active records.

The module must not silently destroy preserved evidence that retention policy requires.

Where Moodle requires deletion, the module must handle records according to defined retention/redaction policy.

---

## 41. Duplication inside a course

Duplicating the activity inside a course must preserve internal structure only when Moodle duplication/backup rules permit it.

Duplication must generate new local record IDs.

Portable identity may preserve or fork UUIDs according to restore policy.

Duplication must not:

```text
make restricted media public
copy disallowed third-party files
drop content advisories
drop cultural protocol restrictions
drop source ownership metadata
drop provenance
```

---

## 42. Cross-course reuse

Cross-course reuse is not implicit.

A media object or collection used in another course must be:

```text
copied through backup/restore
exported/imported with manifest
referenced through a controlled relation
shared through a controlled institutional mechanism
```

Cross-course reuse must preserve:

```text
source uuid
rights metadata
content advisories
cultural protocol restrictions
visibility
redaction state
provenance
```

---

## 43. Course import

Moodle course import may copy activity instances.

Import must behave like controlled restore.

Imported archive/media records must not lose:

```text
file ownership
content markers
content reviews
external work references
media source records
validation state
restricted state
cultural protocol restrictions
```

Course import must not import gradebook authority into the archive.

---

## 44. Course reporting boundary

`mod_uckkarchive` may provide course-level archive views and export packages.

`report_uckk` owns institutional reporting.

The archive module may expose course activity data to reporting plugins through controlled APIs.

The archive module must not become the institutional reporting authority.

---

## 45. Course export behavior

Course-level archive exports may include:

```text
selected archive items
course media collections
proof bundles
validated items
public summaries
external work metadata
content markers
content advisory tags
export manifests
```

Exports must exclude unauthorized restricted records.

Exports must preserve content advisory and cultural protocol metadata where policy permits.

Exports must not include third-party files unless rights and policy permit.

---

## 46. Events in course context

Course integration must trigger Moodle events in the correct context.

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

Events must use `context_module`.

Events must not expose restricted content in event data.

---

## 47. Course services

External services used in course views must accept and validate:

```text
course module id
archive instance id
record id or uuid
context
sesskey where required
```

Services must return permission-filtered data.

Services must not return hidden records for client-side filtering.

Services must not expose restricted records through autocomplete, search, preview, or card-render endpoints.

---

## 48. Course UI rendering

Course UI rendering uses:

```text
classes/output/archive_view.php
classes/output/archive_item_card.php
classes/output/media_library.php
classes/output/media_card.php
classes/output/media_collection.php
classes/output/content_advisory_panel.php
classes/output/external_work_card.php
classes/output/renderer.php
```

Templates receive already-filtered render data.

Templates must not make access decisions.

AMD modules enhance UI behavior only.

---

## 49. Language strings

Course-facing strings belong in:

```text
lang/en/uckkarchive.php
lang/fr/uckkarchive.php
```

Strings must cover:

```text
activity names
course view labels
archive actions
media actions
collection actions
content advisory notices
cultural protocol notices
external work labels
completion descriptions
capability names
error messages
privacy descriptions
backup/restore descriptions
```

English and French keys should remain aligned.

---

## 50. Installation defaults

New activity instances should define safe defaults.

Recommended safe defaults:

```text
default visibility = course
default media visibility = course
default audience suitability = guided
allow media library = enabled
allow external work references = enabled
allow content advisories = enabled
allow public summaries = disabled unless configured
allow exports = capability-controlled
restricted cultural access = disabled by default for ordinary roles
restricted integrity access = disabled by default for ordinary roles
```

Safe defaults may be changed by site/admin settings and activity settings.

---

## 51. Settings hierarchy

Settings may exist at:

```text
site plugin settings
activity instance settings
record-level settings
media-level settings
content advisory settings
```

The most restrictive applicable rule wins.

Activity settings must not override site-level restrictions.

Record-level settings must not bypass capability or policy checks.

---

## 52. Course integration files

Files that implement course integration:

```text
index.php
view.php
item.php
media.php
add.php
export.php
validate.php
lib.php
mod_form.php
settings.php
classes/completion/custom_completion.php
classes/local/context_resolver.php
classes/local/archive_policy.php
classes/local/media_policy.php
classes/local/content_policy.php
classes/output/archive_view.php
classes/output/media_library.php
classes/output/content_advisory_panel.php
classes/privacy/provider.php
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

---

## 53. Required tests

Course integration tests must cover:

```text
activity can be created in a course
activity resolves context_module
course visibility blocks ordinary access
activity visibility blocks ordinary access
view capability gates activity shell
media capability gates media library
group mode filters archive records
group mode filters media records
content advisory policy affects course display
cultural protocol restriction blocks unauthorized view
public summary excludes restricted media
completion respects permissions
backup preserves course-owned archive/media records
restore remaps course/module/activity ids
course import preserves content advisories
course export excludes unauthorized files
privacy provider exports user data by context
pluginfile uses course module context
services reject wrong cmid
services return filtered data
```

---

## 54. Final rule

This document defines the final target behavior for course integration.

```text
Moodle owns the course shell.
mod_uckkarchive owns archive/media/content-advisory records inside its module context.
Moodle gradebook owns grades.
```

Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
