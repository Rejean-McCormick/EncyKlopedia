# Skope 0.13.15 — consolidation

## Source of truth
- Starting repository: user snapshot `znapshot_EncyKlopedia_10131918.zip` (0.13.13, density visualization).
- Feature set: `EncyKlopedia_v0.13.14_English_Results_Wizard.zip` (working massive batch API, results ZIP, Windows clipboard, progress popup and convergence ?).
- Consolidated in the single EncyKlopedia repository, Skope under `00_system/tools/skope`.

## Preserved additions from user snapshot
- Canvas density graph with 3 connectivity layers, hue/visibility controls, density thresholds, labels, magnifier and inspect-by-QID.
- The view remains schematic, not geographic, and uses the bounded preview report (up to 10,000 entities).

## Restored from 0.13.14
- English UI and Wizard; batch progress dialog, results ZIP, open-folder, Windows file-to-clipboard action; external convergence help.
- Unlimited QID inventory on disk, pause and resume, read-only compact source index.
- Geography priority (Canada / North America) records intent but is not applied as a massive-inventory filter.

## Limitations
- `completed` means the requested graph traversal ended; not all North American plants were discovered.
- Results ZIP contains QIDs and metadata, not full Wikidata JSON, occurrence verification or Kristal canonical imports.
- Windows clipboard integration requires local Windows validation; browsers cannot directly copy a ZIP file object using ordinary navigator.clipboard.

- Fixed a stale French-string check that prevented the English Resume action from reusing a paused or interrupted job.
