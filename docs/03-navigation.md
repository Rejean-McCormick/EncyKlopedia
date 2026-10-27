# Navigation adaptative

## 1. Idée centrale

Konstellation n'associe pas une interface à un domaine. Il reconnaît des **affordances structurelles** et compose des recettes de navigation réutilisables.

```text
structure visible
  -> affordances
  -> recettes applicables
  -> NavigationPlan
  -> projection
  -> renderer
```

## 2. Vocabulaire d'affordances

Le vocabulaire cible comprend au minimum :

- `network`
- `temporal`
- `hierarchy`
- `dependency`
- `sequence`
- `stateMachine`
- `conditionalTransition`
- `causal`
- `signedCausal`
- `cycle`
- `spatial`
- `multiScale`
- `multiplex`
- `proof`
- `argumentation`
- `multidimensional`
- `quantitative`
- `evidential`
- `provenance`
- `versioned`
- `eventStream`
- `resourceAllocation`
- `classification`
- `conflict`
- `succession`
- `lineage`
- `actionability`
- `stateful`

Un score d'affordance mesure **la pertinence navigationnelle**, pas la vérité, la qualité ou l'importance scientifique.

## 3. Sources de signal

Ordre de préférence :

1. structure canonique explicite du Kristal ;
2. `navigationHints` validés ;
3. schémas de types/relations ;
4. topologie observée ;
5. heuristiques lexicales en fallback.

Les hints doivent renforcer une structure cohérente, pas inventer une structure absente.

## 4. Profils multi-portée

Konstellation peut calculer :

- profil global du pack ;
- profil par type d'entité ;
- profil d'un result set ;
- profil du focus courant.

Le planner combine ces profils plutôt que de choisir une UI une fois pour toutes à l'ouverture.

## 5. Recettes

Recettes génériques principales :

| Recette | Affordances principales | Intention |
|---|---|---|
| `catalogue` | universelle | Parcourir la sélection |
| `constellation` | network | Explorer le voisinage |
| `timeline` | temporal | Explorer dans le temps |
| `hierarchy` | hierarchy | Parcourir une structure parent/enfant |
| `dependencies` | dependency | Comprendre prérequis et dérivations |
| `path` | sequence/stateMachine/conditionalTransition | Suivre un parcours |
| `feedback` | causal + cycle | Comprendre une boucle |
| `proofs` | proof | Explorer preuve/réfutation/dépendances |
| `arguments` | argumentation | Comparer positions et arguments |
| `dimensions` | multidimensional | Comparer des profils |
| `states` | stateful/eventStream | Explorer états et changements |
| `evolution` | lineage/succession/versioned | Suivre une lignée ou révision |
| `divergences` | conflict | Examiner les conflits explicites |
| `traceability` | evidential/provenance | Suivre évidence et provenance |
| `action-context` | actionability | Comprendre conditions de décision/action |
| `table` | universelle | Comparer de façon tabulaire |

La cible 1.0 ajoute explicitement les recettes `multiscale` et `spatial` lorsque les renderers correspondants sont disponibles.

## 6. Planner

Conceptuellement :

```text
score(recipe) =
  applicabilité(structure)
  + force(affordances)
  + préférence Lens/hints
  + pertinence focus
  - coût projection
  - redondance avec recettes déjà proposées
```

Une recette requise est rejetée si ses affordances minimales sont sous le seuil d'applicabilité.

## 7. NavigationPlan

Le plan doit contenir :

- version du schéma ;
- mode ;
- `derived: true` ;
- sémantique explicite `navigation-affordances-not-kristal-authority` ;
- type et Lens ;
- recette primaire ;
- vues alternatives ;
- actions contextuelles ;
- profil d'affordances ;
- raisons et relations structurantes.

## 8. Intentions UX

L'UI ne doit pas obligatoirement exposer les noms techniques des renderers. Elle peut parler en intentions :

- « Suivre la trajectoire »
- « Voir les prérequis »
- « Comprendre la preuve »
- « Changer d'échelle »
- « Examiner les divergences »

Le `recipeId` reste stable sous ces labels contextuels.
