# Opérations Konstellation 1.0

## Configuration

Voir [22-deployment.md](22-deployment.md) pour la table complète. Les variables structurantes sont `KONSTELLATION_DEPLOYMENT_PROFILE`, `KONSTELLATION_AUTH_TOKENS`, `KONSTELLATION_ALLOWED_HOSTS`, `KONSTELLATION_PACK`, `KONSTELLATION_LENSES`, `KONSTELLATION_CURSOR_SECRET` et `KONSTELLATION_BUILD_ID`.

## Démarrage qualifié

```bash
npm ci
npm run release:preflight
npm run build
npm start
```

Vérifier ensuite :

```text
GET /api/health
GET /api/ready
GET /api/version
```

## Shutdown

Le processus écoute SIGTERM/SIGINT, arrête d’accepter de nouvelles connexions via `server.close()` et force la sortie après un délai de sécurité de 5 s.

## Incident projection

1. relever `requestId`, version, recipe et renderer ;
2. utiliser le fallback accessible sans modifier QuerySpec/focus ;
3. examiner `navigation_projection_duration_ms`, `navigation_projection_total` et erreurs ;
4. corriger projection/renderer sans modifier le canon ;
5. rejouer golden test + E2E.

## Incident policy / fuite suspectée

1. retirer l’instance du trafic ;
2. conserver logs/requestIds sans copier les payloads sensibles ;
3. reproduire avec le même ensemble de rôles et Reader Policy ;
4. vérifier query, bootstrap, entity, evidence, plan, projection et explication ;
5. ajouter un test de non-régression avant remise en service.

## Saturation / latence

Examiner mémoire, result set size, cache hit/miss, temps planning/projection et taux de troncation. Réduire LOD/budgets ou affiner la sélection avant d’augmenter arbitrairement les caps.

## Rollback

Rollback atomique code + lockfile + build + contrats + configuration. Les projections sont reconstructibles : ne jamais restaurer un dérivé comme vérité canonique.
