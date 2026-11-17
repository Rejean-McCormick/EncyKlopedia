# 17 — Multiple Kristals per hosting collection

One hosting repository can contain multiple independently owned Kristals. Each Kristal keeps its own `state_ref` and v9 State Commitment. A discovery index is a **derived operational projection**, not one big logical knowledge state.

Recommended structural distinction:

```text
kristals/index.json                          # derived collection index, produced by Manager
kristals/<slug>/AI_START_HERE.md             # approved reader entrypoint
kristals/<slug>/ai/INDEX.json                # derived navigation
kristals/<slug>/state/state-snapshot.json    # exact v9 state
kristals/<slug>/.kristal/sync-manifest.json  # Manager-owned host inventory
```

The Local Kit does not create `kristals/index.json` and should not infer access rights from the existence of this directory. The Manager-produced index and C3 checks must preserve per-state ownership, provenance and access policies. Two equal slugs or GitHub paths do not establish equivalent `state_ref` identities.
