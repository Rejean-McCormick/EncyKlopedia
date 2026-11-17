# Changelog

## 0.5.1 - 2026-10-27

- Synchronize the **exact** EncyK source-evidence-handoff v2 schema from Skope unified EncyK 0.14.0 (17 pinned supported producer versions, including historical 0.12.0).
- Add `--instance-root` to target one existing SQLite/filesystem Médiathèque instance, refusing mixed instance-root/DB/storage arguments; the legacy explicit paths remain available.
- Validate current Skope producer version, unknown-version refusal, instance isolation and replay idempotence in new regression tests.
- No publication authorization, canonical Kristal writes, actual Wikidata data import, data migration, or Moodle instance changes.


## 0.5.0 - 2026-10-03

- Enrichit le bootstrap UCKK avec 58 références GitHub publiques dérivées de `Kristal-kOA-Ecosystem v0.6.3`, dont 12 avec commit explicitement épinglé.
- Ajoute la collection Moodle `Référentiels GitHub — écosystème kOA` et l’import `--mode=repositories`.
- Expose les URLs GitHub comme médias `external_reference` publics, avec UUID déterministes, provenance, boundary, rôle et métadonnées d’observation.
- Ajoute un badge/bouton GitHub direct sur les cartes média.
- Corrige `media_source` pour traduire les anciens alias riches (`creator`, `ownership`, `licence`, etc.) vers le schéma réellement installé au lieu d’échouer sur des colonnes absentes.
- Le bootstrap UCKK passe de 175 à 233 objets : 111 Kristals + 64 médias Korpus + 58 références GitHub.
- Rétablit la Médiathèque comme autorité consumer-neutral des sources avec le schéma v4 `source_*`; les anciennes tables source `kristal_*` sont conservées uniquement pour migration/compatibilité.
- Les nouveaux fichiers source utilisent `02_STORAGE/source_files/`; les anciens `kristal_source_files` restent lisibles sans migration destructive.
- Remplace la page GUI « Sources Kristal » par une page `Sources` filtrable par système/instance consommateur.

## 0.4.0 - 2026-10-03

- Ajoute le bootstrap UCKK : 111 stubs Kristal + inventaire de 64 médias Korpus.
- Ajoute `uckkarchive_kartifact` et `uckkarchive_kversion` pour stocker les Kristals canoniques sans réutiliser l’ancien objet `uckkarchive_kristal`.
- Ajoute le type média `kristal_artifact`; les octets passent par la File API et les versions média existantes.
- Préserve `kristal_ref` comme identité sémantique externe; les UUID de Médiathèque restent des identités de stockage/catalogue distinctes.
- Ajoute `import_uckk_bootstrap.php` pour importer hiérarchie Kristal et Korpus dans la bibliothèque `uckk`.
- Aligne le contrat sur `kristal_state/6.0` et Kristal/Kristall `7.0.0-draft.3.2`.

## 0.3.0 - 2026-10-03

- Sépare explicitement l’Engine `mediatheque/` de toutes les instances de données.
- Une instance est désormais un dossier frère (`mediatheque-privee/`, `mediatheque-uckk/`, `mediatheque-universite-math/`, etc.).
- L’Engine ne contient aucune DB ni contenu runtime.
- Déplace l’intégration Moodle `mod_uckkarchive` sous `mediatheque/integrations/moodle/` comme adapter partagé.
- Les instances UCKK et Université Math sélectionnent le même adapter par manifeste, sans embarquer l’Engine.
- Les instances locales lancent l’Engine en lui passant explicitement leur propre dossier comme `KOA_CONTENT_ROOT`.

## 0.2.2 - 2026-10-03

- Rend les deux surfaces Médiathèque explicites au niveau workspace : `mediatheque-local/` et `mediatheque-uckk/`.
- Place le contenu privé local directement à côté de l’application sous `mediatheque-local/content/`.
- Le défaut de `KOA_CONTENT_ROOT` devient `../content`.
- La Médiathèque UCKK reste une implémentation Moodle distincte (`mod_uckkarchive`).

## 0.2.1 — 2026-10-03

- Remplace la séparation artificielle « standalone » / « local privé » par une seule application.
- Ajoute le workspace adjacent `../content` comme racine canonique des données.
- Déplace les schémas SQL dans `schemas/sqlite/` côté application.
- Les lanceurs, la GUI et l'outil de workspace résolvent automatiquement le contenu adjacent.
- `KOA_CONTENT_ROOT` permet de déplacer le contenu sans dupliquer l'application.
- La Médiathèque UCKK reste une implémentation séparée.

## 0.2.0 — 2026-10-03

- Makes the standalone distribution explicitly data-empty.
- Defines the local private workspace as configuration/data, not a fork.
- Adds `config.private.example.toml` and `KoaLocalWorkspace.py`.
- Adds private-by-default reference indexing for local documents.
- Adds a local Kristal corpus catalog with version/hash tracking.
- Keeps UCKK Médiathèque as a separate Moodle implementation.
- Removes the shipped XLSX runtime export from the repository.
- Adds schema `006_kristal_catalog.sql`; no UCKK publication tables are created locally.
