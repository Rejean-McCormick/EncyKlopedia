# ADR-0009 — Actionability n'est pas une autorité d'exécution

- Statut : accepté

## Décision

`actionability.mode = automatic` est une information sémantique du Kristal. Elle ne confère aucune permission d'exécuter une opération.

## Conséquence

La recette `action-context` est purement informative. Toute future exécution doit passer par un contrat séparé d'autorisation et d'audit.
