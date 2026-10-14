# Skope 0.13.14 — English UI + batch results

After a batch QID inventory begins, the progress dialog opens. While running,
watch **QIDs selected**, **Expanded nodes**, **Pending expansions**, and pause at batch
boundaries. Unlimited inventory has NO meaningful completion percentage until the
graph traversal finishes. A finite target gives progress toward that requested
count only, not completeness.

When state is **Completed**, the following actions unlock:

- **Open Results folder**: opens Windows Explorer on the D: working folder.
- **Download Results ZIP**: local HTTP response streaming disk-backed ZIP.
- **Copy ZIP File to Clipboard**: on Windows, uses native CF_HDROP so you can
  paste a copy of the ZIP into File Explorer using Ctrl+V (not base64 or text).

The result ZIP includes `selected-qids.jsonl`, `recipe.json`, `summary.json`,
`README.txt`—not state.sqlite, the full Wikidata dump, complete Wikidata JSON, or
Kristal canon data. The native Clipboard action requires Windows; Download ZIP
works in any browser. Only loopback clients are accepted; POST requests with a
foreign Origin are rejected. Result file paths derive solely from validated
server-issued hexadecimal job IDs. No arbitrary file paths are accepted.

The **?** next to **External convergence** explains threshold, minimum connections
and extra depth. This algorithm does not run during the massive QID inventory.
Geographic priorities likewise do not filter the massive QID inventory.
