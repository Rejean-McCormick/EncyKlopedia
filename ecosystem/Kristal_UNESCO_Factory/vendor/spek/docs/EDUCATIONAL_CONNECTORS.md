# Curated Ekole and Kompose connectors

## Separation of responsibilities

- **Ekole** owns curriculum, approved student-readable exports, learning objectives, pedagogical review and school constraints.
- **Kompose** owns roles, missions, sessions and access decisions; its deterministic `read_answer` only returns prewritten sourced content after an upstream access check.
- **Kontexte** owns missions/scenario frames and supported rendering of authorized mission fragments; it is not a publication authority for private school artifacts.
- **Spek** owns only the derived multilingual publication, typed cards and source inspection. It remains independently usable without any of these products.

## Input contract `spek.educational-projection/1`

Prepare an **explicitly curated JSON** with exactly `format`, `producer` (`ekole` or `kompose`), `complete:true`, `scope`, `document`, `realizations`, and a `selection` only when the producer is `kompose`.

`scope` requires `audience` (`student` or `general`), `data_classification` (`public_demo` or `public_released_excerpt`), `export_status:authorized_local_preview`, `dataset_ref`, `reader_policy_ref`, and `pedagogical_review` (`not_submitted` or `reviewed`). A real released excerpt must already have received upstream pedagogical review. Every unit and evidence item must carry its true **external_ref**, rather than acquiring a fabricated reference. Unrecognized fields anywhere in the exported document or realization entries are rejected. The compiler checks the full semantic type/cardinality contract on build.

A Kompose projection additionally supplies a `selection` with `kristal_id`, `topic_id`, `question_id`, `version` and `access_scope:preauthorized_public_excerpt`. **Do not put an auth token, session ID, role assignments, student identifier or teacher notes into this file.** Any access check and redistribution decision must occur upstream. A permitted classroom-only answer may NOT be converted to a public static site. The sample is fictitious and does not imply integration into Kompose's `PresentationPort` is deployed.

## Compile

```
python -m spek import-educational --adapter ekole --input examples/education/ekole-curated-preview.json --out-dir education-ekole
python -m spek build --source education-ekole/article.json --realizations education-ekole/realizations.json --out dist-education --formats html,pdf,tex
python -m spek verify-site dist-education
```

For Kompose, replace `ekole` by `kompose`, the input file by `examples/education/kompose-public-excerpt.json`, and the output dirs accordingly.

## Source alignment

- Ekole snapshot: `docs/PROTOCOLE_PUBLICATION_V12.md` defines **P0–P4**; `docs/CONTRAT_LECTEUR_HORS_LIGNE.md` separates public/student delivery from the teacher core; `docs/CONTRAT_PROPRIETE_SEMANTIQUE_V3.md` separates course selection from assertions owned elsewhere.
- Kompose snapshot: `src/kompose/reader.py` requires `access_granted` and sourced, prewritten answers; `docs/18-architecture-ports-adapters.md` assigns presentation to the PresentationPort; `contracts/schemas/integration-manifest.schema.json` lists `render_kristals` and forbids exports of student PII/diagnostics/teacher constraints.
- Kontexte snapshot: `docs/CONTRATS.md` and `docs/ekole-orgo/06_MEDIAS_IDENTITE_CONFIDENTIALITE.md` require trusted fragment release and withheld media in case of absent or revoked permission.

These upstream paths are documentation references, **not bundled source code**. No live upstream installation has been called or verified by this build.
