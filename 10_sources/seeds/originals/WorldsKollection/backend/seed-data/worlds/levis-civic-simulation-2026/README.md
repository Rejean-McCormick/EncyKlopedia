# Lévis Civic Simulation 2026 — World pack v0.2.1

This directory is a drop-in World pack. It preserves the sourced v0.1 civic corpus and adds a deliberately small multi-module content layer.

## Primary civic arcs

1. Growth Lévis 2030 — wastewater capacity, growth financing, housing and the financial framework.
2. Mobility Lévis 2035 — inter-river mobility, Guillaume-Couture and portfolio comparison.
3. Territory & civic mandate — Rabaska/Lévis-Est, participation and territorial memory.

The eight original v0.1 issue polls are retained for provenance/regression coverage but are archived in v0.2.1. Only the three integrated master consultations are part of the primary live experience.

## Canon / simulation boundary

- Existing public positions and arguments remain sourced reconstructed facts.
- Six EkoH expert personas are explicitly simulated.
- Master consultations, projects, tasks, impact items and learning activities are simulation content.
- Topic and consultation relevance vectors describe **domain relevance only**; they do not encode truth, endorsement, competence of political actors, or a preferred political outcome.
- Smart Vote results are never seeded; they remain runtime-derived and must keep the unweighted baseline visible.
- No EkoH score is invented for real politicians or political organizations.

## Runtime wiring in v0.2.1

The canonical `ethikos-demo-scenario/v3` payload now embeds:

- Korum topics, stances, arguments and sources;
- the three master Konsultations plus archived v0.1 polls;
- six simulated EkoH profiles;
- normalized `topic_relevance` for all eight Korum topics;
- normalized `consultation_relevance` for the two declared Smart Vote demonstrations;
- simulated impact items.

## Module sidecars

`modules/*.json` contains stable IDs and cross-module links for Knowledge, CertifiKation, Smart Vote presentation policy, Konstruct, Stockage, Kontact and Konservation. The current supplied Konnaxion snapshot does not yet contain a generic World importer for those modules, so those files remain staged data contracts rather than pretend-imported records.
