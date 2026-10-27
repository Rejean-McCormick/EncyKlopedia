# État d’implémentation — Konstellation 1.0 RC

Ce document est la source de vérité sur l’état **réel du code**. La spécification 1.0 est implémentée dans cette branche sous le numéro `1.0.0-rc.2`. Le suffixe RC est conservé tant que tous les gates opérationnels de [25-release-1.0.md](25-release-1.0.md) ne sont pas exécutés avec succès dans l’environnement de release supporté.

## Résumé

Implémenté :

- lecture native Kristal v6 avec `kristal_state` comme autorité canonique ;
- QuerySpec/Lens/Reader Policy séparés ;
- introspection structurelle globale, par type, result set et focus ;
- affordances 1.0 explicables et policy-scoped ;
- `navigationHints` 1.0 déclaratifs, avec compatibilité des anciennes clés ;
- `NavigationPlan` 1.0 versionné et validé ;
- Renderer Registry fermé et validé ;
- projections natives pour toutes les familles prioritaires 1.0 ;
- shell adaptatif Svelte avec fallback accessible et LOD ;
- ExplorationState 1.0 + migration 0.2 ;
- auth multi-principal pour profils partagés, scopes, rate limiting, CSP par profil ;
- health/readiness/version, erreurs corrélables, logs JSON et métriques ;
- golden tests positifs/négatifs, test DAG profond et benchmark 10k/100k/1M + scénarios structurels ;
- gates statiques frontend : aucun `style=`/`style:`, aucun sink HTML/dynamic-code (`{@html}`, `innerHTML`, `eval`, `new Function`), SVG interactifs nommés et focusables, blocs structuraux équilibrés, CSS Astro externalisé ;
- aucun branchement runtime sur un domaine ou Kristal nommé.

Non qualifié dans ce snapshot :

- `npm ci` reproductible, car `package-lock.json` est absent du snapshot amont ;
- compilation Astro/Svelte sous Node `>=24.15.0`, l’environnement courant étant Node 22.16.0 sans `node_modules` ;
- suite Vitest complète ;
- Playwright complet ;
- qualification accessibilité navigateur ;
- qualification des SLOs HTTP/rendering sur matériel de production.

Ces points empêchent de publier honnêtement `1.0.0` final, mais ne sont plus des gaps d’architecture ou de code métier.

## Matrice d’implémentation

| Fonction | État RC 1.0 |
|---|---|
| QuerySpec 0.2 | conservé, stable |
| Lens 0.2 | conservée + génération générique automatique |
| Reader Policy | appliquée avant query/facets/entity/evidence/constellation/plan/projection |
| Kristal v6 adapter | natif, loss report + métadonnées structurelles |
| StructuralProfiler | global/type/result-set/focus, agrégats indexés |
| Navigation affordances | 28 affordances 1.0, evidence explicable |
| NavigationHints | contrat 1.0, aucun code exécutable |
| NavigationPlan | contrat 1.0, `derived=true` |
| Renderer Registry | contrat 1.0, fermé, budgets/fallbacks/LOD |
| Liste | implémentée |
| Tableau | implémenté |
| Constellation | implémentée, domain-neutral |
| Timeline / Evolution | `timeline-lineage` |
| Hiérarchie | `tree` |
| Dépendances / Preuves | `dag-proof` |
| Parcours | `flow-path` |
| Boucles | `causal-feedback` |
| Dimensions | `matrix-profile` |
| États / Action context | `state-flow` |
| Divergences / Traçabilité | `traceability` |
| Multi-échelle | `multiscale-layer` |
| Spatial | `spatial` |
| ExplorationState | 1.0 + migration 0.2 |
| Auth partagé | tokens multi-principaux + rôles + scopes |
| Observabilité | logs JSON, requestId, métriques p50/p95/p99 |
| Release automation | `release:preflight` + `release:check` |
| Reproductibilité | manifest SHA-256 déterministe + SBOM CycloneDX ; lockfile obligatoire pour promotion finale |
| Runbooks prod | startup, rollback, backup/restore, incident, threat model, upgrade |

## Introspection policy-scoped

Le profiler utilisé par le planner est construit sur l’état **déjà visible** selon Reader Policy et rôles. Les relations sans assertions visibles ne contribuent pas aux affordances policy-scoped. Les sources, preuves, conflits et lignées invisibles ne peuvent pas réapparaître comme compteur, score, raison ou projection.

Ordre des signaux :

```text
structure canonique explicite
  > hints déclaratifs compatibles
  > schéma/topologie observés
  > heuristiques lexicales de fallback
```

En mode non restreint, les hints peuvent renforcer une structure observée. En mode policy-scoped, les scores/raisons globaux ainsi que les hints de présentation (`preferredRecipes`, `recipeLabels`) sont ignorés ; seuls les mappings sémantiques de relations effectivement visibles peuvent aider à classifier la structure. Ainsi un score, un texte ou un ordre déclaré ne constitue pas un canal latéral.

## Planner 1.0

Le planner combine :

```text
KristalProfile
  + TypeProfile
  + ResultSetProfile
  + FocusProfile
  + Lens
  + coût/budget
  -> NavigationPlan 1.0
```

Sans focus, un échantillon déterministe borné du result set visible alimente `forResultSet()`. Avec focus, `forFocus()` prévaut. Le résultat contient recettes, renderer IDs, raisons, relations structurantes et actions contextuelles.

## Projections 1.0

`server/navigation/projection.mjs` fournit des DTOs bornés et validés pour :

- `timeline-lineage` ;
- `tree` ;
- `dag` ;
- `flow` ;
- `causal-feedback` ;
- `matrix` ;
- `state-flow` ;
- `traceability` ;
- `multiscale` ;
- `spatial`.

Les graphes utilisent `nodeBudget`/`edgeBudget`, les séquences/records utilisent pagination/cursors lorsque pertinent, et le frontend permet expansion progressive ou fallback tabulaire. Les DTOs publics sanitizés n’exposent pas les payloads upstream bruts : `actionability`, `lineage`, `valuations` et `coordinates` sont réduits à des formes publiques strictement nécessaires au renderer.

## Sécurité

Profils supportés : `local`, `lan`, `shared`, `public`.

- `local` : principal local explicite, bind local par défaut ;
- profils non locaux : principal authentifié obligatoire sauf opt-in `KONSTELLATION_ANONYMOUS_READONLY=true` ;
- `KONSTELLATION_AUTH_TOKENS` mappe des tokens vers `{id, roles, scopes}` ;
- ancien `KONSTELLATION_AUTH_TOKEN` conservé pour compatibilité ;
- moteurs/caches sont isolés par ensemble de rôles ;
- cursors sont liés à l’accessRef ;
- `actionability` n’est jamais transformé en permission/exécution ;
- CSP publique n’utilise pas `unsafe-inline` ; Astro externalise les feuilles de style et le source Svelte interdit les attributs/directives de style inline ;
- headers de défense en profondeur : `Permissions-Policy`, COOP/CORP, `nosniff`, `no-referrer`, frame denial et cross-domain policy ;
- l’identité du corpus n’est exposée par `/api/version` que si `KONSTELLATION_EXPOSE_CORPUS_IDENTITY=true`.

## Performance validée dans cet environnement

Commande :

```bash
node scripts/benchmark-navigation.mjs --full
```

Dernier résultat observé dans ce conteneur :

| Assertions | Profiler | Planner |
|---:|---:|---:|
| 10k mixte | ~40 ms | ~3 ms |
| 100k mixte | ~78 ms | ~5 ms |
| 1M mixte | ~753 ms | ~27 ms |
| 100k dense | ~87 ms | <1 ms |
| 100k timeline | ~91 ms | <1 ms |
| 100k DAG profond | ~175 ms | ~27 ms |
| 100k multi-échelle | ~1030 ms | ~14 ms |
| 100k forte cardinalité | ~109 ms | <1 ms |

Ces mesures sont des résultats de développement, pas des SLOs contractuels. Les plafonds de régression automatisés sont dans `benchmarks/navigation-baseline.json`.

## Tests exécutables sans dépendances dans ce snapshot

Le corpus navigation dependency-free passe actuellement 24/24 :

```bash
node --test \
  tests/navigation-adaptive.test.mjs \
  tests/navigation-variety.test.mjs \
  tests/kristal-v6-navigation.test.mjs \
  tests/navigation-golden-1.0.test.mjs
```

Des tests supplémentaires 1.0 couvrent contracts, sécurité, Lens génériques et non-fuite policy ; ils font partie de `npm test` et nécessitent les dépendances du projet.

## Gate de release

```bash
npm run release:preflight
npm run release:check
```

Dans l’environnement courant, le preflight échoue volontairement sur :

1. Node 22.16.0 au lieu de `>=24.15.0` ;
2. absence de `package-lock.json` ;
3. SBOM marqué incomplet, conséquence directe de l’absence de lockfile.

Aucun contournement artificiel n’est ajouté au repo. La promotion `1.0.0-rc.2 -> 1.0.0` doit avoir lieu seulement après exécution réussie de `npm ci`, tests Node, Vitest, build, Playwright et benchmark complet sous Node supporté.

## Addendum du 2026-10-08 — lecteur opérationnel v10

Le correctif v10 GitHub ajoute un adaptateur **facultatif** de navigation technique.
Il conserve l’architecture 1.0 RC (`1.0.0-rc.2`) et ne requalifie pas sa release :
aucun changement des contrats QuerySpec, Lens, NavigationPlan, UI ou Reader Policy.
Vérification octet/SHA-256, index et sync manifest, cohérence des références AI
et du Snapshot v9, refus des chemins dangereux et fichiers non gérés.
La valeur `checks.semanticCommitmentVerified=false` est intentionnelle :
ce contrôle n’est pas une preuve de la logique des membres du Snapshot.
Les tests unitaires Node autonomes sont exécutables hors dépendances ; le
build Astro, la suite complète Node 24/Vitest/Playwright restent à qualifier.

Voir [30-kristal-v10-github.md](30-kristal-v10-github.md).
