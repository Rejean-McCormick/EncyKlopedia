# 03 — File Architecture

**Path:** `docs/03_file_architecture.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** Complete file and folder architecture for the self-contained UCKK Archive, Media Library, and Content Advisory Moodle activity module.

---

## 1. Purpose

This document defines the final file architecture for `mod_uckkarchive`.

The module is:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

The file architecture must support:

```text
archive memory
media library management
content advisories
cultural sensitivity tags
content markers
external works
foreign media references
proof records
Kristals
provenance
revision history
validation
restricted metadata
exports
backup/restore
privacy
testing
```

This document is descriptive. It defines the final target structure to code.

It is not a historical document, gap register, release note, or acceptance checklist.

---

## 2. Canonical plugin paths

Canonical Moodle path:

```text
mod/uckkarchive
```

Active Moodle path:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
```

Source repository path:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive
```

Documentation path:

```text
mod/uckkarchive/docs
```

Moodle component:

```text
mod_uckkarchive
```

Plugin type:

```text
mod
```

Plugin folder:

```text
uckkarchive
```

---

## 3. Top-level folder architecture

```text
mod/uckkarchive/
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

Top-level rule:

```text
Root PHP files coordinate HTTP requests and Moodle entry points.
Business authority belongs in classes/local.
External service contracts belong in classes/external.
Renderable data belongs in classes/output.
Templates render pre-filtered data.
AMD modules provide client-side behavior only.
```

---

## 4. Root PHP files

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
validate.php
version.php
view.php
```

| File | Role |
|---|---|
| `add.php` | Controller for adding archive items, media references, proof records, or draft archive material. |
| `export.php` | Controller for export preview, export request, export download flow, and export status display. |
| `index.php` | Moodle course-level index page for all `uckkarchive` activities in a course. |
| `item.php` | Controller for a single archive item, including item view, item panels, media links, provenance, and validation display. |
| `lib.php` | Moodle module callbacks, pluginfile handler, navigation integration, feature declarations, deletion hooks, and core plugin callbacks. |
| `locallib.php` | Procedural helper compatibility layer. New domain logic belongs in `classes/local`. |
| `media.php` | Controller for the media library page, media browsing, media collection browsing, and media-management entry points. |
| `mod_form.php` | Moodle activity instance configuration form. |
| `settings.php` | Moodle site administration settings for the plugin. |
| `validate.php` | Controller for validation, revision, contestation, restriction, and review flows. |
| `version.php` | Moodle plugin version, maturity, release, component, and dependency metadata. |
| `view.php` | Main activity view controller. |

Controller rule:

```text
Controllers do not own policy.
Controllers resolve request context and delegate to classes/local, classes/form, classes/output, and external service contracts.
```

---

## 5. Root asset files

```text
styles.css
```

| File | Role |
|---|---|
| `styles.css` | Plugin CSS for archive, media library, cards, panels, advisory badges, restricted markers, validation states, and collections. |

CSS rule:

```text
CSS must not hide restricted data as a security mechanism.
Restricted data must be filtered server-side before rendering.
```

---

## 6. AMD source files

```text
amd/src/archive.js
amd/src/content_advisory.js
amd/src/export.js
amd/src/external_work.js
amd/src/kristal.js
amd/src/media.js
amd/src/media_collection.js
```

| File | Role |
|---|---|
| `amd/src/archive.js` | Archive item list interactions, filtering, archive item cards, item panels, and archive UI refresh. |
| `amd/src/content_advisory.js` | Content advisory panel interactions, marker UI, advisory badges, suitability display, and reviewer UI behavior. |
| `amd/src/export.js` | Export preview, export option UI, export progress, export status, and export action wiring. |
| `amd/src/external_work.js` | External work lookup, reference display, work-card refresh, and locator UI behavior. |
| `amd/src/kristal.js` | Kristal card interactions, Kristal edit UI, and Kristal-specific service calls. |
| `amd/src/media.js` | Media library browsing, media upload UI, media cards, previews, thumbnails, filtering, and media metadata editing. |
| `amd/src/media_collection.js` | Media collection creation, ordering, membership editing, and collection view interactions. |

AMD source rule:

```text
AMD source files drive UI behavior.
They do not authorize access.
They do not decide validation, restriction, redaction, cultural protocol, or export permission.
```

---

## 7. AMD build files

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
amd/src/* is the source of truth.
amd/build/* is generated for Moodle runtime.
Generated AMD files are not edited manually.
```

---

## 8. Backup and restore files

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

| File | Role |
|---|---|
| `backup/moodle2/backup_uckkarchive_activity_task.class.php` | Moodle backup task class. Registers backup steps, file areas, and encoded links. |
| `backup/moodle2/backup_uckkarchive_stepslib.php` | Backup structure for activity, archive items, media objects, media versions, collections, tags, relations, content advisories, external works, proofs, Kristals, provenance, revisions, exports, files, and metadata. |
| `backup/moodle2/restore_uckkarchive_activity_task.class.php` | Moodle restore task class. Registers restore steps and link decoding. |
| `backup/moodle2/restore_uckkarchive_stepslib.php` | Restore implementation for records, remapped IDs, restored UUIDs, files, relations, collections, advisories, and external references. |

Backup/restore rule:

```text
Backup preserves module-owned archive/media/content-advisory state.
Restore reconstructs module-owned records only.
Restore does not create gradebook authority, Assembly authority, integrity case authority, or report authority.
```

---

## 9. Completion files

```text
classes/completion/custom_completion.php
```

| File | Role |
|---|---|
| `classes/completion/custom_completion.php` | Custom Moodle completion logic for viewing, submitting, revising, validating, or interacting with archive/media records. |

---

## 10. Event classes

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

| File | Role |
|---|---|
| `classes/event/archive_viewed.php` | Fired when an archive activity or archive view is viewed. |
| `classes/event/archive_item_created.php` | Fired when an archive item is created. |
| `classes/event/archive_item_validated.php` | Fired when an archive item validation state changes. |
| `classes/event/archive_item_revised.php` | Fired when an archive item revision is created. |
| `classes/event/archive_item_exported.php` | Fired when archive material is exported. |
| `classes/event/media_created.php` | Fired when a media object is created. |
| `classes/event/media_updated.php` | Fired when media metadata or lifecycle state changes. |
| `classes/event/media_version_created.php` | Fired when a media version is created. |
| `classes/event/media_collection_created.php` | Fired when a media collection is created. |
| `classes/event/media_exported.php` | Fired when media is exported. |
| `classes/event/content_marker_created.php` | Fired when a content marker/advisory locator is created. |
| `classes/event/content_marker_reviewed.php` | Fired when a content marker or content advisory is reviewed. |
| `classes/event/external_work_created.php` | Fired when an external work reference is created. |

Event rule:

```text
Events record successful state changes.
Events must not expose restricted content, raw media, private notes, culturally restricted details, or redacted data.
```

---

## 11. External service files — archive

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

Archive service rule:

```text
Archive services check context, capability, ownership, visibility, validation state, restricted state, provenance, redaction, and workflow policy.
```

---

## 12. External service files — media library

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

Media service rule:

```text
Media services check media policy, media status, file access, ownership, collection membership, relation validity, download authority, export authority, and restricted media access.
```

---

## 13. External service files — content advisories and external works

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

Content advisory service rule:

```text
Content advisory services check context, capability, visibility, cultural protocol restrictions, review state, redaction, and suitability rules.
```

---

## 14. External service files — exports

```text
classes/external/get_export_preview.php
classes/external/export_items.php
classes/external/export_media.php
classes/external/export_collection.php
classes/external/get_export_status.php
```

Export service rule:

```text
Export services generate permission-filtered, redaction-aware, culturally aware, manifest-backed export packages.
```

---

## 15. Form files

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

| File | Role |
|---|---|
| `classes/form/archive_item_form.php` | Archive item create/edit form. |
| `classes/form/content_marker_form.php` | Content marker/advisory locator form. |
| `classes/form/content_review_form.php` | Human review form for content markers and cultural protocol notes. |
| `classes/form/content_tag_form.php` | Content advisory and cultural tag form. |
| `classes/form/export_form.php` | Archive/media export options form. |
| `classes/form/external_work_form.php` | External/foreign work reference form. |
| `classes/form/kristal_form.php` | Kristal create/edit form. |
| `classes/form/media_collection_form.php` | Media collection create/edit form. |
| `classes/form/media_form.php` | Media object create/edit/upload form. |
| `classes/form/media_relation_form.php` | Media relation create/edit form. |
| `classes/form/media_version_form.php` | Media version upload/edit form. |
| `classes/form/validation_form.php` | Archive validation, revision, restriction, and contestation form. |

Form rule:

```text
Forms collect and shape input.
Policy remains in classes/local.
```

---

## 16. Local domain files — archive

```text
classes/local/archive_item.php
classes/local/archive_policy.php
classes/local/export_package.php
classes/local/kristal.php
classes/local/proof.php
classes/local/provenance.php
classes/local/revision.php
```

| File | Role |
|---|---|
| `classes/local/archive_item.php` | Archive item domain logic. |
| `classes/local/archive_policy.php` | Archive policy for access, visibility, validation, restriction, revision, and export. |
| `classes/local/export_package.php` | Export package creation, manifest generation, and export file coordination. |
| `classes/local/kristal.php` | Kristal domain logic. |
| `classes/local/proof.php` | Proof record domain logic. |
| `classes/local/provenance.php` | Provenance and provenance hash logic. |
| `classes/local/revision.php` | Archive revision and version history logic. |

---

## 17. Local domain files — media

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

| File | Role |
|---|---|
| `classes/local/media.php` | Media object domain logic. |
| `classes/local/media_collection.php` | Media collection logic. |
| `classes/local/media_file.php` | Moodle File API coordination for media file areas. |
| `classes/local/media_policy.php` | Media access, download, edit, versioning, export, and restriction policy. |
| `classes/local/media_relation.php` | Media relation graph logic. |
| `classes/local/media_search.php` | Media search/filter logic. |
| `classes/local/media_source.php` | Media source and ownership classification logic. |
| `classes/local/media_tag.php` | Media tag logic. |
| `classes/local/media_version.php` | Media versioning logic. |

---

## 18. Local domain files — content advisory and external work

```text
classes/local/content_marker.php
classes/local/content_policy.php
classes/local/content_review.php
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/external_work.php
```

| File | Role |
|---|---|
| `classes/local/content_marker.php` | Content advisory locator logic for timecodes, pages, scenes, sections, and manual references. |
| `classes/local/content_policy.php` | Content advisory, cultural protocol, suitability, and restricted-cultural access policy. |
| `classes/local/content_review.php` | Human review workflow for content markers, advisory tags, suitability, and cultural protocol notes. |
| `classes/local/content_tag.php` | Content advisory and cultural sensitivity tag logic. |
| `classes/local/content_tag_set.php` | Reusable tag-set vocabulary logic. |
| `classes/local/external_work.php` | External/foreign media and third-party work reference logic. |

---

## 19. Local infrastructure files

```text
classes/local/context_resolver.php
classes/local/file_area_registry.php
classes/local/manifest_builder.php
classes/local/metadata_validator.php
classes/local/uuid.php
```

| File | Role |
|---|---|
| `classes/local/context_resolver.php` | Central context, course, cm, archive, item, and media resolution. |
| `classes/local/file_area_registry.php` | Single source of truth for all archive, media, and content-advisory file areas. |
| `classes/local/manifest_builder.php` | Export manifest builder for archive/media/content advisory packages. |
| `classes/local/metadata_validator.php` | JSON metadata validation and normalization. |
| `classes/local/uuid.php` | Stable UUID generation, validation, and normalization. |

Local rule:

```text
classes/local is the authority layer for archive, media, content advisory, external work, and export behavior.
```

---

## 20. Output files

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

| File | Role |
|---|---|
| `classes/output/archive_item_card.php` | Renderable archive item card data. |
| `classes/output/archive_view.php` | Main archive view renderable data. |
| `classes/output/content_advisory_panel.php` | Renderable content advisory panel data. |
| `classes/output/external_work_card.php` | Renderable external work reference card data. |
| `classes/output/kristal_card.php` | Renderable Kristal card data. |
| `classes/output/media_card.php` | Renderable media card data. |
| `classes/output/media_collection.php` | Renderable media collection data. |
| `classes/output/media_library.php` | Renderable media library page data. |
| `classes/output/media_version_list.php` | Renderable media version list data. |
| `classes/output/provenance_panel.php` | Renderable provenance panel data. |
| `classes/output/renderer.php` | Moodle renderer for module templates. |

Output rule:

```text
Output classes prepare already-authorized data for templates.
Output classes do not grant access.
```

---

## 21. Privacy files

```text
classes/privacy/provider.php
```

Privacy provider covers:

```text
archive items
proofs
Kristals
provenance
revisions
exports
media objects
media versions
media collections
media relations
media tags
media sources
content tags
content tag sets
content markers
content reviews
external works
user-linked files
restricted metadata
culturally restricted metadata
```

Privacy rule:

```text
Privacy API behavior belongs to mod_uckkarchive for all records stored by mod_uckkarchive.
```

---

## 22. Observer and scheduled task files

```text
classes/observer.php
classes/task/generate_archive_exports.php
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
classes/task/validate_pending_items.php
```

| File | Role |
|---|---|
| `classes/observer.php` | Moodle event observer handlers. |
| `classes/task/generate_archive_exports.php` | Queued archive export generation. |
| `classes/task/generate_media_derivatives.php` | Queued media derivative generation. |
| `classes/task/generate_media_thumbnails.php` | Queued thumbnail generation. |
| `classes/task/purge_expired_exports.php` | Export retention cleanup. |
| `classes/task/rebuild_media_search.php` | Media search/index maintenance. |
| `classes/task/rebuild_content_marker_index.php` | Content marker and advisory locator index maintenance. |
| `classes/task/validate_pending_items.php` | Scheduled validation/maintenance helper. |

Task rule:

```text
Scheduled tasks reuse classes/local domain logic.
Scheduled tasks do not bypass policy checks for generated outputs.
```

---

## 23. Database files

```text
db/access.php
db/events.php
db/install.xml
db/services.php
db/tasks.php
db/upgrade.php
```

| File | Role |
|---|---|
| `db/access.php` | Moodle capability definitions. |
| `db/events.php` | Moodle observer declarations. |
| `db/install.xml` | Full current target database schema. |
| `db/services.php` | External service declarations. |
| `db/tasks.php` | Scheduled task declarations. |
| `db/upgrade.php` | Schema and data migration logic. |

Database file rule:

```text
db/install.xml defines the current target schema.
db/upgrade.php migrates existing installs to the current target schema.
```

---

## 24. Language files

```text
lang/en/uckkarchive.php
lang/fr/uckkarchive.php
```

Language files contain strings for:

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
cultural protocol messages
audience suitability messages
```

Language rule:

```text
Language files must not contain strings for removed or unused capabilities.
English and French language keys must remain aligned.
```

---

## 25. Template files

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

Template rule:

```text
Templates render permission-filtered data.
Templates do not enforce authority, visibility, cultural protocol, restriction, redaction, or download access.
```

---

## 26. Test files

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

| File | Role |
|---|---|
| `tests/archive_test.php` | Archive domain tests. |
| `tests/backup_restore_test.php` | Backup and restore tests. |
| `tests/content_advisory_test.php` | Content advisory, tag set, marker, review, and cultural protocol tests. |
| `tests/export_test.php` | Archive/media/content advisory export tests. |
| `tests/external_work_test.php` | External/foreign work reference tests. |
| `tests/file_api_test.php` | File API, pluginfile, file-area, and access tests. |
| `tests/lib_test.php` | Moodle callback and helper tests. |
| `tests/media_library_test.php` | Media object, version, collection, relation, source, and tag tests. |
| `tests/privacy_provider_test.php` | Privacy provider tests. |
| `tests/services_test.php` | External service and permission-filtering tests. |
| `tests/behat/uckkarchive.feature` | Archive UI behavior tests. |
| `tests/behat/uckkarchive_media.feature` | Media library UI behavior tests. |
| `tests/behat/uckkarchive_content_advisory.feature` | Content advisory UI behavior tests. |

Test rule:

```text
Tests verify final target behavior.
Tests must not depend on historical gap documents.
Tests must not require mod/uckkarchive:versionitem.
```

---

## 27. Pix assets

```text
pix/icon.svg
pix/media.svg
pix/collection.svg
pix/content_advisory.svg
pix/external_work.svg
```

| File | Role |
|---|---|
| `pix/icon.svg` | Main Moodle activity icon. |
| `pix/media.svg` | Media library icon. |
| `pix/collection.svg` | Media collection icon. |
| `pix/content_advisory.svg` | Content advisory icon. |
| `pix/external_work.svg` | External work reference icon. |

Pix rule:

```text
pix contains static plugin interface assets only.
User-uploaded media never belongs in pix.
```

---

## 28. Documentation files

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
Documentation describes final target behavior.
Documentation does not keep historical gap registers.
Documentation does not contain acceptance-checklist process files.
Documentation does not contain release-note process files.
```

---

## 29. Required database tables supported by this architecture

Archive tables:

```text
uckkarchive
uckkarchive_item
uckkarchive_proof
uckkarchive_kristal
uckkarchive_prov
uckkarchive_rev
uckkarchive_export
```

Media tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
```

Content advisory and external-work tables:

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
id is the local Moodle database primary key.
uuid is the stable portable object identity.
```

---

## 30. Canonical File API areas supported by this architecture

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

File-area registry rule:

```text
classes/local/file_area_registry.php is the single source of truth for file areas.
```

---

## 31. Non-release files

These files are not part of the clean release package:

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
runtime export files outside Moodle File API
codedump files
AI scratch files
```

Non-release rule:

```text
Generated runtime data belongs in Moodle runtime storage or Moodle File API, not in source control.
```

---

## 32. Final architecture rule

```text
mod_uckkarchive is a self-contained archive, media-library, and content-advisory module.

Root files coordinate.
classes/local owns authority.
classes/external exposes services.
classes/output prepares render data.
templates render.
AMD modules provide UI behavior.
db declares schema, capabilities, services, tasks, events, and upgrades.
backup/moodle2 preserves and restores module-owned records.
lang provides strings.
tests verify final target behavior.
pix provides static UI assets.
docs define the target implementation.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
