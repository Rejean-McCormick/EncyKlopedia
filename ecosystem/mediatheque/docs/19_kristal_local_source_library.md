# 19 — Adaptateur des anciennes sources locales Kristal

## Statut

Ce composant est désormais un **adaptateur de migration/compatibilité**. Il ne définit plus l'autorité source de la Médiathèque.

Le modèle canonique en schéma v4 est consumer-neutral :

```text
source_consumer_registry
source_registry
source_bindings
source_snapshots
source_representations
source_import_log
        │
        ▼
library_rows
```

Les tables historiques `kristal_sources`, `kristal_source_links`, `kristal_source_snapshots`, `kristal_source_representations` et `kristal_source_import_log` sont conservées pour migration et inspection d'anciennes bases. Les nouvelles écritures passent par `source_*`.

## Import d'une ancienne external-source-library

Le format historique reste accepté :

```text
Kristal/external-source-library/source-store.json
        │
        ▼
KoaKristalSources.py
        │
        ▼
source_consumer_registry
  consumer_system = kristal
  consumer_instance = <kristal_id>
        │
        ├── source_bindings
        │      external_source_id = <ancien source_id>
        │
        └── source_registry
                └── source_snapshots
                        └── source_representations
                                └── library_rows.version_uuid
```

Le `source_id` d'un Kristal est donc un **binding externe**, pas l'identité physique de la source.

## Stockage

Les nouveaux imports écrivent dans :

```text
02_STORAGE/source_files/
```

Le filearea historique :

```text
02_STORAGE/kristal_source_files/
```

reste valide pour les lignes déjà existantes. Aucun déplacement destructif d'octets n'est imposé.

## Déduplication

La déduplication physique repose sur le SHA-256 calculé localement dans `library_rows`. Deux Kristals — ou demain EncyK et un Kristal — peuvent donc référer les mêmes octets sans dupliquer le fichier.

## Commandes compatibles

```powershell
python 05_TOOLS/KoaKristalSources.py discover --root D:\Kristals --include-candidates
python 05_TOOLS/KoaKristalSources.py plan --store D:\...\external-source-library\source-store.json
python 05_TOOLS/KoaKristalSources.py init --db D:\KOA_MEDIATHEQUE\01_DB\koa_mediatheque.sqlite
python 05_TOOLS/KoaKristalSources.py import-store `
  --db D:\KOA_MEDIATHEQUE\01_DB\koa_mediatheque.sqlite `
  --storage-root D:\KOA_MEDIATHEQUE\02_STORAGE `
  --store D:\...\external-source-library\source-store.json
python 05_TOOLS/KoaKristalSources.py verify --db D:\KOA_MEDIATHEQUE\01_DB\koa_mediatheque.sqlite
```

Les commandes gardent leur nom pour compatibilité, mais leur destination est le catalogue générique.

## Bindings vers Kristal

La Médiathèque peut toujours exporter des pointeurs :

```text
koa-media://version/<version_uuid>
```

Le manifest conserve le `source_id` attendu par le Kristal, mais les octets restent sous autorité Médiathèque.

## GUI

La page **Sources** affiche désormais tous les consommateurs et permet de filtrer par `consumer_system` / `consumer_instance`. Kristal n'est qu'un consommateur possible parmi d'autres.

## Règle d'autorité

```text
Médiathèque  = source_uuid / snapshot_uuid / version_uuid / SHA-256 / octets
Kristal      = identité et relations sémantiques
EncyK        = découverte / acquisition / extraction / handoff
DaaT         = admission / mapping de contrat vers Kristal
```

Ces identités sont reliables mais non substituables.
