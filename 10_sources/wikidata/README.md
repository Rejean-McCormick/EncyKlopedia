# Source Wikidata locale

- `dumps/current/` : dump officiel actuellement utilisé (JSON bz2, jamais décompressé en entier sur disque).
- `dumps/archive/` : snapshots conservés volontairement; la politique cible est normalement 1 dump complet actif.
- `checksums/` : checksum/manifest officiel associé au dump.
- `manifests/` : métadonnées de téléchargement et provenance.

Le dump est une **source**, pas le canon EncyKlopedia. L’index compact et toute exploration vivent sous `30_working/`.
