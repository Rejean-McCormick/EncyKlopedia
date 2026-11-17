# Kristal Authoring Kit (Local Kit)

**Version:** `4.0.0-draft.4` (opt-in Framework v11 semantic authoring; v9/v10 contracts preserved) | **Local workspace:** `kristal.local-workspace/3.2.0` | **Semantic state:** `kristal.state/9.0` | **Optional hosting:** `kristal.hosting/10.0` | **Optional AI reader:** `kristal.portable-ai/1.0`

Kristal Authoring Kit creates, structures, checks, and builds portable local Kristals. It owns local authoring and semantic build operations; it does **not** grant public access, synchronize GitHub collections, or activate a hosted release.

## Framework v11 semantic identity profile (v4 draft.4)

The Kit adds **opt-in** strict KQ/KP/KA/KS semantic graph authoring, namespace and evidence checks, a verified multilingual lexical catalog, and an external KQ↔Wikidata Q / KP↔P crosswalk. Existing Kristals remain under their old profiles unless explicitly enabled.

```bash
python tools/kristal.py enable-v11 ./My-Kristal --graph canon/domain/v11/graph.json --registry canon/domain/v11/registry.json --crosswalk canon/domain/v11/crosswalk.json --catalog canon/domain/v11/dictionaries/catalog.json
python tools/kristal.py check-v11 ./My-Kristal
python tools/kristal.py coverage-v11 ./My-Kristal --locales fr,en,fr-CA
python tools/kristal.py build-v9 ./My-Kristal
```

**First register** the four existing JSON files as v9 Logical Artifacts with `register-artifact`; activation fails closed otherwise. Active v11 profiles are checked automatically before `check` and `build-v9`, and canonical words as graph identities are rejected. diK can propose a migration plan; the Kit has read-only plan validation and a limited approved-plan producer that accepts a **v11-shaped** graph only, creates a new artifact, never rewrites the original, and requires an independently reviewed identity-role map. It does not automatically transform arbitrary older models or download dictionaries.

An [opted-in demonstration workspace](examples/demo-semantic-v11/README.md) includes a complete sample KQ/KP graph with deliberately incomplete French translations. `select-v11-graph` can explicitly choose a newly registered graph after conversion while archiving the previous profile.

See [Framework v11 authoring](docs/26_V11_SEMANTIC_AUTHORING.md) and [diK integration](docs/27_DIK_INTEGRATION.md). **v4.0.0-draft.4:** the complete Framework `11.0.0-draft.4` pin (13 exact SHA-256 files) is shared with Integration Pack `0.3.0-alpha.1`; v11 normative schema/tool files remain identical to draft.3, and the read-only interop preflight is newly pinned. Prior draft.3 qualification remains historical. Independent Framework, diK reference coverage and Integration Pack read checks agree on the shipped v11 example. This remains a draft: arbitrary legacy-schema conversion, full power-loss-qualified multi-file transactions and hosted Konstellation integration are not complete. See [Independent v11 qualification](docs/28_V11_FRAMEWORK_QUALIFICATION.md).

### Framework v11 qualification (draft.4; prior draft history retained)

The Kit now includes a read-only, **pinned** verifier for its active v11 profile:

```bash
python tools/kristal.py qualify-v11 ./examples/demo-semantic-v11 \
  --framework ../kristal-11.0.0-draft.4 \
  --integration-pack ../Kristal-Integration-Pack-0.3.0-alpha.1 \
  --locales fr,fr-CA
```

This requires the full Authoring Kit checkout and the optional `jsonschema` dependency. Ordinary workspace creation/building remains stdlib-only. See [qualification protocol](docs/28_V11_FRAMEWORK_QUALIFICATION.md).

## Responsibility boundaries

| Component | Responsibility |
| --- | --- |
| Local Kit | Local workspace, validation, deterministic v9 build, optional reader projection |
| Kristal Manager | Operator inventory, validation orchestration, authorized GitHub read-surface synchronization |
| Kristal GitHub Setup / Bootstrap | Network setup, qualification, publication and activation workflows |
| Kompiler | Optional read-only retrieval and LLM Context Packs |

**Knowledge, build, materialization, read-surface sync, hosting, publication and activation are distinct.** Changes to repository names, URLs, GitHub visibility or optional AI readers do not redefine semantic identity.

## Quick start

```bash
python tools/kristal.py init ./My-Kristal --slug my-kristal --title "My Kristal" --profile open
python tools/kristal.py check ./My-Kristal
```

After adding canonical payload content:

```bash
python tools/kristal.py register-artifact ./My-Kristal --file canon/domain/core.json --artifact-id urn:kristal:my-kristal:core --contract-id my-kristal.core
python tools/kristal.py build-v9 ./My-Kristal
```

By default, `build-v9` builds the v9 semantic layer **without** automatically generating an AI capsule.

## Reader discovery and Arketype classification (3.3.0)

New Kristals expose `kristal.discovery.json`, `derived/reader-inventory.json` and `derived/reader-profile.json`. These provide optional classification, measured sizes of registered files, and advisory reader strategies (including JSON/JSONL and federation). Legacy Kristals without these files remain valid. **They do not modify the v9 canon or authorize file access.**

```bash
python tools/kristal.py classify ./My-Kristal --arketype-dir ../Arketype-v1.4.0 --usage PRF-15
python tools/kristal.py build-discovery ./My-Kristal
python tools/kristal.py check ./My-Kristal
python tools/kristal.py inspect ./My-Kristal
```

Consumer preflight (read-only; **not** access authorization):

```bash
python tools/kristal.py audit-discovery ./My-Kristal --compact
python tools/kristal.py audit-discovery ./My-Kristal --require-fresh
```

See [Consumer integration contracts](docs/24_CONSOLIDATION_CONSUMER_CONTRACTS.md) for Manager/Konstellation/Light responsibilities, and [local snapshot cleanup](docs/25_NETTOYAGE_LOCAL.md) for the root `.pyw` tool.

For raw declarations without a local Arketype catalog, use `classify ... --archetype ARK-08 --usage PRF-15 --organization single`. `build-v9` refreshes the reader metadata after compiling the state. Consult [Discovery and reader profiles](docs/23_DISCOVERY_AND_READER_PROFILES.md) for measurement boundaries, freshness, parser and privacy controls.

## Materializations

Local Kit preserves existing v9 materialization manifests, including segmented, factored, compressed, dictionary-based and custom profiles, rather than reducing them to `inline-json/1`. Manifests are discovered in `materializations/v9/manifests/` and the legacy `.kristal/v9/materializations/` path. Registered manifests must losslessly refer to the source artifact's current Logical Commitment. Available local blobs are checked by size and SHA-256; missing or remote blobs are not silently downloaded. Large blobs are not duplicated on every build.

```bash
python tools/kristal.py register-materialization ./My-Kristal --manifest path/to/materialization.json
python tools/kristal.py check ./My-Kristal
python tools/kristal.py build-v9 ./My-Kristal
```

## Optional AI read surface

```bash
python tools/kristal.py build-ai ./My-Kristal
python tools/kristal.py check-ai ./My-Kristal
python tools/kristal.py pack-ai ./My-Kristal --output My-Kristal-portable-ai.zip
```

To inspect the exact reader projection used by Manager:

```bash
python tools/kristal.py read-surface ./My-Kristal --require-ready
```

You can also request the derived AI layer at build time:

```bash
python tools/kristal.py build-v9 ./My-Kristal --with-ai
```

The projection includes relevant state, canonical/provenance references and AI navigation files such as `AI_START_HERE.md` and `ai/INDEX.json`. It is narrower than a full workspace mirror and broader than a state-only export. This layer remains **derived and removable**, outside the Logical Commitment.

## GitHub synchronization and publication

Manager synchronizes the Local Kit's exact validated read surface under `kristals/<slug>/` in a configured public or private GitHub collection. **Sync is distinct from immutable publication, but a push into a public GitHub repository already exposes the synced bytes. Public synchronization must pass the owner-authorized disclosure and independent qualification gates before network writes.** GitHub Setup / Bootstrap handles explicitly qualified publication and activation; the legacy advanced `configure-*`, `export-hosted`, `github-status`, `github-qualify` and `github-publish` commands remain separate from the recommended operator workflow.

## Local lifecycle and migration

```bash
python tools/kristal.py publish-v9 ./My-Kristal
python tools/kristal.py activate-v9 ./My-Kristal --channel current
python tools/kristal.py migrate-v10 ./Old-Kristal
python tools/kristal.py check ./Old-Kristal
```

Local v9 publishing and activation are not the same as hosted v10 publication. Migration from 3.1 to 3.2 preserves State Index and commitments, including an existing optional AI layer.

Keep independent Kristals in sibling directories rather than nesting complete independent workspaces. The standard current-state discovery locations are `state/state-snapshot.json`, `build/v9/state-snapshot.json`, immutable `release/v9/states/**/state-snapshot.json` releases and supported `.kristal/v9/` legacy paths.

For read-only machine inspection:

```bash
python tools/kristal.py inspect ./My-Kristal
```

The `kristal.local-inspection/1.0` result reports local state candidates and the derived GitHub read surface without changing any semantic commitment. `check` requires `AI_MANIFEST.json` only when `portable_ai.enabled=true`.

## Documentation

Documentation chapters `01`–`13` cover local authoring and v9, `14`–`17` cover v10 hosting, and `18_PORTABLE_AI_CAPSULE.md`, `19_TOOLCHAIN_ROLES.md`, `20_TOOLCHAIN_INTEROP.md` and `21_V9_MATERIALIZATION_AUTHORING.md` cover optional AI readers, tool ownership, local interoperability and materialization preservation.


## V10 interoperability hardening (3.2.5-rc.1 candidate)

The read surface remains `kristal.github-read-surface/1.0`; its indexed file paths are constrained to the permitted workspace reader roots. The CLI now checks actual byte length **and** SHA-256 before marking a file ready, and rejects path traversal, symlink escapes, disallowed tooling paths and duplicated index paths. This does **not** authorize public sync.

For a strictly read-only comparison between an untouched original and a separate upgraded workspace copy:

```bash
python scripts/audit_workspace_migration.py --before ../Original-Kristal --after ../Staging-Kristal
```

Results distinguish `PRESERVED`, `BLOCKED`, and `NOT_FULLY_QUALIFIED` (for example when no comparable state snapshots are available). The tool never performs a migration or modifies either workspace. See [V10 alignment](docs/22_V10_ALIGNMENT_READINESS.md) and [English migration guidance](docs/13_MIGRATION_V1_TO_V2.md).

## New in draft.3: explicit diK catalog promotion and recoverable migrations

The Kit can now consume a diK alpha.7-style **Wikidata-only lexical snapshot**, validate its namespace/KQ/KP and imported shard hashes, and create a separate candidate catalog that keeps existing curated labels. Nothing is activated by the import itself. Use `import-dik-catalog --register`, explicitly `select-v11-catalog`, then check coverage and deliberately rebuild v9 semantic state.

`apply-v11-plan` and new catalog registration use a recoverable, journalled two-file protocol. The `recover-v11` command supports status, finish and rollback (rollback permitted only before the registry commit). **No generic conversion of arbitrary legacy JSON, strong human-review authentication or actual power-cut qualification is claimed.**

See [diK exchange](docs/29_DIK_CATALOG_PROMOTION.md) and [recovery](docs/30_V11_TRANSACTION_RECOVERY.md).
