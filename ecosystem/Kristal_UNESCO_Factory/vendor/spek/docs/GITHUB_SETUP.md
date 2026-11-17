# GitHub repository setup

The supplied distribution is a **local Git-ready project**, not evidence that a remote repository exists. GitHub repository creation requires an authorized account and an intentional visibility choice.

## Recommended first publication: private repository

1. Create a **private** repository named `Spek` in the desired GitHub account or organization. Do not initialize it with a README; Spek already has one.
2. Push the prepared local `main` branch:

   ```bash
   git remote add origin git@github.com:OWNER/Spek.git
   git push -u origin main
   ```

3. Review repository contents, dependabot settings, access permissions, and workflow permissions.
4. Enable the GitHub Wiki feature and create its first `Home` page (GitHub needs this to initialize the wiki Git repository).
5. Publish wiki content as described in [WIKI_PUBLISHING.md](WIKI_PUBLISHING.md).

## Publication controls

A repository must **not** be made public just to test a demonstration. Test locally or in a private repository. Before deploying a scientifically reviewed public output:

1. In repository **Settings → Pages**, select **GitHub Actions** as build/deployment source.
2. Create the environment `public-pages` with **required reviewers**, and restrict its deployment branches to `main`.
3. Add an environment-level secret `KRISTAL_PUBLICATION_GATE=authorized` *only after* external publication/disclosure authorization. Protect the environment from unreviewed edits.
4. Compile a real, qualified production candidate locally into `published-site/`; review all output files and the manifest.
5. Commit only the authorized public assets (use `git add -f published-site/` because the folder is ignored by default).
6. Launch the manual workflow `Deploy locally compiled qualified publication` on the approved `main` revision and approve deployment via the protected environment.

**Do not** commit private Kristal canonical blobs or unapproved evidence into public repositories.

GitHub Docs: [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## v0.4 operator note

Spek has **no default upstream GitHub repository**. The downloadable Git Bundle is a self-contained local history. Restore it with `git clone Spek_Repository_0.4.0.bundle Spek`; set a new remote with `git remote set-url origin https://github.com/OWNER/Spek.git` **after** creating and authorizing your own GitHub repository. Wiki synchronization is a separate, explicit operation. Do not push source-system exports, bearer tokens, query files or publication drafts into a public repository without review.
