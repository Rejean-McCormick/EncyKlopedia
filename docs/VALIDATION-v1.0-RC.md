# Validation Konstellation 1.0 RC

Date : 2026-10-02  
Version source : `1.0.0-rc.2`

Ce rapport distingue les contrôles **effectivement exécutés dans ce snapshot** des gates qui nécessitent l’environnement de release supporté.

## Exécuté et vert

### Navigation dependency-free

```bash
node --test \
  tests/navigation-adaptive.test.mjs \
  tests/navigation-variety.test.mjs \
  tests/kristal-v6-navigation.test.mjs \
  tests/navigation-golden-1.0.test.mjs
```

Résultat : **24/24 tests passent**.

Couverture : Kristal v6, recettes génériques, Math/HumanBody/HistoryTech/ScolQc/HospitalOps/Power, Catho-like, Kristal générique minimal, hints 1.0, attentes positives/négatives, suppression des hints de présentation sous policy et DAG profond sans récursion de pile.

### Sécurité bootstrap dependency-free

```bash
node --test tests/security-1.0.test.mjs
```

Résultat : **5/5 tests passent**. La couche `auth/config` ne dépend plus d’Ajv pour construire ses erreurs ; elle peut donc être testée avant chargement des schémas. Couverture : fail-closed hors profil local, multi-principal rôles/scopes, token legacy, CSP publique sans `unsafe-inline`, principal local explicite.

### Validation hors-ligne des contrats

```bash
python tools/validate.py
```

Résultat : **62 contrôles passent**. Le validateur Python résout explicitement les URN des schémas sans réseau. Les 10 familles de projection ont des fixtures positives et des rejets négatifs ciblés.

Le contrat `navigation-projection` lie `projectionKind`, `rendererId` et `recipeId`, impose les champs de chaque famille et valide les structures internes (nœuds, arêtes, transitions, conditions, événements, cellules, records, points). Les métadonnées upstream sensibles/inutiles ne sont pas autorisées dans les DTOs publics.

### Structure Svelte / CSP / accessibilité statique

```bash
node scripts/check-svelte-structure.mjs
```

Résultat : **17 composants Svelte, 0 problème**. Le gate vérifie notamment : blocs Svelte équilibrés, scripts/SVG équilibrés, SVG `role=button` focusables et nommés, absence de `button role=listitem`, et absence d’attribut/directive de style inline.

Le source n’utilise plus `style=`/`style:`. Les positions dynamiques SVG utilisent l’attribut `transform`, les indentations utilisent des classes déterministes, et `astro.config.mjs` fixe `build.inlineStylesheets = "never"`. Cela aligne le source sur la CSP publique sans `unsafe-inline`; le comportement du bundle construit reste à confirmer par le gate navigateur.

### Gate statique sécurité frontend

```bash
node scripts/check-frontend-security.mjs
```

Résultat : **20 fichiers frontend inspectés, 0 problème**. Le gate interdit raw HTML sinks, évaluation JavaScript dynamique, styles inline, scripts Astro inline et imports CSS distants ; il vérifie aussi `build.inlineStylesheets = "never"`.

### Syntaxe / JSON / documentation

- **66** fichiers JS/MJS vérifiés par `node --check` ;
- **65** fichiers JSON parsés sans erreur ;
- **62** fichiers Markdown inspectés ;
- **75** liens locaux vérifiés, **0 problème**.

### Benchmark navigation complet

```bash
node scripts/benchmark-navigation.mjs --full
```

Mesure exécutée dans cet environnement :

| Scénario | Assertions | Profiler | Planner | Baseline |
|---|---:|---:|---:|---|
| mixte | 10 000 | 40.06 ms | 3.41 ms | OK |
| mixte | 100 000 | 78.32 ms | 4.61 ms | OK |
| mixte | 1 000 000 | 752.53 ms | 26.95 ms | OK |
| dense | 100 000 | 86.94 ms | 0.20 ms | OK |
| timeline | 100 000 | 90.95 ms | 0.18 ms | OK |
| DAG profond | 100 000 | 174.51 ms | 26.94 ms | OK |
| multi-échelle | 100 000 | 1030.33 ms | 14.12 ms | OK |
| forte cardinalité | 100 000 | 108.72 ms | 0.24 ms | OK |

Tous les scénarios restent sous les plafonds de régression de `benchmarks/navigation-baseline.json`. Ces mesures sont des résultats de développement, pas des SLOs contractuels de production.

## Durcissements confirmés par cette RC

- Reader Policy appliquée avant introspection, planification et projection ;
- relation entièrement masquée absente des affordances/recommandations ;
- DTOs de projection stricts et métadonnées publiques sanitizées ;
- `actionability` reste informative et n’accorde jamais une permission ;
- CSP publique sans `unsafe-inline` au niveau source/configuration ;
- navigation clavier Tree et SVG interactifs avec noms accessibles ;
- couches auth/config découplées du validateur Ajv ;
- manifest source, SBOM et release gates présents.

## Tests présents mais non exécutables ici

Ils nécessitent `node_modules` et/ou Node supporté :

- `tests/contracts-1.0.test.mjs` avec Ajv ;
- `tests/lenses-1.0.test.mjs` ;
- `tests/navigation-policy-1.0.test.mjs` ;
- tests Engine/API/intégrations dépendant d’Ajv/hyparquet ;
- Vitest/Svelte, dont les renderers spécialisés ;
- Playwright complet.

## Reproductibilité

Le repo contient :

- `scripts/release-manifest.mjs` : manifest déterministe SHA-256 du source ;
- `scripts/generate-sbom.mjs` : SBOM CycloneDX 1.6 ;
- `release:manifest:check` et `release:sbom:check` ;
- `/api/version` avec build ID, hash de manifest source et hash d’artefact optionnel.

Le SBOM généré sans lockfile est volontairement marqué incomplet et `release:sbom:check` échoue : cela empêche une qualification trompeuse. Une tentative de génération du lockfile depuis ce conteneur n’a pas pu résoudre le registre npm ; aucun lockfile artificiel n’est produit.

## Gates bloquées dans ce conteneur

`npm run release:preflight` doit rester rouge ici sur :

- Node `22.16.0` alors que `package.json` exige `>=24.15.0` ;
- absence de `package-lock.json` ;
- SBOM de dépendances nécessairement incomplet sans lockfile.

Ces points sont des **gates de qualification**, pas des contournements à coder.

## Non exécuté dans cet environnement

- `npm ci` ;
- suite Node complète dépendante d’Ajv/hyparquet ;
- Vitest/Svelte ;
- `astro build` ;
- Playwright complet ;
- audit navigateur réel avec CSP publique ;
- qualification accessibilité navigateur ;
- SLO HTTP/rendering sur matériel cible.

## Statut

Le code est implémenté selon la cible 1.0 et reste `1.0.0-rc.2` jusqu’à exécution réussie, sous Node supporté et avec lockfile commité, de :

```bash
npm ci
npm run release:prepare
npm run release:check
```
