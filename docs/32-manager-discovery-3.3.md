# Konstellation — Manager inventory and Authoring Kit 3.3 Discovery

**Status:** working-tree, read-only, local-only integration. The Manager producer contract is a **candidate**, not a ratified inter-project contract. Discovery metadata is **noncanonical and advisory**. No sync, mutation, publication, qualification or activation is added. This changes only Konstellation's local consumer.

## 1. Inputs and ownership

- **Kristal Manager** exports `kristal.manager-local-inventory/0.1-candidate` (`records[]`) using `python -m kristal_manager export ... --output PRIVATE.json`. This is operational observation, not proof of publication. Do **not** use `--include-paths` for this integration.
- **Konstellation operator** supplies a separate private `konstellation.manager-access-policy/0.1`. Manager does not supply principals or roles; permissions **must not** be inferred from title, slug, state_ref, readiness or file location. Missing policy means no raw Manager inventory is displayed.
- **Authoring Kit 3.3** produces `kristal.discovery/1.0` + `kristal.reader-inventory/1.0` + `kristal.reader-profile/1.0`. Konstellation optionally consumes a *small projected catalog*, not arbitrary private files or executable reader instructions.
- **Konstellation** filters the authorized Manager projection on the server before delivering titles/counts, attaches Discovery metadata only to local, visible, exact `state_ref` matches, and never merges hosted reader entries with local entries.

## 2. Local use

Requires Node.js >=24.15 and dependencies installed as documented in the project README. Configure only on the trusted local workstation; default bind address is `127.0.0.1`. No network-facing My Kristals endpoint is allowed.

```powershell
# Export separately from the existing local Kristal Manager installation.
python -m kristal_manager export C:\mycode\Kristal --output C:\private\manager-inventory.json

# Make a PRIVATE operator-only policy, based on examples/fleet/manager-access-policy.example.json.
# Use the exact state_ref and State Commitment reported by the authorized Manager inventory.
$env:KONSTELLATION_DEPLOYMENT_PROFILE = 'local'
$env:KONSTELLATION_ENABLE_MY_KRISTALS = 'true'
$env:KONSTELLATION_FLEET_EXPORT = 'C:\private\manager-inventory.json'
$env:KONSTELLATION_FLEET_POLICY = 'C:\private\manager-access-policy.json'
$env:KONSTELLATION_LOCAL_PRINCIPAL = 'local-user'
# Optional Discovery catalog (see below)
$env:KONSTELLATION_DISCOVERY_CATALOG = 'C:\private\discovery-catalog.json'
npm start
```

`examples/fleet/manager-access-policy.example.json` is *synthetic*: replace its references and digest with data that actually appears in the Manager export. Grant only specific local principals wherever possible. Missing/invalid policy fails closed. Exact State Commitment match is required when present. Rows with missing `state_ref`, identity collisions or duplicate `state_ref` are never exposed. Matching by slug/title is forbidden. The Manager's `READY` means structurally observed local readiness, not C1 qualification or hosted publication. Local inventory items remain **not openable** until an independently authorized compatible reader is configured.

The old `konstellation.manager-inventory-preview/0.1` sample remains supported as a *legacy fixture* and is now at `examples/fleet/legacy/manager-preview.example.json`; it already carries explicit per-entry authorization but is not produced by current Manager.

## 3. Build a minimal Discovery catalog

You can supply **explicit** Authoring Kit 3.3 manifests, never an auto-discovered directory:

```powershell
node scripts/project-discovery.mjs --output C:\private\discovery-catalog.json C:\Kristals\VehiculeDiag\kristal.discovery.json
```

The script reads only the named discovery file plus its adjacent `derived/reader-profile.json` when present; it checks format, status and shared `source_fingerprint`. The output only carries `state_ref`, declared classification (`ARK-xx` / `PRF-xx`), organization, suggested reader, optional access pattern, measured registered bytes and the source fingerprint for lineage. The source fingerprint is **not** a v9 logical commitment and cannot authorize access. An operator must ensure metadata is suitable for disclosure before configuring it. Missing classifications use the generic reader; no classification is inferred. No parser configuration is executed automatically, and no local filesystem path or source payload is returned to the browser.

**Important limit:** the catalog's source fingerprint is a *declared link*, not proof that its measured source files are still identical. For a trustworthy runtime reader, separately verify actual artefacts and freshness using the Authoring Kit. This consumer never promotes advisory metadata to semantic state.

## 4. Security and tests

- Entire `/api/fleet` capability remains opt-in on loopback (`local` profile and loopback HOST only), with authenticated principal scope `read`. No network publication.
- Bounded explicit local regular files only: Manager export/policy <=1 MiB each; discovery catalog <=256 KiB. Symlink inputs rejected. No recursive scan or paths in normalized Manager rows.
- ACL matching occurs server-side before any results, facet counts, or metadata are sent. Duplicate local identities are denied, and hosted observations stay independent.
- The three Authoring Kit files are derived **noncanonical** data, not authorization or C2/C4 receipts. GitHub index listings are unverified until their existing reader checks bytes/manifests.
- If no Discovery catalog is supplied, My Kristals works as before and displays `Unknown` for undeclared Arketype type.
- Disabling `KONSTELLATION_ENABLE_MY_KRISTALS` rolls back to existing Explorer without any change to the canonical state or Manager repo.

```bash
node --test tests/fleet.test.mjs tests/manager-discovery.test.mjs tests/kristal-v10.test.mjs
node scripts/check-svelte-structure.mjs
npm test
npm run test:ui
npm run build
```

Full validation requires a supported Node 24.15 environment, the original dependencies, Windows smoke, an authorized real Manager sample, and v9/v10/browser tests. These are not implied by the unit tests.

## 5. Snapshot migration / cleanup

Historical synthetic preview example was moved to `examples/fleet/legacy/manager-preview.example.json`. The root-level `Nettoyage_Konstellation.pyw` offers **manual** deletion of the old unmodified copy at `examples/fleet/manager-preview.example.json` after hash verification and user confirmation. It does not search for or remove other files; it never touches `.kristal-integration-backup` or canonical data. `maintenance-cleanup.json` is the reviewable allowlist. If the former file was modified locally, it is intentionally preserved.
