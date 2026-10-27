# Audit des sources et références d'architecture

## 1. Références utilisées

La conception finale de Konstellation s'appuie sur les contrats et snapshots de l'écosystème, notamment :

- Kristal Standard / `kristal-framework` ;
- `kristal-reference` ;
- Interaction Kernel ;
- SemantiK Architect ;
- SemantiK Runtime Orchestrator ;
- Koali / Scenario / Mosaic / Index ;
- Konnaxion ;
- Orgo ;
- Kristal Kollection ;
- exemples de Kristals Math, HumanBody, HistoryTech, ScolQc, HospitalOps, Power et autres corpus disponibles.

## 2. Enseignements structurants

### Kristal v6

Le centre canonique est `kristal_state`, incluant notamment :

- `coordinates` ;
- `valuations` ;
- `record_role` ;
- `actionability` ;
- conflits ;
- succession ;
- lineage ;
- evidence ;
- provenance.

Les timelines, pathways, indexes et graphes d'interface sont des **vues dérivées**.

### SemantiK / runtime

Le terme **capability** est déjà utilisé pour des promesses ou capacités runtime. Konstellation emploie donc le terme **navigation affordance / affordance de navigation** pour ses observations dérivées.

### Actionability

`automatic` n'est pas une autorisation d'exécution. Cette distinction est normative dans Konstellation.

## 3. Sources de vérité dans le repo

Ordre de priorité documentaire :

1. schémas sous `contracts/` pour les formats effectivement implémentés ;
2. ADRs pour les décisions d'architecture ;
3. docs 1.0 pour la cible normative ;
4. `IMPLEMENTATION.md` pour le delta entre code et cible ;
5. rapports `VALIDATION-v0.x.md` pour l'historique.

## 4. Règle d'audit futur

Lorsqu'un contrat upstream change :

1. enregistrer la version exacte ;
2. comparer le schéma ;
3. identifier les hypothèses Konstellation affectées ;
4. mettre à jour l'adaptateur ;
5. ajouter/mettre à jour un ADR si la frontière d'autorité change ;
6. ajouter des tests de compatibilité.
