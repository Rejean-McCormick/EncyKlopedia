# My Kristals — KNAV implementation preview

**Status:** local-only, explicitly opt-in **working-tree implementation**. **Not a ratified Manager ↔ Konstellation contract, not a v10 publication or a qualified Konstellation release.** This document implements a bounded KNAV-02/KNAV-03 preview from the consolidated 12 October 2026 harmonization plan. KNAV-01, KNAV-04 and end-to-end gates remain blocked or incomplete.

## Responsibilities and precise limits

| Owner | Responsibility | Status in this worktree |
|---|---|---|
| Kristal Manager | Discover and inspect local Kristal instances; produce authorized registry/export | **Not modified.** The examined Manager recovery snapshot contains `kristal_manager/inventory.py`; its candidate export is now accepted through a separate explicit operator access policy. Its contract is still provisional, not ratified. |
| Konstellation | Session security, permission-filtered list, My Kristals UI, existing corpus navigation | Implemented as optional local preview; no canonical state mutation. |
| GitHub v10 | Verified hosted read surfaces | Existing index-and-reader adapter retained. The listing verifies the index; individual entry bytes/manifests are verified **when opened**, not when listed. |
| Kompiler | Read-only semantic Context Packs | No new integration here; a technical hosting view is **not** a conceptual decoder. |
| Arketype | Optional declared archetype and visual taxonomy | Optional `archetype` string only, **not** inferred and not used for identity. |
| Konstellation Light / Publisher | Static public view / software deployment | Not touched. Neither publishes Kristal states. |

The library supports two levels: **My Kristals** (authorized inventory and configured readers), then **Explorer** (existing Lens / graph / query navigation for an opened supported reader). An inventory-only entry is explicitly **not openable**. This prevents accidental reinterpretation of `kristal.workspace.json`, a Manager record, or arbitrary v9 content as semantic v6 assertions.

## Launch locally on Windows

Requires Node.js >=24.15 and installed dependencies. The provided `.cmd` only selects the historic Kristal-Kollection when `KONSTELLATION_USE_LEGACY_KOLLECTION=true` is set. For an interactive local fleet preview, set these environment variables **for the current process/session**, then use the existing start procedure:

```powershell
$env:KONSTELLATION_DEPLOYMENT_PROFILE = 'local'
$env:KONSTELLATION_ENABLE_MY_KRISTALS = 'true'
$env:KONSTELLATION_FLEET_EXPORT = 'C:\mycode\Konstellation\Konstellation\examples\fleet\legacy\manager-preview.example.json'
# Optionally choose an existing v10 checkout reader config, if its index is valid:
# $env:KONSTELLATION_BACKEND_CONFIG = 'C:\mycode\Konstellation\Konstellation\examples\integrations\kristal-github-v10.json'
npm start
```

The sample records are **synthetic**; they do not represent the actual 126 local Kristals. No workspace is searched or modified, no `build-ai`, `read-surface`, sync, publication or activation is run. If no export file is supplied, the fleet starts with only any already-configured backend reader entries. If none are configured, it shows an empty inventory and offers a button to explore the current corpus.

The `Launch_My_Kristals.cmd` convenience wrapper enables the page using `Konstellation_Launcher.cmd` (still requires dependencies / supported Node). The Windows launcher honors an explicitly set `KONSTELLATION_BACKEND_CONFIG` for a v10 checkout, prefers the user-provided portable Node 24 if present, and will **not terminate** an existing process on port 4321; `KONSTELLATION_FLEET_EXPORT` can be set beforehand to a private local file. Its legacy default is no longer selected implicitly.

## Experimental, non-normative export

`konstellation.manager-inventory-preview/0.1` remains a **legacy local synthetic fixture**, not an approved Manager format. The real Manager candidate `kristal.manager-local-inventory/0.1-candidate` is now supported through a separate authorization policy. Manager's producer contract remains to be negotiated between its owner, Konstellation and C0. Format example: [`../examples/fleet/manager-preview.example.json`](../examples/fleet/manager-preview.example.json).

Per record, required `id`, `title`, `visibility` (`public` or `private`), `readiness` (`unknown`, `not_checked`, `not_ready`, `ready`, `blocked`, `unavailable`), `availability` (`unknown`, `available`, `unavailable`), `allowed_principals` and `allowed_roles`. Optional `state_ref`, `state_commitment` (`sha256:<64 hexadecimal>`), and explicitly declared `archetype`. All other fields are rejected; **filesystem paths, private locators, tokens, trust receipts and canonical content are never exported**. `state_commitment` is display-only and **declared**, not independently recomputed.

Every record must explicitly authorize the current session principal by ID or role; **default deny**. Server-side filtering is performed before the list or count reaches the browser. If it is not known whether the entry is allowed, omit it. For strict isolation use `allowed_principals` with individual principals rather than broad `allowed_roles`. The default local principal identifier is `local-user` unless configured otherwise.

The local file must be explicitly configured, be a regular non-symlink file and be no larger than 1 MiB; up to 1,000 entries are accepted. Only local deployment with loopback listening (`127.0.0.1`, `::1` or `localhost`) allows the feature. The API `GET /api/fleet` is authenticated, needs `read` scope and returns `Cache-Control: no-store`. The endpoint responds 404 when disabled or outside the local profile. No private filesystem pathname is returned to the browser. Errors do not block the existing Explorer startup.

The response `konstellation.fleet-view/0.1` is a **non-normative view** with separate source observations (`local:<id>`, `reader:<id>`). Same name/slug or same `state_ref` **never merges** local and hosted states. GitHub index-listed entries use `verification=index_only` until their reader performs strict file checks; no status implies qualified, published or activated. Local observations use `verification=declared_only` and remain inventory-only until a separately authorized compatible reader exists.

## Validation, rollback and remaining gates

Run:

```bash
node --test tests/fleet.test.mjs tests/manager-discovery.test.mjs tests/kristal-v10.test.mjs
node scripts/check-svelte-structure.mjs
npm test                 # requires project dependencies
npm run test:ui          # requires project dependencies
npm run build            # requires Node >=24.15, dependencies
npm run test:e2e:smoke  # browser/Playwright qualification
```

Manager and Discovery 3.3 extensions, example files and operator-only access policies are documented in [the local integration guide](32-manager-discovery-3.3.md).

Minimum negative cases: invalid version, secrets/paths in export, duplicate IDs, unauthorized private title/count, symlink export, >1 MiB, bad digest, index absent, same slug across sources, non-openable inventory only, and deployment profile other than local. A complete acceptance gate additionally requires a real Manager producer, version/policy approval and supported Node, browser and Windows validation.

Rollback is **disable `KONSTELLATION_ENABLE_MY_KRISTALS`** and use the existing Explorer. The original `/api/kristals`, runtime, Reader Policies, query handlers, existing adapters and canonical Kristals have not been changed by this preview.
