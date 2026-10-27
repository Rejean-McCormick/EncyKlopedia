# Correctif — Sélecteur neutre / session locale privée

## Symptôme

`AppError: Le catalogue local nécessite une session locale privée.` lors du lancement de `Konstellation.cmd`, avant l’ouverture de la page.

## Cause

`server/config.mjs` utilise `local` lorsque `KONSTELLATION_DEPLOYMENT_PROFILE` est absent, mais l’ancien `server/integrations/local-catalog.mjs` exigeait `process.env.KONSTELLATION_DEPLOYMENT_PROFILE === "local"`. Le lanceur neutre n’exportait pas cette variable.

## Correctif

- Le catalogue s’appuie maintenant sur `loadConfig()` et ses paramètres normalisés, identiques au serveur.
- Le lanceur définit explicitement `KONSTELLATION_DEPLOYMENT_PROFILE=local`, `HOST=127.0.0.1` et désactive les options de lecture publique héritées.
- Les protections refusant un service public, une écoute non locale ou une session anonyme restent en place.
- Aucun changement aux Kristals, au Framework, à Manager, à Daat ni à Interaction Kernel.

## Installation Windows

1. Arrêter Konstellation, puis sauvegarder `C:\mycode\Konstellation\Konstellation`.
2. Extraire le présent ZIP dans ce dossier en conservant l’arborescence et en remplaçant les trois fichiers existants.
3. Double-cliquer sur `Konstellation.cmd`.
4. Visiter `http://127.0.0.1:4321` et sélectionner `A-Kristal-Catho` dans « Mes Kristals ».

Catho reste à `C:\mycode\Kristal\locals\A-Kristal-Catho`.

## Contrôles effectués dans l’environnement de préparation

- 15/15 tests ciblés réussis (`neutral-local-catalog` et `kristal-local-v10`).
- Sur l’archive fournie de Catho : entrée disponible dans le catalogue, 4 527 entités et 13 217 assertions chargées par `loadLocalCatalog()`.
- Les modes public, anonyme et hors loopback sont toujours refusés.

Le démarrage complet de l’interface sur Windows/Node 24 reste à confirmer localement.
