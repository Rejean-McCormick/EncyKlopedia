# Guide opérateur

## Avant démarrage

- Node `>=24.15.0` ;
- lockfile correspondant à l’artefact ;
- corpus/config/policies/Lens validés ;
- secrets hors repo ;
- Host allowlist et profil de déploiement explicites ;
- principals/scopes configurés pour les profils partagés.

## Démarrage

```bash
npm ci
npm run release:preflight
npm run build
npm start
```

## Vérifications

- `/api/health` ;
- `/api/ready` ;
- `/api/version` ;
- logs JSON sans erreurs ;
- principal réel capable de lire `/api/bootstrap` ;
- Reader Policy attendue ;
- projection spécialisée + fallback.

## Observabilité

Surveiller : latence HTTP, query, planner, projection, taille result sets, taux de troncation, cache hit/miss, mémoire et distribution des recettes.

## Incidents

Toujours capturer `requestId`, build/version, recipe/renderer et code erreur, sans secrets. Voir [`../runbooks/`](../runbooks/README.md).

Ne jamais corriger un incident de vue en modifiant la connaissance canonique.
