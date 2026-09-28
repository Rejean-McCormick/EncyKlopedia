# Historical Intellectuals — Konnaxion seed v0.1.0

This is a **starter registry**, not a claim of exhaustive coverage. It contains **211** curated entries spanning multiple civilizations, periods and disciplines.

## Core design

1. **UNESCO taxonomy** — fields are tagged with **ISCED-F 2013** codes, matching the existing Konnaxion `isced-f` fixture convention.
2. **Domain ≠ score** — a seeded domain says “this is a relevant field”; it does not fabricate a numeric EkoH expertise score.
3. **Historical persona ≠ live account** — personas cannot authenticate or cast a live ballot.
4. **Synthetic proposal/vote** — later reconstructions may generate proposals or vote-like positions from sourced preferences, but must be labeled as derived reconstructions and must never be mixed into a live baseline.
5. **Influence has two axes** — cultural/intellectual influence is stored separately from effective decision weight. Historical personas default to live-governance factor `0.0` because they are not live participants. A separate historical-council factor may be governed per persona; Julius Caesar is seeded at `0.0` as the explicit example requested, while others remain unrated.
6. **Ethics** — numeric EkoH ethics scores are not invented from fame, ideology or retrospective moral judgment. `ethics_score` starts `null`. The zero live-governance factor is a representation guard, not an ethical condemnation.

## 1926 rule

The seed interprets the requested “nothing after 1926” rule as **birth year ≤ 1926**, because some explicitly requested examples (e.g. Einstein) lived after 1926. **Grigori Perelman** is retained as an explicit named exception and is visibly flagged as such.

## Special representation cases

- **Jesus of Nazareth**: historical religious figure; historical-critical sources and confessional tradition must remain distinguishable.
- **Quetzalcoatl**: stored as a mythic/religious culture-hero identity, separate from **Ce Acatl Topiltzin Quetzalcoatl**, a semi-historical tradition figure.
- **Socrates**: reconstruction must rely on ancient witnesses; no surviving writings by Socrates.
- **Julius Caesar**: present as a historical persona. His reconstructed positions may be displayed. He is also seeded with `historical_council_ethics_factor: 0.0` as the explicit example requested; this does not erase his cultural/intellectual influence.

## Next hydration step

For each entry, add canonical source bundles and then derive:

- proposition templates / recurring principles;
- preference vectors by topic;
- confidence and disagreement metadata;
- synthetic votes only when a consultation can be mapped to documented positions;
- optional EkoH scores only under an explicit, governed scoring rubric.

The seed intentionally uses `unknown_position: omit` to prevent invented opinions.
