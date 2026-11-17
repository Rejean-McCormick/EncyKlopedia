# 11 — V9 State Architecture for authors

## Logical Artifact

Owns domain-native logical content under a declared Logical Contract and commitment profile. Physical serialization or byte transport does not redefine logical meaning.

## State Snapshot

Combines members, pinned references, parent links and a deterministic State Commitment. Each referenced Kristal keeps its semantic ownership and revision.

## Materialization

A descriptor relates physical representations, segments, dictionaries, compression profiles and external locators to an exact Logical Artifact. Incomplete physical availability may be recorded rather than automatically repaired.

## Derivation

Derived search indexes, teaching views, Context Packs and AI summaries are outputs with traceable sources. They are not canonical unless admitted as a separately defined Logical Artifact.

## Runtime

Reader and execution environments may cache, index, display, simulate or query the state. A runtime is not a State Snapshot, and an authorized operational action cannot be inferred from the existence of a protocol document.
