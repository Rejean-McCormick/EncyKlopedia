# UCKK Archive — Shared Documentation Variables

**Path:** `docs/_alignment_variables.md`  
**Component:** `mod_uckkarchive`  
**Purpose:** Canonical variables for generating the clean final-state documentation set across separate conversations.  
**Use:** Paste this file at the beginning of every document-generation conversation.

---

## 1. Documentation mode

```text
DOC_MODE = final_state_specification
DOC_STYLE = descriptive
DOC_HISTORY = forbidden
DOC_GAPS = forbidden
DOC_ACCEPTANCE_CHECKLIST = forbidden
DOC_RELEASE_NOTES = forbidden
DOC_TARGET = build-ready module specification
```

Rules:

```text
Do not write historical narrative.
Do not keep gap registers.
Do not write acceptance checklists.
Do not write release notes.
Do not describe old decisions as alternatives.
Do not say "future optional" for required target features.
Describe only the final target architecture to be coded.
```

---

## 2. Plugin identity

```text
PLUGIN_NAME = UCKK Archive
PLUGIN_TYPE = mod
PLUGIN_FOLDER = uckkarchive
MOODLE_COMPONENT = mod_uckkarchive
MOODLE_PLUGIN_PATH = mod/uckkarchive
```

Canonical paths:

```text
SOURCE_DOCS_PATH = C:\mycode\UCKK\uckk-moodle\mod\uckkarchive\docs
ACTIVE_MOODLE_DOCS_PATH = C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive\docs
SOURCE_PLUGIN_PATH = C:\mycode\UCKK\uckk-moodle\mod\uckkarchive
ACTIVE_MOODLE_PLUGIN_PATH = C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
```

---

## 3. Core architecture formula

```text
ARCHITECTURE_FORMULA = Moodle-native on the outside, self-contained archive/media/content-advisory system on the inside.
```

Canonical module definition:

```text
mod_uckkarchive = self-contained Moodle activity module for archive memory, media library management, and content advisory governance.
```

The module owns internally:

```text
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
cultural sensitivity tags
content tag sets
content markers
content reviews
external works
foreign media references
media source records
audience suitability rules
export packages
export manifests
```

The module uses Moodle for:

```text
plugin lifecycle
course module context
users
roles
capabilities
groups
File API
Privacy API
Backup API
Restore API
External Services API
events
settings
language strings
rendering
scheduled tasks
```

---

## 4. Boundary variables

```text
GRADE_OWNER = Moodle gradebook
REGISTRY_OWNER = local_uckk
CHALLENGE_OWNER = mod_uckkchallenge
ASSEMBLY_OWNER = mod_uckkassembly
INTEGRITY_OWNER = tool_uckkintegrity
REPORT_OWNER = report_uckk
ARCHIVE_OWNER = mod_uckkarchive
```

Boundary rules:

```text
mod_uckkarchive does not own grades.
mod_uckkarchive does not own transcripts.
mod_uckkarchive does not own enrolment authority.
mod_uckkarchive does not own administrative academic registry authority.
mod_uckkarchive may reference challenge ids, assembly ids, integrity case ids, course ids, and competency ids.
mod_uckkarchive must degrade gracefully when optional owner plugins are not installed.
```

Optional integration variables:

```text
OPTIONAL_CHALLENGE_COMPONENT = mod_uckkchallenge
OPTIONAL_ASSEMBLY_COMPONENT = mod_uckkassembly
OPTIONAL_INTEGRITY_COMPONENT = tool_uckkintegrity
OPTIONAL_REPORT_COMPONENT = report_uckk
```

No hard dependency rule:

```text
No install-time hard dependency on mod_uckkchallenge, mod_uckkassembly, tool_uckkintegrity, or report_uckk.
```

---

## 5. Active documentation set

Use this clean final-state documentation set:

```text
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
docs/25_mediatheque_public_explorer.md
```

Do not generate these old/process files:

```text
docs/05_media_database_division.md
docs/09_didactic_material_workflows.md
docs/24_acceptance_checklist.md
docs/25_known_gaps_and_corrections.md
docs/26_release_notes.md
docs/27_file_architecture_manifest.md
```

Documentation-set rule:

```text
docs/25_mediatheque_public_explorer.md defines the public Médiathèque façade.
It does not define a second internal media-library engine.
```

---

## 6. Root file architecture

Required root files:

```text
version.php
lib.php
locallib.php
mod_form.php
view.php
index.php
media.php
export.php
item.php
styles.css
settings.php
README.md
```

Root rule:

```text
Root PHP files are controllers, integration hooks, or Moodle entry points.
Domain logic belongs in classes/local.
Output shaping belongs in classes/output.
AJAX/external contracts belong in classes/external.
```

---

## 7. Database tables

Canonical table prefix:

```text
TABLE_PREFIX = uckkarchive_
```

Required core tables:

```text
uckkarchive
uckkarchive_item
uckkarchive_proof
uckkarchive_revision
uckkarchive_validation
uckkarchive_kristal
uckkarchive_export
```

Required media tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_file
uckkarchive_media_collection
uckkarchive_media_collection_item
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_source
```

Required content advisory tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
```

Database rules:

```text
All tables must have id as primary key.
All portable objects must have uuid where applicable.
All human-created mutable tables must have timecreated and timemodified.
All user-authored tables must have userid or createdby/modifiedby where relevant.
```

UUID rule:

```text
Archive objects, media objects, content markers, external works, and export packages use UUIDs for export, restore, duplication, and cross-site portability.
```

---

## 8. Capabilities

Canonical archive capabilities:

```text
mod/uckkarchive:addinstance
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Canonical media capabilities:

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

Canonical content advisory capabilities:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
mod/uckkarchive:viewculturallyrestricted
mod/uckkarchive:manageexternalworks
```

Capability rules:

```text
Capabilities are gates, not full authority.
Policy classes still enforce context, ownership, visibility, status, validation state, restricted state, content advisory rules, cultural protocol rules, retention, and redaction.
```

Removed capability:

```text
mod/uckkarchive:versionitem = not used
```

Versioning permissions:

```text
archive item revision = mod/uckkarchive:reviseitem
media versioning = mod/uckkarchive:versionmedia
```

---

## 9. File API areas

Component:

```text
FILE_COMPONENT = mod_uckkarchive
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

File area rule:

```text
classes/local/file_area_registry.php is the central file-area registry.
All controllers, services, pluginfile handling, privacy provider, backup, restore, and tests must use the registry.
```

Forbidden storage:

```text
No production archive/media files in unmanaged public folders.
No binary media files directly in custom database fields.
No direct public file URLs as authority.
```

---

## 10. Media lifecycle

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

Media lifecycle rule:

```text
File existence is not media availability.
Media status controls usability.
Visibility controls access.
Policy controls download and export.
Content advisories describe suitability, cultural protocol, and access conditions.
Retention controls deletion.
```

---

## 11. Archive item statuses

Canonical archive item statuses:

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

---

## 12. Validation states

Canonical validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Validation rules:

```text
Validation is human-final.
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
AI cannot approve cultural protocol access.
```

---

## 13. Visibility values

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

---

## 14. Provenance values

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

Provenance rule:

```text
Provenance explains origin.
Provenance does not grant authority by itself.
```

---

## 15. Media relation types

Canonical media relation types:

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

Relation rule:

```text
Relations describe media graph meaning.
Relations do not transfer ownership to external plugins or external rights holders.
```

---

## 16. Content advisory subsystem

Canonical subsystem name:

```text
CONTENT_ADVISORY_SYSTEM = content advisories, cultural sensitivity tags, content markers, external works, reviews, and audience suitability rules
```

User-facing wording:

```text
content advisory
content warning
cultural advisory
cultural protocol
audience suitability
```

Avoid using `trigger` alone as the database/system name because it can be confused with database triggers.

Allowed user-facing phrase:

```text
trigger warning
```

Architecture rule:

```text
A content advisory does not ban the media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
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

Content advisory severity values:

```text
notice
moderate
strong
restricted
```

Content advisory review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Content tag set rule:

```text
uckkarchive_content_tag_set groups advisory tags into reusable vocabularies.
Examples: general_advisories, cultural_protocols, classroom_suitability, integrity_sensitive, youth_access.
```

Content review rule:

```text
uckkarchive_content_review records human review of content markers, advisory tags, cultural protocol notes, suitability, and restriction decisions.
AI may suggest tags or markers, but human review is required before advisory status becomes approved.
```

---

## 17. Content markers and locators

Canonical content marker table:

```text
uckkarchive_content_marker
```

Content marker purpose:

```text
Link a content advisory or cultural protocol tag to a precise location inside an internal media object, archive item, or external work.
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

Canonical locator examples:

```text
Movie Maïna -> sexual_violence -> 01:12:30-01:15:10
Book The Body Keeps the Score -> sexual_violence -> page 42-45
PDF -> culturally_sensitive -> page 7
Audio -> grief_or_mourning -> 00:08:12-00:09:40
Website -> colonial_violence -> url_fragment #section-3
```

Content marker rule:

```text
A content marker can point to internal media, archive items, media versions, external works, or manual references.
A content marker must include enough locator information to be useful without storing unauthorized copies of external content.
```

---

## 18. External works and foreign media

Canonical external work table:

```text
uckkarchive_external_work
```

External work purpose:

```text
Represent works not produced by UCKK that may be referenced, taught, reviewed, tagged, or connected to archive/media records.
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

Canonical media source table:

```text
uckkarchive_media_source
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

External/foreign media rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 18.1 Public Médiathèque surface

Canonical public surface variables:

```text
PUBLIC_MEDIATHEQUE_PAGE_NAME = Médiathèque
PUBLIC_MEDIATHEQUE_PAGE_KEY = mediatheque
PUBLIC_MEDIATHEQUE_EXPLORER_NAME = Explorateur Médiathèque
PUBLIC_MEDIATHEQUE_EXPLORER_KEY = mediatheque_explorer
PUBLIC_MEDIATHEQUE_ROUTE = /local/uckk/mediatheque.php
PUBLIC_MEDIATHEQUE_SURFACE_COMPONENT = local_uckk
PUBLIC_MEDIATHEQUE_DATA_COMPONENT = mod_uckkarchive
PUBLIC_MEDIATHEQUE_SERVICE = mod_uckkarchive_search_mediatheque
PUBLIC_MEDIATHEQUE_SITEWIDE_ARCHIVEID = 0
PUBLIC_MEDIATHEQUE_SITEWIDE_CMID = 0
```

Canonical architecture rule:

```text
Médiathèque = public page.
Explorateur Médiathèque = public search/filter/navigation component.
mod_uckkarchive = media data owner and policy authority.
local_uckk = public shell, route, page rendering and navigation.
```

Canonical runtime flow:

```text
local/uckk/mediatheque.php
→ local_uckk public page shell
→ local/uckk/amd/src/mediatheque_explorer.js
→ mod_uckkarchive_search_mediatheque
→ classes/local/public_mediatheque_service.php
→ classes/local/public_mediatheque_repository.php
→ existing media tables and policies
```

Public scope rule:

```text
cmid > 0 = module-scoped public search.
archiveid > 0 = archive-scoped public search.
cmid = 0 and archiveid = 0 = site-wide public search.
```

Public DTO envelope:

```text
context
filters
facets
items
pagination
notices
warnings
empty
```

Public item DTO:

```text
uuid
objecttype
title
subtitle
summary
mediatype
mimetype
language
thumbnailurl
detailurl
source
rights
status
visibility
validation
badges
advisories
culturalprotocol
relations
actions
```

Public safety rule:

```text
The public Médiathèque never exposes original files, private notes, cultural protocol notes, raw metadata, review rationale, provenance hashes, integrity case ids, or internal database identifiers.
```

Public reuse rule:

```text
Do not create a second media-library engine.
Do not create mediatheque_card.mustache, mediatheque_detail.mustache, mediatheque_marker.mustache, get_mediatheque_item.php, get_mediatheque_filters.php, or get_mediatheque_collection.php unless the public contract explicitly changes.
Reuse the existing media library domain, templates, cards, advisories, collections and policies.
```

---

## 19. Export manifest

Canonical manifest filename:

```text
manifest.json
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
Exports are portable and explainable.
Exports do not bypass permissions, visibility, retention, redaction, cultural protocol restrictions, or content advisory policy.
```

---

## 20. Required classes/local files

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
classes/local/public_mediatheque_repository.php
classes/local/public_mediatheque_service.php
classes/local/revision.php
classes/local/uuid.php
```

Local rule:

```text
classes/local is the authority layer for archive/media/content-advisory behavior.
public_mediatheque_repository.php and public_mediatheque_service.php are public façade adapters, not a second media engine.
```

---

## 21. Required external service files

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
classes/external/search_mediatheque.php
```

Service rule:

```text
Content advisory services must check context, capability, visibility, cultural protocol restrictions, review state, and redaction rules.
search_mediatheque.php is the single public Médiathèque AJAX endpoint.
search_mediatheque.php delegates to public_mediatheque_service.php and does not implement media search logic directly.
```

---

## 22. Required database files

```text
db/access.php
db/events.php
db/install.xml
db/services.php
db/tasks.php
db/upgrade.php
```

Database rule:

```text
db/install.xml defines the full current target schema.
db/upgrade.php migrates existing installs to the current target schema.
```

---

## 23. Required form files

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
Policy remains in classes/local.
```

---

## 24. Required output and template files

Required output files:

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

Required template files:

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
Templates receive pre-filtered render data.
Templates do not enforce authority.
```

---

## 25. Required AMD files

```text
amd/src/archive.js
amd/src/content_advisory.js
amd/src/export.js
amd/src/external_work.js
amd/src/kristal.js
amd/src/media.js
amd/src/media_collection.js
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

---

## 26. Required event classes

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

Event rule:

```text
Events audit successful state changes.
Events must not expose restricted content, raw content, private cultural protocol notes, or redacted details.
```

---

## 27. Required task files

```text
classes/task/generate_archive_exports.php
classes/task/generate_media_derivatives.php
classes/task/generate_media_thumbnails.php
classes/task/purge_expired_exports.php
classes/task/rebuild_media_search.php
classes/task/rebuild_content_marker_index.php
classes/task/validate_pending_items.php
```

Task rule:

```text
Scheduled tasks reuse classes/local domain logic.
Scheduled tasks do not bypass policy checks for generated outputs.
```

---

## 28. Required test files

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
tests/public_mediatheque_repository_test.php
tests/public_mediatheque_service_test.php
tests/external/search_mediatheque_test.php
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

Testing rule:

```text
Tests verify the final target behavior, not historical transitions.
Public Médiathèque tests verify the public façade contract only.
They do not duplicate the internal media-library engine tests.
```

---

## 29. Writing instructions for every generated doc

Each document must:

```text
describe final target behavior
use the variables in this file
avoid historical framing
avoid gap language
avoid acceptance checklist language
avoid release notes language
avoid "future optional" for required media-library architecture
avoid "future optional" for content advisory architecture
use consistent table names
use consistent capabilities
use consistent file areas
use consistent plugin boundaries
use content advisory terminology consistently
include cultural protocol handling where relevant
include external/foreign media handling where relevant
distinguish public Médiathèque façade from internal media-library engine
use search_mediatheque.php only as the public AJAX endpoint
state that local_uckk renders the public page and mod_uckkarchive owns media data and policies
```

Each document must not include:

```text
known gaps
known corrections
acceptance checklist
release notes
old architecture debate
media as only generic item attachment
content advisories as only a JSON field
versionitem capability
hard dependency on tool_uckkintegrity
a second Médiathèque media engine
duplicated mediatheque_card or mediatheque_detail templates
duplicated get_mediatheque_item, get_mediatheque_filters, or get_mediatheque_collection services
authorization decisions in AMD or Mustache
```

---

## 30. Standard final sentence

Every generated document may end with a variant of this rule:

```text
This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
```