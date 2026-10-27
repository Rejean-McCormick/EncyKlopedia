# Tests et golden corpus

## 1. Pyramide de tests

1. schémas/contrats ;
2. fonctions profiler/planner ;
3. moteur/query/policy ;
4. projections ;
5. composants UI ;
6. API ;
7. Playwright ;
8. benchmarks et sécurité.

## 2. Golden corpus minimal

| Famille | Structure attendue | Recettes positives | Tests négatifs |
|---|---|---|---|
| Math | dependency/proof | proofs, dependencies, path | pas timeline sans dates |
| HumanBody | multiplex/multiScale/causal/cycle | feedback, path, multiscale | cycle non causal != feedback |
| HistoryTech | temporal/lineage/spatial | timeline, evolution, spatial | dérivation != causalité |
| ScolQc | hierarchy/conditionalTransition/versioned | path, hierarchy, evolution | relation simple != admission valide |
| HospitalOps | stateMachine/resourceAllocation | path, states, action-context | actionability != permission |
| Power | multidimensional/quantitative/network | dimensions, constellation | métrique != vérité globale |
| Catho | argumentation/evidence/provenance/conflict | arguments, traceability, divergences | relation éditoriale != influence |
| Generic | network minimal | list/table/constellation | aucune recette spécialisée inventée |

## 3. Fixtures

Les fixtures golden doivent être petites, lisibles et stables. Les gros corpus servent aux benchmarks, pas aux assertions fines.

Chaque fixture contient :

- source canonique ou pack ;
- Reader Policy ;
- Lens ;
- navigationHints éventuels ;
- expected affordances ;
- expected recipes ;
- forbidden recipes ;
- snapshots de projection ciblés.

## 4. Tests d'invariants

Obligatoires :

- policy avant toute projection ;
- pas de faits inventés ;
- déterminisme ;
- bounded projection ;
- actionability non exécutable ;
- loss report import ;
- context fingerprint ;
- migration de contrat.

## 5. Tests de mutations

Recommandés pour :

- seuils d'affordances ;
- mapping relations -> affordances ;
- conditions de recette ;
- validation de policy.

## 6. Performance regression

La CI dédiée benchmark doit conserver une baseline et refuser une régression au-delà d'un seuil accepté.
