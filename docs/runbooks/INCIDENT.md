# Runbook — Incident

## Données à collecter

- `requestId` ;
- `buildId` / version ;
- endpoint ;
- recipe/renderer ;
- profil de déploiement ;
- Reader Policy et ensemble de rôles (sans token) ;
- métriques de latence/troncation/cache ;
- code erreur structuré.

Ne pas copier de payloads sensibles dans les logs/tickets par défaut.

## Projection dégradée

Basculer vers le fallback déclaré en conservant QuerySpec, focus et historique. Corriger la projection/renderer, jamais le Kristal canonique.

## Fuite policy suspectée

Retirer l’instance du trafic, reproduire avec le même ensemble de rôles/policy, tester toutes les surfaces secondaires, corriger et ajouter un test négatif avant reprise.

## Saturation

Réduire LOD/budgets ou affiner la sélection avant d’augmenter les caps. Vérifier mémoire, result size, cache hit/miss, temps de planning et projection.
