# Validation v0.4 — 27 septembre 2026

Environnement : Node 24.19.0. Dépendances verrouillées dans package-lock.json.

| Vérification exécutée | Résultat |
|---|---|
| `npm test` | 29 tests réussis |
| `npm run test:ui` | 6 tests Svelte DOM réussis |
| `npm run build` | Construction Astro réussie, dist inclus |
| `node scripts/smoke-dev.mjs` | Frontend et POST via proxy : 132 résultats |
| Serveur de production avec configuration Parquet fournie | Démarrage, bootstrap et requête : 132 résultats |

Les tests d'intégration couvrent le décodage Parquet de 637 assertions, les empreintes et signatures Ed25519, les budgets, les mappings incomplets, les chemins sortants, les politiques de lecture, les capacités indisponibles, sept pages HTTP, les erreurs de complétude/contexte, la génération SA, les obligations/sources omises et le cycle HTTP découverte-validation-rendu.

Les tests DOM couvrent filtres, changement de perspective, pivots, historique, vues, inspection sous politiques différentes, période, sauvegarde/restauration, pagination, préparation de requête SA, invalidation lorsque la sélection change et indisponibilité d'une facette.

Aucun RuntimeSet SA/GF réel ni corpus de production externe n'a été qualifié ici. Le serveur SA de test est une fixture de contrat. Le profil sémantique Konstellation doit être publié par le runtime externe pour activer la formulation. Les exemples Kristal sont synthétiques.

La tentative Chromium antérieure a échoué avant chargement de page. Le rendu visuel natif, le débordement mobile et les téléchargements dans un navigateur complet restent non qualifiés; les tests Playwright sont fournis. Les tests DOM ne remplacent pas cette qualification.

Le manifeste de livraison contient les SHA-256 des fichiers de l'archive hors manifeste lui-même. Les sources, configurations, tests et dist sont inclus; node_modules et caches sont exclus.
