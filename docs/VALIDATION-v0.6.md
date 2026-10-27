# Validation v0.6 — navigation adaptative

Date : 2026-10-01

## Exécuté dans le snapshot

- `node --check` sur les modules serveur, intégrations et tests modifiés : OK.
- Parsing JSON de `package.json`, `exploration-state.schema.json` et `navigation-hints.schema.json` : OK.
- Extraction des blocs `<script>` des composants Svelte modifiés puis `node --check` : OK.
- Vérification de l’équilibre des blocs Svelte `if/each/...` des composants modifiés : OK.
- `node --test tests/navigation-adaptive.test.mjs tests/navigation-variety.test.mjs` : **10/10 tests passent**.
- Les cas représentatifs couvrent Math, HumanBody, HistoryTech, ScolQc, HospitalOps et Power sans branchement sur le nom du domaine.
- Test synthétique du `StructuralProfiler` : 100 000 assertions / 120 relations, environ **32 ms** dans le conteneur de validation. Cette mesure est indicative, pas un SLA.

## Non exécuté dans ce conteneur

Le snapshot ne contient pas `node_modules`. Le runtime disponible ici est Node 22 alors que le projet déclare Node >= 24.15.0. Une tentative d’installation des dépendances nécessaires à Svelte/Astro a expiré dans l’environnement. Par conséquent, les commandes suivantes n’ont pas été déclarées comme validées :

- `npm test` complet (les tests qui importent Ajv/Hyparquet exigent les dépendances) ;
- `npm run test:ui` ;
- `npm run build` ;
- Playwright.

Sur une machine conforme au `package.json`, exécuter :

```bash
npm ci
npm test
npm run test:ui
npm run build
npm run test:e2e:smoke
```

## Compatibilité visée

- `exploration-state` reste en `0.2`; les nouveaux champs de navigation sont optionnels.
- Liste, Tableau et Constellation restent disponibles.
- Les `navigationHints` sont optionnels : leur absence déclenche l’introspection seule.
- Les hints ne permettent pas d’injecter du code UI.
