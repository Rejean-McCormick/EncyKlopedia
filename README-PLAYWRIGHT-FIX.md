# Konstellation — correctif Playwright 1.1

Correctif du démarrage E2E lorsque `data/biblical.pack.json` n'existe pas.

Le corpus de test est maintenant préparé automatiquement :

1. réutilise `data/biblical.pack.local.json` s'il est valide ;
2. sinon part de `data/demo.pack.json` ;
3. exécute `scripts/update-biblical-corpus.mjs` ;
4. tente BibleData en ligne ;
5. retombe sur le corpus biblique hors ligne si nécessaire ;
6. démarre ensuite le serveur Playwright sur le port 4323.

Le test des 3000+ figures BibleData est automatiquement ignoré si l'import complet n'est pas disponible; les autres tests restent actifs.
