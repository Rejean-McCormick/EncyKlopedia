# Tools — Kristal Local Kit 3.3.1

The local CLI relies only on Python's standard library. The GitHub CLI is relevant only to advanced legacy `github-*` operations. It does not provide an authorization or qualification service.

## Create and inspect local workspaces

```bash
python tools/kristal.py init PATH --title "Title" --slug slug --profile open
python tools/kristal.py check PATH
python tools/kristal.py status PATH
python tools/kristal.py inspect PATH --compact
python tools/kristal.py audit-discovery PATH --compact
```

Legacy envelope migration (only on a **separate copy**, after backup):

```bash
python tools/kristal.py migrate-v10 STAGING_PATH
python scripts/audit_workspace_migration.py --before ORIGINAL_PATH --after STAGING_PATH
```

## Source and v9 domain state

```bash
python tools/kristal.py add-source PATH --id src:1 --title "Source" --locator external://source
python tools/kristal.py register-artifact PATH --file canon/domain/core.json --artifact-id urn:kristal:demo:core --contract-id demo.core
python tools/kristal.py register-materialization PATH --manifest path/to/materialization.json
python tools/kristal.py add-reference PATH --kind state --id urn:kristal:state:child --digest sha256:<64hex>
python tools/kristal.py build-v9 PATH
```

`build-v9` performs a semantic build by default and does **not** regenerate optional AI files unless explicitly requested. Existing verified v9 Materialization Manifests remain separate from source Logical Commitments and do not force physical blob copies.

## Derived AI reading and Manager interoperability

```bash
python tools/kristal.py build-ai PATH
python tools/kristal.py check-ai PATH
python tools/kristal.py read-surface PATH --compact --require-ready
python tools/kristal.py pack-ai PATH --output portable-reader.zip
```

`inspect` emits `kristal.local-inspection/1.0`. `read-surface` emits `kristal.github-read-surface/1.0` and verifies the exact list of safe reader paths, roles, sizes and SHA-256 values. It does **not** synchronize anything or grant disclosure permission. Large materialization blobs remain separate transport candidates.

## Local v9 lifecycle, separate from hosted v10

```bash
python tools/kristal.py qualify-v9 PATH --profile V9-State-Reader
python tools/kristal.py publish-v9 PATH
python tools/kristal.py activate-v9 PATH --channel current
```

## Hosted v10 — advanced compatibility operations only

The recommended path uses **Manager** for inventory and authorized reader synchronization, plus independent **C1/C2/C3** and **GitHub Bootstrap** for trust and publication. Legacy operators may inspect the existing CLI options:

```bash
python tools/kristal.py configure-from-network PATH --network ../network.toml --repository kristal-public
python tools/kristal.py configure-github PATH --repository OWNER/REPO --framework-repository OWNER/Kristal-Framework --framework-sha <40sha>
python tools/kristal.py github-status PATH
```

The further `export-hosted`, `github-qualify`, and `github-publish` commands are **advanced compatibility paths**, not instructions to bypass independent qualification or owner authorization. A public sync already discloses bytes, before an immutable release is published.

## Local archives

```bash
python tools/kristal.py hash-manifest PATH
python tools/kristal.py pack PATH --output workspace.zip
```

`pack` does not build an AI capsule implicitly; use `pack-ai` for that derived output.

`audit-discovery` is read-only and produces a consumer diagnostic; it never authorizes
publication, identity merging, nor access to protected local artifacts.

## v11 authoring commands (v4 draft.1)

`enable-v11`, `check-v11`, `coverage-v11`, `check-v11-plan`, `apply-v11-plan`, `select-v11-graph`. See [semantic authoring](docs/26_V11_SEMANTIC_AUTHORING.md) for exact examples, scope and limits. All new graph and label checks are strictly opt-in; the historical `check`, `build-v9` and `publish-v9` lifecycle is preserved.
