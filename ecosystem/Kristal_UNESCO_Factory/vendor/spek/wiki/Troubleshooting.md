# Troubleshooting

**`Missing realization <key>/<lang>`** — Every used phrase key must have an entry for every requested language. Add reviewed text; do not invent a fallback.

**`Wrong kind <kind>`** — A section slot references a semantic unit of the wrong type. Consult the JSON layout's `allowed_kinds`.

**`Cardinality violation`** — A slot contains fewer than its required minimum or more than its allowed maximum.

**`Result ... evidence not linked to claim`** — Add a legitimate claim-to-evidence relation in the source projection, or remove the unsupported evidence card.

**`Publishing refuses fixtures or unqualified realizations`** — Real publishing is blocked for illustrative content. Do not change status flags just to bypass the gate; obtain actual qualified inputs and approvals.

**`Missing source state reference check`** — A production candidate requires a matching supplied state snapshot and origin reference. This check alone does not authenticate a JCS commitment.

**`File altered since compilation`** — An output changed after manifest generation. Rebuild from verified sources; do not edit generated files by hand.

**`No module named reportlab`** — Install `requirements.txt`, or build only `--formats html,tex`.

**Wiki clone fails** — Enable Wiki and create its first `Home` page on GitHub. Check the owner/repository spelling and your authentication.

**No remote GitHub repository** — The local archive is Git-ready, but GitHub account creation is an explicit external action. Follow project `docs/GITHUB_SETUP.md`.
