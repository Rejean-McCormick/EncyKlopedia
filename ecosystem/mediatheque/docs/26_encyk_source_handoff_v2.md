# EncyKlopedia 0.12 → Médiathèque kOA 0.5 — handoff d'évidence v2

**Statut : adaptateur local candidat, non déployé**. Source de schéma immuable : `00_system/contracts/source-evidence-handoff/2.0.0/schema.json` du snapshot EncyK. Une copie **inchangée** est incluse dans `koa_mediatheque/contracts/encyk_source_handoff_2/schema.json` pour valider les imports hors-ligne.

## Responsabilités

- **EncyKlopedia** choisit scope, acquiert, extrait et prépare un handoff immuable `encyk.source-evidence-handoff/2.0.0`.
- **Médiathèque** attribue les UUID persistants, vérifie les octets, garde Source, Snapshot, Representation, library row et locator `koa-media://version/...`.
- **Kristal/Kristall** garde exclusivement les identités et engagements sémantiques. Cet import **ne crée pas de Referent Registry, KQ, KP, KA, KS ou Mesh**.
- `encyklopedia.corpus-harvest-handoff/1.0.0` (carte kOA documentaire historique) **n'est pas accepté** et n'est pas supposé convertible sans adaptateur qualifié.

## Correspondance champ par champ

| EncyK v2 | Médiathèque | Sémantique |
|---|---|---|
| `handoff_id` | `encyk_handoff_receipts.handoff_id`, `source_import_log.import_uuid` | Idempotence, preuve de livraison ; hash EncyK vérifié |
| `producer`, `consumer`, `contract`, `schema_version` | Validation du schéma v2 copié inchangé | Aucun downgrade implicite |
| `scope_key` | `source_consumer_registry.consumer_instance`, `source_bindings.consumer_instance`, métadonnées Snapshot | Périmètre local de travail EncyK, pas une autorité de Source |
| `snapshot_id` | `source_snapshots.snapshot_id = encyk:{scope_key}:{snapshot_id}` | Namespace propre au consommateur ; original conservé dans metadata |
| `source_descriptor.canonical_url` | `source_registry.canonical_url[_key]` | Déduplication par URL canonique, Médiathèque choisit `source_uuid` |
| `source_descriptor.external_source_id` | `source_bindings.external_source_id` | Identifiant externe, non `source_uuid` |
| `source_descriptor.title/publisher/source_kind/source_family` | `source_registry` | Métadonnées de description, pas canon sémantique |
| `created_at` | `source_snapshots.retrieved_at` pour le handoff | Horodatage du manifeste, **non preuve de date d'acquisition du dump** ; `source_snapshot` conservé |
| `source_snapshot` | `source_snapshots.metadata_json` | Métadonnées originales préservées |
| `scope_config` et `files[*]` | `source_representations`, `library_rows`, octets sous `source_files/` | `role` devient `representation_kind`, `path` devient `original_relative_path`; taille/SHA vérifiés |
| `invariants` | Validés non vides dans le manifeste, non interprétés | Aucun ajout d'autorité sémantique |
| Droits/accès | `library_rows.visibility=private`, `export_to_public=no`, `rights_status=unknown` | Source sans licence explicite : aucun droit de publication inféré |
| Acceptation | `encyk_handoff_receipts.receipt_json` | Reçu local, JSON ; référence les UUID, SHA-256, localisateurs physiques |

## Commandes locales (Windows/Python >=3.11)

Préparer les dossiers EncyK et Médiathèque dans un contexte **privé**. L'application Médiathèque doit être installée avec ses dépendances Python, notamment `jsonschema`. La base SQLite Médiathèque doit être initialisée.

```powershell
# Vérification seulement, zéro écriture
python 05_TOOLS/ImportEncyKHandoff.py --handoff "C:\EncyK\20_evidence\handoffs\mediatheque\pilot\handoff-xxxxxxxxxxxxxxxxxxxx.json" --evidence-root "C:\EncyK"

# Acceptation explicite en stockage privé, après plan et revue des fichiers
python 05_TOOLS/ImportEncyKHandoff.py --accept --handoff "C:\EncyK\20_evidence\handoffs\mediatheque\pilot\handoff-xxxxxxxxxxxxxxxxxxxx.json" --evidence-root "C:\EncyK" --db "C:\Mediatheque\01_DB\koa_mediatheque.sqlite" --storage "C:\Mediatheque\02_STORAGE"
```

Option `--receipt-out chemin.json` : export local facultatif du résultat, **y compris un refus**. Un refus n’est pas inséré dans les tables de source ; ne pas confondre une tentative rejetée et une acquisition acceptée. Le stdout/stderr est également JSON.

**Plan** : schéma Draft 2020-12, digest de `handoff_id`, fichiers attendus, unicité des rôles/chemins, absence de traversal/symlinks, SHA-256 et tailles de *toutes* les pièces. **Accept** : prévalidation, relecture du contenu copié, transaction SQLite unique pour les écritures du handoff, reçu et localisateurs privés. Une réimportation avec même identité vérifie également l'intégrité du stockage avant `already_accepted`.

## Limites et précautions

- Aucun handoff **réel** n'est contenu dans le snapshot EncyK fourni : les tests utilisent une fixture synthétique construite selon le schéma et le calcul exact du producteur. À tester ensuite sur un véritable handoff EncyK.
- `handoff_id` est un identifiant dérivé d'un hash non signé. La vérification établit une cohérence des données, **pas l'authentification de l'émetteur**. Le dossier importé doit être approuvé/trusté par l'opérateur local.
- Le précontrôle et la copie ne constituent pas une transaction unique au niveau du système de fichiers : après crash du processus, des fichiers orphelins non publics peuvent exister, à examiner avant nettoyage. Un échec Python intercepté annule la transaction DB et nettoie les nouveaux fichiers copiés.
- Aucun réseau, aucun changement GitHub, aucune opération de publication et aucune identité Kristal.
- Le format de reçu Médiathèque `koa.encyk-source-handoff-receipt/1.0.0` est une **extension proposée côté consommateur**, non une version de contrat déjà acceptée par EncyK. Il reste à faire accepter le reçu par le producteur et à tester le cycle réel de confirmation.

## 2026-10-27 — EncyK 0.14.0

This document originally described the EncyK 0.12.0 baseline. Current producer
compatibility and instance selection are documented in `27_skope_encyk014_instance_import.md`.
