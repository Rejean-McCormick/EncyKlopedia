# Médiathèque — Shared Engine

**Technical engine:** `koa-mediatheque` | **Version:** `0.5.1`

Médiathèque is the shared source-preservation and content-instance engine within the kOA ecosystem. It maintains source records, snapshots, representations, file versions and integrity facts. It does **not** become the semantic authority of Kristal or invent Kristal identities.

## Engine versus instances

The engine contains code, schemas, adapters, tests and user interfaces, **not the data for any particular library**. Real libraries are sibling instances that consume the shared engine:

```text
workspace/
├── mediatheque/                 # Shared engine, no instance data
├── mediatheque-private/         # Private local instance
├── mediatheque-uckk/            # UCKK instance
└── mediatheque-math/            # Another instance
```

An instance selects its content root via `KOA_CONTENT_ROOT` or `-ContentPath`, or configures a remote/Moodle adapter. Do not copy the engine source tree into each instance.

## Local launch

From a configured sibling instance:

```powershell
./Start.ps1
```

The instance launcher calls the shared `Start-KoaGui.ps1 -ContentPath <instance>` entry point. Use a prepared instance such as `Mediatheque-blank` when starting a new local library.

## Moodle adapter

The shared Moodle integration is in `integrations/moodle/mod_uckkarchive/`. UCKK and mathematics instances reference the engine adapter; they do not each maintain a separate copy.

The Moodle storage model distinguishes legacy insight/archive objects (`uckkarchive_kristal`), stable stored artifact identities (`uckkarchive_kartifact`), immutable versions with SHA-256 (`uckkarchive_kversion`), physical media (`uckkarchive_media`) and physical file versions (`uckkarchive_media_version`). A `kristalref` must not be replaced with an unrelated Moodle UUID. See `docs/23_uckk_kristal_artifact_catalog.md`.

## Source authority and provenance

Médiathèque owns `source_uuid`, preserved snapshots, representations and physical file versions. Kristal and EncyK use source bindings without taking ownership of the preserved bytes. The v4 source model uses `source_*` and `02_STORAGE/source_files/`; older `kristal_*` source tables remain only for non-destructive migration. See `docs/19_kristal_local_source_library.md` and `docs/25_source_authority.md`.

## External GitHub references

Public GitHub repositories may be cataloged as `external_reference` media. A GitHub URL or commit is a **reference**, not a claim that the remote contents were cloned, preserved or verified locally. The UCKK 0.5.0 bootstrap catalog lives at `bootstrap/repositories/github-repositories.json` and may include role, provenance and pinned-commit metadata. See `docs/24_github_repository_catalog.md`.

**Separation rule:** the engine owns its implementation; instances own their data; Kristal retains semantic identity and commitments.


## EncyK / Skope current handoffs (0.5.1)

The shared engine accepts `encyk.source-evidence-handoff/2.0.0` from Skope's EncyK
0.14.0 producer. For local SQLite/filesystem instances, provide an explicit
`--instance-root` to select **one** existing private library; this never discovers
or updates other instances. The original explicit `--db` / `--storage` interface
remains supported. See `docs/27_skope_encyk014_instance_import.md`.
