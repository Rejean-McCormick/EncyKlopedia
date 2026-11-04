# UNESCO private research reader (EncyKlopedia 0.2 alpha)

Second, **read-only local mode**. It reads a private Workbench snapshot generated from UNESCO source anchors, provisional Kristal v11 identity mapping, a 2025 LinkedDataHub RDF comparison extract, and 19 unapproved research proposals.

- `demo`: previous synthetic-only demonstration (`Start_EncyKlopedia.cmd`).
- `research`: explicit local `research-view.json`, with matching SHA-256 `build-report.json`. Launch `Start_UNESCO_Research.cmd` after Workbench's `build` and `check`.
- `public` and other values: **blocked**.

Security: loopback-only binding; HTTP GET/HEAD; no mutation or arbitrary file-loading routes; external references are HTTPS links displayed as text and links; no public mode, identity, source or claim approvals. The digest is draft-integrity evidence, NOT an authority signature or publication permission.

Private API:

```
GET /api/v1/status
GET /api/v1/search?q=right&lang=en
GET /api/v1/articles/right-to-education?lang=en
GET /api/v1/unesco/branch
```

The branch endpoint exposes the **88-branch local registry** (when installed), with SKOS snapshot differences. The article exposes 19 `claim_proposals`, six `source_refs`, and unapproved status.

Source licensing, human reviewer decisions, permanent KS source captures, canonical KA assertions, independently authorized C2/C4 publication and large-scale production search remain **not implemented**; do not distribute the private view as a public publication.
