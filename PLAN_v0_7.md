# SUPERSEDED by `PLAN_v0_8.md`

# EncyKlopedia v0.7 — optimized Wikidata / Kristal plan

## Decision

The project now uses a **two-resolution architecture**.

### Global layer — broad, compact, lossy

`wikidata.compact.sqlite` is a discovery map. It keeps enough structure to resolve names, inspect first-level property coverage, traverse entity-valued relationships and find reverse author links such as `work --P50--> person`.

It is **not** a source epistemic corpus and is never treated as a complete representation of Wikidata.

### Project layer — narrow, complete, evidence-preserving

A project is centered on selected people. The global map discovers nearby works, places, institutions, fields, movements and influences. The resulting QID set is frozen. For every selected QID, the complete entity JSON is extracted from the raw Wikidata dump.

The project layer preserves:

- all labels, aliases and descriptions present in the entity;
- all claims and literal values;
- statement ranks;
- qualifiers;
- references;
- sitelinks;
- external identifiers and URLs present in Wikidata.

This is where Kristal provenance work starts.

## Why people-first

People are stable navigation anchors for the intellectual corpus. From a person we can discover:

- biography and geography;
- institutions and affiliations;
- fields, occupations and intellectual movements;
- explicit influence relations;
- notable works;
- **all authored works discoverable in reverse through `P50`**.

Works/documents then connect naturally to UCKK Mediatheque. Currents and fields organize the intellectual graph without replacing the people axis.

## Why not a fully indexed lossless Wikidata clone

A full general-purpose Wikidata query index can approach several hundred GiB and duplicates infrastructure we do not need for the next project. The current compact discovery index is expected to remain in the rough 100–160 GiB class; selected project evidence is much smaller because only admitted entities are retained at full fidelity.

## First production target

The first production vertical slice is the **Catholic intellectual corpus**, because an existing structured Catholic Kristal already exists. The pilot root list is deliberately tiny until the real Catholic corpus author registry is supplied.

After the pipeline is validated, the same machinery expands to the historical-intellectual registry.

## Authority boundaries

```text
Wikidata raw evidence
     ↓
working/project index
     ↓
Da'at mapping boundary
     ↓
Kristal Structured Epistemic State / lifecycle
```

No Wikidata statement becomes a validated Kristal assertion merely because Wikidata contains it.

Konnaxion remains a consumer/projection/debate layer; UCKK Mediatheque remains authoritative for media editions/providers/rights.
