# Guide développeur

## Où intervenir

- `server/navigation/profiler.mjs` : dérivation d’affordances et profils global/type/result-set/focus ;
- `server/navigation/planner.mjs` : recettes, scoring et explication ;
- `server/navigation/registry.mjs` : registre fermé de renderers ;
- `server/navigation/projection.mjs` : projections DTO bornées ;
- `server/navigation/projector.mjs` : Constellation générique ;
- `server/engine.mjs` : query/policy/cache et orchestration ;
- `server/auth.mjs`, `server/config.mjs` : identité/déploiement ;
- `contracts/` : schémas publics ;
- `src/components/` : shell et renderers ;
- `tests/` : contrats, moteur, policy, UI, API, E2E ;
- `benchmarks/` + `scripts/benchmark-navigation.mjs` : budgets de régression.

## Ajouter une affordance

1. démontrer qu’elle est cross-domain ;
2. ajouter l’identifiant au contrat NavigationPlan/NavigationHints ;
3. privilégier les signaux explicites avant l’heuristique lexicale ;
4. ajouter evidence explicable ;
5. ajouter tests golden positifs **et négatifs** ;
6. vérifier qu’une Reader Policy peut la masquer sans fuite.

## Ajouter une recette

1. définir l’intention cognitive ;
2. définir requirements/benefits ;
3. associer un renderer contrôlé ;
4. définir DTO/projection/budgets ;
5. définir fallback accessible ;
6. tester déterminisme, coûts et policy.

## Ajouter un renderer

Le Kristal ne fournit jamais le code. Ajouter le composant au repo, l’enregistrer dans `registry.mjs`, mettre à jour le JSON Schema, fournir clavier/focus/fallback/export si déclaré, et couvrir au moins un E2E.

## Gates locaux

```bash
npm run docs:check
npm test
npm run test:ui
npm run build
npm run test:e2e
npm run benchmark -- --full
```

Avant tag final : `npm run release:check`.

## Règle de sécurité

Une donnée masquée ne doit jamais remonter dans `reason`, `evidence`, compteurs, labels, suggestions, graphes ou traces client. `actionability` n’autorise aucune exécution.
