# 06 — Workspace layout and lifecycle

## 1. A workspace organizes responsibilities, not one domain payload shape

The local layout separates canonical content, sources, projections, build results, releases, runtime materializations, optional AI files, and host configuration.

## 2. Current local workspace skeleton

```text
kristal.workspace.json
canon/state.index.json
canon/domain/                  # owned domain artifacts
canon/epistemic/               # epistemic layer when applicable
canon/operations/              # domain operations when applicable
sources/source-catalog.json
projections/recipes/
docs/
materializations/v9/manifests/
build/v9/                      # generated, noncanonical
state/state-snapshot.json      # optional explicit reader export
release/v9/                    # immutable local release outputs
hosting/                       # operational v10 host bindings
ai/ and AI_MANIFEST.json       # optional derived portable reader
```

## 3. Three separate lifecycles

**Semantic authoring:** edit and validate native content, then `build-v9`. **Local offline release:** `publish-v9`, optionally `activate-v9` to a local channel. **Hosted v10 lifecycle:** separately qualified/authorized sync, immutable release, and optional activation. Neither one authorizes the other.

## 4. Ownership and federation

A parent can refer to a child Kristal by pinned identity and commitment without duplicating its canon. Hosting multiple Kristals in one GitHub collection does not merge their ownership.

## 5. Canon versus build/materialization/runtime

`canon/` owns admitted logical content. Materialization descriptors describe physical representations, including remote or partially available blobs; `build/`, `ai/`, runtime packs, views and collection indexes are derived/operational. A GitHub upload is a transport/exposure decision, not a canonical mutation.
