# UCKK MathKristal bridge — changeset

Date: 2026-10-01

## What changed

The Univers-Cité des mathématiques now consumes a pinned MathKristal as its epistemic/reference authority. UCKK deterministically projects that state into pedagogical pathways, projected course steps and semantic page specifications. SemantiK Architect is declared as the linguistic realization stage for those already-selected communication obligations. Moodle remains the runtime for public surfaces and human/transactional learning state.

Current pin:

- MathKristal release: `1.6.0`
- state: `sha256:35aef425c4029076e1af3ada6a52413e975ed402ce0c64644943b11a5849ff71`
- referent registry: `sha256:140aad0f12061f1717c0b9f960871b515279f68052f93c54a4d034f06fb37e1a`
- distribution archive SHA-256: `904bfc98f50761c957316130c303b09f54ac82418454d747df599c3dd389c2f7`

Generated projection:

- 14 pedagogical pathways;
- 72 projected course steps;
- 72 semantic page specifications;
- stable MathKristal URNs and source provenance retained.

## Main implementation files

- `docs/16_math_university_kristal_bridge.md`
- `docs/contracts/math-university-projection/1.0.0/`
- `local/uckk/atlas/math_kristal_lock.json`
- `local/uckk/atlas/math_university_projection.json`
- `tools/uckk-ops/kristal/build_math_university_projection.py`
- `local/uckk/classes/local/atlas/math_university_projection.php`
- `local/uckk/atlas/math_universe.json`
- `local/uckk/classes/local/public_pages/math/`
- `local/uckk/courses.php`
- `local/uckk/classes/external/search_public_courses.php`

## Compatibility policy

`MATH-CURRICULUM-2.0` (8 pathways / 64 courses) remains readable as a historical compatibility snapshot. It is no longer the current public Math navigation source or epistemic authority. Its fixed cardinality guards were removed.

Existing Moodle enrolments, grades, submissions, annotations and editorial work are never rebuilt from the Kristal. A future materializer must be explicit, idempotent and state-preserving.

## SemantiK Architect boundary

The projector owns content selection. It emits page-level communication obligations from the pinned Kristal. SemantiK Architect may realize those obligations in a qualified target-language RuntimeSet, preferably compile-ahead. It does not choose mathematical facts, prerequisites, proofs, sources or curriculum topology. No generative-AI call is required for the deterministic rendering path.

## Public Moodle binding

In Math context, public catalogue code now reads `MATH-*` courses. A course whose `shortname` or `idnumber` contains a projected id such as `MATH-EUL-101` is enriched, read-only, with its projected pathway, MathKristal referent and `page_spec_id`. The AJAX search endpoint applies the same rule and includes projection metadata in Math searches.

This binding does not create or modify Moodle courses. It exposes whether an existing Moodle materialization is connected to the current projection.

## Validation performed

- JSON parse: changed bridge JSON files;
- JSON Schema Draft 2020-12: full projection and compact example;
- pin verification: all 6 locked MathKristal files, including byte counts;
- archive SHA-256 verification;
- deterministic rebuild: generated projection and lock are byte-identical;
- projection integrity: 14 / 72 / 72 and one page spec per projected course;
- PHP syntax lint: changed PHP files;
- Python bytecode compile: projection builder.

A broad baseline scan also finds an unrelated pre-existing malformed/empty `local/uckk/data/challenges.json`; the bridge does not modify that file.
