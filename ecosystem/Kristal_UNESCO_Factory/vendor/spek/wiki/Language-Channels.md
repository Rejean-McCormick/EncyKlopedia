# Language Channels

Each Spek phrase is supplied by **either SemantiK Architect or preconstructed AI text**, independently of which connector supplied the knowledge. Spek itself does not invent the sentence.

- **SemantiK Architect:** short expressions can carry `request_id` and `runtime_set_id`; `qualified` is reserved for claimed SemantiK runtime qualification. Spek does not authenticate that runtime attestation.
- **Preconstructed AI:** sentences are generated elsewhere, imported locally with `model_id`, `generation_ref`, `prompt_sha256` and `human_review`. They are `fixture` while unreviewed or `reviewed` with an explicit human review reference, never GF-qualified. No SemantiK fields are added.
- **Legacy:** existing manual fixtures and old imported phrase prototype files remain classified `legacy`; no silent provenance upgrade.

```powershell
python -m spek import-ai --input examples/bridge/ai-preconstructed-example.json --base examples/bridge/realizations-without-example-claim.json --out ai-realizations.json
python -m spek build --realizations ai-realizations.json --out dist-ai
```

The sample is **illustrative**, and does not represent a real AI model invocation. It demonstrates the format and the isolation rule only. Review provenance is not independently authenticated by Spek.

See `docs/LANGUAGE_CHANNELS.md` and [Source Explorer](Source-Explorer).
