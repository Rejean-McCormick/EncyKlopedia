# ADR-0008 — Séparer planner, projection et renderer

- Statut : accepté

## Décision

Le Navigation Planner choisit les recettes. Le Projection Service construit des DTOs bornés. Le Renderer affiche ces DTOs.

## Raisons

- testabilité ;
- sécurité ;
- déterminisme ;
- réutilisation cross-domain ;
- possibilité de fallback ;
- possibilité d'optimiser projection et UI indépendamment.

## Interdiction

Un renderer ne doit pas exécuter sa propre logique de policy ou inventer une query cachée hors contrat.
