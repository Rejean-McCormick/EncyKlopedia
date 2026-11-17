# Spek Wiki templates by Arketype — `spek.wiki-archetype-templates/1.0`

This is a **presentation layer** for the Kristal Wiki, not a second language generator.

1. **Kristal / Manager** selects eligible assertions and prepares a canonical, traceable public projection; no editorial template authorizes that selection.
2. **SemantiK Architect** produces exact bounded formulations for title, subtitle, abstract, section headings and every semantic unit, with request and RuntimeSet identity. The upstream integrator maps these to `kristal.layout-realizations/0.1` entries (`channel: semantik_architect`).
3. **Spek** validates the typed `kristal.layout-article-source/0.1` slots and composes the chosen Arketype page layout, using the *existing* eight Spek editorial contracts from `layouts/*.json`.
4. **Kristal Manager / public gates** verify C1/C2/C3 and Semantic RuntimeSet evidence outside Spek. The GitHub Wiki receives only independently approved pages after a separate publish operation.

## Template library

Wiki profiles live under `template_library/wiki/` at the root of Spek. Other template families have their own folders under `template_library/` and are currently reserved. Shared typed components continue to live in `layouts/`. Discover categories with `python -m spek list-template-categories`.

## Archetype selection

The `template_library/wiki/archetype-profiles.json` registry records **19 Arketype slugs** with a preferred layout and other admitted layouts. This is a composition hint, not an instruction to force facts into required slots. An Arketype whose data cannot satisfy a Spek layout is **blocked**; the generator never manufactures `evidence`, `limits`, assertions or realizations.

The existing Spek layouts are `result-card`, `argument-map`, `comparison`, `concept-card`, `learning-path`, `evidence-comparison`, `observation-inference`, `chronology`. For topology, taxonomy, mathematical formulae, graphs or other specialized data, add a **new, versioned Spek layout contract** rather than squeezing content into an unrelated card.

Each Kristal can have multiple compatible sections. A page is composed in source-declared section order; the template does not choose which sections or units should be present.

## Use

List profiles:

```powershell
python -m spek list-wiki-templates
```

Build a Markdown draft after *upstream* mapping and SemantiK realization:

```powershell
python -m spek build-wiki --source C:\private\article.json --realizations C:\private\realizations.json --archetype diagnostic-causal --slug kristal-diagnostic --language fr --state-snapshot C:\private\state-snapshot.json --out C:\private\wiki-draft
python -m spek verify-wiki C:\private\wiki-draft
```

The default mode requires verified v9 state references, reviewed source/disclosure/language flags, and **every used realization key** to be labelled `qualified` with SemantiK channel, `request_id` and `runtime_set_id`. These flags are checked for **presence and consistency**, not independently authenticated. C1/C2 authority, actual GF release validation, signed approvals and GitHub authorization remain external.

For testing only, against Spek's illustrative fixtures:

```powershell
python -m spek build-wiki --source examples/article.json --realizations examples/realizations.json --archetype composition-hybride --slug spek-demo --language fr --out C:\private\spek-wiki-demo --demonstration
```

The output has `Home.md`, `_Sidebar.md`, `Kristal-<slug>.md`, and a SHA-256 `manifest.json`, all marked as a private, **not published** candidate. It does not push Git or activate a wiki. Spek avoids publishing source locators/semantic internal IDs by default; upstream editorial approval is still required for the rendered content.

## Important integration boundary

SemantiK `semantik.kristal-v6.communication-projection/1.0` is not the same as a Spek article. A trusted upstream adapter must map selected assertions into Spek units / slots, and separately map realized communication results into exact realization keys. Spek will never parse arbitrary Kristal files and infer an article, and will never synthesize fallback wording. The current renderer is a functioning **Spek Markdown draft engine**; the automatic Kristal Manager → SemantiK → Spek bridge is a separate integration requirement.
