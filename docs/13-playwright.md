# Playwright et validation navigateur

## Objectif

Playwright couvre les comportements que les tests unitaires/DOM ne qualifient pas : navigation réelle, layout, clavier, responsive, téléchargement, historique et intégration frontend/API.

## Suites 1.0 minimales

### Smoke

- page charge ;
- bootstrap valide ;
- recherche ;
- sélection d'une entité ;
- inspecteur ;
- navigation de base.

### Adaptive navigation

- le plan recommandé apparaît ;
- changement de recette ;
- mode pinned ;
- changement de focus ;
- fallback si la recette devient inapplicable.

### Renderers

Pour chaque renderer :

- état normal ;
- vide ;
- troncation/pagination ;
- erreur ;
- clavier ;
- mobile ;
- fallback accessible.

### Policy

- changement de policy ;
- absence de fuite dans facets/autocomplete/projection/traceability ;
- invalidation de contexte.

### Persistance

- sauvegarde ;
- import/export ;
- lien partageable ;
- migration d'un état ancien.

## Environnement

La CI 1.0 doit exécuter Playwright avec la version Node supportée par `package.json`, sur un build produit avec `npm ci` et le lockfile du repo.

## Artefacts

Conserver sur échec :

- screenshot ;
- trace ;
- vidéo pour scénarios critiques ;
- logs API corrélés si disponibles.
