# Pinned Kristal / Interaction Kernel contracts

These JSON Schemas are pinned copies from the supplied Interaction Kernel / Kristal integration snapshot.

```text
Interaction Kernel schema boundary: 1.1
Kristal Standard baseline: 6.0.0
Files:
- artifact-ref.schema.json
- export-manifest.schema.json
```

They are used only to validate the Médiathèque kOA boundary export. They do not make the médiathèque a Kristal database or transfer ownership of local media to Kristal.

The source of truth for media bytes and catalog records remains Médiathèque kOA. Exported locators are opaque `koa-media://` references; local filesystem paths are intentionally not exposed.
