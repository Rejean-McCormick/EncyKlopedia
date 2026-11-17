# diK → Authoring Kit: immutable catalog promotion (draft.3)

## Authority boundary

The **Authoring Kit** produces canonical v11 graphs and registers their identity/Logical Artifacts. **diK** handles dictionaries, external lexical sources and reconciliation *proposals*. Wikidata Q/P remain **external IDs** mapped to stable KQ/KP via an exactMatch independently accepted and supported by registered KS evidence. No term replaces a KQ/KP in a graph.

## Import a diK lexical snapshot

`dik sync import-large` (alpha.7) produces a `catalog.json` and versioned JSONL layers (one namespace, locale tags, SHA-256 records). On a **copy** of a real Authoring project, run:

```bash
python tools/kristal.py import-dik-catalog ./MyKristal \
  --catalog /outside/dik/immutable-import/catalog.json \
  --revision wd2026-10-17 --register \
  --artifact-id urn:project:dik:catalog:wd2026-10-17 \
  --contract-id project.v11.lexical-catalog

python tools/kristal.py select-v11-catalog ./MyKristal \
  --catalog canon/domain/v11/dictionaries/dik-revisions/wd2026-10-17/catalog.json

python tools/kristal.py check-v11 ./MyKristal
python tools/kristal.py coverage-v11 ./MyKristal --locales fr,en
```

`import-dik-catalog` checks the source catalog, hashes every shard, validates KQ/KP and accepted Wikidata alignment, then creates a **new directory**. It preserves existing curated/external layers, previous catalog files and existing locale fallback definitions. For locales present in the new diK snapshot, it replaces only prior **Wikidata-imported** layers, not reviewed curated layers. Newly declared locales have no automatic fallback. No background download occurs.

The new revision directory includes `DIK_IMPORT_RECEIPT.json`, identifying the old, source and new catalogue digests. It is a *proposal receipt*, not a signature or proof of Wikidata authenticity. A high-priority curated term remains separate. Unsupported external/curated source layers in an incoming `import-dik-catalog` input are rejected: curate and review those separately.

The `--register` action creates a **new** v9 Logical Artifact entry and a recoverable journal. It does not activate the catalog. Without `--register`, the import only stages an unregistered candidate that `select-v11-catalog` must refuse. `select-v11-catalog` requires registration and validates the full v11 profile before an atomic pointer change, archiving the old profile bytes by SHA-256. Neither command runs `build-v9`, `publish-v9`, GitHub synchronization or activation.

## Missing coverage and failure modes

- A lexical label absent from the input remains absent; the Kit does not fabricate any of the planned 300 languages.
- An incoming Q not approved by the active crosswalk is **rejected**, rather than silently allocated a new KQ.
- Colliding layer IDs, wrong namespace, bad SHA-256 and unregistered IDs are **rejected**.
- A failed copy may leave an unregistered orphan proposal directory only if the process is killed abnormally; it never selects a new catalog silently. Inspect before manual cleanup.
- Large input libraries are copied by streams, but the local framework auditor may still use memory proportional to registry and lexical metadata. Huge Wikidata ingestion, incremental changes and multi-namespace workflows require additional qualification.
- If a new canonical transaction remains pending, `check-v11`, `build-v9`, and further registration fail closed until recovery.

## Responsibilities of surrounding components

The authoritative Framework owns the v11 schemas. The Integration Pack consumes projections read-only. diK provides lexical material and a *candidate* plan. The Kit owns any canonical graph generation, state-index registration and deliberate `build-v9`. Network publication is a separate authority-controlled operation.
