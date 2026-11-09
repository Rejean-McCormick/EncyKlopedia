# UNESCO Educational policy — scoped integration candidate

Repository: `EncyKlopedia`  
Windows path: `C:\mycode\EncyKlopedia\EncyKlopedia`  
Role: `private_inventory_and_public_reader`

This file is a **non-normative pilot integration record**, not a claim of interoperability or a public release. The 41 UNESCO concepts are **seed membership**, not 41 canonical KQ or 41 published articles. The 36 Wikidata P3916 candidates remain unreviewed. The Wikipedia EN SQL index and compressed XML remain local on D:; this repo must not redistribute them.

**Consumes:** `unesco_41_scope_zip`, `local_wikipedia_en_sqlite`, `approved_publication_bundle`.  
**Produces:** `private_wikipedia_candidate_inventory`, `eventual_public_read_only_articles`.

**Next correction:** Use tools/unesco_pilot/local_wikipedia_bridge.py for a private metadata-only 41-concept preflight; no public mode enabled.

## Mandatory invariants

- **One branch Kristal** `unesco-mt1-10`; 41 starting concepts; individual multilingual encyclopedia articles are **projections**, not distinct Kristals or copies/translations of Wikipedia.
- KQ/KP/KA/KS require their own native provenance and appropriate canonical review. QID and UNESCO identifiers remain external. An AI suggestion or Wikipedia reference does not create canonical KA or KS.
- The 14 requested locales are an **objective**, not proof of GF/SemantiK/Spek qualification or 574 completed articles.
- Never enable GitHub synchronization, Pages, wiki upload or public mode based solely on this pilot manifest. C1/C2/C3/C4 authorizations remain external and blocked.
- All source readings and candidate handoffs are local or explicitly chosen; never rewrite D: source dumps, framework pins, existing Kristal commitments, or private databases.

An additive contract smoke test is at `tests/test_unesco_mt1_10_handoff.py`; run it without touching existing repository semantics.
