# 22 — Installation

**Path:** `docs/22_installation.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Installation, deployment, upgrade preparation, runtime requirements, packaging, and verification for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines the final installation contract for `mod_uckkarchive`.

`mod_uckkarchive` is a Moodle-native activity module with a self-contained archive, media library, and content advisory system.

Canonical architecture:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

Installation must place the plugin inside Moodle as a standard activity module while preserving the module’s internal ownership of:

```text
archive records
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
proofs
Kristals
provenance
revisions
validation state
restricted metadata
export packages
export manifests
```

---

## 2. Canonical paths

Source of truth path:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive
```

Active Moodle plugin path:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
```

Canonical Moodle relative path:

```text
mod/uckkarchive
```

Documentation path:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive\docs
```

Active Moodle documentation mirror:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive\docs
```

The plugin must not be installed at:

```text
local/uckkarchive
blocks/uckkarchive
admin/tool/uckkarchive
report/uckkarchive
mod/mod_uckkarchive
```

Correct plugin folder:

```text
uckkarchive
```

Correct component name:

```text
mod_uckkarchive
```

---

## 3. Installation target

The final installed tree must be:

```text
moodle/public/mod/uckkarchive/
├── add.php
├── export.php
├── index.php
├── item.php
├── lib.php
├── locallib.php
├── media.php
├── mod_form.php
├── settings.php
├── styles.css
├── validate.php
├── version.php
├── view.php
├── amd/
├── backup/
├── classes/
├── db/
├── docs/
├── lang/
├── pix/
├── templates/
└── tests/
```

The plugin is installed when Moodle detects:

```text
mod/uckkarchive/version.php
```

and the component declared in code is:

```text
mod_uckkarchive
```

---

## 4. Installation mode

The plugin may be installed by either:

```text
copy deployment
git checkout / pull
package extraction
```

The installed folder must contain the clean release package only.

Do not install generated codedump files, scratch files, backup files, temporary files, or process documents.

Forbidden install artifacts:

```text
*.bak
*.tmp
*.orig
*.rej
*.patch
*.log
.DS_Store
Thumbs.db
node_modules/
codedump files
AI scratch files
runtime export files outside Moodle File API
```

---

## 5. Required top-level files

The installation package must include:

```text
add.php
export.php
index.php
item.php
lib.php
locallib.php
media.php
mod_form.php
settings.php
styles.css
validate.php
version.php
view.php
```

Root files are request controllers or Moodle callback files.

Business logic must remain in:

```text
classes/local
```

External services must remain in:

```text
classes/external
```

Renderable data must remain in:

```text
classes/output
```

Mustache templates must remain in:

```text
templates
```

AMD source and build files must remain in:

```text
amd
```

---

## 6. Required database files

The installation package must include:

```text
db/access.php
db/events.php
db/install.xml
db/services.php
db/tasks.php
db/upgrade.php
```

Database file roles:

| File | Required role |
|---|---|
| `db/access.php` | Defines archive, media, and content advisory capabilities. |
| `db/events.php` | Registers observers. |
| `db/install.xml` | Defines the full install schema for new installations. |
| `db/services.php` | Defines Moodle external services. |
| `db/tasks.php` | Defines scheduled tasks. |
| `db/upgrade.php` | Migrates existing installations to the current schema. |

New installations use:

```text
db/install.xml
```

Existing installations use:

```text
db/upgrade.php
```

---

## 7. Required database schema

New installation must create archive tables:

```text
uckkarchive
uckkarchive_item
uckkarchive_proof
uckkarchive_kristal
uckkarchive_prov
uckkarchive_rev
uckkarchive_export
```

New installation must create media library tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
```

New installation must create content advisory and external-work tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_media_source
```

Identifier rule:

```text
id = local Moodle database primary key
uuid = stable portable object identity
```

UUIDs must be available for:

```text
archive items
media objects
media versions
media collections
content markers
external works
export packages
```

---

## 8. Required capabilities

Installation must register archive capabilities:

```text
mod/uckkarchive:addinstance
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Installation must register media capabilities:

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

Installation must register content advisory capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:manageexternalworks
```

Do not register this removed capability:

```text
mod/uckkarchive:versionitem
```

Archive item revision uses:

```text
mod/uckkarchive:reviseitem
```

Media versioning uses:

```text
mod/uckkarchive:versionmedia
```

---

## 9. Required local classes

Installation must include archive local classes:

```text
classes/local/archive_item.php
classes/local/archive_policy.php
classes/local/export_package.php
classes/local/kristal.php
classes/local/proof.php
classes/local/provenance.php
classes/local/revision.php
```

Installation must include media local classes:

```text
classes/local/media.php
classes/local/media_collection.php
classes/local/media_file.php
classes/local/media_policy.php
classes/local/media_relation.php
classes/local/media_search.php
classes/local/media_source.php
classes/local/media_tag.php
classes/local/media_version.php
```

Installation must include content advisory local classes:

```text
classes/local/content_marker.php
classes/local/content_policy.php
classes/local/content_review.php
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/external_work.php
```

Installation must include shared local infrastructure:

```text
classes/local/context_resolver.php
classes/local/file_area_registry.php
classes/local/manifest_builder.php
classes/local/metadata_validator.php
classes/local/uuid.php
```

`classes/local` is the authority layer for archive, media, and content advisory behavior.

---

## 10. Required external service classes

Installation must include archive service classes:

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

Installation must include media service classes:

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

Installation must include content advisory and external-work service classes:

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

Installation must include export service classes:

```text
classes/external/get_export_preview.php
classes/external/export_items.php
classes/external/export_media.php
classes/external/export_collection.php
classes/external/get_export_status.php
```

Every external service must resolve context, check capabilities, call policy classes, and return permission-filtered data.

---

## 11. Required forms

Installation must include:

```text
classes/form/archive_item_form.php
classes/form/content_marker_form.php
classes/form/content_review_form.php
classes/form/content_tag_form.php
classes/form/export_form.php
classes/form/external_work_form.php
classes/form/kristal_form.php
classes/form/media_collection_form.php
classes/form/media_form.php
classes/form/media_relation_form.php
classes/form/media_version_form.php
classes/form/validation_form.php
```

Forms collect and shape input.

Forms do not replace policy classes.

---

## 12. Required output classes

Installation must include:

```text
classes/output/archive_item_card.php
classes/output/archive_view.php
classes/output/content_advisory_panel.php
classes/output/external_work_card.php
classes/output/kristal_card.php
classes/output/media_card.php
classes/output/media_collection.php
classes/output/media_library.php
classes/output/media_version_list.php
classes/output/provenance_panel.php
classes/output/renderer.php
```

Output classes format permission-filtered data.

Output classes do not authorize access.

---

## 13. Required templates

Installation must include:

```text
templates/archive_item_card.mustache
templates/archive_view.mustache
templates/content_advisory_panel.mustache
templates/external_work_card.mustache
templates/kristal_card.mustache
templates/media_card.mustache
templates/media_collection.mustache
templates/media_library.mustache
templates/media_relation_list.mustache
templates/media_upload.mustache
templates/media_version_list.mustache
templates/proof_card.mustache
templates/provenance_panel.mustache
templates/validation_panel.mustache
```

Templates receive pre-filtered render data.

Templates do not enforce authority.

---

## 14. Required AMD files

Installation must include AMD source files:

```text
amd/src/archive.js
amd/src/content_advisory.js
amd/src/export.js
amd/src/external_work.js
amd/src/kristal.js
amd/src/media.js
amd/src/media_collection.js
```

Runtime package must include AMD build files:

```text
amd/build/archive.min.js
amd/build/content_advisory.min.js
amd/build/export.min.js
amd/build/external_work.min.js
amd/build/kristal.min.js
amd/build/media.min.js
amd/build/media_collection.min.js
```

AMD rule:

```text
amd/src is source.
amd/build is generated.
AMD modules do not authorize access.
```

After changing AMD source files, rebuild Moodle AMD assets before packaging.

---

## 15. Required backup and restore files

Installation must include:

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

Backup/restore must cover archive-owned records:

```text
archive items
proofs
Kristals
provenance
revisions
exports
media objects
media versions
media relations
media tags
media collections
media collection items
content tags
content tag sets
content markers
content reviews
external works
media source records
File API files
```

Restore must not create external authority:

```text
grades
transcripts
course enrolment authority
Assembly authority
challenge workflow authority
integrity case authority
institutional reporting authority
```

---

## 16. Required events and tasks

Installation must include event classes:

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

Installation must include scheduled task classes:

```text
classes/task/generate_archive_exports.php
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
classes/task/validate_pending_items.php
```

Scheduled task declarations belong in:

```text
db/tasks.php
```

---

## 17. Required language files

Installation must include:

```text
lang/en/uckkarchive.php
lang/fr/uckkarchive.php
```

Language files must contain matching keys for:

```text
plugin identity
capabilities
settings
forms
services
events
archive UI
media UI
content advisory UI
external work UI
collections
relations
versions
validation
privacy
backup/restore
errors
warnings
access messages
```

Do not ship backup language files:

```text
lang/en/uckkarchive.php.bak_20260522_124454
```

Do not ship any `*.bak` language files.

---

## 18. Required visual assets

Installation must include:

```text
pix/icon.svg
```

Optional visual assets:

```text
pix/media.svg
pix/collection.svg
```

User-uploaded media must not be stored in:

```text
pix
```

`pix` is for static plugin interface assets only.

---

## 19. Moodle File API requirement

The plugin must store files through Moodle File API.

Component:

```text
mod_uckkarchive
```

Required archive file areas:

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

Required media file areas:

```text
media_original
media_preview
media_thumbnail
media_derivative
media_caption
media_transcript
media_attachment
```

Required content advisory file areas:

```text
content_review_files
external_work_reference_files
cultural_protocol_files
```

File-area registry:

```text
classes/local/file_area_registry.php
```

Installation is incomplete if file areas are hard-coded inconsistently across callbacks, services, backup, restore, privacy, tests, and pluginfile handling.

---

## 20. Optional integration dependencies

The archive may integrate with:

```text
local_uckk
mod_uckkchallenge
mod_uckkassembly
tool_uckkintegrity
report_uckk
```

Ordinary archive, media, and content advisory operation must not require optional integrations.

Integration rule:

```text
optional integration absent = hide, disable, or fail closed for integration-specific features
ordinary archive/media/content-advisory features continue
```

`tool_uckkintegrity` is optional.

Integrity-specific features must not break ordinary installation when `tool_uckkintegrity` is absent.

---

## 21. Installation procedure — copy deployment

Copy the clean plugin folder into Moodle:

```text
from:
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive

to:
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
```

Then run Moodle upgrade using one of:

```text
Site administration → Notifications
```

or CLI:

```text
php admin/cli/upgrade.php
```

After upgrade, purge caches:

```text
php admin/cli/purge_caches.php
```

Then verify that the plugin appears as an activity module.

---

## 22. Installation procedure — development mirror

During development, the repository source of truth remains:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive
```

The active Moodle copy remains:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
```

Development mirror rule:

```text
Generate or edit source files in the source plugin path.
Mirror the plugin into the active Moodle path for runtime testing.
Do not manually edit generated AMD build files except through the Moodle AMD build process.
```

Documentation mirror rule:

```text
Source docs live in the source plugin docs folder.
Active Moodle docs may be mirrored for local reference.
```

---

## 23. Installation procedure — new Moodle site

For a new Moodle site:

```text
copy mod/uckkarchive into Moodle mod directory
confirm version.php component = mod_uckkarchive
confirm db/install.xml includes all target tables
confirm amd/build files exist
run Moodle upgrade
purge caches
assign capabilities to roles
create a course
add UCKK Archive activity
verify archive view
verify media library view
verify content advisory panel
verify backup/restore availability
```

New site installation uses:

```text
db/install.xml
```

---

## 24. Installation procedure — existing Moodle site

For an existing Moodle site:

```text
back up Moodle database
back up moodledata
copy updated plugin files
confirm version.php version bump
run Moodle upgrade
verify db/upgrade.php completed
purge caches
verify capabilities
verify services
verify scheduled tasks
verify backup/restore
verify privacy provider
verify archive item access
verify media library access
verify content advisory access
```

Existing site installation uses:

```text
db/upgrade.php
```

Upgrade must migrate existing archive data without silently losing:

```text
archive items
files
provenance
validation state
revisions
exports
visibility
restricted status
```

---

## 25. Post-install verification

After installation, verify Moodle detects the plugin:

```text
Site administration → Plugins → Activity modules → UCKK Archive
```

Verify activity creation:

```text
course → turn editing on → add activity or resource → UCKK Archive
```

Verify root pages:

```text
view.php
index.php
add.php
item.php
media.php
export.php
validate.php
```

Verify that access is controlled by Moodle login and capabilities.

---

## 26. Database verification

Verify these table groups exist:

```text
archive tables
media tables
content advisory tables
external work tables
```

Minimum table verification:

```text
uckkarchive
uckkarchive_item
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_collection
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_media_source
```

Verify UUID fields exist where required.

Verify indexes exist for:

```text
context lookups
archive id lookups
media id lookups
uuid lookups
status filtering
visibility filtering
source references
content marker locators
external work references
```

---

## 27. Capability verification

Verify role permissions for:

```text
student
teacher
editingteacher
manager
```

Minimum role expectations:

```text
students may view permitted archive/media records
teachers may create and manage course-level archive/media records
reviewers may validate archive records where assigned
managers may administer restricted archive/media records
culturally restricted material requires explicit authority
external work management requires explicit authority
```

Do not grant culturally restricted access through ordinary media viewing alone.

Do not grant restricted integrity access through ordinary archive viewing alone.

---

## 28. Service verification

Verify service declarations in:

```text
db/services.php
```

Service verification includes:

```text
archive item services
media services
media collection services
content advisory services
external work services
export services
```

Every service must:

```text
require login
resolve Moodle context
validate parameters
check capabilities
call policy classes
return permission-filtered data
avoid leaking restricted metadata
```

---

## 29. Backup/restore verification

Verify backup includes:

```text
archive items
media objects
media versions
media collections
content markers
content reviews
external works
media source records
File API files
```

Verify restore preserves:

```text
uuid identity
visibility
restriction state
content advisory state
cultural protocol state
validation state
provenance
revision history
relations
collections
export metadata
```

Verify restore does not create:

```text
grades
transcripts
Assembly authority
challenge workflow authority
integrity case authority
institutional report authority
```

---

## 30. Privacy verification

Verify Moodle privacy subsystem recognizes:

```text
classes/privacy/provider.php
```

Privacy provider must cover user-linked data in:

```text
archive items
proofs
Kristals
provenance
revisions
exports
media objects
media versions
media relations
media collections
media tags
content tags
content tag sets
content markers
content reviews
external works where user-linked
media source records where user-linked
files
```

Privacy behavior must respect:

```text
retention
redaction
restricted access
cultural protocol
institutional memory
legal/ethical preservation needs
```

---

## 31. AMD and cache verification

After installing or updating AMD files:

```text
build AMD modules
purge Moodle caches
reload pages using browser cache bypass
```

Verify runtime AMD modules are available for:

```text
archive UI
media UI
media collection UI
content advisory UI
external work UI
export UI
Kristal UI
```

Required build files:

```text
amd/build/archive.min.js
amd/build/content_advisory.min.js
amd/build/export.min.js
amd/build/external_work.min.js
amd/build/kristal.min.js
amd/build/media.min.js
amd/build/media_collection.min.js
```

---

## 32. File access verification

Verify `lib.php` pluginfile handling supports registered file areas.

File access verification must confirm:

```text
users cannot access files without context permission
restricted files are not leaked
culturally restricted files require explicit permission
integrity-restricted files require explicit permission
media derivatives do not expose originals without permission
exports do not expose restricted files without permission
external works are referenced without unauthorized copying
```

No production files are served from unmanaged public folders.

---

## 33. Content advisory verification

Verify content advisory system can:

```text
create tags
group tags into tag sets
create content markers
attach locators
link markers to media
link markers to archive items
link markers to external works
review markers
approve markers
contest markers
retire markers
enforce audience suitability
enforce cultural protocol restrictions
```

Verify locator types:

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

Verify examples such as:

```text
film content marker with timecode range
book content marker with page range
PDF content marker with page locator
audio content marker with timestamp range
external work content marker without copied media
```

---

## 34. External work verification

Verify external work records can represent:

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

Verify the archive can store:

```text
bibliographic metadata
source ownership
rights notes
content markers
content advisories
cultural protocol notes
teaching notes
manual locators
references
```

Verify the archive does not imply ownership over third-party works.

---

## 35. Packaging verification

Before packaging, confirm the package contains:

```text
root PHP files
amd/src files
amd/build files
backup files
classes files
db files
lang/en and lang/fr files
pix/icon.svg
templates
tests
docs
```

Before packaging, confirm the package excludes:

```text
*.bak
*.tmp
*.orig
*.rej
*.patch
*.log
.DS_Store
Thumbs.db
node_modules/
runtime exports outside Moodle File API
codedump files
AI scratch files
```

The package root must be:

```text
uckkarchive
```

The package must install to:

```text
mod/uckkarchive
```

---

## 36. Installation failure behavior

If installation fails, the plugin must fail safely.

Failure handling must avoid:

```text
partial public file exposure
partial restricted file exposure
silent capability creation failure
silent schema loss
silent media table omission
silent content advisory table omission
silent external work table omission
silent File API area mismatch
```

Failures should be visible through Moodle upgrade errors, PHP errors, database exceptions, or admin notifications.

---

## 37. Clean installation rule

A clean installation is valid only when:

```text
Moodle detects mod_uckkarchive.
All required tables are created.
All required capabilities are registered.
All required services are registered.
All required scheduled tasks are registered.
All required file areas are handled.
All required templates are present.
All required AMD build files are present.
Backup and restore are available.
Privacy provider is available.
Archive workflows work.
Media library workflows work.
Content advisory workflows work.
External work references work.
Restricted and culturally restricted access fail closed.
```

---

## 38. Final installation rule

```text
Install mod_uckkarchive as a Moodle activity module at mod/uckkarchive.
Keep Moodle responsible for plugin lifecycle, context, roles, capabilities, files, privacy, backup, restore, services, events, settings, and rendering.
Keep mod_uckkarchive responsible for its self-contained archive, media library, content advisory system, external work references, provenance, validation, revision, restriction, and export behavior.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
