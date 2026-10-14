# EncyK Skope v0.13.15 — validation report

- Repository validator: PASS.
- Skope unit tests including source search, massive resume, ZIP export, geography, Wizard, merge guards: PASS.
- Scope Builder tests: PASS.
- Browser smoke via Chromium Playwright: PASS (density report, magnifier, convergence help, Wizard, completed-job results modal, no JS errors) on mocked local API and synthetic data.
- JS syntax check (Node): PASS.
- `tests/test_density_dom.cjs` is preserved from the user snapshot but requires optional `jsdom` and `@napi-rs/canvas` packages for standalone execution; browser smoke covers the runtime here.
- Large real Wikidata index on D: and Windows OS clipboard/open-folder integration were not available for testing in this container.
