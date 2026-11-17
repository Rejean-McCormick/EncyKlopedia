# UNESCO Educational Policy — English v11 review candidate

This folder is a PRIVATE, UNRELEASED **review candidate**, reconstructed from the user's
`UNESCO-Educational-Policy-Scope-EN-20261104-100028-fb5dd7.zip`.

**Install:** unzip the top-level overlay into `C:\mycode\EncyKlopedia`.
Nothing is written into the active `UNESCO_Kristals\branches\unesco-mt1-10`.

The generated working copy is at:
`UNESCO_Workbench\candidates\educational-policy-en-v11\unesco-mt1-10`.

## What has been created

- An enabled v11 authoring profile **in the isolated candidate only**.
- 41 **provisional** KQ IDs, 3 provisional SKOS relation KP IDs and one provisional
  KS identifying the UNESCO *source snapshot* (NOT a reviewed scientific attestation).
- 36 non-accepted candidate Wikidata exact-match mappings in the external crosswalk.
- An English UNESCO lexical dictionary of 41 source terms plus 3 property terms,
  held as an external-provenance layer, *not* forged human-reviewed curated labels.
- Source SKOS edges kept under `derived/v11` for later relation-level editorial review;
  **no KA assertions** have been automatically inserted.
- A noncanonical research dossier for `concept10` / *Right to education* with
  links to authoritative international instruments. **No KS/KA has been
  assigned to those web research cards** pending independent source capture and review.

## Validation and next steps

1. Run `UNESCO_Workbench\LANCER_SCAN_EDUCATIONAL_POLICY_V11.cmd` (if Kristalizer is
   still at `C:\mycode\Kristal\Kristalizer`). It scans the candidate copy only,
   writing `UNESCO_Workbench\reports\educational-policy-v11`.
2. Inspect `CANDIDATS.csv` and review disambiguation; no decision is approved by the scanner.
3. Prioritize human review of concept10 and the 36 QID candidates; resolve the 2
   ambiguous and 3 unlinked concepts separately.
4. Capture source snapshots, define correct ownership/identity of new entities,
   then progressively register evidenced KS/KA *under the Authoring Kit's rules*.
5. Never publish or activate the candidate until qualification and explicit approval.

**Contracts:** the v11 profile is checked by the exact `kristal_v11_core.py` from
this candidate workspace, and the static scan has been checked against the provided
Kristalizer 1.2.2 code. Do not overwrite canon or existing decisions with this draft.

**Language:** English first. The preserved UNESCO source snapshot happens to include
other labels but the new lexical/research layer uses English only.
