# EncyKlopedia private derived view preflight — Branch 04 final-system integration

**Scope:** `TARGET_DESIGN` plus named local tests; not a public release, current Git HEAD or production assertion.

EncyKlopedia's public website remains blocked by its documented C1–C4 publication gates. This branch adds **only** a local private command that understands a Framework-v11-derived Integration Pack view; it does not import that view into `src/server.mjs`, enable public mode, create qualified articles, or validate the Framework itself.

```bash
node tools/private-v11-preflight.mjs --view /private/view.json --graph /private/semantic-graph.json --registry /private/identity-registry.json --crosswalk /private/external-crosswalk.json --catalog /private/dictionaries/catalog.json
```

The command requires the four **exact original input files** to verify SHA-256 provenance, validates the `kristal.integration.read-view/v11.0-draft.1` structure and identity references, refuses invented missing labels or invalid external mappings, and outputs an informational receipt `encyklopedia.private-v11-preflight/1.0`. It does not print article data or give permission to serve. The reported `framework_validation_performed: false` means a **consumer-side check only**; the producer must separately prove Framework validation, rights, privacy, authorization, editorial quality and a per-target release. The included `examples/derived-v11-demo.json` is a copied **synthetic** Pack fixture.

**Verification:** `npm run verify`; to test against a real Pack producer, generate a view from Framework draft.4 and run this command with the exact four input files. Kompiler's opt-in bilateral suite performs this sequence automatically.

**Future-owner gate:** read-view → editorial article import → approved publication bundle must be specified and tested as a **separate** boundary; C1–C4 remain blocked in this snapshot.

