# Migration Report — v3.1 → v3.2

Le format racine devient `kristal.local-workspace/3.2.0`. Cette migration est une évolution d'enveloppe/outillage, pas une redéfinition du state v9.

## Préservé

- `state_ref` ;
- State Index v9 et Logical Contracts ;
- canon, sources, docs, projections ;
- commitments et profils v9 ;
- configuration GitHub existante ;
- couche IA existante, si présente.

## Changé

- vocabulaire UX : **Local Kristal** ;
- AI/Kompiler devient optionnel ;
- `build-v9` ne construit plus l'IA par défaut pour un nouveau Local Kristal ;
- `portable_ai.enabled` indique si un workspace souhaite reconstruire automatiquement la couche IA avec `build-v9` ;
- Manager devient le propriétaire de l'inventaire et de la synchronisation GitHub ; GitHub Setup/Bootstrap devient le propriétaire du lifecycle réseau principal.

Commande :

```bash
python tools/kristal.py migrate-v10 PATH
python tools/kristal.py check PATH
```
