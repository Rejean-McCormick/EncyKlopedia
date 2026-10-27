# Contribuer à Konstellation

## Avant de modifier le comportement

Lire :

1. `docs/00-decisions.md`
2. `docs/01-architecture.md`
3. `docs/03-navigation.md`
4. l'ADR correspondant dans `docs/adr/`
5. `docs/IMPLEMENTATION.md`

## Règles de contribution

- ne jamais promouvoir une projection Konstellation au rang de fait Kristal ;
- ne jamais contourner Reader Policy ;
- ne jamais ajouter une branche planner basée uniquement sur un nom de domaine ;
- préférer une affordance/recette cross-domain ;
- ne pas accepter de code UI fourni par un Kristal ;
- versionner tout contrat public ;
- ajouter des tests positifs et négatifs ;
- documenter toute rupture dans `docs/08-migration.md` et `CHANGELOG.md`.

## Tests

```bash
npm test
npm run test:ui
npm run build
npm run test:browser
```

Pour une nouvelle affordance, recette ou projection, ajouter au minimum :

- tests profiler ;
- tests planner ;
- tests de policy/non-fuite ;
- fixture golden ;
- test UI ou navigateur si visible.

## Documentation

La documentation normative vit dans `docs/`. Mettre à jour `docs/README.md` lorsqu'un nouveau document majeur est ajouté.
