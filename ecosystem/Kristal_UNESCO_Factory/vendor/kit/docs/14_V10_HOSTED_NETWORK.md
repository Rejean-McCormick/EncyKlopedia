# 14 — Kristal v10 hosted network for authors

Kristal v10 does not replace the v9 State Snapshot or its Logical/State Commitments. It adds operational **Node Manifest**, **Host Binding**, **Publication**, and **Directory** concepts. The Framework `10.0.0-draft.3.1` reviewed for this plan is a **draft**, not a formally released stable v10.

```text
v9 = exact logical knowledge state
v10 = where/how a qualified state is hosted, discovered, and optionally activated
```

Local `hosting/github.json` is configuration, **not semantic content** and never an input to the Logical Commitment. One GitHub repository can host several separately owned Kristals under `kristals/<slug>/`, each with its own `state_ref`, state revision and access scope. A repository is therefore an operational permission boundary, not necessarily a Kristal.

The current Authoring Kit can describe a GitHub target but cannot attest that a remote collection has passed C1/C2/C3 qualification. Use the operator Manager/Bootstrap workflows rather than assuming a host binding is authorization. Never equate Git SHA, byte digest or read-surface digest with the v9 State Commitment.
