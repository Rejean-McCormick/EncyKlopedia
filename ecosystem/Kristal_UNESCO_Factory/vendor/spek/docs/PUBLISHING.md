# Publication and release pipeline

The main principle is **build locally, review independently, publish only approved derived assets**. These are separate operations:

`build ≠ semantic qualification ≠ disclosure approval ≠ public deployment ≠ Kristal activation`.

## Development and private preview

1. Make editorial changes in `examples/` or a separate article folder.
2. Validate: `python -m spek check`.
3. Compile local demonstration: `python -m spek build --out dist --formats html,pdf,tex`.
4. Verify: `python -m spek verify-site dist`.
5. Review visual layout, science, terminology, citations, and language equivalence. Current checks are syntactic and referential, not an independent scientific review.

GitHub CI builds demonstration previews as private downloadable workflow artifacts. No push triggers a public Pages deployment.

## Production preflight (technical checks only)

```bash
python -m spek build \
  --source vetted-article.json \
  --realizations reviewed-realizations.json \
  --state-snapshot vetted-v9-state-snapshot.json \
  --languages fr,en,it \
  --production --out published-site

python -m spek verify-site published-site --require-production
```

The production flag requires a pinned v9 **reference match** to the supplied state snapshot, declarations of scientific/disclosure/language reviews, and qualified realization declarations. The compiler does **not** compute or authenticate the canonical commitment, verify external review decisions, certify SemantiK RuntimeSets, or authorize publication.

## Deployment

After actual upstream authorization, manually add and commit the approved `published-site/` assets. Then run `.github/workflows/publish.yml`. It requires an authenticated `public-pages` environment review plus an environment-scoped authorization secret and rejects fixture manifests.

No CI workflow rewrites canonical Kristal state. No push to `main` alone publishes the site. The live wiki has its own separate manual sync (see [WIKI_PUBLISHING.md](WIKI_PUBLISHING.md)).
