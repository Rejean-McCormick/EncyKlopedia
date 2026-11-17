# 24 — Release Specification

**Path:** `docs/24_release_spec.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Release package, build requirements, file inclusion/exclusion, installation readiness, upgrade readiness, tests, privacy, backup/restore, UI assets, and packaging rules for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines the final release specification for `mod_uckkarchive`.

It is not a release history.

It is not a changelog.

It is not a gap register.

It is not an acceptance checklist.

It defines what the clean release package must contain and how it must be prepared for installation, duplication, troubleshooting, and deployment.

Canonical module formula:

```text
mod_uckkarchive = archive engine + media library engine + content advisory system + Moodle adapter layer
```

Canonical architecture rule:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

---

## 2. Release package root

The release package root is:

```text
mod/uckkarchive
```

Source path:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive
```

Active Moodle path:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
```

The release package must install as the Moodle component:

```text
mod_uckkarchive
```

The release package must not depend on being installed outside Moodle’s normal plugin structure.

---

## 3. Release identity

Required plugin identity:

```text
PLUGIN_NAME = UCKK Archive
PLUGIN_TYPE = mod
PLUGIN_FOLDER = uckkarchive
MOODLE_COMPONENT = mod_uckkarchive
MOODLE_PLUGIN_PATH = mod/uckkarchive
```

Required Moodle metadata file:

```text
version.php
```

`version.php` must define:

```text
$plugin->component = 'mod_uckkarchive';
$plugin->version
$plugin->requires
$plugin->maturity
$plugin->release
```

Dependency rule:

```text
mod_uckkarchive must not declare a dependency on itself.
```

Integrity dependency rule:

```text
tool_uckkintegrity is an optional integration.
Ordinary archive/media/content-advisory operation must not require tool_uckkintegrity.
```

---

## 4. Required top-level files

The release package must include:

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

Top-level file rule:

```text
Root PHP files coordinate requests only.
Business policy belongs in classes/local.
Service contracts belong in classes/external.
Renderable payloads belong in classes/output.
```

---

## 5. Required top-level folders

The release package must include:

```text
amd/
backup/
classes/
db/
docs/
lang/
pix/
templates/
tests/
```

The following folders must not be used to store production user media:

```text
pix/
docs/
templates/
amd/
```

Production archive and media files must be stored through Moodle File API only.

---

## 6. Required documentation files

The clean documentation set must include:

```text
docs/_alignment_variables.md
docs/00_index.md
docs/01_architecture_decision.md
docs/02_domain_boundaries.md
docs/03_file_architecture.md
docs/04_data_model.md
docs/05_media_library.md
docs/06_file_api_and_storage.md
docs/07_permissions_and_roles.md
docs/08_archive_workflows.md
docs/09_media_workflows.md
docs/10_provenance_versioning_validation.md
docs/11_privacy_retention_redaction.md
docs/12_backup_restore.md
docs/13_services_and_ajax_api.md
docs/14_events_and_audit.md
docs/15_ui_templates_and_amd.md
docs/16_integration_with_courses.md
docs/17_integration_with_challenges.md
docs/18_integration_with_assemblies.md
docs/19_integration_with_integrity.md
docs/20_reporting_and_exports.md
docs/21_testing_strategy.md
docs/22_installation.md
docs/23_upgrade.md
docs/24_release_spec.md
```

Documentation rule:

```text
Documentation describes the final target state.
Documentation does not keep historical gap records.
Documentation does not contain release notes.
Documentation does not contain acceptance-checklist process documents.
```

---

## 7. Files excluded from the clean documentation set

The clean documentation set must not include:

```text
docs/05_media_database_division.md
docs/09_didactic_material_workflows.md
docs/24_acceptance_checklist.md
docs/25_known_gaps_and_corrections.md
docs/26_release_notes.md
docs/27_file_architecture_manifest.md
```

Replacement mapping:

| Removed file | Replacement |
|---|---|
| `docs/05_media_database_division.md` | `docs/05_media_library.md` |
| `docs/09_didactic_material_workflows.md` | `docs/08_archive_workflows.md` and `docs/09_media_workflows.md` |
| `docs/24_acceptance_checklist.md` | `docs/24_release_spec.md` |
| `docs/25_known_gaps_and_corrections.md` | No replacement. Historical gap registry is not part of final-state docs. |
| `docs/26_release_notes.md` | No replacement. Release notes are not part of this final-state specification set. |
| `docs/27_file_architecture_manifest.md` | `docs/03_file_architecture.md` |

---

## 8. Required database files

The release package must include:

```text
db/access.php
db/events.php
db/install.xml
db/services.php
db/tasks.php
db/upgrade.php
```

Database release rule:

```text
db/install.xml defines the full current target schema.
db/upgrade.php migrates existing installs to the full current target schema.
```

The release must include database support for:

```text
archive records
media records
media versions
media collections
media collection membership
media relations
media tags
media source records
content advisory tags
content tag sets
content markers
content reviews
external works
proofs
Kristals
provenance
revisions
exports
```

---

## 9. Required database tables

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
uckkarchive_media_source
```

Required content advisory and external-work tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
```

Identifier rule:

```text
id = local Moodle database primary key
uuid = stable portable object identity
```

Release schema rule:

```text
Archive objects, media objects, content markers, external works, and export packages must support UUID identity for export, restore, duplication, and cross-site portability.
```

---

## 10. Required capabilities

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

Removed capability:

```text
mod/uckkarchive:versionitem
```

The release must not use or document `mod/uckkarchive:versionitem`.

Archive item revision uses:

```text
mod/uckkarchive:reviseitem
```

Media versioning uses:

```text
mod/uckkarchive:versionmedia
```

---

## 11. Required local domain classes

The release package must include:

```text
classes/local/archive_item.php
classes/local/archive_policy.php
classes/local/content_marker.php
classes/local/content_policy.php
classes/local/content_review.php
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/context_resolver.php
classes/local/export_package.php
classes/local/external_work.php
classes/local/file_area_registry.php
classes/local/kristal.php
classes/local/manifest_builder.php
classes/local/media.php
classes/local/media_collection.php
classes/local/media_file.php
classes/local/media_policy.php
classes/local/media_relation.php
classes/local/media_search.php
classes/local/media_source.php
classes/local/media_tag.php
classes/local/media_version.php
classes/local/metadata_validator.php
classes/local/proof.php
classes/local/provenance.php
classes/local/revision.php
classes/local/uuid.php
```

Local class rule:

```text
classes/local is the authority layer for archive, media, content advisory, and export behavior.
```

---

## 12. Required external service classes

The release package must include archive services:

```text
classes/external/add_item.php
classes/external/add_proof.php
classes/external/create_kristal.php
classes/external/export_items.php
classes/external/get_archive.php
classes/external/get_archive_item.php
classes/external/get_archive_item_card.php
classes/external/get_archive_items.php
classes/external/get_export_preview.php
classes/external/get_export_status.php
classes/external/get_kristal.php
classes/external/get_proofs.php
classes/external/get_provenance_panel.php
classes/external/get_restricted_item.php
classes/external/get_revisions.php
classes/external/revise_item.php
classes/external/save_item_draft.php
classes/external/update_kristal.php
classes/external/update_provenance.php
classes/external/validate_item.php
```

The release package must include media services:

```text
classes/external/add_media.php
classes/external/add_media_relation.php
classes/external/add_media_to_collection.php
classes/external/add_media_version.php
classes/external/add_media_collection.php
classes/external/delete_media.php
classes/external/export_collection.php
classes/external/export_media.php
classes/external/get_media.php
classes/external/get_media_card.php
classes/external/get_media_collection.php
classes/external/get_media_collections.php
classes/external/get_media_item.php
classes/external/get_media_relations.php
classes/external/get_media_versions.php
classes/external/remove_media_from_collection.php
classes/external/remove_media_relation.php
classes/external/search_media.php
classes/external/tag_media.php
classes/external/untag_media.php
classes/external/update_media.php
classes/external/update_media_collection.php
```

The release package must include content advisory and external work services:

```text
classes/external/add_content_marker.php
classes/external/add_external_work.php
classes/external/delete_content_marker.php
classes/external/get_content_markers.php
classes/external/get_content_tag_sets.php
classes/external/get_content_tags.php
classes/external/get_external_work.php
classes/external/get_external_works.php
classes/external/review_content_marker.php
classes/external/update_content_marker.php
classes/external/update_external_work.php
```

Service rule:

```text
Every service checks context, capability, policy, visibility, lifecycle state, content advisory policy, cultural protocol restrictions, retention, and redaction server-side.
```

---

## 13. Required form classes

The release package must include:

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

Form rule:

```text
Forms collect and shape input.
Final authority remains in classes/local policy and domain classes.
```

---

## 14. Required output classes

The release package must include:

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

Recommended output classes:

```text
classes/output/export_preview.php
classes/output/media_relation_list.php
classes/output/restricted_notice.php
classes/output/validation_panel.php
```

Output rule:

```text
Output classes format permission-filtered data.
Output classes must not authorize access or expose hidden metadata.
```

---

## 15. Required templates

The release package must include:

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

Recommended templates:

```text
templates/action_menu.mustache
templates/empty_state.mustache
templates/export_preview.mustache
templates/filter_bar.mustache
templates/restricted_notice.mustache
```

Template rule:

```text
Templates render pre-filtered data.
Templates must not contain hidden restricted data for later client-side display.
```

---

## 16. Required AMD files

Required AMD source files:

```text
amd/src/archive.js
amd/src/content_advisory.js
amd/src/export.js
amd/src/external_work.js
amd/src/kristal.js
amd/src/media.js
amd/src/media_collection.js
```

Required AMD build files:

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
Generated AMD build files are not edited by hand.
```

Release build rule:

```text
A release package must include generated amd/build files.
```

---

## 17. Required event classes

The release package must include:

```text
classes/event/archive_viewed.php
classes/event/archive_item_created.php
classes/event/archive_item_validated.php
classes/event/archive_item_revised.php
classes/event/archive_item_exported.php
classes/event/content_marker_created.php
classes/event/content_marker_reviewed.php
classes/event/external_work_created.php
classes/event/media_collection_created.php
classes/event/media_created.php
classes/event/media_exported.php
classes/event/media_updated.php
classes/event/media_version_created.php
```

Event rule:

```text
Events audit successful state changes.
Events must not expose raw media, restricted content, private cultural protocol notes, hidden integrity details, or redacted data.
```

---

## 18. Required scheduled tasks

The release package must include:

```text
classes/task/generate_archive_exports.php
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_content_marker_index.php
classes/task/rebuild_media_search.php
classes/task/validate_pending_items.php
```

Scheduled task registration belongs in:

```text
db/tasks.php
```

Task rule:

```text
Scheduled tasks reuse classes/local domain logic.
Scheduled tasks do not bypass policy checks for generated outputs.
```

---

## 19. Required backup and restore files

The release package must include:

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

Backup/restore must preserve:

```text
archive records
archive items
proofs
Kristals
provenance
revisions
exports
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
file areas
UUIDs
visibility
restricted state
audience suitability
cultural protocol flags
manifest references
```

Backup/restore rule:

```text
Restore reconstructs module-owned state.
Restore does not create external authority or make restricted material public.
```

---

## 20. Required privacy provider

The release package must include:

```text
classes/privacy/provider.php
```

The privacy provider must cover:

```text
archive records created by user
archive records modified by user
proof records created by user
Kristals created by user
provenance records involving user
revision records created by user
export records created by user
media records created by user
media versions created by user
media collections created by user
media relations created by user
media tags created by user
media source records created by user
content markers created by user
content reviews performed by user
external works created by user
files uploaded by user
review notes containing personal data
metadata containing personal data
```

Privacy rule:

```text
Privacy export is not a permission bypass.
Restricted cultural protocol notes and third-party data must be redacted or filtered.
```

---

## 21. Required language files

The release package must include:

```text
lang/en/uckkarchive.php
lang/fr/uckkarchive.php
```

Language files must include strings for:

```text
plugin identity
capabilities
settings
forms
services
events
archive UI
media UI
collections
relations
versions
content advisories
cultural protocols
external works
validation
privacy
backup/restore
exports
errors
warnings
access messages
```

Language rule:

```text
Every public UI string has matching English and French keys.
Templates and AMD modules use language strings, not hard-coded display text.
```

---

## 22. Required pix files

The release package must include:

```text
pix/icon.svg
```

Recommended pix files:

```text
pix/media.svg
pix/collection.svg
pix/content_advisory.svg
pix/external_work.svg
```

Pix rule:

```text
pix contains static plugin interface assets only.
User-uploaded media never belongs in pix.
```

---

## 23. Required tests

The release package must include:

```text
tests/archive_test.php
tests/backup_restore_test.php
tests/content_advisory_test.php
tests/export_test.php
tests/external_work_test.php
tests/file_api_test.php
tests/lib_test.php
tests/media_library_test.php
tests/privacy_provider_test.php
tests/services_test.php
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

Testing coverage must include:

```text
installation schema
upgrade migration
capabilities
archive workflows
media workflows
media versioning
media collections
media relations
media tags
media source records
external works
content advisory tags
content tag sets
content markers
content reviews
file areas
pluginfile access
privacy provider
backup/restore
export manifest
restricted access
cultural protocol restrictions
service authorization
UI rendering
AMD service error handling
```

Testing rule:

```text
Tests verify final target behavior, not historical transitions.
```

---

## 24. Required File API areas

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

File-area rule:

```text
classes/local/file_area_registry.php is the central file-area registry.
Pluginfile handling, privacy, backup, restore, services, and tests must use the registry.
```

---

## 25. Export package requirements

Archive/media export packages must include:

```text
manifest.json
```

The manifest must include:

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
Exports are portable and explainable.
Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.
```

---

## 26. Build requirements

Before packaging, generated files must be current.

Required generated AMD build outputs:

```text
amd/build/archive.min.js
amd/build/content_advisory.min.js
amd/build/export.min.js
amd/build/external_work.min.js
amd/build/kristal.min.js
amd/build/media.min.js
amd/build/media_collection.min.js
```

Build rule:

```text
Do not ship stale AMD build files.
Do not edit generated AMD build files manually.
```

The release package must not require a developer build step to run after installation in ordinary Moodle use.

---

## 27. Installation requirements

The release package must install cleanly from:

```text
mod/uckkarchive
```

Installation must create:

```text
all required archive tables
all required media tables
all required content advisory tables
all required external work tables
all capabilities
all scheduled tasks
all service declarations
all event observers
```

Installation must not require:

```text
manual database edits
manual file area creation
manual public folder creation
manual copying of user media
hard dependency on tool_uckkintegrity
```

---

## 28. Upgrade requirements

Upgrade must support existing installs through:

```text
db/upgrade.php
```

Upgrade must be able to add or migrate:

```text
media tables
media source records
media versions
media collections
media relations
content tags
content tag sets
content markers
content reviews
external works
new file areas
new capabilities
new service declarations
new scheduled tasks
UUID fields
visibility normalization
```

Upgrade rule:

```text
Upgrade must preserve existing archive data.
Upgrade must not make restricted records public.
Upgrade must not delete user files unless explicitly governed by retention policy.
```

Compatibility normalization:

```text
institutional -> institution
```

---

## 29. Security requirements

The release must enforce:

```text
require_login
context validation
capability checks
sesskey checks for mutations
server-side policy checks
Moodle File API pluginfile checks
service parameter validation
service return filtering
privacy-aware redaction
restricted data filtering
cultural protocol filtering
```

Security rule:

```text
No template, AMD module, or client-side filter is trusted as an authority layer.
```

---

## 30. Privacy requirements

The release must support:

```text
privacy metadata declaration
user data export
user data deletion where permitted
context deletion where permitted
redaction where required
retention-aware deletion
restricted data filtering
third-party data filtering
cultural protocol note protection
```

Privacy rule:

```text
Privacy compliance must include archive, media, content advisory, external work, and file records owned by the module.
```

---

## 31. Backup/restore requirements

The release must support Moodle backup and restore for:

```text
activity instance
archive records
media records
content advisory records
external works
files
UUID mappings
relations
collections
visibility
review states
restricted states
export manifests
```

Restore rule:

```text
Restored data remains subject to restored capabilities, visibility, restricted state, content advisory rules, and cultural protocol rules.
```

---

## 32. UI release requirements

The release UI must include:

```text
archive view
archive item card
media library
media card
media upload
media collection
media version list
media relation list
content advisory panel
content marker locator display
content review UI
external work card
proof card
Kristal card
provenance panel
validation panel
export preview
restricted notice
```

UI rule:

```text
The UI must render only policy-filtered data.
The UI must not leak restricted archive, media, cultural protocol, content review, or external work metadata.
```

---

## 33. Content advisory release requirements

The release must support:

```text
content advisory tags
content tag sets
content markers
content reviews
cultural protocol tags
audience suitability
locator types
external work markers
internal media markers
manual reference markers
review states
restricted cultural visibility
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

Content advisory rule:

```text
A content advisory does not ban media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 34. External work release requirements

The release must support external works such as:

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

External work rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 35. Non-release files

The release package must not include:

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
vendor/ unless intentionally required and documented
runtime export files outside Moodle File API
codedump files
AI scratch files
local environment notes
database dumps
test output artifacts
coverage reports
```

Known non-release example pattern:

```text
lang/en/uckkarchive.php.bak_*
```

Backup language files must not be shipped.

---

## 36. Packaging layout

The final package must expand to:

```text
uckkarchive/
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

Packaging rule:

```text
The ZIP root should be uckkarchive/, not mod/uckkarchive/uckkarchive/ and not a repository wrapper folder.
```

---

## 37. Duplication and reuse requirements

The module must be structured so troubleshooting can focus on:

```text
mod_uckkarchive code
mod_uckkarchive tables
mod_uckkarchive capabilities
mod_uckkarchive file areas
mod_uckkarchive services
mod_uckkarchive privacy provider
mod_uckkarchive backup/restore logic
mod_uckkarchive UI
```

Duplication rule:

```text
The module must remain modular enough to duplicate or adapt for future archive/media use cases without becoming detached from Moodle APIs.
```

---

## 38. Release verification commands

Before release, the implementation should be compatible with Moodle checks for:

```text
PHP syntax
Moodle code checker
PHPUnit tests
Behat tests
AMD build generation
install test
upgrade test
backup/restore test
privacy provider test
external services test
```

Command names and exact tooling may vary by Moodle development environment.

The release specification requires the corresponding checks, not a particular local shell layout.

---

## 39. Final release rule

A clean `mod_uckkarchive` release contains a Moodle-native, self-contained archive/media/content-advisory module.

It includes the database schema, upgrade path, capabilities, services, tasks, events, File API areas, privacy provider, backup/restore implementation, UI layer, AMD build files, templates, tests, and final-state documentation needed to install, troubleshoot, duplicate, and maintain the module.

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
