# Threat model — Konstellation 1.0

Ce runbook décrit le modèle de menace opérationnel de Konstellation 1.0. Il complète [19-security.md](../19-security.md) et doit être adapté à l'environnement réellement déployé.

## Actifs à protéger

Konstellation protège en priorité : le `kristal_state` canonique, les entités et assertions filtrées par Reader Policy, les sources/évidences/provenances, les identités et rôles, les secrets de cursor/auth, les plans/projections dérivés, les logs opérationnels et l'intégrité du build.

Les vues, plans et projections sont reconstructibles et ne doivent jamais être traités comme une autorité supérieure au Kristal canonique.

## Frontières de confiance

```text
Client navigateur
  -> reverse proxy / réseau
  -> serveur Konstellation
  -> authentification + rôles/scopes
  -> Reader Policy
  -> Engine policy-scoped
  -> profiler/planner/projections
  -> Kristal canonique en lecture
```

Chaque flèche est une frontière. Une donnée masquée à une frontière ne doit pas réapparaître plus loin sous forme de label, compteur, score, raison, autocomplete, entité, relation, source, plan ou projection.

## Menaces principales

| Menace | Exemple | Contrôles obligatoires |
|---|---|---|
| Contournement Reader Policy | déduire une relation masquée via une recette Timeline | profil/planner policy-scoped, relations visibles uniquement, hints de présentation supprimés sous policy |
| IDOR / accès par identifiant | appeler `/api/entity?id=secret` | résolution dans le scope visible, jamais dans le pack global |
| Escalade de rôle | réutiliser un cursor d'un rôle plus large | cursor signé et lié à `accessRef`, caches isolés par rôles |
| Fuite par métadonnées | compteur, label ou reason révèle un domaine masqué | métriques métier non exposées par défaut, explications issues du scope visible |
| Injection de code par Kristal | renderer fourni dans `navigationHints` | Renderer Registry fermé ; hints strictement déclaratifs |
| Confusion actionability/autorité | `automatic` déclenche une action | `actionability` informatif uniquement ; aucune exécution implicite |
| DoS | requêtes très larges, graphes denses, payload énorme | limites payload, rate limit, budgets LOD, pagination, deadlines |
| Poisoning / données malformées | schéma relationnel incohérent | validation d'import/contrats, fail-fast startup/readiness |
| CSRF / cross-site | requête mutative depuis un autre Origin | contrôles Host/Origin/Sec-Fetch-Site, auth Bearer, CSP |
| Vol de token | secret dans URL/log | Bearer header uniquement, redaction logs, gestion de secrets externe |
| Supply-chain | dépendance ou build différent | lockfile obligatoire pour release, SBOM, release manifest, versions exactes |
| XSS | labels du Kristal injectés dans DOM | rendu échappé Svelte, CSP stricte en public, aucune UI exécutable fournie par Kristal |

## Règles policy-scoped non négociables

Le moteur doit appliquer Reader Policy **avant** : liste, facettes, bootstrap, autocomplete, inspecteur entité, evidence/source, Constellation, introspection, NavigationPlan et projection.

En mode policy-scoped :

- une relation avec zéro assertion visible ne contribue pas au profil ;
- les scores/raisons d’affordances déclarés sont ignorés dans le profiler policy-scoped ; les mappings relation→affordance ne sont utilisés que pour des relations effectivement visibles ;
- `preferredRecipes` et `recipeLabels` déclarés sont supprimés avant le planner afin d'éviter une fuite sémantique par présentation ;
- les raisons du planner ne proviennent que d'éléments visibles ;
- les caches sont séparés par contexte d'autorisation.

## Profils de déploiement

### `local`

Risque principal : accès local non intentionnel et Kristal non fiable. Bind local par défaut, principal local explicite et validation du pack restent obligatoires.

### `lan`

Risque supplémentaire : autre machine du réseau. Auth recommandée/obligatoire selon configuration, allowlist Host, TLS au proxy si le réseau n'est pas entièrement de confiance.

### `shared`

Auth multi-principal, rôles/scopes, TLS, rate limit, rotation des secrets, logs corrélables et tests policy sont obligatoires.

### `public`

Tous les contrôles `shared` plus reverse proxy durci, CSP publique stricte, TLS, monitoring/alerting, limites agressives, gestion externe des secrets et audit de sécurité avant promotion.

## Abuse cases à tester avant release

1. requêter directement un ID masqué ;
2. faire varier Lens/recipe/focus pour tenter de révéler une relation cachée ;
3. fournir un label de recette sensible dans `navigationHints` ;
4. réutiliser un cursor entre principals/roles ;
5. envoyer Origin/Host malformés ;
6. varier des tokens invalides pour contourner le rate limit ;
7. envoyer un payload supérieur à la limite ;
8. provoquer DAG profond/cycle dense pour épuiser pile/CPU ;
9. fournir du HTML/script dans labels et sources ;
10. tenter d'interpréter `actionability=automatic` comme permission.

Chaque incident ou découverte doit produire un test de non-régression avant remise en service.

## Réponse à incident de confidentialité

1. retirer l'instance affectée du trafic ;
2. préserver requestIds, version, build ID et logs structurés sans dupliquer les payloads sensibles ;
3. identifier principal, rôles, Reader Policy, Lens et requête ;
4. reproduire sur une copie contrôlée ;
5. vérifier toutes les surfaces policy-scoped, pas seulement l'endpoint signalé ;
6. corriger au niveau le plus amont possible ;
7. ajouter test golden/security négatif ;
8. relancer release gates ;
9. documenter l'incident et la rotation éventuelle des secrets.

## Critères de sortie

Une release partagée/publique ne peut être promue si un test montre qu'une donnée masquée peut influencer une sortie visible, même indirectement par score, ordre, label, compteur ou explication.
