# Migration v0.7 vers 1.0

## 1. Principes

La migration doit être additive autant que possible.

- les anciens `recipeId` restent interprétables ;
- les aliases `capabilities` sont lus mais réémis sous `affordances` ;
- les explorations v0.7 sont migrées explicitement ;
- les renderers génériques restent des fallbacks ;
- aucune donnée canonique n'est réécrite par la migration.

## 2. NavigationPlan

La branche 1.0 émet `NavigationPlan` 1.0. La migration depuis le plan 0.2 a appliqué les règles suivantes :

- garder `derived: true` ;
- garder la sémantique `navigation-affordances-not-kristal-authority` ;
- remplacer progressivement `renderer: adaptive` par des `rendererId` spécifiques ;
- versionner les DTOs de projection.

## 3. ExplorationState

La migration doit convertir l'état sans changer la sélection :

```text
v0.7 exploration-state 0.2
  + navigation.recipeId/mode
  -> v1.0 state
     query inchangé
     lensRef conservé
     policy conservée
     focus conservé si valide
     navigation migrée
```

Si une recette sauvegardée n'existe plus, utiliser un fallback et enregistrer une explication de migration.

## 4. navigationHints

Entrées anciennes :

- `capabilities`
- `relationCapabilities`

Entrées cibles :

- `affordances`
- `relationAffordances`

Le parser 1.0 accepte les anciennes clés pendant la fenêtre de compatibilité, mais les contrats, la documentation et les nouveaux exports utilisent les nouvelles.

## 5. Projections

La branche 1.0 remplace les anciennes projections génériques par des DTOs spécialisés versionnés pour timeline/lignée, arbre, DAG/preuves, parcours, feedback causal, matrice/profil, états/action, traçabilité/divergences, multi-échelle et spatial. Cette migration ne modifie jamais la vérité source : les projections restent dérivées et reconstructibles.

## 6. Dépréciations

Toute dépréciation doit comporter :

- version d'introduction ;
- version de retrait prévue ;
- migration automatique ou guide ;
- tests de compatibilité ;
- message opérateur explicite.
