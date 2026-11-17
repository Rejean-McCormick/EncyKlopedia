# 13 — Workspace migration and compatibility audit

The established migration command is `python tools/kristal.py migrate-v10 PATH`. It accepts legacy local v1/v2 workspaces and handles v3/v3.1 envelope migration according to the existing implementation. It is **not** the proper first step on the owner's only copy.

## Legacy envelopes

- **v1 → v2:** adds `state_ref` and v9 target; converts the legacy State Index to structured Logical Artifact entries. Unresolved legacy contracts are explicitly marked with the placeholder `Local Kristal.legacy-json-artifact/1.0` and a migration note; no factual contract is inferred.
- **v2/v3 → 3.2:** upgrades the workspace envelope to `kristal.local-workspace/3.2.0`, declares optional target `kristal.hosting/10.0`, and adds `hosting/` and `build/v10/` organization. The existing canonical index, canonical payload and v9 Logical/State Commitments are not meant to change.
- **3.2.2/3.2.3 tools → candidate 3.2.5-rc.1:** the file tool and local layout are versioned independently. Do not replace embedded tools in the original 126 workspaces en masse. Stage a separate copy, record file digests, run check/inspect/build-v9, and compare independently.

## Required migration gate

```bash
python scripts/audit_workspace_migration.py --before ../Original --after ../Staging
```

The audit is **read-only**. It compares canonical file membership/bytes, `state_ref` and any available v9 State Snapshot commitments. An absent snapshot is `NOT_FULLY_QUALIFIED`, **not** evidence of equality. Any canonical drift or commitment difference is `BLOCKED` and needs a separate domain migration decision. Preserve the original workspace for rollback.

No target GitHub repository, grant, host binding or publication is inferred during migration. Run `configure-github` only when the owner has deliberately chosen a real repository and a verified Framework commit SHA.
