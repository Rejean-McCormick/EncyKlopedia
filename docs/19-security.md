# Sécurité et confidentialité — 1.0

## 1. Profils de déploiement

- **local** : single-user, principal local implicite et bind local par défaut ;
- **lan** : réseau interne, configuration Host explicite et authentification ;
- **shared** : principals, rôles, scopes, rate limiting et audit ;
- **public** : mêmes garanties + CSP stricte, TLS/gateway recommandés et threat model complet.

Un profil non local échoue au démarrage s’il n’existe ni principal authentifié ni opt-in explicite `KONSTELLATION_ANONYMOUS_READONLY=true`.

## 2. AuthN / AuthZ

Configuration recommandée :

```bash
export KONSTELLATION_DEPLOYMENT_PROFILE=shared
export KONSTELLATION_AUTH_TOKENS='{
  "0123456789abcdef0123456789abcdef": {
    "id": "researcher-a",
    "roles": ["public", "research"],
    "scopes": ["read", "metrics"]
  }
}'
```

- **roles** déterminent ce qui peut être lu dans le pack ;
- **scopes** déterminent quels endpoints peuvent être appelés ;
- les cursors sont signés et liés à l’`accessRef` dérivé des rôles ;
- les caches/Engine sont séparés par ensemble de rôles ;
- les tokens ne sont jamais loggés.

`KONSTELLATION_AUTH_TOKEN` reste accepté pour migration mais `KONSTELLATION_AUTH_TOKENS` est le contrat recommandé.

## 3. Invariants de non-fuite

Reader Policy doit être appliquée avant :

- query ;
- facets ;
- bootstrap (entités, types, relations, facettes/pivots de Lens et groupes de Constellation) ;
- entity ;
- evidence ;
- provenance ;
- constellation ;
- navigation plan ;
- projection ;
- raisons/explications de recommandation.

Une donnée invisible ne doit pas réapparaître comme compteur, edge, label, raison, tooltip, source, conflit, lineage ou signal d’affordance. Le profiler utilisé par le planner est reconstruit/caché sur l’état policy-scoped. Les `preferredRecipes` et `recipeLabels` déclarés sont supprimés en mode policy-scoped ; ils ne peuvent donc pas servir de canal latéral. La validation QuerySpec utilise elle aussi les IDs et relations visibles, afin qu’un identifiant masqué soit indistinguable d’un identifiant inconnu.

## 4. Entrées non fiables

Traiter comme non fiables : Kristals importés, labels, navigationHints, URLs externes, fichiers d’intégration et paramètres HTTP.

Les `navigationHints` sont validés par JSON Schema et n’acceptent aucun champ permettant de charger du code, un composant ou une URL de renderer.

## 5. Host / Origin / CSRF

Le serveur vérifie :

- allowlist Host ;
- Origin lorsque présent ;
- `Sec-Fetch-Site` cross-site ;
- Content-Type JSON ;
- taille de payload ;
- rate limit.

Les tokens Bearer n’utilisent pas de cookies, donc le risque CSRF classique est réduit ; un futur mode cookie devra ajouter une protection CSRF explicite.

## 6. CSP

Le profil `public` utilise une CSP sans `unsafe-inline`. Le source Svelte interdit les attributs/directives de style inline via `scripts/check-svelte-structure.mjs`; les transformations dynamiques SVG utilisent des attributs SVG et les indentations dynamiques des classes déterministes. `astro.config.mjs` force aussi l’externalisation des feuilles de style (`build.inlineStylesheets = "never"`). Les profils non publics conservent une compatibilité plus permissive.

Le gate build/Playwright doit encore confirmer que les assets Astro/Svelte **construits** restent fonctionnels avec la CSP publique avant promotion 1.0 finale.

Le serveur ajoute également `Permissions-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` et `X-Permitted-Cross-Domain-Policies` comme défense en profondeur.

## 7. Actionability

`actionability.mode = automatic` **n’est jamais une permission**.

Konstellation peut afficher conditions, rôle, état et contexte d’action, mais aucun endpoint de navigation ne déclenche une action métier. Une future exécution nécessiterait un contrat distinct, autorisation explicite, anti-replay et audit.

## 8. `/api/version`

L’identité/fingerprint du corpus peut constituer une information sensible. Elle est masquée par défaut sur l’endpoint public et n’est exposée qu’avec :

```bash
KONSTELLATION_EXPOSE_CORPUS_IDENTITY=true
```

Le contexte complet reste disponible aux utilisateurs autorisés via `/api/bootstrap`.

## 9. Threat model de release

Chaque déploiement doit documenter acteurs, assets, frontières de confiance, menaces, mitigations, tests et risques acceptés. Voir [runbooks/THREAT-MODEL.md](runbooks/THREAT-MODEL.md), [runbooks/BACKUP-RESTORE.md](runbooks/BACKUP-RESTORE.md) et [25-release-1.0.md](25-release-1.0.md).
