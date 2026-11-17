# 05 — Orientations, axes, surfaces and projections

## 1. Do not begin with axes

Understand the native domain before optimizing an interactive or printed view.

## 2. Essential distinctions

- **Subject:** what the knowledge state concerns.
- **Domain dimension:** a meaningful variable or relationship inside the native model.
- **Coordinate:** a value within a domain space.
- **Facet/filter:** a query/navigation convenience.
- **Axis Type:** a defined category of orientation.
- **Orientation Axis:** a selected reader-oriented dimension; the portable projection uses one primary and at most one secondary axis.

## 3. Surface

A Surface is a contextual view over owned or referenced data. The view may be temporary and should not gain authority merely by rendering.

## 4. Portable projection

A persistent portable projection records the source, transformation, parameters, provenance and possible loss. It is a reader artifact, not a canonical replacement.

## 5. Several major viewpoints

If a model demands several equally important orientations, represent multiple separately referenced projections or a domain-specific native view instead of violating the portable two-axis convention.

## 6. V8/V9 recomposition

Query plans, search indexes and Context Packs may compose fragments without merging independent Semantic Owners or mutating v9 Logical Commitments.

## 7. Projection versus v9 Logical Artifact

A derived view may itself be admitted as a separate logical artifact **only under its own explicit domain contract**; it is not automatically promoted by its existence or publication.
