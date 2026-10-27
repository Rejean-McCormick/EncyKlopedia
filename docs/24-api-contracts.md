# API et contrats publics — 1.0

## 1. Endpoints

| Méthode | Endpoint | Scope | Rôle |
|---|---|---|---|
| GET | `/api/health` | public | liveness + version |
| GET | `/api/ready` | public | readiness du service |
| GET | `/api/version` | public | version/build/schémas ; identité corpus optionnelle |
| GET | `/api/bootstrap[?readerPolicyRef=…]` | `read` | contexte, Lens/registry policy-scoped, renderer catalog, profil visible |
| GET | `/api/capabilities` | `read` | capacités d’intégration et navigation |
| GET | `/api/metrics` | `metrics` | métriques structurées |
| POST | `/api/query` | `read` | ResultSet |
| POST | `/api/facets` | `read` | facettes policy-scoped |
| POST | `/api/entity` | `read` | inspecteur entité |
| POST | `/api/constellation` | `read` | projection Constellation |
| POST | `/api/navigation/plan` | `read` | NavigationPlan 1.0 |
| POST | `/api/navigation/project` | `read` | projection spécialisée 1.0 |
| POST | `/api/evidence` | `read` | assertions/evidence visibles |
| POST | `/api/validate-state` | `read` | validation/migration ExplorationState |
| POST | `/api/sa/request` | `sa` | construction requête SA |
| POST | `/api/sa` | `sa` | réalisation SA configurée |

`GET /api/health`, `/api/ready` et `/api/version` sont volontairement minimaux. `/api/ready` vérifie notamment les index policy-scoped et le profil navigation préchauffé. `/api/version` expose `version`, `buildId`, `sourceManifestSha256`, `sourceFileCount` et, si fourni par le pipeline, `artifactSha256`; l’identité du corpus n’est ajoutée que si `KONSTELLATION_EXPOSE_CORPUS_IDENTITY=true`.

## 2. Authentification

Les profils non locaux utilisent :

```http
Authorization: Bearer <token>
```

`KONSTELLATION_AUTH_TOKENS` mappe les tokens vers un principal :

```json
{
  "<token-long>": {
    "id": "reader-1",
    "roles": ["public", "research"],
    "scopes": ["read", "metrics"]
  }
}
```

Les scopes API sont distincts des rôles d’accès au contenu. Deux principaux ayant les mêmes rôles peuvent partager les mêmes index de lecture ; leurs scopes continuent de contrôler les endpoints accessibles.

## 3. Erreurs

Format stable :

```json
{
  "error": {
    "code": "UNSUPPORTED_CAPABILITY",
    "message": "...",
    "requestId": "...",
    "details": {}
  }
}
```

`X-Request-ID` est renvoyé dans les headers et le même identifiant est utilisé dans les logs. `details` ne doit jamais contenir de données masquées par policy.

## 4. NavigationPlan 1.0

```json
{
  "schemaVersion": "1.0",
  "mode": "adaptive",
  "derived": true,
  "semantics": "navigation-affordances-not-kristal-authority",
  "scope": {"kind": "selection", "entityType": "node"},
  "primaryRecipeId": "proofs",
  "views": [
    {
      "id": "proofs",
      "label": "Preuves",
      "rendererId": "dag-proof",
      "score": 0.93,
      "reason": "...",
      "relationIds": ["proof_dependency"]
    }
  ],
  "actions": [],
  "profile": {"schemaVersion":"1.0","scope":"result-set","entityType":"node","affordances":{}}
}
```

Sans focus, le planner peut utiliser un `ResultSetProfile` borné. Avec focus, le `FocusProfile` prévaut.

## 5. Navigation Projection 1.0

Toutes les projections spécialisées contiennent au minimum :

```json
{
  "schemaVersion": "1.0",
  "projectionKind": "dag",
  "recipeId": "proofs",
  "rendererId": "dag-proof",
  "derived": true,
  "truncated": false,
  "nextCursor": null,
  "totalCandidates": 42,
  "explanation": {
    "reason": "...",
    "relationIds": ["proof_dependency"]
  }
}
```

Les champs spécifiques sont **obligatoires et validés par famille** :

| `projectionKind` | Champs structurants requis |
|---|---|
| `timeline-lineage` | `items`, `links` |
| `tree` | `nodes`, `edges`, `roots` |
| `dag` | `nodes`, `edges`, `roots`, `terminals`, `acyclic`, `cycles` |
| `flow` | `nodes`, `transitions`, `starts`, `terminals` |
| `causal-feedback` | `nodes`, `edges`, `cycles` |
| `matrix` | `rows`, `columns`, `cells` |
| `state-flow` | `records`, `transitions`, `semantics` |
| `traceability` | `nodes`, `edges` |
| `multiscale` | `layers`, `memberships`, `nodes`, `crossLinks` |
| `spatial` | `points`, `places` |

Le schéma valide aussi la forme interne des nœuds, arêtes, transitions, cellules, records et points. Les 10 fixtures de référence sont dans `examples/projections/`. Les données restent bornées par `pageSize`, `nodeBudget`, `edgeBudget` et le Renderer Registry.

## 6. Reader Policy

La policy est résolue depuis `query.context.readerPolicyRef` avant : query, facets, entity, bootstrap, evidence, constellation, planning et projection. `GET /api/bootstrap?readerPolicyRef=…` retourne le registre relationnel, les Lens/facettes/pivots et les groupes de Constellation filtrés pour ce même scope. Les plans/projections sont donc dérivés du **même état visible** que les résultats.

## 7. Versioning

Chaque contrat public possède :

- `schemaVersion` ;
- JSON Schema ;
- tests ;
- compatibilité documentée ;
- migration lorsqu’une rupture est nécessaire.

QuerySpec, Lens et relation registry restent actuellement en 0.2 : ils ne sont pas artificiellement renumérotés lorsqu’aucune rupture de contrat n’est nécessaire. Les nouveaux contrats de navigation/exploration sont en 1.0.

## 8. Idempotence

Les endpoints de lecture sont déterministes pour un même corpus, Reader Policy, roles, Lens, QuerySpec et version de service. Une projection est toujours une opération dérivée de lecture.
