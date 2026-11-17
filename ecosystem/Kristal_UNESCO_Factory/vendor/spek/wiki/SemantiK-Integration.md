# SemantiK Integration

SemantiK provides **short linguistic realizations**. Spek provides the **editorial composition** that makes those realizations coherent and scannable without asking the language generator to invent multi-paragraph reasoning.

## Import the historical test fixture

```bash
python -m spek import-semantik \
  --input examples/semantik-prototype-minimal.json \
  --mapping examples/semantik-case-mapping.json \
  --out semantik-import.json
```

The importer accepts the known `cases` JSON shape and an explicit mapping of case ID to realization key and language. It retains request/runtime metadata when available. All imported entries are marked `fixture`: a successful prototype status is **not** a certification of GF grammar, PGF runtime, or linguistic equivalence.

## Requirements for a qualified live bridge

- Upstream-approved read-only derived projection of Kristal state.
- Verified canonical state identity/commitment by the owning Framework workflow.
- Versioned SemantiK RuntimeSet, request/response identities, supported language declarations, reviewed expressions.
- Independent scientific, linguistic and disclosure permissions for release.

These integrations are future work; refer to [[Roadmap]].
