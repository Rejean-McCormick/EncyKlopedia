# Comportement attendu par famille de Kristal

Ce document sert de référence de comportement pour le planner. Les noms de corpus ne doivent pas devenir des branches métier ; ils servent ici à définir des **golden expectations**.

## Catho / Théophile

Structure dominante : argumentation, evidence, provenance, sources, thèmes, auteurs, conflits/relations positionnelles.

Recettes attendues :

- Constellation ;
- Positions/arguments ;
- Traçabilité ;
- Divergences si conflits explicites ;
- Chronologie si dates pertinentes.

Ne pas déduire une influence historique à partir d'un simple lien éditorial.

## HistoryTech

Structure dominante : occurrences, temporalité, lieux, lignées, dérivation/transmission.

Recettes attendues :

- Chronologie ;
- Évolution/lignée ;
- Spatial lorsque coordonnées/lieux le permettent ;
- Dépendances pour les dérivations explicites.

Une date portée par une occurrence reliée doit rester navigable par saut sémantique borné.

## HumanBody

Structure dominante : network, multiplex, multiScale, causal, signedCausal, cycle, pathways.

Recettes attendues :

- Constellation ;
- Parcours ;
- Boucles ;
- Multi-échelle ;
- éventuellement spatial/anatomique selon données.

Un cycle non causal ne suffit pas à déclencher la recette feedback.

## Math

Structure dominante : dependency, proof, refutation, counterexample, pédagogique.

Recettes attendues :

- Preuves ;
- Dépendances ;
- Parcours pédagogique ;
- Constellation en fallback.

Ne pas imposer une racine ontologique unique si le corpus est polycentrique.

## ScolQc

Structure dominante : hierarchy, conditionalTransition, prerequisites, versioned rules.

Recettes attendues :

- Parcours ;
- Hiérarchie ;
- Évolution/version ;
- Dépendances/prérequis.

Une relation `may_transition_to` ne doit pas être affichée comme transition garantie sans ses conditions.

## HospitalOps

Structure dominante : stateMachine, workflows, resourceAllocation, metrics, roles.

Recettes attendues :

- Parcours ;
- États ;
- Décisions & action ;
- Comparaison métrique si disponible.

Aucune affordance actionability ne constitue une permission d'opérer le système hospitalier.

## Power

Structure dominante : multidimensional, quantitative, network, mechanisms, metrics.

Recettes attendues :

- Comparer / matrix-profile ;
- Constellation ;
- Dépendances/mécanismes si structurées.

Les scores dimensionnels ne doivent pas être transformés en verdict global implicite.

## FoodBrands / source-centric

Structure dominante : providers, sources, acquisition, provenance.

Recettes attendues :

- Catalogue ;
- Tableau ;
- Traçabilité ;
- éventuellement réseau de sources.

Ne pas forcer une vue spectaculaire si la structure ne la justifie pas.

## Kristal inconnu

Attendu minimum :

- recherche ;
- facettes ;
- liste ;
- tableau ;
- Constellation si relations entité-entité ;
- inspecteur ;
- provenance/evidence si présentes.

L'absence d'affordance spécialisée est un résultat valide.
