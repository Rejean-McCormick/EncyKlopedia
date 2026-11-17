# GitHub Publishing

## Principle

**Compile locally. Publish approved static artifacts. Never compile or activate Kristal in GitHub Actions.**

## CI preview

The `quality.yml` workflow validates the project and uploads a **private workflow artifact** for preview. It is not a public website and never publishes GitHub Pages.

## Controlled public deployment

1. Obtain actual scientific, linguistic and disclosure approvals and upstream Kristal release authorization.
2. Create a `production_candidate` build locally using qualified real inputs and `--state-snapshot`. This is a technical preflight only, not a grant of approval.
3. Review and verify `published-site/` and force-add **only these approved derived assets** to an authorized commit.
4. In GitHub repository settings, configure Pages to use Actions and create protected environment `public-pages` with required reviewers. Add environment secret `KRISTAL_PUBLICATION_GATE=authorized` only for approved releases.
5. Run `Deploy locally compiled qualified publication` manually from the approved `main` revision.

The workflow checks the manifest and environment secret before uploading; the deployment job needs `pages: write` and `id-token: write`. A push alone does **not** deploy.

## The separate GitHub wiki

Main code and wiki are different Git repositories. See [[Publishing the Wiki]] for first-page initialization and controlled sync.

**Security:** make sure public output does not contain canonical private blobs, credentials, or sensitive provenance. The compiler cannot decide whether information may be disclosed.
