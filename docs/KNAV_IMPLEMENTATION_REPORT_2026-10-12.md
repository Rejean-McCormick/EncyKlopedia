# Konstellation KNAV — implementation and test report

**Date:** 2026-10-12. **Repository owner:** Konstellation only. **Status:** working-tree preview; **not** an approved multi-repository contract and **not** a release-qualified Konstellation build.

## Scope delivered

- `server/integrations/fleet.mjs`: bounded optional input of one explicitly configured JSON export, schema `konstellation.manager-inventory-preview/0.1`; separate authorized observations, strict field whitelist, principal/role filtering before API response, no recursive scan or path leakage.
- `server/config.mjs`: feature gated by `KONSTELLATION_ENABLE_MY_KRISTALS=true`, **local profile only**.
- `server/index.mjs`: authenticated `GET /api/fleet`, read scope required, feature disabled responds 404; existing `/api/kristals` and all query/Reader Policy routes are unchanged.
- `src/components/MyKristals.svelte`, `src/components/Explorer.svelte`, `src/styles/global.css`: fleet cards, filters, properties, read-only status, existing viewer link and return preserving selection/filters; entries without readers not openable.
- `examples/fleet/legacy/manager-preview.example.json`: **synthetic fixture only**; does not represent the 126 real local instances.
- `Launch_My_Kristals.cmd`: opt-in Windows entry point; historic Kollection auto-select disabled by default in `Konstellation_Launcher.cmd`, now requires `KONSTELLATION_USE_LEGACY_KOLLECTION=true`; occupied port is **not forcibly terminated**; an explicitly configured v10 backend is preserved by the Windows launcher, which prefers a known portable Node 24 and rejects versions below 24.15.
- `docs/31-my-kristals-manager-preview.md`, `README.md`, `CHANGELOG.md`, `tests/fleet.test.mjs`: behavior, compatibility constraints, security and rollback.

## Scope deliberately excluded / blocked

1. **Real Manager integration:** Manager package `kristal_manager/` is absent from the provided snapshot. Manager must publish and approve an authenticated/versioned export (KNAV-01) and agree with Konstellation/C0 before an official integration can replace this preview.
2. **Automatically showing all 126 local workspaces:** not claimed or implemented. Konstellation does not crawl `C:\\mycode\\Kristal\\locals` and does not read canonical domain data for inventory.
3. **General v9/v10 semantic decoding:** not implemented. Existing v10 adapter remains strictly a technical hosting topology; a Context Pack or supported domain reader is needed for semantic concepts (KNAV-04).
4. **Remote GitHub fetch / publication / activation:** absent by design. The v10 adapter reads a local verified checkout; Bootstrap/Manager keep ownership of network operations.
5. **Public and shared fleet views:** feature disabled outside local deployment until a ratified per-user ACL integration exists. Konstellation Light and Publisher are unchanged.
6. **Arketype auto-classification:** not implemented. Any archetype is *explicitly declared display metadata*, never inferred or authority-bearing.

## Verified tests on this environment

| Check | Result |
|---|---|
| `node --test tests/fleet.test.mjs tests/kristal-v10.test.mjs` | **13/13 PASS** (6 preview/authorization + 7 existing v10) |
| `node scripts/check-svelte-structure.mjs` | **PASS, 19 components, 0 problems** |
| `node scripts/check-frontend-security.mjs` | **PASS, 22 files, 0 problems** |
| `node scripts/check-docs.mjs` | **PASS, 64 Markdown files, 79 links, 0 problems** |
| `python tools/validate.py` | **PASS, 62 offline checks** |
| `node --check` on modified server modules | **PASS** |

### Checks not performed successfully

- Full `npm test`, `npm run test:ui`, `npm run build`, browser Playwright and Windows GUI: **NOT RUN**. This environment provides Node **22.16.0**, while Konstellation requires **>=24.15.0**, and `npm install --ignore-scripts --no-audit --no-fund --prefer-offline` timed out because `registry.npmjs.org` was not reachable (`EAI_AGAIN`). No compiled UI or browser success is claimed.
- End-to-end Manager→Konstellation→real Kristal: **BLOCKED** on official Manager producer and reader compatibility.
- GitHub v10 collection hosted pilot: the supplied `kristal-public` checkout lacks `kristals/index.json`; the strict reader must continue to reject it.

## Changes and rollback

No upstream repository, GitHub resource, release, local canonical workspace, publication, activation or sync has been modified. Roll back My Kristals by removing/unsetting `KONSTELLATION_ENABLE_MY_KRISTALS` or launching the original Explorer. The legacy collection selector remains available only by explicit opt-in. Nothing in this preview changes logical commitments or workspace identity.

**Before merging into a production branch:** verify Node >=24.15, install pinned dependencies, compile Astro/Svelte, run full tests and Playwright, run security review of real Manager export (producer and consumer), and validate deployment scope/revision and C0 acceptance. Do not describe this as finished full ecosystem harmonization.
