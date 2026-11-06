# Architecture — EncyKlopedia 0.2.0-alpha.1

## Boundary map

```text
External sources
   |
Skope + EncyK  [research/acquisition, noncanonical evidence]
   |
Médiathèque kOA  [durable source and snapshot authority]
   |
Kristal Framework / Authoring Kit [semantic identity, validation, approved state]
   |
Kristal Integration Pack [read-only derived v11 reading view; not publication]
   |
  [FUTURE: reviewed semantic-to-lexical interface + curated diK dictionaries]
   |
  [FUTURE: GF abstract trees, concrete grammars and language realization]
   |
  [FUTURE: independent, authorized C2/C4 PUBLICATION BOUNDARY]
   |
  [FUTURE: immutable public artifact + search indexes + CDN/object storage]
   |
EncyKlopedia [read-only public website, search and API]
```

Konstellation is a parallel *interactive exploration* consumer of qualified data; EncyKlopedia is the general public encyclopedia delivery surface. They may share approved read projections, but neither grants semantic authority, and one must not reimport the other's display pages as canonical evidence.

The arrows show **logical responsibilities**, not existing runtime integrations. The linguistic branch is a *proposed future qualification path*, not proof that current alpha code links diK or GF. Language realization may consume approved non-canonical views, but it must never turn its lexical or grammatical choices back into Kristal authority.

## Language-independent semantics and realization boundary

**An approved Kristal is a language-independent semantic object.** KQ/KP/KA/KS identities, predicate signatures, role bindings, assertion contexts, qualifications, epistemic statuses and provenance are not English- or French-specific. Language-tagged SKOS labels, quotations and source excerpts can exist as *evidence or annotations*, not as substitutes for stable semantic identity.

The future realization path has distinct authorities:

| Layer | Responsibility | Not allowed |
|---|---|---|
| Kristal Framework / Authoring Kit | Govern stable semantic identities, proposition roles, assertions, approval status and provenance | Store a final English sentence as the canonical meaning of an assertion |
| Integration Pack read projection | Produce a validated, derived semantic handoff | Mint new Kristal identities or grant publication rights |
| Source lexical pipeline (local v0.2–v0.6) | Inventory Kaikki, UniMorph and Wikidata Lexemes; stage provenance and review candidates | Turn common spellings, QIDs or Lexemes into approved equivalents |
| Curated diK dictionaries (target handoff) | Manage reviewed sense-level, language-specific lexicalizations and construction bindings | Grant semantic or publication authority to unreviewed candidates |
| GF / GF Wordbench (target handoff) | Assemble typed abstract trees; use language-specific concrete grammar, morphology and lexicon to linearize | Invent assertions or treat a grammatical sentence as proof of truth |
| EncyKlopedia | Assemble qualified realized text into articles and disclose coverage and fallback | Silently translate a canonical assertion or hide unqualified locale coverage |

Binding must be by stable **semantic identifiers and explicit predicate-argument roles**, not string resemblance. The exact handoff schema and governance are **not yet ratified**. A proposed interface must express subject/predicate/object or typed role signatures, context/qualifiers, approval references and provenance; the linguistic layer separately supplies lexeme/sense selection, construction frames and GF mappings per language. A sentence must be blocked or explicitly labelled unavailable when a required binding is missing.

For the full logical dictionaries organization, example, proposed interface, target tests and the difference between lexical and reader fallback, see **[LANGUAGE_ARCHITECTURE.md](LANGUAGE_ARCHITECTURE.md)**. This document is an architectural baseline; it does not modify upstream Framework contracts.

## Current implementation

The alpha provides a local Node.js reader of **synthetic fixtures and, separately, an unapproved private UNESCO research view**. The demonstration validates a local `encyklopedia.publication-bundle/0.1.0` envelope. The private adapter reads a bounded Workbench-derived view from supplied historical RDF and a provisional v11 candidate, not a qualified Integration Pack publication or production article corpus.

The local reader bundle is an **application draft contract**. Kristal Framework v11 remains the only normative owner of KQ/KP/KA/KS identifiers, source binding and lexical validation. The demo's `semantic_id` has a fake `demo:` prefix by design.

Security baseline:
- local loopback binding only, no public-network mode;
- strict demo/private-research validation and no content ingestion route;
- HTTP GET/HEAD only; no mutation endpoints, wildcard CORS, or filesystem traversal;
- bounded search and narrow slug routing;
- content rendered as text via DOM APIs; no user-supplied HTML;
- `no-store` responses, browser security headers, no analytics.

## Future non-negotiable properties

1. **C1:** pin implementation/code and normative contract revisions by digest.
2. **C2:** verify source owner, licensing, privacy/redaction and unambiguous public scope; no private or experimental workspace leakage.
3. **C3:** verify publication materialization, references, integrity, reproducibility and rollback.
4. **C4:** separately approve public publication and profile-specific disclosure, never infer release authorization from a derived reading view.
5. **Identity:** never mint or silently rewrite KQ, KP, KA or KS identifiers for convenience.
6. **Multilingual:** preserve provenance and measured *semantic binding*, *lexical*, *grammar* and *display* coverage separately; fallback is visible, never claimed as a direct translation.
7. **Scale:** use partitioned read services, indexes, object storage, cache/CDN and operations appropriate to traffic. GitHub stores code/governance, not bulk content.
8. **Trust:** reject unknown profiles, versions, digests and incomplete source artifacts; do not turn an API response into an authority declaration.

## Source alignment used for this starter

- `Kristal Framework` snapshot: `11.0.0-draft.4` (normative semantics).
- `Kristal Integration Pack` snapshot: `0.3.0-alpha.1`, derived view `kristal.integration.read-view/v11.0-draft.1`.
- `Konstellation` snapshot: `1.0.0-rc.2`, separate navigation responsibility.
- `Skope` + `EncyK` integrated code snapshots, separate upstream source processing.

These are **reference baselines**, not a tested live end-to-end production deployment. No adapter or contract is presumed ratified beyond what the individual sources establish.
