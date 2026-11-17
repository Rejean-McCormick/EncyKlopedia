# 22 — V10 alignment: candidate 3.2.5-rc.1

This is a **maintenance candidate**, based on the exact Authoring Kit 3.2.4 snapshot provided on 2026-10-12. The established workspace, v9 commitment and GitHub read-surface format identifiers are unchanged. This documentation does not claim the upstream Framework v10 draft is finalized or that any hosted collection passed end-to-end qualification.

## Scope of this candidate

| Harmonization item | Implemented in candidate | Boundary |
| --- | --- | --- |
| A-01 read-surface verification | Added allowlisted index path/role checks, true byte-size verification, duplicate path rejection; tests for tampering and deterministic projection | Source of files remains the Kit; readiness is not consent |
| A-02 older Kit migration | Read-only two-copy audit script, compares canon bytes, state identity and any comparable built commitments | Does not migrate or rewrite 126 workspaces |
| A-03 optional AI | Verifies stale AI regardless of `portable_ai.enabled=false` when explicitly checking a surface; added negative tests | `check` still does not require AI if disabled |
| A-04 v10 workflow boundaries | English owner/gate documentation separating local build, C1/C2 qualification, Manager sync, C3 and release | No authorization or GitHub mutation provided |
| A-05 materialization availability | Negative test for remote locator and coverage; manifests remain linked without remote fetch | No automatic blob transport or new semantic contract |

## Compatibility evidence to preserve

- `kristal.local-workspace/3.2.0`, `kristal.authoring-state-index/2.0.0`, `kristal.state/9.0`, `kristal.hosting/10.0` and `kristal.github-read-surface/1.0` identifiers remain unchanged.
- Previous 3.2.4 tool SHA is an **external baseline**, not the SHA of the newly modified candidate. Do not put the candidate under the official 3.2.4 pin without formally updating the consumer's trust policy.
- The existing `examples/` tool copies and sample AI manifests retain historical metadata. They were not migrated or reissued as new commitments.
- Public `kristal-public` index/manifest readiness and the incomplete Manager snapshot remain independently **BLOCKED**, not solved by this package.

## Test commands

```bash
python -m unittest -v tests.test_v10_alignment
python scripts/check_repo.py
python scripts/audit_workspace_migration.py --before ../Untouched --after ../UpgradedCopy
```

The audit reports `PRESERVED`, `BLOCKED` or `NOT_FULLY_QUALIFIED`. The last is expected if comparable built states are not present; source absence is not an implicit pass. To advance this candidate, compare the same fixtures against the selected Framework v10 contract-set, obtain Manager/C3 consumer acknowledgement and test a qualified private staging read path.

## Security and release status

The Kit never independently verifies C1/C2 signatures and never grants permission to synchronize to a public repository. A public GitHub sync is a disclosure operation **even if it is not an immutable release**. Only the Manager/C1/C2/C3 owners may permit it at an approved exact revision and scope.
