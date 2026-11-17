# Framework v11 / diK semantic authoring — Kit v4.0.0-draft.4

**Status: opt-in candidate.** New commands preserve v9 logical-state commitments and v10 hosting. They do **not** rewrite frozen v6–v10 historical artifacts or make every existing Kristal KQ/KP-native. The source snapshot is `Kristal-Authoring-Kit 3.3.1`; the Kit now provides an independent pinned qualifier against the **actual** Framework `11.0.0-draft.4` archive; see [qualification](28_V11_FRAMEWORK_QUALIFICATION.md). This repo intentionally does not invent or reserve KQ/P identifiers from Wikidata.

## Concepts

- `KQ`: namespaced semantic referent/entity identity, never a word, never a Wikidata `Q`.
- `KP`: semantic property identity; `KA`: assertion; `KS`: evidence/source identity.
- Crosswalk: accepted `exactMatch` KQ↔Wikidata Q or KP↔Wikidata P, with proof and decision; candidate/closeMatch are never used for trusted lexical import.
- Lexicon: labels and synonyms in catalogued, hash-verified language layers; graph nodes, subjects, predicates and qualifiers do not contain the labels.
- Legacy `canon/domain/…` and v9 Logical Artifacts still work under their declared historical contracts when no v11 profile has been opted in.

## Activate v11 on an existing workspace

Create **four separate v11 JSON artifacts** (the graph, KQ/KP/KA/KS registry, Wikidata external crosswalk, lexical dictionary catalog) inside the workspace, for example:

```text
canon/domain/v11/registry.json
canon/domain/v11/graph.json
canon/domain/v11/crosswalk.json
canon/domain/v11/dictionaries/catalog.json
```

Ensure the catalog uses relative, safe paths to its hash-verified `wikidata`, `external`, and `curated` layers. No dummy KQ or guessed Wikipedia Q item should be minted to populate the graph. For each of the four **JSON** files, register its versioned Logical Contract:

```bash
python tools/kristal.py register-artifact ./Project \
  --file canon/domain/v11/registry.json \
  --artifact-id urn:example:registry --contract-id kristal.v11.identity-registry --contract-version 11.0

python tools/kristal.py register-artifact ./Project \
  --file canon/domain/v11/graph.json \
  --artifact-id urn:example:graph --contract-id kristal.v11.semantic-graph --contract-version 11.0

python tools/kristal.py register-artifact ./Project \
  --file canon/domain/v11/crosswalk.json \
  --artifact-id urn:example:crosswalk --contract-id kristal.v11.external-crosswalk --contract-version 11.0

python tools/kristal.py register-artifact ./Project \
  --file canon/domain/v11/dictionaries/catalog.json \
  --artifact-id urn:example:catalog --contract-id kristal.v11.dictionary-catalog --contract-version 11.0

python tools/kristal.py enable-v11 ./Project \
  --registry canon/domain/v11/registry.json \
  --graph canon/domain/v11/graph.json \
  --crosswalk canon/domain/v11/crosswalk.json \
  --catalog canon/domain/v11/dictionaries/catalog.json

python tools/kristal.py check-v11 ./Project
python tools/kristal.py check ./Project
python tools/kristal.py build-v9 ./Project
```

`enable-v11` refuses to write the profile unless all four input files already exist, pass strict identity/graph/lexical checks, and are registered as v9 Logical Artifacts. A new profile record is written to `.kristal/v11/authoring.json`, outside the canon. Once this exists, **all future `check` and `build-v9` invocations** must pass the v11 gate. Build/publish/activate remain deliberately separate. The lexical catalog itself is registered, and its SHA-256-verified layer files are included indirectly by hashes; all imported layer snapshots remain immutable.

## diK coverage

```bash
python tools/kristal.py coverage-v11 ./Project --locales fr,en,fr-CA
python tools/kristal.py coverage-v11 ./Project \
  --locales fr,en,fr-CA --output derived/v11/coverage-2026-10-16.json
```

The output matches the `kristal_dik_coverage_report` field structure: `KQ` and `KP` distinct denominators, `direct`, `fallback`, `missing`, `conflicted` per language, and the number covered in **every** selected locale. It does not treat `fr-CA → fr` as a translation direct in French Canadian. Reports are derived data and may not be registered as semantic canon. The implementation is file-backed and scans language layers; 300-language-scale performance remains to be qualified on production data.

## Reviewed conversion of a legacy word-bearing draft

The Kit does **not** use naive find-and-replace. A proposed migration is a three-part, reviewed input:

1. **Source JSON** carrying a full hash in the diK plan. The structure must be convertible by replacing nominated identity fields alone into a **complete v11 semantic graph**. More complex historical domain models need a separate explicit schema adapter before this command can work.
2. **diK plan** (`kristal_dik_conversion_plan`) listing JSON Pointer source paths, old values, target KQ/KP, `approved` reviewer decisions, nonempty reasons and registered `KS` proof references. `pending` and `rejected` may be inspected but not applied.
3. **Identity-role map**, locally reviewed and hash-bound to the exact source, with `format: kristal.identity-role-map/11.0`, `source_sha256`, `review`, and an exhaustive list of semantic identity paths (`entity`/`property`). A path pointing to a quotation or typed literal is forbidden by the migration process; reviewers must verify classifications explicitly.

Read-only checks:

```bash
python tools/kristal.py check-v11-plan ./Project \
  --source docs/staged-legacy.json --plan docs/migration-plan.json --roles docs/identity-roles.json
```

Writing a **new** canonical graph with a reviewed plan:

```bash
python tools/kristal.py apply-v11-plan ./Project \
  --source docs/staged-legacy.json \
  --plan docs/migration-plan.json \
  --roles docs/identity-roles.json \
  --output canon/domain/v11/converted-graph.json \
  --artifact-id urn:example:converted-v11 \
  --contract-id kristal.v11.semantic-graph
```

This refuses every unapproved operation, changes in SHA-256, target-kind mismatch, missing source/review evidence, destination overwrite, noncanonical output location, and results that do not validate as a complete v11 KQ/KP graph. The historical source is never edited. On success, it registers the **new** Logical Artifact, leaving `build-v9` to deliberately produce new v9 commitments. To explicitly select a newly created canonical graph as the workspace active v11 graph (the original graph remains registered and intact):

```bash
python tools/kristal.py select-v11-graph ./Project \
  --graph canon/domain/v11/converted-graph.json
python tools/kristal.py check ./Project
python tools/kristal.py build-v9 ./Project
```

`select-v11-graph` keeps a digest-named copy of the previous profile in `.kristal/v11/history/` and will switch only to another **registered and valid** graph. Selection does not publish or activate a state.

File + state-index registration is now recoverably journalled in draft.3. The `recover-v11` command can finish an interrupted registration or roll it back **before** the index commit. This is not a simultaneously atomic two-file update, and operating-system power-cut qualification, complete historical schema adapters and reversibility testing remain required before a final release. See [recovery protocol](30_V11_TRANSACTION_RECOVERY.md).

## Boundaries and deployment requirements

- The default Kit is still standard-library-only and offline; v11 opt-in checks are also standard-library-only and validate the important profile invariants, but **the Framework JSON Schema/TCK qualification remains independently required** before claiming full v11 compliance.
- No download or syncing of Wikidata, no auto-minting of KQ and no automatic translation is performed by this Kit. Those are diK concerns.
- None of these tools grants GitHub read-surface disclosure/publication rights or qualifies semantic truth.
- New v11-related files must be published under their actual profiles and checked by independent framework conformance and existing v9 commitment diagnostics.
- The Kit's current local `kristal.workspace.json` still uses `kristal.local-workspace/3.2.0` to preserve workspace compatibility; the new semantic profile is an explicit opt-in sidecar.
