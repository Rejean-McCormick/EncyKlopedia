# EncyKlopedia v0.8 — direct Wikidata evidence → Da'at/Kristal

## Core decision

The database/index layer is no longer a mandatory transformation stage.

```text
people seeds
   ↓ resolve
scope discovery
   ├─ complete compact SQLite, when available = accelerator
   └─ raw Wikidata dump = direct fallback
   ↓
frozen QID scope
   ↓
ONE direct raw-dump scan for all requested scopes
   ↓
lossless selected-entity evidence
   ↓
Da'at mapping boundary
   ↓
Kristal lifecycle
```

## What is optional now

- `wikidata.compact.sqlite`: optional global discovery accelerator. Useful, not authoritative, not required.
- `entity-vault.sqlite`: optional cache for selected raw entities. Not required.
- per-project SQLite: optional query/materialization convenience. Not required by Da'at handoff.

## What is mandatory

- immutable raw Wikidata dump;
- people/root identity resolution;
- frozen scope manifest;
- complete raw JSON for every admitted Wikidata entity;
- provenance/content hashes;
- Da'at as the mapping boundary into Kristal.

## No field-level pruning after admission

Properties help decide **which entity enters the scope**. Once admitted, the whole Wikidata entity is preserved: labels, aliases, descriptions, all claims, literals, ranks, qualifiers, references, sitelinks, URLs/external identifiers, etc.

## Discovery modes

- `auto` — use completed global compact index if available; otherwise raw dump.
- `index` — explicitly require completed compact index.
- `raw` — never require global SQLite; discover directly by sequential dump scans.

Raw discovery may need more than one sequential pass to reach closure around newly discovered works/places/concepts. This costs time but avoids constructing a universal database first.

## First production slice

`catholic-pilot` has explicit Wikidata roots for Augustine of Hippo (`Q8018`) and Thomas Aquinas (`Q9438`). The pilot can therefore run in raw mode without waiting for name-index construction.

## Interaction Kernel

The drive includes the current kOA IK reference documentation only. The kOA snapshot describes `kristal.build.request/1.0.0` and related Profiles, but the Da'at↔Kristal IK path is mapped/planned rather than qualified by the Konnaxion↔Orgo evidence. v0.8 therefore records IK readiness in the handoff but does **not** fabricate an IK-conformant message or claim runtime conformance.
