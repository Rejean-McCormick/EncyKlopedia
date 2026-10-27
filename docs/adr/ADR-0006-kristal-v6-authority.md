# ADR-0006 — Kristal v6 reste l'autorité canonique

- Statut : accepté
- Portée : architecture 1.0

## Contexte

Konstellation construit des packs locaux, profils, timelines, graphes et autres dérivés pour rendre un Kristal navigable.

## Décision

`kristal_state` v6 reste l'autorité canonique. Tous les artefacts Konstellation sont des vues ou index dérivés.

## Conséquences

- l'identité d'un pack local ne remplace pas `state_id`/`content_hash` ;
- les pertes d'import sont explicites ;
- les projections peuvent être supprimées/recalculées ;
- les renderers ne créent jamais d'assertions.
