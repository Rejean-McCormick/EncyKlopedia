# ADR-0007 — Utiliser des affordances de navigation dérivées

- Statut : accepté

## Contexte

Le terme capability est déjà utilisé dans l'écosystème pour des capacités runtime. Konstellation a besoin de représenter la pertinence d'une structure pour la navigation.

## Décision

Utiliser le terme **affordance de navigation** pour `temporal`, `proof`, `hierarchy`, etc. Une affordance est dérivée, scorée et accompagnée d'evidence.

## Conséquences

- elle n'est pas canonique ;
- elle n'est pas une permission ;
- les aliases `capabilities` peuvent être lus pour compatibilité, mais ne sont plus la terminologie cible ;
- les recettes s'appuient sur des affordances plutôt que sur des catégories métier.
