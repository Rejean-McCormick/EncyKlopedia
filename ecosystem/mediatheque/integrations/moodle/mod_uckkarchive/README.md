# UCKK Archive

`mod_uckkarchive` is the Moodle activity module responsible for UCKK archive memory, didactic material, evidence preservation, provenance, validation, revision history, restricted archive records, Kristals, portfolio items, and exportable archive packages.

This module is part of the UCKK-Moodle implementation.

---

## Location

Development location in the active Moodle instance:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
````

Distribution / source location:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive
```

Plugin type:

```text
mod_uckkarchive
```

Moodle plugin path:

```text
mod/uckkarchive
```

---

## Purpose

UCKK Archive owns the archive domain.

It stores and manages:

* didactic material;
* media-linked archive items;
* evidence and proof files;
* course work records;
* challenge result records;
* Assembly minutes and preserved decisions;
* Kristals;
* portfolio items;
* integrity summaries;
* version records;
* provenance trails;
* validation state;
* restricted archive metadata;
* exportable archive packages.

The archive is not a gradebook, not an administrative registry, and not the owner of Assembly or integrity workflows.

---

## Architectural decision

The accepted division is:

```text
mod_uckkarchive     = didactic material, archive items, evidence, media, provenance
Moodle gradebook    = grades, grade items, grade reports
local_uckk          = shared UCKK registry and institutional structure
tool_uckkintegrity  = integrity procedures and case workflow
mod_uckkassembly    = motions, deliberations, Assembly decisions
report_uckk         = reporting and institutional exports
```

UCKK Archive may preserve records from those systems, but it does not own their authority.

---

## Domain boundaries

`mod_uckkarchive` owns:

* archive activity instances;
* archive items;
* proof packages;
* Kristals;
* provenance records;
* revision records;
* validation history;
* visibility state;
* restricted archive records;
* archive exports.

`mod_uckkarchive` does not own:

* global UCKK registry permissions;
* course-format display rules;
* challenge workflow authority;
* Assembly workflow authority;
* integrity case authority;
* reporting authority;
* gradebook ownership;
* administrative procedures.

---

## Storage model

The module uses Moodle database tables for metadata and Moodle File API for files.

Files must not be stored in arbitrary public folders such as:

```text
public/media
public/uckk_media
public/db_media
```

Files belong in Moodle file areas attached to the `mod_uckkarchive` component.

Canonical component:

```text
mod_uckkarchive
```

Recommended file areas:

```text
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

---

## Current data model

Current archive tables include:

```text
uckkarchive
uckkarchive_item
uckkarchive_kristal
uckkarchive_proof
uckkarchive_prov
uckkarchive_rev
uckkarchive_export
```

These tables currently represent the archive, evidence, Kristal, provenance, revision, and export layers.

---

## Canonical Kristal artifacts (1.3.0-beta)

The historical `uckkarchive_kristal` table remains an archive/insight object attached to Moodle activity records. It is **not** the storage catalog for canonical Kristal/Kristall artifacts.

Canonical stored Kristals now use:

```text
uckkarchive_kartifact   stable kristal_ref + hierarchy/catalog binding
uckkarchive_kversion    immutable artifact versions + SHA-256
uckkarchive_media       stored artifact media identity
uckkarchive_media_version  Moodle File API version identity
```

`kristal_ref` is owned by Kristal/Kristall. Moodle UUIDs identify storage/catalog records only. A stored Kristal may reference other UCKK media, and those media may coexist in the same library without transferring semantic authority to Moodle.

UCKK bootstrap import:

```text
cli/import_uckk_bootstrap.php
```

The current UCKK bootstrap reserves 1 university Kristal, 10 voie Kristals, 100 course Kristals, and imports 64 Korpus media records.

## Media database decision

Didactic material and media must remain separate from grades and administrative procedures.

Current implementation stores media-like material through archive items and attached file areas.

Accepted current interpretation:

```text
uckkarchive_item = generic archive / media / didactic resource object
```

Future optional refinement:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
```

This refinement should be added only if media-specific behavior becomes too large to remain inside `uckkarchive_item`.

---

## Archive item types

Common archive item types include:

```text
proof
decision
course_work
challenge_result
assembly_minutes
integrity_case_summary
kristal
reflection
portfolio_item
version_record
```

---

## Status values

Archive items may move through workflow states such as:

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

## Visibility values

Archive visibility is controlled separately from Moodle course visibility.

Common visibility values include:

```text
private
course
cohort
program
institution
institutional
public
restricted_integrity
```

Restricted records require dedicated capability checks and service-layer policy enforcement.

---

## Provenance values

Archive records may declare provenance such as:

```text
human
ai_assisted
imported
system
archive
assembly
challenge
integrity
```

Provenance is part of the archive record and should be preserved through revisions, exports, backup, restore, and privacy workflows.

---

## Capabilities

The module defines archive-specific Moodle capabilities:

```text
mod/uckkarchive:addinstance
mod/uckkarchive:view
mod/uckkarchive:additem
mod/uckkarchive:validateitem
mod/uckkarchive:reviseitem
mod/uckkarchive:viewrestricted
mod/uckkarchive:export
```

Capabilities are permission gates only.

They do not bypass archive policy, ownership rules, validation state, visibility rules, retention policy, privacy requirements, or restricted-record safeguards.

---

## Main pages

Root activity pages include:

```text
index.php
view.php
add.php
item.php
validate.php
export.php
mod_form.php
settings.php
lib.php
locallib.php
version.php
```

Typical flow:

```text
view.php      → archive overview
add.php       → create archive item
item.php      → view archive item
validate.php  → validate or revise archive item
export.php    → prepare archive export
```

---

## Services

The module exposes external/AJAX services for archive interactions.

Current service areas include:

```text
get_archive
get_archive_items
get_archive_item
get_archive_item_card
get_proofs
get_provenance_panel
get_kristal
get_revisions
get_restricted_item
save_item_draft
add_item
add_proof
update_provenance
validate_item
revise_item
create_kristal
update_kristal
get_export_preview
export_items
get_export_status
```

Server-side services must always enforce Moodle login, context, capability, ownership, visibility, validation, provenance, and restriction checks.

---

## Events

The module includes archive events such as:

```text
archive_viewed
archive_item_created
archive_item_validated
archive_item_revised
archive_item_exported
```

Events are used for auditability, reporting, traceability, and Moodle event integration.

---

## UI

The module uses Moodle templates and AMD modules.

Templates include:

```text
templates/archive_view.mustache
templates/archive_item_card.mustache
templates/proof_card.mustache
templates/provenance_panel.mustache
templates/validation_panel.mustache
templates/kristal_card.mustache
```

AMD modules include:

```text
amd/src/archive.js
amd/src/export.js
amd/src/kristal.js
```

Client-side JavaScript is UI-only.

It must not authoritatively validate records, expose restricted items, revise archive history, export files, open integrity cases, or replace server-side capability checks.

---

## Privacy

The module includes:

```text
classes/privacy/provider.php
```

The privacy provider must cover:

* archive items;
* proof records;
* Kristals;
* provenance;
* revisions;
* exports;
* user-linked metadata;
* file areas;
* restricted archive records;
* validation records.

Archive privacy logic must support export, deletion, redaction, and retention rules according to Moodle privacy API requirements and UCKK institutional policy.

---

## Backup and restore

The module includes Moodle backup and restore support:

```text
backup/moodle2/backup_uckkarchive_activity_task.class.php
backup/moodle2/backup_uckkarchive_stepslib.php
backup/moodle2/restore_uckkarchive_activity_task.class.php
backup/moodle2/restore_uckkarchive_stepslib.php
```

Backup/restore must preserve:

* activity instance data;
* archive items;
* proofs;
* Kristals;
* provenance;
* revisions;
* exports;
* validation state;
* restricted metadata;
* file areas.

File area names must remain consistent between controllers, forms, services, output classes, privacy provider, backup, restore, and tests.

---

## Tests

The module includes PHPUnit and Behat tests:

```text
tests/archive_test.php
tests/lib_test.php
tests/behat/uckkarchive.feature
```

Tests should cover:

* canonical statuses;
* canonical visibility values;
* archive policy helpers;
* restricted item access;
* file area handling;
* validation workflow;
* revision workflow;
* export workflow;
* backup/restore expectations;
* privacy expectations.

---

## Documentation

Plugin documentation belongs inside the plugin:

```text
docs/
```

Recommended documentation set:

```text
docs/00_index.md
docs/01_architecture_decision.md
docs/02_domain_boundaries.md
docs/03_moodle_plugin_structure.md
docs/04_data_model.md
docs/05_media_database_division.md
docs/06_file_api_and_storage.md
docs/07_permissions_and_roles.md
docs/08_archive_workflows.md
docs/09_didactic_material_workflows.md
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
docs/24_acceptance_checklist.md
docs/25_known_gaps_and_corrections.md
docs/26_release_notes.md
```

---

## Installation

Place the plugin in:

```text
mod/uckkarchive
```

Then visit Moodle site administration to complete plugin installation or upgrade.

Development path:

```text
C:\mycode\UCKK\moodle\moodle\public\mod\uckkarchive
```

Distribution path:

```text
C:\mycode\UCKK\uckk-moodle\mod\uckkarchive
```

---

## Development rules

1. Keep didactic material separate from grades and administration.
2. Store files through Moodle File API.
3. Store metadata in archive-owned tables.
4. Do not write directly into gradebook tables.
5. Do not let external systems write directly into Moodle source tables.
6. Do not let JavaScript bypass server-side checks.
7. Do not expose restricted records without `mod/uckkarchive:viewrestricted`.
8. Preserve provenance through revisions, exports, backup, restore, and privacy flows.
9. Keep file area names consistent across the whole module.
10. Keep archive authority separate from Assembly, Integrity, Challenge, Report, and Registry authority.

---

## Known alignment gaps

The current module is aligned with the accepted architecture, but the following corrections remain important:

### 1. Media layer

The module currently treats didactic media as archive items with file attachments.

This is acceptable for now.

If the media database grows, add explicit tables:

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
```

### 2. File area normalization

Normalize file area names across:

```text
add.php
lib.php
classes/privacy/provider.php
backup/moodle2/*
restore/moodle2/*
tests/*
```

No file area name should appear in one layer but not the others.

### 3. Version dependency check

Check `version.php` for accidental self-dependency.

`mod_uckkarchive` should not depend on itself.

### 4. Documentation

Add the full `docs/` set and keep each file aligned with the accepted division:

```text
Archive = didactic material, media, evidence, provenance
Gradebook = notes
Administration = local_uckk and related tools
Assembly = decisions
Integrity = cases and procedures
Reports = reporting and exports
```

---

## Status

Current status:

```text
Architecture alignment: good
Archive domain separation: good
File API direction: good
Privacy provider: present
Backup/restore: present
Tests: present
Dedicated media model: partial
Documentation: to complete
```

Decision:

```text
Keep this module as the base.
Do not restart from zero.
Strengthen it with documentation, file-area normalization, and an optional media submodel.
```



---

## Relation avec Médiathèque kOA standalone

`mod_uckkarchive` est la **Médiathèque UCKK**. Elle est distincte de l'application locale `koa-mediatheque`.

```text
koa-mediatheque
  = application standalone vide au checkout
  = peut ouvrir un workspace local privé
  = SQLite + filesystem local

mod_uckkarchive
  = Médiathèque UCKK
  = Moodle DB + Moodle File API + capabilities
  = surfaces institutionnelles/publiques UCKK
```

Les deux systèmes ne partagent jamais une base writable et le module Moodle ne monte pas le stockage privé local. Tout transfert doit être explicite, autorisé et auditable. Le format d'export natif actuel de ce module reste `uckkarchive_export_v2`.

Les Kristals conservés ou projetés ici ne donnent pas à UCKK l'autorité sémantique sur Kristal/Kristall; UCKK conserve sa propre représentation/archive institutionnelle.

Voir `docs/28_standalone_mediatheque_boundary.md`.
