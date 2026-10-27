# Validation v0.3 — 26 septembre 2026

## Vérifications réussies

Environnement : Node.js 24.19.0; versions npm verrouillées par `package-lock.json`.

| Vérification | Résultat |
|---|---|
| `npm test` | 19 tests réussis : moteur, API HTTP, import SES |
| `npm run test:ui` | 4 tests réussis : véritables composants Svelte dans jsdom, véritable moteur, transport simulé |
| `npm run build` | Construction Astro de production réussie; incluse dans `dist/` |
| `node scripts/smoke-dev.mjs` | Frontend de développement, POST via proxy avec Origin 127.0.0.1 et arrêt supervisé réussis |
| `npm run pack:validate -- data/demo.pack.json` | 278 entités, 637 assertions, 2 politiques; pack valide |
| Import CLI de `examples/import/state.json` avec son mapping | Pack distinct produit, 1 assertion conservée; aucune signature prétendue vérifiée |

Les tests couvrent notamment : pivot sur toute une population au-delà de la première page; corrélation des critères sur un même auteur; politiques avant jointures, facettes et preuves; conflits inaccessibles non exposés; exclusions multivaluées; dates incomplètes; déduplication; curseurs signés et incompatibilités; contrôle d’accès statique; dépassements de budget; contrats de résultats; import sans omission silencieuse; filtres conservés lors d’un changement de Lens; historique; vues tableau/graphe; inspection; périodes et sauvegardes.

## Limites de validation

La suite `npm run test:browser` contient quatre scénarios Playwright. Le téléchargement standard de Chromium a échoué. Un exécutable alternatif a ensuite quitté par SIGTRAP avant de charger la page. Aucun de ces essais ne constitue un test navigateur réussi.

Le rendu visuel réel, le débordement mobile, les téléchargements et le presse-papiers navigateur restent à vérifier sur une machine avec Chromium fonctionnel. Les tests jsdom vérifient les interactions et le DOM; ils ne rendent pas les pixels et ne prouvent pas la mise en page.

Aucune qualification d’un Runtime Pack Kristal binaire, d’un RuntimeSet SA/GF, d’une politique Kristal complète ou d’une installation multiutilisateur n’est revendiquée. Aucune mesure sur grand corpus n’est présentée comme benchmark. Les métadonnées synthétiques de démonstration ne sont pas une validation historique.
