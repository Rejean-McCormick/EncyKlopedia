# Plan de qualification vers Konstellation 1.0.0

La source `1.0.0-rc.2` implémente les contrats, affordances, projections spécialisées, renderers et hardening runtime décrits par cette documentation. Le travail restant avant de retirer le suffixe RC est un **travail de qualification reproductible dans l’environnement de release**, pas une nouvelle refonte architecturale.

## Phase A — Contrats (implémentée)

- figer `NavigationPlan` 1.0 ;
- stabiliser le vocabulaire des affordances ;
- stabiliser les DTOs de projection par famille ;
- définir les règles de compatibilité/migration ;
- normaliser `navigationHints` sous le vocabulaire `affordances`.

### Gate

Tous les schémas publics sont versionnés et validés par tests.

## Phase B — Renderers structurels (implémentée)

Les familles suivantes sont implémentées et doivent rester couvertes par les tests de release :

1. `tree` ;
2. `dag-proof` ;
3. `flow-path` ;
4. `causal-feedback` ;
5. `timeline-lineage` ;
6. `matrix-profile` ;
7. `multiscale-layer` ;
8. `spatial` selon priorité réelle.

Chaque renderer doit avoir :

- projection DTO dédiée ;
- limites et LOD ;
- fallback accessible ;
- export ;
- tests unitaires et navigateur.

## Phase C — Golden corpus (implémentée et extensible)

Les fixtures stables couvrent au minimum :

- Math ;
- HumanBody ;
- HistoryTech ;
- ScolQc ;
- HospitalOps ;
- Power ;
- Catho ;
- un Kristal incomplet/générique ;
- un Kristal v6 riche en metadata ;
- un corpus volumineux synthétique.

Le corpus doit inclure des attentes positives **et négatives**.

## Phase D — Scalabilité (implémentée, à requalifier à chaque release)

- remplacer les hard caps ad hoc par une stratégie uniforme de pagination/LOD ;
- virtualiser listes/tables volumineuses ;
- introduire des index persistants optionnels ;
- benchmarker 10k, 100k, 1M records/assertions ;
- fixer des seuils de régression.

## Phase E — Production hardening (implémentée côté source ; qualification restante)

- lockfile obligatoire ;
- CI Node 24.15+ ;
- `npm ci` ;
- build Astro/Svelte ;
- gate statique Svelte/CSP/accessibilité ;
- Playwright complet ;
- logs structurés ;
- métriques ;
- readiness ;
- `/api/version` ;
- SBOM/checksums ;
- runbooks ;
- threat model selon profil de déploiement.

## Phase F — Qualification et release 1.0.0

La release est produite uniquement lorsque tous les gates de [25-release-1.0.md](25-release-1.0.md) applicables au profil de déploiement sont verts.
