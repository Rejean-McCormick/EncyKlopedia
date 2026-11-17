# 25 — Autorité commune des sources

## Décision

**Médiathèque kOA est l'autorité persistante commune des sources, snapshots et représentations physiques.**

Elle possède :

```text
source_uuid
snapshot_uuid
version_uuid
SHA-256 / taille / MIME
storage locator
provenance physique
accès / restrictions / droits
```

Elle ne possède pas la signification épistémique produite par Kristal/Kristall.

## Modèle v4

```text
source_consumer_registry
  └── système consommateur : kristal, encyk, etc.

source_registry
  └── identité logique partagée d'une source

source_bindings
  └── identifiant/classification propres à un consommateur

source_snapshots
  └── acquisition datée

source_representations
  └── fichiers du snapshot
         │
         ▼
     library_rows
```

### Identités distinctes

```text
external source id
    != source_uuid
    != snapshot_uuid
    != version_uuid
    != kristal_ref
    != KQ/KP/KA/KS
```

## GitHub

Un dépôt GitHub peut être enregistré de deux façons distinctes :

1. **référence externe navigable** : URL GitHub, rôle/boundary, provenance de l'observation;
2. **snapshot immuable** : fichiers/octets importés séparément avec SHA-256.

Une URL GitHub seule n'est jamais présentée comme un snapshot immuable. Un commit épinglé peut renforcer la référence, mais les octets ne sont considérés détenus par Médiathèque qu'après import physique.

## Frontières

- **EncyK** découvre/acquiert/extrait puis remet les faits de source à Médiathèque.
- **Kristal/Kristall** référence les sources et possède l'identité sémantique.
- **DaaT** ne stocke pas les sources; il mappe des contrats vers Kristal.
- **Interaction Kernel** transporte les références sans transférer leur ownership.
- **Univers-Cité/Moodle** consomme les Kristals et médias publiés; il ne redéfinit pas leur identité.

## Compatibilité

Le schéma v4 migre non destructivement les anciennes tables source `kristal_*` vers `source_*`. Les anciennes tables restent présentes afin de lire les installations antérieures, mais les nouveaux imports source utilisent `source_files` et le catalogue générique.
