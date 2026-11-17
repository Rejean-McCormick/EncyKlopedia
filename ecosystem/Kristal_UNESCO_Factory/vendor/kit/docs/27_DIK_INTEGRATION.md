# diK ↔ Kristal Authoring Kit — draft.3

## Contract responsibilities

| Component | Authority |
|---|---|
| Kristal Framework v11 | Semantic IDs, graph/crosswalk/catalog schemas, lexical separation, conformance |
| diK | Dictionary import/reconciliation, crosswalk proposals/review, coverage analysis, migration plans |
| Authoring Kit v4 | Registered workspace graph checks, v9 Logical Artifact commitments, limited approved-plan conversion to a **new complete v11 graph** |
| Integration Pack | Read-only adapter/projections, may not inject labels into graph identifiers |

The Authoring Kit **does not become** a Wikidata dictionary manager. diK may prepare its versioned external lexical layers and plans for Kit consumption. The Kit's v11 adapter checks expected structure, namespaces, evidence and layer hashes. In a final release, Framework draft.4 schemas/vectors are now pinned and checked by `qualify-v11`; the shipped semantic example and diK coverage output were compared against the original Framework tools and the v11 Integration Pack. This remains a candidate until full historical and hosted qualification.

## Safe exchange sequence

1. The **Authoring Kit owns the canonical graph and registry**. diK exports versioned catalog layers, crosswalk *proposals/revisions* and non-executable migration plans. It does not author authoritative graph or registry content.
2. Kit explicitly validates/chooses the authoritative graph, registry and reviewed crosswalk. It registers any imported diK catalog as a **new** Logical Artifact, never as an implicit mutation of the active catalog.
3. `enable-v11` checks that all references are registered and consistent. `check`/`build-v9` reject active v11 drift.
4. diK may export a coverage report; Kit can independently produce its own comparable coverage view.
5. diK proposes a migration plan and reviewed role map. The Kit can stage a **new** v11-shaped canonical graph only after all operations pass approval, type, hash, context and reference checks.
6. The Kit can select the new registered graph with `select-v11-graph`, then builds a **new v9 logical state**; publication/activation remain separate, with historical commitments untouched.

## Outstanding work before v4 final

- Requalification must be repeated whenever Framework v11 changes; pin currently locked to draft.4.
- Historical schema-specific adapters for non-v11-shaped source graphs; do not pretend that a generic JSON plan can preserve arbitrary semantic shape.
- The new `recover-v11` journal handles interruption between artifact installation and state-index registration. Full operating-system crash/power-loss durability is not yet independently qualified (fsync of parent directories, shared-network filesystems, concurrent legacy writers).
- diK production tests with 300+ locales and large Wikidata dumps; no network calls implicit.
- Multi-namespace registry resolution, operational approval policy and signed decisions if required by governance.

## New draft.3 workflows

`import-dik-catalog`, `select-v11-catalog` and `recover-v11` are described in [29_DIK_CATALOG_PROMOTION.md](29_DIK_CATALOG_PROMOTION.md) and [30_V11_TRANSACTION_RECOVERY.md](30_V11_TRANSACTION_RECOVERY.md). The new Kit validates incoming diK Wikidata layers using the current pinned namespace, registry and accepted crosswalk. Curated and external old layers remain separate; no word is copied into KQ/KP identities.

A diK alpha.7 `import-large` output (with `catalog.json` and referenced lexical shards) is an appropriate **candidate input shape**, subject to the Kit's validation. The current tests use matching local v11 fixtures; they are **not** a benchmark on a real massive diK import or a certified live inter-repository test.
