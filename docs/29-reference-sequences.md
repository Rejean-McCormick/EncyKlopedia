# Séquences de référence

## 1. Sélection d'une entité

```text
User -> Shell: select entity
Shell -> Query Service: entity(entityId, context)
Query Service -> Reader Policy: evaluate visibility
Query Service -> Profiler: get FocusProfile
Query Service -> Planner: build plan(context, lens, focus)
Planner -> Shell: NavigationPlan
Shell -> Projection Service: project(primaryRecipe)
Projection Service -> Shell: bounded DTO + explanation
Shell -> Renderer: render + inspector
```

Invariant : aucune mutation QuerySpec sans filtre/pivot explicite.

## 2. Changement de Lens

```text
User -> Shell: choose Lens B
Shell: keep QuerySpec if compatible
Shell -> Planner: recompute with Lens B
Planner: reorder recipes / labels / facets
Shell: preserve active filters not represented by Lens
```

Reader Policy ne change pas.

## 3. Changement de Reader Policy

```text
User -> Shell: choose Policy B
Shell -> Query Service: resolve Policy B
Query Service: invalidate cursor/cache scope
Query Service: re-evaluate QuerySpec
Profiler/Planner: recompute visible profile
Shell: replace results only for newest matching context
```

## 4. Projection spécialisée indisponible

```text
Shell -> Projection Service: request dag-proof
Projection Service: error / budget exceeded
Shell -> Registry: resolve accessibility fallback
Registry -> Shell: table or constellation
Shell: preserve query, focus and history
```

## 5. Import Kristal v6

```text
Source -> Adapter: kristal_state
Adapter: schema validation
Adapter: identity verification
Adapter: lossless mapping
Adapter: loss report
Adapter -> Query Service: local read index
Profiler: derive affordances
Planner: produce initial plan
Shell: generic view first, enriched views next
```

## 6. Action context

```text
Kristal record: actionability=automatic
Profiler: affordance actionability
Planner: recipe action-context
Renderer: show conditions/role/status
NO execution call is produced
```
