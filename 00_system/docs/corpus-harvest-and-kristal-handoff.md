# Corpus harvest and Kristal handoff

EncyKlopedia is the acquisition and evidence-construction layer.

Its responsibility is to discover source material, resolve source identities, freeze project scopes, retain lossless evidence, emit documentary/media candidates, and prepare a content-addressed handoff for Da’at. It does **not** make Wikidata, Project Gutenberg, VIAF, a local SQLite index, or an UCKK projection authoritative Kristal knowledge.

## Domain-neutral pipeline

```text
scope roots
  ↓
source identity resolution
  ↓
scope discovery
  ↓
immutable source evidence
  ├── referent candidates
  ├── documentary/media candidates
  └── optional derived query indexes
  ↓
content-addressed Da’at handoff
  ↓
Kristal lifecycle
```

A scope may be people-first, works-first, installations-first, processes-first, or use another domain-specific root strategy. The Scope Builder therefore treats `root_role` and `root_kind` as scope policy rather than universal ontology.

## Referents

The Referent Registry candidate is an identity/discovery artifact. Source-qualified refs such as `wikidata:Q8018` remain source-qualified candidates until Da’at/Kristal maps or accepts them. External identifiers are evidence for identity resolution; they do not acquire epistemic authority merely by being present.

## Documentary identity

EncyKlopedia must not silently collapse:

```text
work ≠ edition ≠ manifestation/file
```

Wikidata-discovered records sent to `50_mediatheque` are candidates only. UCKK Médiathèque remains responsible for final edition/provider/access/rights resolution.

## Frozen handoff

The EncyKlopedia-owned contract is:

`encyklopedia.corpus-harvest-handoff/1.0.0`

Current compatibility target:

- Kristal `5.0.0-rc.3`
- Referent Registry `kristal.referent-registry/1.0.0`

The exact contract pin is stored in `00_system/contracts/knowledge-baseline.json`.
