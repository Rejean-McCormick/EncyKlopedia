#!/usr/bin/env bash
# Explicit, non-destructive sync of reviewed wiki Markdown to an initialized GitHub wiki.
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo 'Usage: ./scripts/sync-wiki.sh OWNER/REPO [--push]' >&2
  exit 2
fi
repo="$1"
push="${2:-}"
if [[ ! "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo 'Expected OWNER/REPO, such as example/Spek' >&2
  exit 2
fi
if [[ -n "$push" && "$push" != '--push' ]]; then
  echo 'Only optional flag is --push' >&2
  exit 2
fi
here="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
remote="https://github.com/${repo}.wiki.git"
if ! git clone --quiet "$remote" "$tmp/wiki"; then
  echo 'Wiki clone failed. Enable GitHub Wikis and create the first Home page before syncing.' >&2
  exit 1
fi
cp "$here"/wiki/*.md "$tmp/wiki"/
cd "$tmp/wiki"
echo 'Wiki changes to be applied:'
git status --short
if git diff --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
  echo 'Wiki already matches local source.'
  exit 0
fi
if [[ "$push" != '--push' ]]; then
  echo 'Dry run. No remote changes. Rerun with --push to publish reviewed pages.'
  exit 0
fi
git add -- '*.md'
git commit -m 'docs: sync reviewed Spek wiki pages'
git push origin HEAD
printf 'Published reviewed wiki pages to %s\n' "$remote"
