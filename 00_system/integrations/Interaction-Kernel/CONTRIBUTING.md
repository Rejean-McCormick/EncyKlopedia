# Contributing

Interaction Kernel is specification-first.

- Put use-case semantics in Profiles before adding anything to Core.
- Any ownership change requires an ADR.
- Any normative MUST/MUST NOT/SHOULD rule requires TCK coverage when testable.
- Published Profile/schema versions are immutable.
- No production secret, trust root, bearer token or private credential belongs in this repository.
- `CURRENT`, `TARGET`, and `IK PROPOSAL` must remain distinct in upgrade documentation.
