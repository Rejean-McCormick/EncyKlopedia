# Validation v0.7 — Kristal v6 et affordances

Date : 2026-10-01

## Références d'écosystème examinées

Snapshot agrégé fourni : `Code_snapshot_Koali_Scenario_Mosaic_Index.zip`, SHA-256 `8391a70fd69bd998ff6061e1ba318813e786fe1b6f6234d26f1d7fa2e322ddad`.

Références utilisées :

- `kristal-framework` — Standard v6, `kristal_state`, compatibilité v5/v6 ;
- `kristal-reference` — identité JCS v6 et invariants de valuation/actionabilité ;
- `SemantiK_Architect` — distinction entre capability profiles de runtime et planning hints ;
- `Interaction-Kernel` — frontière état opérationnel / artefact ;
- `Koali_Scenario_Mosaic` — architecture capability-first et séparation des intentions humaines des composants.

## Validations exécutées ici

- `node --check` sur les modules serveur modifiés : OK.
- Parsing JSON du schéma upstream v6, des hints et des exemples : OK.
- Identité de l'exemple `kristal_state` v6 recalculée indépendamment : SHA-256 `534d57141a4d1c982e2ddb25abfda19be7d63234667542dd3eea6acc5cf6b759`, conforme au `state_id` fourni.
- `node --test tests/navigation-adaptive.test.mjs tests/navigation-variety.test.mjs tests/kristal-v6-navigation.test.mjs` : **13/13 tests passent**.
- Détection testée : temporalité, quantitatif, multidimensionnel, état, actionabilité, conflits, succession, lignée, évidence et provenance.
- Catalogue de recettes testé : États, Évolution, Divergences, Traçabilité, Décisions & action.
- `NavigationPlan` v0.2 validé contre `contracts/navigation-plan.schema.json` sur un profil v6 synthétique : OK.

## Limite d'environnement

Le snapshot ne contient pas `node_modules` et le runtime du conteneur est Node 22.16.0 alors que le dépôt exige Node >= 24.15.0. Le build Astro/Svelte complet et la suite dépendant d'Ajv/Playwright ne sont donc pas déclarés comme exécutés ici.

À exécuter sur la machine projet :

```bash
npm ci
npm test
npm run test:ui
npm run build
npm run test:e2e:smoke
```

## Invariants vérifiés par conception

- aucune valuation v6 n'est aplatie en pseudo-certitude ;
- les valeurs non connues ne deviennent pas zéro ou faux ;
- `actionability` ne devient pas permission d'exécuter ;
- les omissions de la projection locale v6 sont déclarées, jamais silencieuses ;
- `kristal_state` reste le canon, les vues Konstellation restent dérivées ;
- les hints de navigation n'injectent pas de code UI et ne créent pas de faits.
