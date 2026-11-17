# 15 — GitHub read synchronization versus qualified publication

Two distinct operations exist:

**Read-surface sync** projects a validated derived set of local files under `kristals/<slug>/`, produced **only** by Local Kit `read-surface` and orchestrated by Manager. It is neither a complete workspace mirror nor a semantic build.

**Immutable v10 publication** requires independently qualified State Snapshot/bundle evidence, controlled authorization, an exact verified repository revision and an explicit release/activation lifecycle owned by C1/C2/C3 and Bootstrap.

## Recommended gates

```text
Local Kit: check → build-v9 → build-ai → check-ai → read-surface --require-ready
Manager: inspect → validate exact manifest and state → verify owner authorization
C1: qualify exact candidate revision independently
C2: approve exact disclosure scope, collection, paths, operation, expiry
Manager: authorized sync (public or private, checked before any write)
C3: verify collection index and sync manifests → qualified publication workflow
Activation: separate, explicit operator decision
```

**Important:** “sync is not publication” does *not* mean it is private. Sync into a **public repository** already discloses bytes. A public upload must be protected *before staging, commit and push*, with exact-revision qualification and owner authorization. A passing Local Kit `check` or `read-surface` can never replace those gates.

The Kit's `export-hosted`, `github-status`, `github-qualify` and `github-publish` commands remain **advanced legacy compatibility paths**, not the recommended owner workflow. Their presence is not authorization to use them.
