# Architecture système de Konstellation 1.0

## 1. Vue d'ensemble

```text
+----------------------------+
|        Kristal v6          |
|  état canonique + identité |
+-------------+--------------+
              |
              v
+----------------------------+
| Adapter / Normalizer       |
| validation + loss report   |
+-------------+--------------+
              |
              v
+----------------------------+
| Query Service              |
| - Reader Policy            |
| - Query Engine             |
| - Structural Introspector  |
| - Navigation Planner       |
| - Projection Service       |
+-------------+--------------+
              |
              | DTOs + NavigationPlan
              v
+----------------------------+
| Konstellation Shell        |
| - recherche / facettes     |
| - résultats / inspecteur   |
| - historique / Lens        |
| - Renderer Registry        |
+----------------------------+
```

## 2. Responsabilités

### Kristal Adapter

DOIT :

- valider le schéma source ;
- vérifier l'identité v6 lorsque disponible ;
- construire les index de lecture nécessaires ;
- préserver les métadonnées v6 utiles ;
- déclarer toute perte de représentation.

NE DOIT PAS :

- inventer de faits ;
- convertir silencieusement un type non représentable ;
- remplacer l'identité canonique du Kristal par celle d'un pack local.

### Query Engine

DOIT :

- valider QuerySpec ;
- appliquer la Reader Policy avant toute sortie ;
- exécuter sélection, facettes, compteurs et witnesses ;
- produire un contexte stable et vérifiable.

### Structural Introspector

DOIT analyser la structure observable : types, relations, topologie, métadonnées v6, valeurs, coordonnées, cycles, densité, hiérarchie, temporalité et autres signaux.

Ses résultats sont **dérivés**.

### Navigation Planner

DOIT :

- combiner profils global/local, Lens, focus et hints ;
- calculer l'applicabilité et le score des recettes ;
- produire un `NavigationPlan` versionné ;
- expliquer les raisons d'une recommandation.

### Projection Service

Produit des DTOs bornés propres à chaque famille de vue : timeline, tree, DAG, flow, etc. Une projection reste reconstructible à partir de l'état visible.

### Renderer Registry

Associe un `rendererId` connu à un composant UI approuvé, avec ses exigences, budgets et fallbacks.

### Shell UI

Le shell reste stable entre les Kristals : recherche, Lens, policy, facettes, résultats, surface principale, inspecteur, historique, provenance et navigation arrière/avant.

## 3. Flux d'ouverture

1. charger et valider la source ;
2. résoudre Reader Policy et contexte ;
3. construire les index ;
4. produire le profil structurel global ;
5. afficher immédiatement le fallback générique ;
6. construire le `NavigationPlan` global ;
7. recalculer localement lorsque Lens, QuerySpec ou focus changent.

## 4. Flux de sélection d'une entité

```text
User -> Shell: select entity
Shell -> Query Service: entity(entityId, context)
Query Service -> Policy: visibility
Query Service -> Profiler: FocusProfile
Query Service -> Planner: plan(context, lens, focus)
Planner -> Shell: NavigationPlan
Shell -> Projection Service: project(primaryRecipe)
Projection Service -> Shell: bounded DTO + explanation
Shell -> Renderer: render
```

Aucune mutation de QuerySpec n'a lieu tant que l'utilisateur ne déclenche pas explicitement un filtre ou un pivot.

## 5. Dégradation gracieuse

Un Kristal inconnu doit au minimum permettre :

- recherche ;
- facettes ;
- liste ;
- tableau ;
- Constellation générique ;
- inspecteur ;
- provenance/evidence si disponible.

Chaque structure supplémentaire découverte enrichit l'expérience, mais n'est jamais nécessaire pour rendre le corpus navigable.
