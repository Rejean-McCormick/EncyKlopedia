# Astrolabe dans l'architecture finale

Astrolabe est une **surface d'entrée et de suggestion**, pas le moteur sémantique de Konstellation.

## Rôle cible

Astrolabe peut :

- proposer des entrées de navigation ;
- suggérer des entités/types/recettes pertinentes ;
- refléter la terminologie du Kristal courant ;
- utiliser le NavigationPlan pour ordonner des suggestions.

Il ne doit pas :

- contenir des hypothèses catholiques/bibliques en dur dans son comportement générique ;
- créer de faits ;
- modifier QuerySpec sans action explicite ;
- contourner Lens ou Reader Policy.

## Configuration de domaine

Les entrées propres à Catho/Théophile/Biblical Graph sont des exemples/configurations de corpus. Elles ne doivent s'activer que lorsque le corpus ou la Lens correspondante est chargé.

## Adaptation

Un Astrolabe générique peut utiliser :

- types dominants ;
- labels ;
- hubs calculés/déclarés ;
- recettes recommandées ;
- historique utilisateur local.

Le choix reste une suggestion, jamais une mutation silencieuse.
