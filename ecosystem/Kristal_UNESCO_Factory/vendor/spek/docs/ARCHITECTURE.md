> **Spek v0.4:** Spek is autonomous; all external knowledge integrations are optional. See [Standalone and connectors](STANDALONE_AND_CONNECTORS.md) and [Language channels](LANGUAGE_CHANNELS.md).

# Architecture and roadmap

## Implemented now

- Offline programmatic compiler; does not mutate source canon or access the network.
- Three static editorial **contracts**, not just ad hoc HTML templates, all with typed slots and cardinalities.
- Three language realizations with no fallback and no machine translation claims.
- Local HTML (responsive + accessible language switch), ReportLab A4 PDF (layout-specific cards, argument progression, side-by-side comparison), XeLaTeX source.
- Source and build fingerprints (internal sorted JSON SHA-256; **NOT** JCS Logical Commitments), published-file SHA-256 manifest.
- Fixture importer for historical SemantiK `cases[]/plain_text` format, explicit mapping and retained request IDs.
- Positive/negative tests, fail-closed deployment of demos, manual GitHub Pages workflow using pre-built static files.

## Source snapshots and trust

The Authoring Kit's real Kristal v9 `state/state-snapshot.json` and v9 schema are separate from this lightweight editorial article source. A builder integrating real state must produce a **derived projection** with IDs and an exact state/ref fingerprint. The optional `--state-snapshot` check merely matches `state_ref`, textual `logical_commitment.digest` and referenced `members[].artifact_id` from that supplied metadata. It does NOT compute JCS or validate the underlying member payloads, chain of custody, trust policies or access rights.

No canonical input is copied into static site outputs by default. The HTML metadata and generated manifests contain only derived identifiers and input hashes, never local blob paths or private materialization locators. The user's disclosure rules must still control which content appears in the output.

## Critical missing integrations for a production release

1. Real Kristal Framework/Kit projection adapter: contract-owned reading of native domain state, v9 Logical/State Commitment verification, materialization coverage, original sources, semantic validation, and release receipt pinning.
2. SemantiK Runtime Orchestrator: GF-compiled/qualified RuntimeSets and per-language output with exact semantic/request coverage; truthful runtime attestations and language/terminology QA.
3. Scientific editorial certification: factual/source review, evidence strength and argument validity, accessibility checks, translation equivalence review. Verify typed slot rendering does not inadvertently suppress scope.
4. External publication authority and v10 gates: exact revision, permission/disclosure scope, Manager/C1/C2/C3, plus C4 for Konstellation-Light. GitHub protected environments cannot replace these domain gates.
5. Additional publishing formats and institutional export (PDF/A, JATS XML, CSL citations, Crossref/Zenodo), subject to format standards and licensing.
6. Higher-order argument layouts and long-form discourse for topics that cannot be faithfully communicated in cards.

## Design principle

A layout is defined as a stable editorial **contract**. Its view in HTML/PDF/TeX can evolve independently of content and language; a new version must be tracked and its effects reviewed. Layout reuse can increase scanability, but gains in reading speed are a hypothesis requiring an actual user study, not a proven outcome of this prototype.

## Spek v0.5 educational extension

Spek now also supports curated, read-only Ekole/Kompose **public/demo excerpts** using `spek.educational-projection/1`. Five versioned educational layout contracts are independent of the source adapter. See [Educational Layouts](EDUCATIONAL_LAYOUTS.md), [Educational Connectors](EDUCATIONAL_CONNECTORS.md), and [Educational Privacy](EDUCATIONAL_PRIVACY.md). Spek neither orchestrates missions nor certifies curricula nor authorizes restricted static publication.
