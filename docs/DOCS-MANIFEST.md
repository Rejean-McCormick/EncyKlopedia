# Manifeste documentaire

Ce manifeste classe les documents du repo selon leur rôle.

## Normatifs pour la cible 1.0

- `00-decisions.md`
- `01-architecture.md`
- `02-query-model.md`
- `03-navigation.md`
- `04-knowledge-semantics.md`
- `05-execution.md`
- `06-integrations.md`
- `07-delivery-plan.md`
- `08-migration.md`
- `09-source-audit.md`
- `10-validation-report.md`
- `15-adaptive-navigation.md`
- `16-kristal-v6-alignment.md`
- `17-renderer-registry.md`
- `18-performance-scalability.md`
- `19-security.md`
- `20-observability.md`
- `21-testing-golden-corpus.md`
- `22-deployment.md`
- `23-extension-guide.md`
- `24-api-contracts.md`
- `25-release-1.0.md`
- `26-glossary.md`
- `27-behavior-by-kristal.md`
- `28-anti-patterns.md`
- `29-reference-sequences.md`

## Normatif pour l'état réel du code

- `IMPLEMENTATION.md`
- `VALIDATION-v1.0-RC.md`
- les JSON Schemas dans `../contracts/`
- `package.json`

En cas de divergence entre la cible 1.0 et le code actuel, `IMPLEMENTATION.md` doit la signaler.

## Guides opérationnels

- `IMPORT.md`
- `INTEGRATIONS.md`
- `OPERATIONS.md`
- `guides/USER.md`
- `guides/INTEGRATOR.md`
- `guides/DEVELOPER.md`
- `guides/OPERATOR.md`
- `runbooks/README.md`
- `runbooks/STARTUP.md`
- `runbooks/ROLLBACK.md`
- `runbooks/BACKUP-RESTORE.md`
- `runbooks/THREAT-MODEL.md`
- `runbooks/INCIDENT.md`
- `runbooks/UPGRADE.md`

## ADRs

Les ADRs figent les décisions déjà acceptées et prévalent sur un texte descriptif contradictoire jusqu'à remplacement explicite par un nouvel ADR.

## Exemples de domaine

- `11-astrolabe.md`
- `12-biblical-graph.md`
- `14-theophile-enrichment.md`

Ils illustrent la plateforme mais ne définissent pas son architecture universelle.

## Historique

- `DESIGN-v0.2-README.md`
- `VALIDATION-v0.3.md`
- `VALIDATION-v0.4.md`
- `VALIDATION-v0.5.md`
- `VALIDATION-v0.6.md`
- `VALIDATION-v0.7.md`

Ces fichiers ne doivent pas être utilisés pour déduire l'état courant lorsqu'un document plus récent existe.

## Règle de maintenance

Toute modification de contrat, affordance, recette, renderer ou invariant doit mettre à jour :

1. le schéma ou le code concerné ;
2. le document normatif correspondant ;
3. `IMPLEMENTATION.md` si le statut change ;
4. un ADR si la décision est structurante ;
5. les golden tests ;
6. `CHANGELOG.md`.
