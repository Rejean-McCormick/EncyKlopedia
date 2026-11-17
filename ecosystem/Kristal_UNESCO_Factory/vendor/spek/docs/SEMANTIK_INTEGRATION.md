# SemantiK integration

Spek is deliberately downstream of SemantiK. It **does not** run GF, synthesize paragraphs, translate missing entries, or upgrade prototype realizations into reviewed ones.

## Two distinct inputs

1. `examples/article.json` binds semantic IDs to typed layout slots.
2. `examples/realizations.json` supplies one short textual expression for each referenced key in each requested language.

The separation makes it possible to change a layout without rewriting knowledge, and to change language realizations without reassigning the semantic roles.

## Importing the historical prototype

```bash
python -m spek import-semantik \
  --input examples/semantik-prototype-minimal.json \
  --mapping examples/semantik-case-mapping.json \
  --out semantik-import.json
```

The input is the **historical SemantiK phrase prototype** structure (a `status=PASS` object with `cases[*].plain_text`, request ID, and optional runtime set ID). The mapping explicitly associates each case with a realization key and language. The output always uses `status=fixture`, even for successful prototype cases, and does not backfill languages.

## Integration with a qualified runtime

A future upstream adapter must supply independently authenticated RuntimeSet provenance, a frozen semantic reference, per-language request and output identifiers, recognized licensing/terminology policy, and independently reviewed scientific-language equivalence. The current schema can **declare** `status=qualified`, but Spek cannot authenticate that declaration itself.

For exact validation and rejected conditions see [CONTRACTS.md](CONTRACTS.md) and [SECURITY_MODEL.md](SECURITY_MODEL.md).
