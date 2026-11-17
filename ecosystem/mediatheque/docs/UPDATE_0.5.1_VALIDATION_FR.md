# Médiathèque Engine 0.5.1 — Mise à jour EncyK 0.14 / Skope 1.0 RC1

## Constat prouvé

Le snapshot moteur `znapshot_mediatheque_10271013.zip` embarquait encore une copie
du schéma EncyK `encyk.source-evidence-handoff/2.0.0` limitée au producteur
`0.12.0`. Le snapshot actuel `znapshot_Skope_10270842.zip` possède EncyK
`0.14.0`, qui émet le même contrat v2 avec une énumération de versions étendue.

## Corrections

- Schéma consommateur synchronisé **octet pour octet** au schéma producteur
  d'EncyK 0.14 (SHA-256 `90086656ea04e2bc012dda5bd95d8ff7b075bb08d1a7bd580fd339d50a0a2428`).
- Version de l'Engine portée à `0.5.1` ; aucune migration de données.
- Nouvel argument facultatif `--instance-root` pour choisir explicitement une
  instance privée locale SQLite. La base et le stockage viennent du **même** dossier
  d'instance. Combiner cet argument avec `--db` ou `--storage` est refusé.
- Ancien parcours `--db` + `--storage` conservé.
- Nouveaux tests du producteur 0.14, version inconnue, isolement de deux
  instances et idempotence d'import.

## Validation exécutée le 2026-10-27

- `python -m pytest -q tests/python -k 'not uckk_bootstrap'` : **240 tests réussis**,
  **3 tests ignorés par sélection** car ils nécessitent une instance UCKK soeur
  avec son bootstrap et son catalogue (non contenus dans ce snapshot moteur).
- Tests handoff et source-catalog ciblés : **14 réussis**.
- Correspondance SHA-256 du schéma avec le producteur actuel : **identique**.
- Test croisé avec le **vrai script** `07_prepare_source_handoff.py` extrait de
  Skope EncyK 0.14 sur **données entièrement synthétiques** : génération,
  `plan_valid`, `accepted`, puis `already_accepted` (réimport idempotent).
- Aucun test exécuté sur les dumps Wikidata ou instances Windows de l'opérateur,
  sur Moodle UCKK, ni sur données réelles. Le handoff n'est pas une signature
  d'authenticité; l'opérateur doit approuver la racine de preuves.

## Responsabilités préservées

- Médiathèque : autorités de sources, snapshots, représentations, empreintes et
  droits physiques, UUID locaux durables.
- Skope/EncyK : acquisition et production du manifeste.
- Kristal : sémantique, KQ/KP/KA/KS et engagement canonique.
- Manager : inventaire des workspaces Kristal, **hors de ce transfert**.

Les droits importés restent privés; aucune publication et aucun enregistrement
Kristal canonique ne sont ajoutés. Pas de modification d'une instance, d'une base,
de GitHub ou d'un dossier `D:`.

## Installation sûre

1. Sauvegarder le dossier de code du moteur `mediatheque`.
2. Extraire ce ZIP **à la racine du moteur partagé**, pas dans une instance
   (`mediatheque-privee`, `mediatheque-uckk`, `mediatheque-math`).
3. Préserver `.git` et les configurations locales; ne pas écraser les données
   d'instance. Vérifier `py -3 05_TOOLS/ImportEncyKHandoff.py --help`.
4. Effectuer d'abord un précontrôle sans `--accept` sur un handoff réel. Ne
   sélectionner l'instance qu'après revue des preuves.

Voir `docs/27_skope_encyk014_instance_import.md` pour les exemples de commande.
