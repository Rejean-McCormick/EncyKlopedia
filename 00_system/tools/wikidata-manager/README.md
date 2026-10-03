# Wikidata Acquisition Manager

Optional helper for discovering/downloading/verifying a Wikidata dump and building the rebuildable global discovery index.

Paths:

- acquisition snapshot: `20_evidence/acquisition-snapshots/wikidata/latest.json`;
- verified source manifest: `20_evidence/manifests/wikidata-dump-verified.json`;
- runtime checkpoint: `90_runtime/checkpoints/wikidata-index-state.json`;
- downloaded acquisition cache: `10_sources/wikidata/dumps/current/`;
- optional global index: `30_working/wikidata/wikidata.compact.sqlite`.

The dump and index are EncyK acquisition/workspace inputs. Accepted persistent source storage belongs to Médiathèque after the EncyK handoff. The compact SQLite is an accelerator, never source or semantic authority.

The GUI button **Scopes → Evidence → Médiathèque** opens the current Scope Builder.
