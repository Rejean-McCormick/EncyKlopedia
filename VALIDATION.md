# Validation — EncyK 0.12.0

Validated on 2026-10-03 after the source-authority cleanup.

## Passing checks

- repository architecture validator: **PASS**;
- JSON parsing: **116 files PASS**;
- Python compileall over active tools/launchers: **PASS**;
- Scope Builder + Wikidata Manager pytest suite: **8 tests PASS**;
- end-to-end raw scope pipeline: **PASS**;
- non-person root scope: **PASS**;
- lossless qualifiers/references/external IDs: **PASS**;
- fast-access evidence path: **PASS**;
- optional project query index: **PASS**;
- external identity candidate generation: **PASS**;
- `encyk.source-evidence-handoff/2.0.0` schema validation: **PASS** when `jsonschema` is available;
- repeated source handoff generation is content-address stable: **PASS**.

## Architecture gates

The active repository contains no:

- `40_kristal/`;
- `50_mediatheque/`;
- `20_ingest/`;
- vendored `00_system/integrations/Interaction-Kernel/`;
- active legacy Kristal v5 contract pin;
- active legacy DaaT spelling.

The canonical source handoff targets Médiathèque kOA `>=0.2.0` / `koa.source-catalog/2.0.0` and deliberately does not encode downstream IK, DaaT, Kristal/Kristall or Kompiler versions.

Those downstream compatibility baselines remain documented separately in `00_system/contracts/knowledge-baseline.json`.

## 0.13.0 — 2026-10-13, Skope intégré

- Validateur EncyK du dépôt : PASS.
- Tests existants Scope Builder : 5 PASS (`pytest`).
- Tests existants Wikidata Manager : 3 PASS (`pytest`).
- Tests Skope EncyK : 5 PASS (`unittest`) — index en lecture seule, convergence, export, troncature, Arketype et rejet d’index incomplet.
- Tests de nettoyage local : 4 PASS (`unittest`) — hash, refus des chemins dangereux/symlinks et revalidation.
- Compilation Python des nouveaux outils : PASS.
- **Non vérifié :** interface Tkinter sous Windows réel, performances sur index Wikidata massif, handoff sur vrai dump complet avec une sélection Skope et validation d'un déploiement sur la machine utilisateur.
- Aucune suppression préexistante : manifeste de migration vide.

## 0.13.1 — 2026-10-13 : consolidation

- Archive issue d'EncyK 0.13, complétée uniquement de tests et du manifeste
  de nettoyage des anciens fichiers EncyK intégrés 0.12.
- Répertoire Skope autonome et importeur Skope `entities/edges` **absents**.
- Vérifications exécutées dans l'environnement de préparation : voir le rapport final.
- Aucun nettoyage de dépôt local ni suppression externe n'a été effectué.
