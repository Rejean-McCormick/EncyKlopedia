# Observabilité, fiabilité et exploitation

## 1. Logs structurés

Konstellation 1.0 produit des logs JSON structurés avec :

- timestamp ;
- level ;
- request/correlation id ;
- endpoint ;
- durée ;
- code erreur ;
- contexte non sensible ;
- version du service.

Ne pas logger des payloads sensibles par défaut.

## 2. Métriques

Métriques minimales :

- requêtes par endpoint ;
- latence p50/p95/p99 ;
- erreurs par code ;
- taille result sets ;
- temps de planification ;
- temps de projection ;
- taux de troncation ;
- cache hit/miss ;
- mémoire ;
- temps de bootstrap/import ;
- distribution des recettes utilisées.

Les métriques d'usage ne doivent pas devenir une source de vérité épistémique.

## 3. Health / readiness / version

### `/api/health`

Processus vivant.

### `/api/ready`

Service capable de traiter une requête avec corpus, registry, policy et index chargés.

### `/api/version`

Expose :

- version Konstellation ;
- build id ;
- versions de schémas publics ;
- SHA-256 du manifest source et nombre de fichiers ;
- SHA-256 de l’artefact si le pipeline fournit `KONSTELLATION_ARTIFACT_SHA256` ;
- identité du corpus seulement avec opt-in explicite.

## 4. Dégradation contrôlée

Si un renderer spécialisé échoue :

1. logger l'erreur ;
2. conserver le QuerySpec ;
3. proposer un fallback ;
4. expliquer que la vue spécialisée est indisponible ;
5. ne jamais perdre l'état d'exploration.

## 5. Corrélation

Une erreur UI doit pouvoir être reliée à :

- requête HTTP ;
- plan de navigation ;
- projection ;
- version du corpus ;
- version du service.

## 6. Runbooks

La production doit documenter :

- démarrage ;
- arrêt ;
- rollback ;
- corpus invalide ;
- policy invalide ;
- saturation mémoire ;
- latence élevée ;
- renderer dégradé ;
- restauration de configuration.
