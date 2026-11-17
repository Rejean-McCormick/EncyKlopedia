# Publishing the Wiki

The English wiki source is stored in the main project as `wiki/*.md`, but GitHub's live wiki is a separate repository such as `OWNER/Spek.wiki.git`.

## Initialize

1. Create/push the main Spek repository.
2. Enable **Wikis** in the repository settings.
3. Create an initial `Home` page in the GitHub Wiki UI so its separate Git repository exists.
4. Ensure that you have wiki write permission.

## Preview and sync

```bash
./scripts/sync-wiki.sh OWNER/Spek         # local diff only
./scripts/sync-wiki.sh OWNER/Spek --push  # explicit remote push
```

The script clones the current wiki, copies local Markdown pages without deleting unknown remote pages, commits changes and (only with `--push`) pushes to the wiki's default branch.

Do not use the wiki as a place for unpublished, confidential scientific data. Keep updates reviewed in the main repo first.

GitHub reference: <https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages>.
