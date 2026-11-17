# Contributing to Spek

Thank you for helping advance structured scientific publishing.

## Proposing a change

1. Start with an issue explaining the user-facing problem and the semantic invariant it affects.
2. Keep canonical knowledge, editorial source, realizations, and visual layouts distinct.
3. Include tests for both accepted and rejected inputs.
4. For a layout change, update all three output renderers and the English wiki page.
5. Run `python -m unittest discover -s tests -v`, `python -m spek check`, and manually inspect a trilingual build.
6. Open a pull request with risks, affected schema versions, tests, and screenshots when visuals change.

Do not add private upstream canonical material or undocumented public publication automation. Any real-world scientific statement requires evidence and review.

## Conventions

English is used for code, comments, documentation, issues, and wiki. Example publications may have FR/EN/IT realizations. Preserve stable IDs, explicit epistemic statuses, and no-translation-fallback semantics. Avoid rebranding schema format identifiers without a migration plan.

## Rights

See [LICENSE-DECISION.md](LICENSE-DECISION.md) before submitting third-party code or redistributing this prototype. This project has not yet chosen an outbound license.
