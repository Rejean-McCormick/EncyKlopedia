# Educational layout pack (Spek v0.5)

**Status:** experimental, derived presentation only. These templates do not set grade levels, verify mastery, or change canonical Kristals.

Spek preserves typed slots and semantic identifiers. The editor supplies short reviewed/illustrative phrases; the renderer supplies readable structure; the **Source Explorer** preserves word annotations and provenance when supplied. HTML, PDF and XeLaTeX use the same SpekDocument projection.

| Template | Required slots | Optional slots | Invariant |
| --- | --- | --- | --- |
| `concept-card` | `definition`, `examples`, `context`, `limits` | `counterexamples` | A counterexample must be supplied, never invented. |
| `learning-path` | `objective`, `prerequisites`, 2–6 `steps`, `reflection`, `limits` | None | A study path does not certify learning, proficiency or progression. |
| `evidence-comparison` | `question`, `source_a`, `source_b`, `perspective_a`, `perspective_b`, `synthesis`, `limits` | None | Perspectives are not asserted to be interchangeable; both sources shown. |
| `observation-inference` | `observations`, `interpretation`, `verification`, `limits` | None | Observations are distinct from explanations. |
| `chronology` | `context`, 2–6 `events`, `limits` | `interpretation` | Order is not inferred to be causality. |

This pack is deliberately **separate** from Spek's general `result-card`, `argument-map`, and `comparison`; the latter remain available for research and other non-school contexts. Educators can publish the same knowledge in multiple layouts, but Spek does not assume that semantic graph edges are curricular prerequisites.

## Authoring

- Each section uses the exact layout ID and slot names in `layouts/*.json`.
- Each slot must contain the declared **kind** and satisfy explicit cardinality; missing required data blocks compilation.
- Each phrase is explicitly present in French, English and Italian for the included demonstrations (no fallback or automatic translation).
- Human review and local/institutional publication authorization remain external requirements.

Example: `examples/education/ekole-curated-preview.json`, then `python -m spek import-educational ...` and `python -m spek build ...`.
