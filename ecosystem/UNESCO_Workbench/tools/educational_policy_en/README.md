# Educational policy — English-first scope after the EncyKlopedia move

Double-click `LANCER_SCOPE_EN.cmd` inside:

`C:\mycode\EncyKlopedia\UNESCO_Workbench\tools\educational_policy_en`

Source (read-only):

`C:\mycode\EncyKlopedia\UNESCO_Kristals\branches\unesco-mt1-10`

Private output copies:

`C:\mycode\EncyKlopedia\UNESCO_Workbench\candidates\educational-policy\en\SCOPE-*`

Kristalizer is still at `C:\mycode\Kristal\Kristalizer\kristalizer.py` unless you moved it separately.

1. Click **Vérifier sans modifier**. The source should have 41 UNESCO IDs and `concept10` / Right to education.
2. Click **Préparer + scanner avec Kristalizer**. The tool copies just this Kristal to a unique private directory, writes the 9 research facets, semantic boundaries, 41-concept review CSV and bounded Skope/MaxWD recipes, and executes the documented **scan** command if Kristalizer is found.
3. Return `UNESCO-Educational-Policy-Scope-EN-*.zip` from Downloads, not the full 88-branch folder.

**Expected v9 finding:** Kristalizer v1.2.2 may report `V11_MIGRATION_REQUIRED`, often with **zero KQ/KP candidates**. This is **not** an identity-matching failure: the original UNESCO branch contains a v9 SKOS import, not a native v11 registry/graph. The tool does not fake v11 identities. After receiving the ZIP, the next engineering step is a reviewed v11 bootstrap of the branch and **sourced knowledge for concept10**. Only afterward should we scale up or consider canonical promotion.

**Safety:** no changes to the migrated Kristal; no Wikidata data expanded; no MaxWD/Skope campaigns run; no KA/KS facts created or approved; no Kit build; no publication. `state_scope` and `semantic_ownership` are only in a **private copy** and remain editorial proposals. Current article language is English only. Research keywords are **not** automatically inferred UNESCO classes.

**CLI alternative:** `py -3 prepare.py --check-only`, followed by `py -3 prepare.py`. `--no-scan` is available if Kristalizer is not installed.

The JSON configuration `UNESCO_Workbench/config/en/educational-policy/workspace-paths.json` is updated by this overlay to the new moved Factory and Kristal locations. Original Factory RUNs under Kristalizer are left where they were.
