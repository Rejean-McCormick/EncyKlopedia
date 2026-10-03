# Ecosystem authority boundaries

## EncyK

Finds and acquires source material, freezes a scope, preserves selected records losslessly, extracts external identity hints, and emits a handoff.

## Médiathèque kOA

Owns persistent source bytes, source identity, snapshots, representations, hashes, rights/access facts and stable locators. EncyK does not keep a second canonical catalog.

## DaaT

**DaaT** is the human-facing name; `daat` is the machine identifier. DaaT is an optional external Interaction Kernel anti-corruption/admission and explicit contract-mapping boundary toward Kristal. It is not part of the EncyK pipeline.

## Kristal / Kristall

The portable artifact boundary remains `kristal_state/6.0`. Kristall `7.0.0-draft.3.2` is additive above that source/projection contract and owns semantic identity, Mesh, axes, source registries and crystallization.

EncyK never mints KQ/KP/KA/KS identifiers and never emits a Kristal-shaped Referent Registry.

## Kompiler

Kompiler `0.5.0` is a read-only context compiler over knowledge read surfaces. It is not a source crawler, acquisition pipeline, source store or DaaT replacement. EncyK does not invoke Kompiler as an ingestion stage.

## Identity rule

```text
external id (wikidata:Q8018)
    != Médiathèque source_uuid
    != Médiathèque snapshot_uuid
    != Médiathèque version_uuid
    != Kristall KQ/KP/KA/KS
```

Those identities can be mapped; they are never silently substituted.
