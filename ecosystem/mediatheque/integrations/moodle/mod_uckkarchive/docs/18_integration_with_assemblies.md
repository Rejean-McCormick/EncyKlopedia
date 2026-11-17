# 18 — Integration with Assemblies

**Path:** `docs/18_integration_with_assemblies.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Related plugin:** `mod_uckkassembly`  
**Status:** Final target specification  
**Scope:** Integration contract between the self-contained UCKK Archive, Media Library, Content Advisory system, and UCKK Assembly workflows.

---

## 1. Purpose

This document defines how `mod_uckkarchive` integrates with Assembly workflows.

The archive may preserve Assembly-related memory, evidence, media, summaries, minutes, decision snapshots, provenance, content advisories, and export packages.

The archive does not own Assembly authority.

Canonical rule:

```text
mod_uckkassembly owns Assembly procedure and decision authority.
mod_uckkarchive owns preserved archive memory about Assembly-related material.
```

The integration must preserve institutional memory without moving decision authority into the archive.

---

## 2. Core integration decision

`mod_uckkarchive` is:

```text
Moodle-native on the outside.
Self-contained archive/media/content-advisory system on the inside.
```

For Assembly integration:

```text
mod_uckkassembly = live Assembly workflow, agenda, deliberation, votes, decisions, resolutions, procedural state
mod_uckkarchive = preserved Assembly-related archive memory, media, evidence, provenance, advisories, exports
```

The archive can reference Assembly records.

The archive can preserve snapshots of Assembly records.

The archive can package Assembly-related archive exports.

The archive cannot decide Assembly outcomes.

---

## 3. Ownership boundary

`mod_uckkassembly` owns:

```text
Assembly creation
Assembly membership
Assembly quorum
Assembly agenda
Assembly deliberation workflow
Assembly motions
Assembly votes
Assembly decisions
Assembly resolutions
Assembly minutes as live procedural records
Assembly appeals where implemented by Assembly
Assembly procedural status
Assembly notification workflow
Assembly authority state
```

`mod_uckkarchive` owns:

```text
archived Assembly snapshots
archived Assembly-related media
archived Assembly evidence
archived Assembly minutes copies
archived Assembly public summaries
archived Assembly decision summaries
archived Assembly provenance
archived Assembly validation records
archived Assembly content advisories
archived Assembly cultural protocol notes
archived Assembly external work references
archived Assembly export packages
```

Preservation does not transfer authority.

---

## 4. Non-ownership rules

`mod_uckkarchive` must not:

```text
create Assembly authority
change Assembly decisions
change Assembly vote records
change Assembly quorum status
change Assembly membership authority
change Assembly procedural status
close Assembly disputes
approve Assembly resolutions
invalidate Assembly decisions
replace Assembly minutes as procedural truth
act as the Assembly source of truth
```

`mod_uckkarchive` may:

```text
preserve a copy of an Assembly decision
preserve Assembly evidence
preserve Assembly-related media
preserve a public summary
preserve a restricted summary
preserve Assembly provenance
preserve a contestation note
preserve an invalidation record about an archived copy
preserve an export package
```

---

## 5. Dependency rule

Assembly integration is a module integration.

Ordinary archive, media library, and content advisory operation must not require `mod_uckkassembly`.

When `mod_uckkassembly` is absent:

```text
ordinary archive workflows continue
ordinary media workflows continue
content advisory workflows continue
Assembly-specific linking UI is hidden or disabled
Assembly-specific service calls fail closed
Assembly-specific restoration does not create Assembly authority
```

When `mod_uckkassembly` is present:

```text
archive records may reference Assembly records
archive records may preserve Assembly snapshots
media may be related to Assembly records
content advisories may be applied to Assembly-related material
exports may include Assembly-related archived material when authorised
```

---

## 6. Integration model

The integration uses reference-based linking.

Archive records may store Assembly references using:

```text
sourcecomponent = mod_uckkassembly
sourcearea = assembly | agenda | minutes | decision | motion | vote | evidence | resolution | summary
sourceid = Assembly-side record id
sourceuuid = Assembly-side stable uuid when available
sourcetitle = human-readable source title
sourcetimecreated = source creation time when available
sourcetimemodified = source modification time when available
```

Archive records must not require direct ownership of Assembly database tables.

The archive should support graceful degradation if the Assembly source record is unavailable.

---

## 7. Assembly archive item types

Assembly-related archive items may include:

```text
assembly_snapshot
assembly_minutes_copy
assembly_decision_snapshot
assembly_resolution_snapshot
assembly_motion_snapshot
assembly_evidence_bundle
assembly_public_summary
assembly_restricted_summary
assembly_media_record
assembly_provenance_record
assembly_contestation_record
assembly_export_package
```

These are archive item types, not Assembly procedural records.

---

## 8. Assembly media handling

Assembly-related media is managed as first-class media.

Media tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
```

Assembly media may include:

```text
meeting recording
audio excerpt
transcript
caption file
image
document
agenda PDF
minutes PDF
decision scan
resolution document
evidence file
public summary media
restricted evidence media
external reference media
```

Media files remain in Moodle File API file areas.

Media identity, metadata, relations, source, lifecycle, and advisories remain in archive-owned tables.

---

## 9. Assembly media source

Assembly-related media must identify its source.

Media source table:

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

Assembly media source rule:

```text
The archive preserves source and rights context.
The archive does not imply ownership over third-party or external works.
```

---

## 10. Assembly content advisory integration

Assembly-related archive material may require content advisories.

Content advisory tables:

```text
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
```

Assembly content advisories may apply to:

```text
meeting recording
minutes
transcript
motion text
evidence file
public summary
restricted summary
external work reference
media excerpt
decision context
```

Advisory examples:

```text
sexual_violence
violence
racism
colonial_violence
death
self_harm
substance_use
culturally_sensitive
sacred_content
ceremonial_content
restricted_knowledge
grief_or_mourning
requires_context
not_for_children
```

Content advisory rule:

```text
A content advisory does not ban Assembly material.
It describes responsible warning, teaching context, access conditions, restriction, review, or cultural protocol.
```

---

## 11. Cultural protocol integration

Assembly material may contain culturally sensitive or restricted content.

Cultural protocol tags may include:

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

Cultural protocol workflow:

```text
identify cultural protocol concern
  → create content marker
  → attach cultural protocol tag
  → set visibility = restricted_cultural when required
  → require human review
  → preserve review decision
  → enforce access policy
```

AI cannot approve cultural protocol access.

Archive policy must enforce cultural protocol restrictions independently from ordinary visibility.

---

## 12. Assembly content markers

Content markers link advisories to precise locations.

A marker may point to:

```text
Assembly-related media object
Assembly-related media version
Assembly archive item
Assembly transcript
Assembly minutes copy
Assembly evidence bundle
Assembly external work reference
manual Assembly reference
```

Locator types:

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
Assembly recording -> grief_or_mourning -> 00:18:12-00:21:40
Assembly minutes PDF -> culturally_sensitive -> page 7
Assembly evidence bundle -> sexual_violence -> document 3, page 2
External film discussed in Assembly -> sexual_violence -> 01:12:30-01:15:10
Book discussed in Assembly -> sexual_violence -> page 42-45
```

---

## 13. External works in Assembly context

Assembly may discuss or rely on works not produced by UCKK.

External work table:

```text
uckkarchive_external_work
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

External work workflow:

```text
create external work reference
  → record bibliographic/source metadata
  → record source ownership
  → add content markers where needed
  → add advisory tags
  → link to Assembly archive item
  → preserve reference without claiming ownership
```

External/foreign media rule:

```text
The archive may reference foreign media without copying it.
The archive may store metadata, content advisories, cultural protocol notes, teaching notes, locators, and references for external works.
The archive must not imply ownership over third-party works.
```

---

## 14. Assembly provenance

Assembly-related archive items must preserve provenance.

Provenance values may include:

```text
assembly
human
imported
system
ai_assisted
external_work
content_review
media
```

Assembly provenance must record where applicable:

```text
Assembly source component
Assembly source record id
Assembly source uuid
source title
source timestamp
archiving actor
archiving timestamp
validation actor
validation timestamp
reason for preservation
file hashes
snapshot hash
revision id
export id
```

Provenance explains origin.

Provenance does not grant Assembly authority.

---

## 15. Assembly validation

Archive validation confirms that the archived Assembly-related record is reliable as preserved memory.

Archive validation does not validate the Assembly decision itself.

Validation distinction:

```text
Assembly decision validity = mod_uckkassembly
Archive copy reliability = mod_uckkarchive
```

Archive validation may confirm:

```text
snapshot completeness
file integrity
metadata accuracy
source reference accuracy
visibility policy
content advisory markers
cultural protocol review
export eligibility
```

Archive validation uses:

```text
mod/uckkarchive:validateitem
```

AI cannot validate Assembly-related archive records.

---

## 16. Assembly restriction handling

Assembly-related archive records may be restricted for:

```text
privacy
minor safety
integrity sensitivity
cultural protocol
content advisory severity
copyright
external rights
unvalidated provenance
contested record
confidential deliberation
```

Visibility values used for Assembly archive material:

```text
private
group
course
program
institution
public
restricted
restricted_integrity
restricted_cultural
```

Restriction rule:

```text
Restricted Assembly archive records remain preserved.
Restriction controls access, download, export, display, and metadata exposure.
```

---

## 17. Assembly contestation

Archive contestation records disagreement, uncertainty, objection, or review challenge about the archived copy.

Archive contestation may apply to:

```text
archived minutes copy
archived decision snapshot
archived resolution snapshot
public summary
restricted summary
media metadata
content advisory marker
cultural protocol note
external work reference
provenance claim
```

Archive contestation does not change the live Assembly decision.

If the Assembly decision itself is contested, the authoritative contestation workflow belongs to `mod_uckkassembly`.

The archive may preserve a contestation record or snapshot.

---

## 18. Assembly export packages

`mod_uckkarchive` may export Assembly-related archive packages.

Export package may include:

```text
archive item metadata
Assembly source references
decision snapshots
minutes copies
media objects
media versions
proofs
Kristals
provenance
revision history
content advisory markers
content reviews
external work references
redaction metadata
manifest.json
```

Export must not include:

```text
unauthorised restricted media
unauthorised culturally restricted content
unauthorised integrity-restricted content
private Assembly procedural data outside archive authority
live Assembly workflow state as authority
```

Export rule:

```text
Export packages are portable archive memory.
Export packages do not become Assembly procedural authority.
```

---

## 19. Export manifest requirements

Assembly-related exports must include Assembly integration metadata in `manifest.json`.

Required manifest fields where applicable:

```text
plugin component
archive id
archive item uuid
export id
export timestamp
export actor
sourcecomponent = mod_uckkassembly
sourcearea
sourceid
sourceuuid
sourcetitle
media uuids
media version uuids
external work uuids
content marker uuids
content review state
file hashes
visibility
restricted flags
audience suitability
cultural protocol flags
provenance
relations
redaction level
validation state
revision history
```

Manifest rule:

```text
The manifest explains what was preserved and why.
It does not grant access beyond policy.
```

---

## 20. Backup and restore behavior

Backup includes Assembly-related archive-owned records.

Backup may include:

```text
archive item records
media records
media versions
media relations
media collections
content markers
content reviews
external work references
media source records
provenance records
revision records
export records
File API files
```

Restore reconstructs archive-owned records.

Restore must not:

```text
create live Assembly decisions
create Assembly votes
create Assembly quorum records
create Assembly procedural authority
create Assembly membership authority
```

Restore may preserve:

```text
sourcecomponent
sourcearea
sourceid
sourceuuid
archived snapshots
archived references
```

If matching Assembly source records are unavailable after restore, archive records remain valid as preserved archive memory with unresolved source references.

---

## 21. Privacy behavior

Assembly-related archive material may contain personal, sensitive, cultural, or restricted data.

Privacy provider must cover user-linked data in:

```text
archive items
proofs
Kristals
media objects
media versions
media relations
media collections
content markers
content reviews
external work notes where user-linked
provenance
revisions
exports
files
```

Privacy rule:

```text
Privacy export describes archive-held data.
Privacy deletion/anonymisation must respect retention, institutional memory, cultural protocol, and legal/ethical preservation requirements.
```

The archive privacy provider does not manage live Assembly records owned by `mod_uckkassembly`.

---

## 22. Events and audit

Assembly-related archive workflows may trigger archive events:

```text
archive_item_created
archive_item_validated
archive_item_revised
archive_item_exported
media_created
media_updated
media_version_created
content_marker_created
content_marker_reviewed
external_work_created
```

Events must include:

```text
context
object id
related user where safe
sourcecomponent where applicable
sourcearea where applicable
```

Events must not expose:

```text
raw restricted content
private cultural protocol notes
redacted details
unauthorised Assembly evidence
confidential deliberation material
```

---

## 23. Service contract

Assembly integration services must use Moodle external service patterns.

Services must:

```text
require login
resolve context
validate parameters
check capabilities
call archive policy
call media policy
call content policy
return permission-filtered data
fail closed when Assembly source is unavailable
```

Assembly integration service behavior may be implemented inside broader archive/media services using source references.

Dedicated Assembly service names may be added if needed:

```text
classes/external/get_assembly_archive_items.php
classes/external/link_assembly_item.php
classes/external/create_assembly_snapshot.php
classes/external/export_assembly_archive.php
```

All services must keep Assembly authority outside the archive.

---

## 24. UI behavior

The archive UI may show Assembly-related data as archive memory.

UI may display:

```text
Assembly source reference
archived title
archived summary
decision snapshot label
minutes copy label
media links
content advisory badges
cultural protocol badges
restriction badges
validation state
revision history
export availability
```

UI must not display Assembly-related archive material as the live Assembly source of truth unless explicitly labelled as a preserved snapshot.

Required labels:

```text
Archived Assembly snapshot
Archived copy
Source reference
Preserved evidence
Restricted Assembly archive record
Culturally restricted Assembly archive record
```

---

## 25. Capability map

Archive capabilities used in Assembly integration:

| Workflow | Capability |
|---|---|
| View Assembly-related archive item | `mod/uckkarchive:view` |
| Add Assembly-related archive item | `mod/uckkarchive:additem` |
| Validate Assembly-related archive item | `mod/uckkarchive:validateitem` |
| Revise Assembly-related archive item | `mod/uckkarchive:reviseitem` |
| View restricted Assembly archive item | `mod/uckkarchive:viewrestricted` |
| Export Assembly archive package | `mod/uckkarchive:export` |

Media capabilities used in Assembly integration:

| Workflow | Capability |
|---|---|
| View Assembly media | `mod/uckkarchive:viewmedia` |
| Add Assembly media | `mod/uckkarchive:addmedia` |
| Edit Assembly media | `mod/uckkarchive:editmedia` |
| Download Assembly media | `mod/uckkarchive:downloadmedia` |
| Add Assembly media version | `mod/uckkarchive:versionmedia` |
| Export Assembly media | `mod/uckkarchive:exportmedia` |
| View restricted Assembly media | `mod/uckkarchive:viewrestrictedmedia` |

Content advisory capabilities used in Assembly integration:

| Workflow | Capability |
|---|---|
| View Assembly content advisories | `mod/uckkarchive:viewadvisories` |
| Manage Assembly content advisories | `mod/uckkarchive:manageadvisories` |
| Review Assembly content advisories | `mod/uckkarchive:reviewadvisories` |
| View culturally restricted Assembly material | `mod/uckkarchive:viewculturallyrestricted` |
| Manage external works referenced by Assembly | `mod/uckkarchive:manageexternalworks` |

Capabilities are gates.

Policy classes remain authoritative.

---

## 26. Local class dependencies

Assembly integration depends on archive classes:

```text
classes/local/archive_item.php
classes/local/archive_policy.php
classes/local/provenance.php
classes/local/revision.php
classes/local/export_package.php
classes/local/manifest_builder.php
```

Assembly media integration depends on media classes:

```text
classes/local/media.php
classes/local/media_policy.php
classes/local/media_version.php
classes/local/media_relation.php
classes/local/media_collection.php
classes/local/media_source.php
classes/local/media_file.php
```

Assembly content advisory integration depends on content classes:

```text
classes/local/content_tag.php
classes/local/content_tag_set.php
classes/local/content_marker.php
classes/local/content_review.php
classes/local/content_policy.php
classes/local/external_work.php
```

Shared dependencies:

```text
classes/local/context_resolver.php
classes/local/file_area_registry.php
classes/local/metadata_validator.php
classes/local/uuid.php
```

---

## 27. File areas

Assembly-related archive material may use archive file areas:

```text
item_files
decision_attachments
minutes_files
proof_files
kristal_files
provenance_files
validation_files
revision_files
export_package
export_manifest
```

Assembly-related media uses media file areas:

```text
media_original
media_preview
media_thumbnail
media_derivative
media_caption
media_transcript
media_attachment
```

Assembly content advisory support files may use:

```text
content_review_files
external_work_reference_files
cultural_protocol_files
```

All files must be stored through Moodle File API.

No production Assembly archive or media files are stored in unmanaged public folders.

---

## 28. Testing requirements

Tests must verify:

```text
Assembly source references can be stored
Assembly source absence fails safely
Assembly snapshots do not create Assembly authority
Assembly-related media is permission-filtered
Assembly-related content advisories are permission-filtered
cultural restrictions are enforced
exports include Assembly source metadata
exports do not leak restricted Assembly material
backup preserves archive-owned Assembly references
restore does not create live Assembly authority
privacy provider covers user-linked Assembly archive records
```

Suggested test files:

```text
tests/archive_test.php
tests/media_library_test.php
tests/content_advisory_test.php
tests/backup_restore_test.php
tests/export_test.php
tests/privacy_provider_test.php
tests/services_test.php
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

---

## 29. Final integration rule

```text
Assembly owns decisions.
Archive owns preserved memory.
Media library owns reusable media objects.
Content advisory system owns suitability, warning, cultural protocol, and locator metadata.
Provenance explains origin.
Validation confirms archive reliability, not Assembly authority.
Exports package only what policy allows.
```

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
