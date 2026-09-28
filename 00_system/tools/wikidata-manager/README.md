# EncyKlopedia Wikidata Local Manager — v0.9 portable

Ce gestionnaire est installé dans `00_system/tools/wikidata-manager` et déduit automatiquement la racine `EncyKlopedia` depuis son propre emplacement. Il ne dépend donc pas de la lettre de lecteur.

Chemins principaux :

- dump officiel : `10_sources/wikidata/dumps/current/`
- provenance/snapshot/checkpoints : `20_ingest/`
- index SQLite : `30_working/wikidata/wikidata.compact.sqlite`
- registre actif : `10_sources/seeds/active/intellectual-registry/intellectuals.seed.json`
- QID map : `30_working/registry/`
- signatures/expansions : `30_working/relation-maps/`

Lancer `run_manager.pyw` ou `start_manager.ps1` depuis la racine canonique sur C. Les données lourdes peuvent être exposées depuis D par junctions NTFS.

Le dump JSON bz2 est traité en streaming; aucune copie JSON décompressée complète n'est créée.

L'indexeur utilise SQLite WAL + `synchronous=NORMAL` afin de mieux tolérer une interruption pendant un build long; les commits/checkpoints restent périodiques.


## Scopes → Evidence/Kristal

Le bouton **Scopes → Evidence/Kristal** ouvre `00_system/tools/scope-builder/run_scope_manager.pyw`. Le manager SQLite reste un accélérateur optionnel.

## v0.9 role

The compact SQLite built by this manager is **optional project discovery acceleration**. Scope Builder can now operate directly on the raw dump when the index is absent or intentionally skipped. Do not treat completion of this index as a prerequisite for Da'at/Kristal evidence extraction.


## v0.9 performance

For new dumps, use `.json.gz` when `rapidgzip` is installed. The full compact SQLite remains optional; Fast Access under `30_working/wikidata-fast/` can accelerate scope discovery and raw evidence extraction without becoming an evidence source.
