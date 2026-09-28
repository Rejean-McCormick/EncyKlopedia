# Political Philosophy Lab — World 1

Version 2.1.0 of the drop-in World pack.

## Canon

- 13 canonical thinkers represented as **sourced synthetic reconstructions**, never as verbatim quotations unless an individual source explicitly marks a quote.
- 10 autonomous Korum debates from the supplied corpus.
- No numeric stance, vote, EkoH score, or Smart Vote result is inferred for canonical thinkers.
- `policies/canonical-actors.json` declares canonical thinkers as documentary personas: non-authenticating, non-voting, non-certifiable, and excluded from participant EkoH accumulation.

## Designed extensions

- 4 Knowledge gates.
- 4 fictional applied cases with no canonical answer.
- 1 CertifiKation path with 4 viewpoint-neutral competencies.
- 1 reflective Smart Vote experiment (Expert Council), with the raw baseline always visible.
- 1 Konstruct capstone: **Design a Legitimate Institution**.
- 1 final consultation template.
- EkoH evidence policy, Stockage artifact policy, and optional Kontact team formation.
- Konservation is deliberately disabled.

## Seed namespaces

`world.yaml` keeps three distinct namespaces:

- `module_seeds`: only actual Konnaxion module content.
- `content_seeds`: cross-module narrative content (`cases`, `experience`).
- `policies`: declarative World invariants.

The canonical ethiKos scenario remains `ethikos-demo-scenario/v3` and keeps the same `scenario_key` as v1/v2 so a replace-scenario import can supersede the earlier demo cleanly.

> Runtime note: current Worlds discovery validates the declared ethiKos scenario and preserves the additional manifest metadata. Cross-module sidecars require the generic World module loader/persona bridge to hydrate and enforce them at runtime.
