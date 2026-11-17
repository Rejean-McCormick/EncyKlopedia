# Language Channels: SemantiK Architect **or** Preconstructed AI Sentences

Spek is agnostic about the realization provider. Every used `realization_key` / language entry has **one** channel. Spek does not call LLMs or GF automatically.

## Channel A: SemantiK Architect

When a qualified SemantiK Architect realization is available, an import/adapter can provide a phrase entry with:

```json
{
  "text": "A sentence supplied by SemantiK",
  "channel": "semantik_architect",
  "status": "qualified",
  "provider": "semantik_architect",
  "request_id": "request:example",
  "runtime_set_id": "runtime:reviewed"
}
```

These are illustrative fields, **not** proof of actual GF compilation or qualification. Spek checks presence and syntax only, not runtime attestation. The `import-semantik` command still imports the historical *phrase prototype* as **fixture/unqualified** data.

## Channel B: Preconstructed AI text

No SemantiK Architect is involved. AI text is generated and reviewed **outside** Spek, then imported as frozen sentences with model/generation provenance, a prompt fingerprint and human-review metadata. `import-ai` makes **no network calls**.

```powershell
python -m spek import-ai --input examples/bridge/ai-preconstructed-example.json --base examples/bridge/realizations-without-example-claim.json --out ai-realizations.json
python -m spek check --source examples/article.json --realizations ai-realizations.json
python -m spek build --source examples/article.json --realizations ai-realizations.json --out dist-ai
```

The sample's `model_id` is an explicitly fictitious placeholder and `human_review.status` is `pending`; **no model was run** for the sample. The imported phrase remains a **fixture**.

A genuine AI bundle declares:

```json
{
 "format":"spek.ai-phrases/0.1",
 "phrases":[{
  "realization_key":"u.result.claim", "language":"en",
  "text":"Reviewed sentence.",
  "model_id":"your-actual-model-id",
  "generation_ref":"your-captured-generation-id",
  "prompt_sha256":"sha256:<64-lowercase-hex-digits>",
  "human_review":{"status":"approved", "review_ref":"a-pinned-local-review-record"}
 }]
}
```

Pending human review generates `status: fixture`. Explicitly approved metadata generates `status: reviewed`, **never** `qualified`. A reviewed AI phrase must **not** claim SemantiK request IDs, RuntimeSets, GF functions or qualified GF lexical annotations. Spek cannot authenticate the human review itself; published outputs still require review of all science, language and disclosure conditions from their independent authority.

Existing v0.3 phrases without a `channel` retain `legacy` provenance for backwards compatibility; they are not silently relabeled SemantiK or AI. Mixed channels are allowed across different phrase entries, but **one phrase entry never has both ancestries**. Imported AI entries cannot overwrite existing ones. No language fallback or automatic translation occurs.

## Source Explorer

A card reveals: selected channel, realization status, supplier, SemantiK request/runtime fields **or** AI model/generation/human-review fields, and any explicitly supplied word morphology. Words without supplied attributes are surface-segmented only. This is deliberate: no token-level linguistic analysis is inferred from AI prose.
