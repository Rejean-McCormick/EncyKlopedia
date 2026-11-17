# 02 — Authoring and build protocol

This is a **disciplined sequence for designing a domain Kristal**, not a set of automatically generated factual assertions.

## Phase 0 — Do not model prematurely

Record the actual problem, competing interpretations, available sources, uncertainty and what remains undecided. Avoid selecting a graph/tree/DAG just because it is convenient to render.

## Phase 1 — Identity, boundary and ownership

Define the subject, `state_ref`, owner, inclusion/exclusion boundary, related Kristals and lifecycle. A stub may legitimately own no canonical artifacts yet.

## Phase 2 — Discover the native shape

Use [shape probes](03_SHAPE_DISCOVERY.md) to identify primitives, relations, causality, transitions, invariants, scales and domain-specific structure. Preserve information that a generic assertion model would lose.

## Phase 3 — Define epistemic regimes

Separate claims, observations, hypotheses, accepted findings, counterexamples, valuations, decisions and the evidence supporting each. Mark uncertainty explicitly.

## Phase 4 — Define sources and authority

Record source identity, provenance, collection circumstances, version and authority. Source acquisition is not automatic acceptance as truth.

## Phase 5 — Canonical versus derived

**Potentially canonical:** versioned native domain models, explicit assertions, Logical Artifacts, source-linked operational rules when a domain contract owns them.

**Typically derived:** reader views, search indexes, comparisons, summaries, simulations, Context Packs, host sync indexes and cache files.

## Phase 6 — Optional operational semantics

If a model has executable transitions or workflow rules, define authorized execution separately from the record of those rules. Tests of a model do not authorize real-world actions.

## Phase 7 — Orientations and surfaces

Design reader questions and projections only after the native structure is stable. Record potential loss of detail and preserve semantic references to the source.

## Phase 8 — Population

Add traceable domain content with explicit status, version and provenance. A placeholder, `unknown`, or empty stub is better than fabricated evidence.

## Phase 9 — Validation

Run structural and domain-specific tests; differentiate technical consistency from scientific, legal, and independent qualification.

## Phase 10 — V9 crystallization and qualification

1. Register each canonical Logical Artifact in `canon/state.index.json`.
2. Pin external references to exact Logical Commitments.
3. Register and preserve source-bound v9 Materialization Manifests where relevant.
4. Run `check` to verify bindings and available local blob digests.
5. Run `build-v9` to produce a deterministic candidate State Snapshot.
6. Verify Logical Commitments, State Commitment and declared materialization capabilities.
7. Build v6/v7 projections or v8 indexes as **derived** representations only when needed.
8. Obtain independent qualification from KristalDiag/C1 for exact revisions when available.
9. Keep `publish-v9` and `activate-v9` as a separate local lifecycle; v10 hosting needs separate C1/C2/C3 controls.
10. Do not expose public bytes until owner authorization and applicable qualification have passed.
