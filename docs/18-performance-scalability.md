# Performance et scalabilité

## 1. Objectif

Konstellation doit rester utile avec des milliers de Kristals et des corpus de tailles très différentes. La stratégie n'est pas « tout rendre plus vite », mais **indexer, profiler une fois, paginer et réduire le niveau de détail**.

## 2. Complexité cible

### Chargement

- parsing/validation : O(n) dans la taille de l'état lu ;
- index principaux : O(n) ;
- profil global : O(n + e) ;
- détection de structures coûteuses : bornée ou calculée paresseusement.

### Interaction

- facettes : indexées ;
- profile par type : caché ;
- focus profile : proportionnel au voisinage nécessaire ;
- projection : bornée par recette.

## 3. LOD et pagination

La cible 1.0 remplace les hard caps ad hoc par une politique commune :

1. `pageSize` pour listes/tables ;
2. `nodeBudget` / `edgeBudget` pour graphes ;
3. agrégation quand la densité dépasse un seuil ;
4. expansion à la demande ;
5. virtualisation du DOM ;
6. LOD selon zoom ou niveau sémantique.

## 4. SLOs cibles à benchmarker

Ces valeurs sont des **cibles de qualification**, pas des garanties actuelles :

| Opération | Cible locale chaude |
|---|---:|
| bootstrap shell | < 500 ms après service prêt |
| query/facets courant | p95 < 250 ms sur corpus de référence |
| plan de navigation local | p95 < 50 ms après indexation |
| projection bornée | p95 < 200 ms |
| interaction renderer | 60 fps cible sur pan/zoom courant |
| changement Lens | retour perceptible < 300 ms hors I/O externe |

Les seuils définitifs doivent être dérivés des benchmarks réels du matériel/support visé.

## 5. Benchmarks obligatoires

Au minimum :

- 10k assertions/records ;
- 100k ;
- 1M ;
- graphes clairsemés ;
- graphes denses ;
- fortes cardinalités de facettes ;
- timeline massive ;
- DAG profond ;
- multi-échelle.

## 6. Caches

Les caches doivent être clés par un fingerprint incluant au minimum :

- identité/version du corpus ;
- Reader Policy ;
- registre/relations ;
- Lens si elle affecte le calcul ;
- scope de profil.

Un changement de fingerprint invalide les entrées dépendantes.

## 7. Pré-calcul

Les Kristals peuvent publier des dérivés utiles (hubs, pathways, indexes) mais Konstellation doit :

- les traiter comme dérivés ;
- vérifier leur compatibilité/version ;
- conserver un fallback reconstructible ou clairement signaler la dépendance.
