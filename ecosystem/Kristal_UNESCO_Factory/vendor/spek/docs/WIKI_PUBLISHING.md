# Publishing the GitHub wiki

GitHub keeps wiki pages in a **separate Git repository** named `OWNER/REPOSITORY.wiki.git`, even though the Wiki tab is displayed next to the main repository. The markdown files in `wiki/` are the versioned source of truth in Spek.

## One-time initialization

1. Create and push the primary Spek repository.
2. Enable the repository Wiki feature (Settings → General → Features → Wikis).
3. Open the Wiki tab and create the first page called `Home` to initialize the separate wiki Git repository.
4. Make sure you have write access to the wiki, and use SSH or an authenticated Git credential manager.

## Safely sync the sources

From the Spek repository root:

```bash
# Inspect the pages that will be synced:
find wiki -maxdepth 1 -type f -name '*.md' -print | sort

# Clone, copy updated pages, commit and push; requires explicit --push:
./scripts/sync-wiki.sh OWNER/Spek --push
```

Without `--push` the script creates a temporary local clone and displays a diff summary without publishing. The script copies only the project's Markdown pages, does not delete remote-only pages, and rejects a missing wiki repository rather than attempting to invent one.

GitHub Docs: [Editing wiki pages](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).

## Synchronization policy

- Update Markdown in `wiki/` through a normal pull request first.
- Review generated link targets and technical accuracy.
- Only maintainers should run the push script. It performs an explicit Git push, separate from Pages deployment.
- Treat any live wiki page edited directly in the browser as a potential divergence; reconcile it into `wiki/` before syncing.
