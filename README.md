# Konstellation

**Adaptive, domain-agnostic navigation engine for Kristal knowledge.**

**Release candidate:** `1.0.0-rc.2`. Architecture and target code exist, but a reproducible release build and full E2E gates remain prerequisites for final `1.0.0` qualification. See [implementation status](docs/IMPLEMENTATION.md) and [current validation evidence](docs/VALIDATION-v1.0-RC.md).

## Core principle

> Kristal defines what is knowable. A Lens defines the viewing angle. Konstellation derives explainable navigation affordances from visible structure, creates a `NavigationPlan`, and selects a controlled renderer. A view never creates new semantic truth.

```text
Kristal state v6 / normalized pack
    → Reader Policy + roles
    → Structural Introspection
    → Navigation Affordances
    → Lens + ResultSet + Focus
    → NavigationPlan 1.0
    → Projection DTO 1.0
    → Renderer Registry
    → Konstellation Shell
```

## Renderers

Generic renderers include list, table, constellation, `timeline-lineage`, `tree`, `dag-proof`, `flow-path`, `causal-feedback`, `matrix-profile`, `state-flow`, `traceability`, `multiscale-layer` and `spatial`. They are not hard-coded to a domain such as mathematics, history or medicine.

## Requirements and startup

A qualified release requires **Node.js >= 24.15.0** and a committed, reproducible `package-lock.json` generated under the supported release environment.

```bash
npm ci
npm run build
npm start
```

The default `local` profile listens on `127.0.0.1:4321`.

### My Kristals (KNAV preview)

Konstellation can show an optional **My Kristals** page before opening the existing conceptual Explorer. The preview is read-only and enabled only with `KONSTELLATION_ENABLE_MY_KRISTALS=true` in the `local` deployment profile. It can display an **explicit, separately authorized JSON inventory export** alongside the configured collection reader entries; it **does not** discover all local workspaces on its own. Inventory-only records cannot be opened without a reader. See [My Kristals setup, security, limits and tests](docs/31-my-kristals-manager-preview.md) and `Launch_My_Kristals.cmd`. This is a **working-tree preview**, not a qualified release or a ratified Manager integration. This snapshot also accepts the Manager candidate local export through an explicit ACL file, and can display optional Authoring Kit 3.3 Discovery projections. See [Manager + Discovery guide](docs/32-manager-discovery-3.3.md).

### Lecteur local Kristal v10 (expérimental)

Le lecteur explicite `kristal-local-v10` (voir `docs/33-kristal-v10-local-reader.md`)
ouvre une vue dérivée d'un workspace local à état sémantique v9 (conservé
par le Framework v10) sans modifier ni qualifier le canon. Les diagnostics
Manager alpha.14 peuvent être affichés séparément dans My Kristals, toujours
sous ACL explicite. Ils ne constituent ni permission de lecture ni autorité.
Pour Catho, laissez le Kristal à son emplacement canonique local
`C:\mycode\Kristal\locals\A-Kristal-Catho` et lancez
`Ouvrir_Kristal_Catho_v10.cmd` (Node >=24.15 requis). Le lanceur principal
utilise `config/active-reader.json` lorsqu'il existe, et ne choisit plus la
démonstration Théophile implicitement. Pour rouvrir la démonstration,
lancez `Ouvrir_Theophile_demo.cmd`. Aucun fichier de Catho n'est déplacé.

### Parcours de lecture des Kristals locaux (correctif expérimental)

Quand un graphe dérivé déclare des `kind`, Konstellation les expose comme
**perspectives distinctes** plutôt que d'ouvrir par défaut `V9 state`.
Dans `config/active-reader.json`, `readModel.presentation.preferredKind` et
`featuredKinds` ne sont que des préférences d'interface locales, jamais des
contrats canoniques. Les libellés de types et de relations sont facultatifs;
ils ne confèrent aucune validation ni équivalence à leurs objets.

Pour Catho, les parcours en accueil sont Personnes, Œuvres, Thèmes, Sources,
Assertions historiques et Hypothèses ouvertes. Les états et artefacts v9
restent accessibles dans la liste Perspective. L'avertissement est désormais
« Lecture locale dérivée » et non « Corpus de démonstration ».
Le dossier Catho reste `C:\mycode\Kristal\locals\A-Kristal-Catho`.
Voir `docs/35-parcours-locaux-catho.md`.

### Legacy local Kristal selection

Only when `KONSTELLATION_USE_LEGACY_KOLLECTION=true` is explicitly set and a compatible legacy collection is placed in `../kristals`, `Konstellation_Launcher.cmd` can select `examples/integrations/kristal-kollection.json`. The context header offers a **KRISTAL** selector. The selected reference is retained locally and included in shared/exported navigation metadata. Domains without exactly one readable `*.kristal-state.json` remain visible but disabled. `X-Konstellation-Kristal` scopes a request without mutating the shared server corpus.

The reference to a local **Kristal-Kollection directory/layout** does not rename the separate GitHub hosting repository `kristal-public`.

## Tests and release gates

```bash
npm test
npm run test:ui
npm run build
npm run test:e2e
npm run benchmark -- --full
npm run release:preflight
npm run release:check
```

**Do not tag final `1.0.0`** until `npm run release:check` succeeds in a supported environment with the committed lockfile.

## Deployment profiles

| Profile | Boundary |
| --- | --- |
| `local` | Single local operator |
| `lan` | Trusted-network deployment with configured authentication policy |
| `shared` | Authentication, roles/scopes, audit and rate limiting |
| `public` | Strict CSP, recommended TLS/gateway and authentication unless read-only public access is explicitly enabled |

Read [deployment](docs/22-deployment.md) and [security](docs/19-security.md) before exposing services.

## Repository map

| Path | Contents |
| --- | --- |
| `src/` | Astro/Svelte shell and renderers |
| `server/` | Engine, API, reader policy, profiler, planner and projections |
| `contracts/` | Published and upstream JSON Schemas |
| `tests/` | Policy, API, UI, contract and E2E tests |
| `benchmarks/` | Regression measurements |
| `scripts/` | Import and release tooling |
| `docs/` | Specifications, guides, ADRs and runbooks |
| `data/` | Demonstration corpus |

Start at [documentation index](docs/README.md); consult [release policy](docs/25-release-1.0.md) for qualification requirements.

## Choisir son Kristal local (mode neutre)

Lancer `Konstellation.cmd`, puis sélectionner un Kristal dans **Mes Kristals**.
Le dossier `C:/mycode/Kristal/locals` reste à son emplacement d'origine.
Pour changer ce dossier, éditer `config/local-catalog.json`. Aucune modification canonique n'est effectuée.
Voir `docs/LOCAL_SELECTOR_2026-10-16.md` pour les limites et les outils de migration.
