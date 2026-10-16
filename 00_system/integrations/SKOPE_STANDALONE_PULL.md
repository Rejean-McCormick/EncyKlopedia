# Skope Standalone → EncyK pull integration

Standalone Skope and EncyK are **separate applications**. Skope v0.14.1
explores Wikidata; EncyK discovers/acquires/verifies source evidence and
prepares Médiathèque handoffs. Neither application imports code from the other.

## Start the applications

1. Start Skope v0.14.1 with `C:\mycode\Skope\Start_Skope.cmd` and keep it running at `http://127.0.0.1:8767`.
2. Start EncyK as usual with `EncyKlopedia_Manager.cmd`.
3. In its `5 · Skope externe` tab, click **Check Skope API**, then **Latest jobs**.
4. Paste a **completed** Skope job's 32-character hex ID and choose **Pull completed QID ZIP**. EncyK checks the result and writes it to the external intake on D:.

Alternatively use PowerShell 7:

```powershell
$repo = 'C:\mycode\EncyKlopedia\EncyKlopedia'
$bridge = "$repo\00_system\integrations\skope_bridge.py"
python -B $bridge doctor
python -B $bridge list
python -B $bridge pull --job 'fb7791e61d814ca1879044a5c82f8c62'
```

The Catho job above is an **example from the prior session**. Only use it if this
job still exists and is complete in the running Skope instance. The API does not
provide a full history listing; `/api/large/latest` and `/api/author-campaign/latest`
only return the most recent recorded job of their respective types.

## Outcome

An explicit pull writes a validated original ZIP and individual, vetted entries
under `D:\EncyKlopedia\20_evidence\external-intake\skope\<job-id>`:

- QID JSONL inventory and exact `recipe.json`.
- Skope summary or author-match provenance if the result ZIP contains them.
- `receipt.json`, with SHA-256, source job, status and source URL.

The importer rejects unfinished jobs, missing inventory, duplicate/unsorted QIDs,
ZIP entry path traversal, oversized archives and mismatched status/counts. Repeating
an identical import reports `already_imported`, but changed bytes block reuse.

The importer **does not** call start/resume endpoints, rebuild a Wikidata index,
perform a new dump scan, extract full source JSON, mutate EncyK's scope freezes,
or write a Kristal/Médiathèque canon. It keeps a *reported* Skope evidence path
as metadata only; the path is not validated as independent evidence.

## Compatibilities and what comes next

Existing EncyK `scope-builder` (rooted discovery and full-record source-extraction)
remains intact. Imported Skope QIDs are an **external intake inventory** to inspect
and explicitly use in future scopes; they are **not automatically accepted** as
frozen EncyK scopes or merged into Kristal. A future alignment can add a separately
authorized conversion from selected QIDs into frozen scope manifests, with content
hashes and explicit source validation, leaving this v1 contract unchanged.

Contract: `00_system/contracts/skope-pull/1.0.0/`.
