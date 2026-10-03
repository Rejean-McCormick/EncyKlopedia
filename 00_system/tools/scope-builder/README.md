# Scope Builder — EncyK 0.12

The Scope Builder is the primary EncyK pipeline.

```text
configured roots
   ↓
01_resolve_roots.py
   ↓
02_discover_scope.py
   ↓
03_freeze_scope.py
   ↓
04_extract_evidence.py
   ↓
[05_build_scope_index.py]     optional/rebuildable
   ↓
06_prepare_identity_candidates.py
   ↓
07_prepare_source_handoff.py
   ↓
Médiathèque kOA source authority
```

## Core invariant

**Selection may be selective; admitted evidence is lossless.**

Once a Wikidata entity enters a frozen scope, the complete source entity JSON is preserved. Qualifiers, references, ranks, literal values, aliases, descriptions, sitelinks and external IDs are not field-pruned.

## Identity candidates

`06_prepare_identity_candidates.py` emits consumer-neutral, source-qualified external identity hints under:

```text
20_evidence/identity-candidates/<scope>/
```

A record such as `wikidata:Q8018` is not a Kristall KQ/KP/KA/KS identity and is not a Kristal assertion. `kind_hint` and scope roles are local discovery/classification hints only.

## Handoff

`07_prepare_source_handoff.py` emits:

```text
encyk.source-evidence-handoff/2.0.0
```

under:

```text
20_evidence/handoffs/mediatheque/<scope>/
```

The handoff target is Médiathèque kOA `>=0.2.0` using `koa.source-catalog/2.0.0`. It carries lossless source evidence plus source identity hints. It does not carry a Kristal Referent Registry or a DaaT mapping.

## Downstream boundary

After source ownership is established in Médiathèque, owner-preserving references may flow through Interaction Kernel and **DaaT** (`daat`) toward the portable `kristal_state/6.0` interface. Kristall v7 owns semantic identity and crystallization. Kompiler is a separate read-only context compiler.

## Backends

`--discovery-backend auto` selects a completed global index when available, then fast random access when available, otherwise raw source scanning.

All indexes and caches are rebuildable accelerators, not source or semantic authority.
