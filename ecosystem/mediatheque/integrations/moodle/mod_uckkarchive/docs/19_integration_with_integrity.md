# 19 — Integration with Integrity

**Path:** `docs/19_integration_with_integrity.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Related component:** `tool_uckkintegrity`  
**Status:** Final target specification  
**Scope:** Optional integration between the UCKK Archive/Media Library module and the UCKK Integrity tool.

---

## 1. Purpose

This document defines how `mod_uckkarchive` integrates with integrity-related workflows while preserving clear domain ownership.

`mod_uckkarchive` is a self-contained Moodle activity module for archive memory, media library management, and content advisory governance.

`tool_uckkintegrity` is the integrity procedure authority.

The integration is optional.

Ordinary archive, media, and content advisory workflows must work without `tool_uckkintegrity`.

---

## 2. Core decision

Canonical integration rule:

```text
tool_uckkintegrity owns integrity procedure.
mod_uckkarchive owns archive/media preservation.
```

`mod_uckkarchive` may preserve:

```text
integrity-related archive items
integrity-related media
integrity evidence bundles
restricted summaries
proof files
content advisories
content markers
provenance
revision history
validation state
export packages
export manifests
```

`mod_uckkarchive` must not own:

```text
integrity case authority
integrity investigation procedure
integrity findings
integrity sanctions
integrity appeal workflow
integrity case closure
integrity officer assignment
integrity procedural deadlines
```

Preservation does not transfer authority.

---

## 3. Dependency rule

`tool_uckkintegrity` is optional.

Dependency rule:

```text
tool_uckkintegrity = optional integration
ordinary archive/media/content-advisory operation must not require tool_uckkintegrity
integrity-specific features must be hidden, disabled, or fail closed when tool_uckkintegrity is absent
```

The plugin must not declare a hard runtime dependency on `tool_uckkintegrity` unless a future release intentionally changes the architecture.

Allowed behavior when `tool_uckkintegrity` is absent:

```text
archive items continue to work
media library continues to work
content advisories continue to work
external works continue to work
ordinary exports continue to work
integrity-specific links are unavailable
integrity-specific import/sync is disabled
integrity-specific restricted views fail closed
```

---

## 4. Architecture boundary

Canonical ownership:

```text
INTEGRITY_OWNER = tool_uckkintegrity
ARCHIVE_OWNER = mod_uckkarchive
```

Boundary rules:

```text
mod_uckkarchive can reference integrity cases.
mod_uckkarchive can preserve integrity-related evidence.
mod_uckkarchive can preserve integrity-related media.
mod_uckkarchive can preserve integrity-related summaries.
mod_uckkarchive can preserve integrity-related exports.
mod_uckkarchive can apply restricted visibility to integrity-related records.
mod_uckkarchive can record provenance showing integrity origin.
mod_uckkarchive cannot decide the integrity case.
mod_uckkarchive cannot replace the integrity workflow.
mod_uckkarchive cannot become the integrity case registry.
```

---

## 5. Integration object model

Integrity references in `mod_uckkarchive` must be stored as archive-owned references, not as copied procedure authority.

Archive-owned records may include:

```text
sourcecomponent = tool_uckkintegrity
sourcearea = case | evidence | finding_summary | export | note | attachment
sourceid = external integrity record id
sourceuuid = external integrity UUID when available
sourcelabel = human-readable reference
sourcetimecreated = source creation timestamp when available
sourcetimemodified = source modification timestamp when available
```

Reference rule:

```text
Integrity source references identify origin.
They do not make mod_uckkarchive the procedural authority.
```

---

## 6. Archive item integration

Integrity-related archive items may represent:

```text
case evidence snapshot
restricted case summary
integrity media bundle
integrity proof record
integrity export record
integrity timeline snapshot
appeal-supporting archive material
redacted public summary
validated institutional memory item
```

Archive item fields should support:

```text
type = integrity_summary | integrity_evidence | integrity_export | proof | media_bundle | restricted_summary
visibility = restricted_integrity
validationstate = unverified | human_reviewed | verified | contested | invalidated | archived
provenance = integrity
```

Archive item rule:

```text
An integrity-related archive item preserves a record or snapshot.
It does not become the active integrity case.
```

---

## 7. Media integration

Integrity-related media is managed through the normal media library model.

Relevant tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
uckkarchive_media_source
```

Integrity media source values may include:

```text
submitted_to_uckk
imported
restricted_reference
external_reference_only
```

Integrity media visibility should normally use:

```text
restricted_integrity
restricted
private
staff_only
```

Media rule:

```text
Integrity-related media remains a media object.
It is not stored as unmanaged evidence files outside Moodle File API.
```

---

## 8. File API integration

Integrity-related files are stored through Moodle File API under `mod_uckkarchive`.

Relevant archive file areas:

```text
integrity_exports
proof_files
item_files
decision_attachments
provenance_files
validation_files
revision_files
export_package
export_manifest
```

Relevant media file areas:

```text
media_original
media_preview
media_thumbnail
media_derivative
media_caption
media_transcript
media_attachment
```

Relevant content advisory file areas:

```text
content_review_files
external_work_reference_files
cultural_protocol_files
```

File rule:

```text
Integrity files preserved by mod_uckkarchive are archive/media files.
They are not live integrity procedure files unless explicitly accessed from tool_uckkintegrity.
```

---

## 9. Restricted integrity visibility

Canonical visibility value:

```text
restricted_integrity
```

Restricted integrity visibility applies to:

```text
archive items
media objects
media versions
media collections
content markers
content reviews
external work references
export packages
manifest entries
proof records
provenance records
revision records
```

Restricted integrity rule:

```text
restricted_integrity records must not leak through search, thumbnails, previews, export manifests, course displays, backup previews, events, logs, or AJAX responses.
```

---

## 10. Capability model

Archive capabilities relevant to integrity integration:

```text
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Media capabilities relevant to integrity integration:

```text
mod/uckkarchive:viewmedia
mod/uckkarchive:addmedia
mod/uckkarchive:editmedia
mod/uckkarchive:downloadmedia
mod/uckkarchive:versionmedia
mod/uckkarchive:exportmedia
mod/uckkarchive:viewrestrictedmedia
```

Content advisory capabilities relevant to integrity integration:

```text
mod/uckkarchive:viewadvisories
mod/uckkarchive:manageadvisories
mod/uckkarchive:reviewadvisories
```

Restricted cultural capability may also apply where cultural protocol intersects with integrity evidence:

```text
mod/uckkarchive:viewculturallyrestricted
```

Capability rule:

```text
Capabilities are gates, not full authority.
Policy classes still enforce context, ownership, visibility, status, validation state, restricted state, content advisory rules, cultural protocol rules, retention, and redaction.
```

---

## 11. Policy enforcement

Archive policy:

```text
classes/local/archive_policy.php
```

Media policy:

```text
classes/local/media_policy.php
```

Content advisory policy:

```text
classes/local/content_policy.php
```

Integrity integration policy may be implemented as:

```text
classes/local/integrity_link.php
classes/local/integrity_policy.php
```

Policy checks must include:

```text
context access
course module visibility
capability gates
source component availability
integrity integration enabled state
restricted_integrity visibility
restricted media visibility
content advisory status
cultural protocol restrictions
retention requirements
redaction requirements
export authorization
download authorization
search visibility
preview visibility
thumbnail visibility
```

Policy rule:

```text
Integrity-linked records fail closed when authority cannot be verified.
```

---

## 12. Content advisory integration

Integrity-related records may contain sensitive material.

The content advisory subsystem must support integrity-related advisories through:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

Relevant advisory examples:

```text
sexual_violence
violence
racism
colonial_violence
death
self_harm
substance_use
explicit_language
culturally_sensitive
restricted_knowledge
grief_or_mourning
requires_context
not_for_children
```

Integrity-sensitive tag set examples:

```text
integrity_sensitive
restricted_case_material
investigation_evidence
appeal_sensitive
witness_sensitive
```

Content advisory rule:

```text
A content advisory does not decide the integrity case.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 13. Content marker integration

Integrity-related content markers may point to:

```text
media object
media version
archive item
proof record
external work
manual reference
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

Examples:

```text
Evidence video -> violence -> 00:02:10-00:03:45
Case PDF -> restricted_integrity -> page 8-12
External article -> racism -> url_fragment #section-2
Witness audio -> grief_or_mourning -> 00:08:12-00:09:40
```

Content marker rule:

```text
Integrity-related content markers must respect restricted_integrity visibility and must not expose sensitive locator details to unauthorized users.
```

---

## 14. Cultural protocol intersection

Some integrity-related records may also be culturally restricted.

Relevant visibility:

```text
restricted_cultural
restricted_integrity
```

Relevant capability:

```text
mod/uckkarchive:viewculturallyrestricted
```

Cultural protocol examples:

```text
culturally_sensitive
sacred_content
ceremonial_content
restricted_knowledge
community_permission_required
elder_review_required
not_for_public_export
requires_context
```

Intersection rule:

```text
When restricted_integrity and restricted_cultural both apply, the stricter access rule wins.
```

Cultural protocol rule:

```text
Restricted cultural material must not become public through integrity export, archive export, search, thumbnails, previews, backup preview, or course display.
```

---

## 15. Import from integrity tool

When `tool_uckkintegrity` is installed and integration is enabled, `mod_uckkarchive` may import or snapshot integrity records.

Import workflow:

```text
1. Authorized user requests integrity import or snapshot.
2. System verifies tool_uckkintegrity exists and integration is enabled.
3. Integrity source record is located through approved API or service.
4. Archive policy checks permission to preserve the source.
5. Media policy checks permission to preserve files or references.
6. Content policy checks sensitive advisory defaults.
7. Archive item is created or updated.
8. Media objects are created or linked.
9. Provenance records source component, source id, actor, and timestamp.
10. Restricted visibility is applied by default.
11. Import event or archive event is triggered.
```

Import rule:

```text
Imports create archive/media snapshots.
They do not move the integrity case into mod_uckkarchive.
```

---

## 16. Export to integrity tool

`mod_uckkarchive` may provide archive/media records to `tool_uckkintegrity` only through explicit authorized workflow.

Export-to-integrity workflow:

```text
1. Authorized user selects archive/media material.
2. Export preview is generated.
3. Policy checks export authority and restricted access.
4. Content advisories and redaction rules are applied.
5. Export package or reference bundle is generated.
6. tool_uckkintegrity receives references or package through approved integration.
7. Provenance and export manifest are preserved.
```

Export-to-integrity rule:

```text
mod_uckkarchive may supply records to an integrity process.
It does not decide how tool_uckkintegrity uses them procedurally.
```

---

## 17. Provenance integration

Integrity-related archive/media records must preserve provenance.

Canonical provenance value:

```text
integrity
```

Provenance metadata should include:

```text
source component
source area
source id
source uuid
source label
source timestamp
import actor
import timestamp
review actor
review timestamp
hash values
manifest reference
restriction state
redaction state
```

Provenance rule:

```text
Provenance explains origin.
Provenance does not grant authority by itself.
```

---

## 18. Validation integration

Archive validation is human-final.

Canonical validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Validation rule:

```text
Validation of an archive record does not validate or close the integrity case.
It validates the archive record as preserved material.
```

AI rule:

```text
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
AI cannot approve cultural protocol access.
AI cannot decide integrity outcomes.
```

---

## 19. Revision integration

Integrity-linked archive records and media must remain revisionable.

Archive item revision uses:

```text
mod/uckkarchive:reviseitem
```

Media versioning uses:

```text
mod/uckkarchive:versionmedia
```

Removed capability:

```text
mod/uckkarchive:versionitem = not used
```

Revision rule:

```text
Integrity-linked records must not be silently overwritten.
Corrections, replacements, redactions, and metadata changes must preserve revision history.
```

---

## 20. Search integration

Search may include integrity-linked records only when authorized.

Search dimensions may include:

```text
archive type
media type
source component
source reference
restricted state
content advisory tag
collection
provenance
validation state
review state
```

Search rule:

```text
Unauthorized users must not see restricted_integrity records in results, counts, facets, snippets, thumbnails, previews, or advisory summaries.
```

---

## 21. UI integration

Integrity-related UI appears only when relevant and authorized.

Possible UI elements:

```text
integrity source badge
restricted integrity label
provenance panel
content advisory panel
redaction status
export preview warning
media relation graph
external work card
```

UI rule:

```text
Server-side policy is authoritative.
Client-side UI is never the security boundary.
```

---

## 22. Events and audit

Integrity-related archive/media events may include:

```text
archive_item_created
archive_item_revised
archive_item_validated
archive_item_exported
media_created
media_updated
media_version_created
media_exported
content_marker_created
content_marker_reviewed
```

Optional integration-specific events may include:

```text
integrity_snapshot_created
integrity_reference_linked
integrity_export_created
```

Event rule:

```text
Events audit successful state changes.
Events must not expose restricted integrity content, raw evidence, private notes, cultural protocol details, or redacted information.
```

---

## 23. Backup and restore

Backup must include archive-owned integrity references and preserved records.

Backup may include:

```text
archive items
media records
media versions
media files
proof records
provenance
revisions
content advisories
content markers
content reviews
external works
media sources
collections
relations
export manifests
restricted_integrity visibility
```

Backup must not include:

```text
live integrity procedure state owned by tool_uckkintegrity
integrity officer assignment state
case deadlines
active procedural decisions
sanction execution workflow
appeal workflow state unless preserved as archive snapshot
```

Restore rule:

```text
Restore preserves archive-owned records.
Restore must not recreate or claim authority over live integrity cases.
Restore must not make restricted_integrity records public.
```

---

## 24. Privacy and retention

Privacy provider:

```text
classes/privacy/provider.php
```

Privacy coverage includes archive-owned integrity-related:

```text
archive items
media records
media versions
proof records
content markers
content reviews
external work references
media source records
provenance
revisions
exports
```

Privacy rule:

```text
Privacy export is not a permission bypass.
Restricted integrity evidence, third-party information, witness information, cultural protocol notes, and redacted data must be filtered or redacted.
```

Retention rule:

```text
Integrity-linked records may require preservation even when ordinary media would be deleted.
Retention policy must be checked before purge.
```

---

## 25. Reporting boundary

`mod_uckkarchive` owns archive/media export packages.

`report_uckk` owns institutional reporting.

`tool_uckkintegrity` owns integrity procedure.

Reporting boundary:

```text
mod_uckkarchive may expose archive-owned records to report_uckk when authorized.
report_uckk may aggregate institutional views.
tool_uckkintegrity remains the integrity authority.
```

Reporting rule:

```text
Integrity-linked archive/media data must not become available in institutional reports unless reporting policy, restricted visibility, redaction, and authority checks allow it.
```

---

## 26. External services

Integrity integration services should be explicit and permission-gated.

Possible service files:

```text
classes/external/get_integrity_links.php
classes/external/link_integrity_reference.php
classes/external/import_integrity_snapshot.php
classes/external/export_to_integrity.php
```

Service rules:

```text
Services must check tool availability.
Services must check integration enabled state.
Services must check context.
Services must check capabilities.
Services must check restricted_integrity visibility.
Services must check cultural protocol restrictions.
Services must check content advisory review state.
Services must filter output.
Services must fail closed.
```

No service may expose raw integrity evidence without policy approval.

---

## 27. Settings

Plugin settings may include:

```text
enableintegrityintegration
allowintegritysnapshots
allowintegrityexports
defaultintegrityvisibility
defaultintegrityredaction
showintegritybadges
```

Default values should be conservative:

```text
enableintegrityintegration = disabled unless explicitly enabled
defaultintegrityvisibility = restricted_integrity
defaultintegrityredaction = enabled
showintegritybadges = authorized users only
```

Settings rule:

```text
Settings can enable integration surfaces.
Settings cannot bypass context, capability, privacy, redaction, cultural protocol, or retention policy.
```

---

## 28. Failure modes

When `tool_uckkintegrity` is missing:

```text
ordinary archive workflows continue
ordinary media workflows continue
ordinary content advisory workflows continue
integrity import is disabled
integrity export-to-tool is disabled
integrity live reference refresh is disabled
stored archive snapshots remain available according to policy
```

When an integrity source reference cannot be resolved:

```text
stored archive snapshot remains preserved
live source refresh fails closed
UI displays unavailable source to authorized users only
export manifest records unresolved source reference when authorized
```

When permission cannot be verified:

```text
access is denied
download is denied
export is denied
thumbnail/preview is denied
search leak is prevented
```

---

## 29. Testing requirements

Tests must cover:

```text
archive works without tool_uckkintegrity
media library works without tool_uckkintegrity
content advisories work without tool_uckkintegrity
integrity features hidden when tool absent
restricted_integrity visibility enforced
restricted_integrity not leaked in search
restricted_integrity not leaked in thumbnails/previews
restricted_integrity not leaked in exports
integrity snapshot preserves provenance
integrity snapshot does not create live case authority
backup/restore preserves restricted state
privacy export redacts restricted data
content advisory review required
cultural restriction overrides ordinary access
```

Recommended test files:

```text
tests/integration_integrity_test.php
tests/content_advisory_test.php
tests/media_library_test.php
tests/backup_restore_test.php
tests/privacy_provider_test.php
tests/services_test.php
tests/behat/uckkarchive_integrity.feature
```

Testing rule:

```text
Tests verify the final target behavior, not historical transitions.
```

---

## 30. Final integration rule

```text
mod_uckkarchive integrates with tool_uckkintegrity only as an optional archive/media preservation and reference layer.

tool_uckkintegrity remains the integrity procedure authority.

mod_uckkarchive may preserve evidence, media, content advisories, provenance, revisions, restricted summaries, external references, and export packages.

mod_uckkarchive must not decide, close, replace, or own integrity procedure.

This document defines the final target behavior for implementation.
Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
```
