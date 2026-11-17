# Kristal UNESCO Factory 1.6 — Lecteur Wikidata BZIP2 isolé

## Incident corrigé

RUN de référence : `RUN-20261103-083758-42cf03`. Les 88 kristals v9, 88 volumes Spek, 4 500 notices UNESCO et 9 000 plans discursifs ont été construits, MAIS les faits complets Wikidata étaient absents (`full_entities=0`, `wikidata_statements=0`). Le dump local EncyK est en `.json.bz2`, avec index Skope, et le Python 3.14 utilisé par la Fabrique ne possède pas de roue binaire `indexed_bzip2`.

La v1.6 sépare le lecteur BZIP2 du Python de la Fabrique :

1. Réutilise **en lecture seule** les index Skope déjà présents : `qid-locator.bin` et `compression.bz2blocks.pkl` (aucun scan intégral, aucun réindexage).
2. Détecte un CPython 3.11–3.13 déjà installé. Sinon, utilise `uv` pour télécharger **dans `C:\mycode\Kristal\.factory_runtime\wikidata`** un Python 3.13 géré, sans modifier l'installation système. La première fois, l'accès réseau est requis. `uv` est installé au besoin dans la venv courante uniquement.
3. Installe `indexed_bzip2==1.7.0` (roue binaire) dans une venv de lecture **distincte et privée**. Aucune tentative d'installation de cette dépendance incompatible dans Python 3.14.
4. Lance `wikidata_reader_worker.py` dans cet environnement pour extraire exclusivement les QID uniques P3916 et vérifie chaque QID trouvé. Une entrée corrompue est rejetée.
5. Transmet le résultat à `wikidata_full.py` pour enregistrer **faits, qualificatifs, références, entités brutes** et provenance originale sans modifier les kristals canoniques. Le résultat s'affiche dans le bouton « Ouvrir faits WD » et `reader_runtime.json` s'ouvre par « Diagnostic WD ».

## Interface

Toujours **TOUT CONSTRUIRE + VALIDER**. Nouveau bouton « Diagnostic WD » ouvrant `02_WIKIDATA/FAITS_COMPLETS/reader_runtime.json`; le journal détaillé de l'étape est accessible par arbre et par « Copier log ». Répartition des boutons sur deux rangées pour garder leur accès sur écran Windows.

Les RUN précédents et les sources ne sont pas modifiés. La v1.6 conserve la composition rhétorique de Spek vNext et 62 templates.

## Cas d'échec documentés

- Index Skope absent / incompatible / non importable : pas de scan séquentiel automatique du dump Wikidata, rapport `FAITS COMPLETS NON IMPORTÉS` avec diagnostic spécifique.
- Téléchargement Python ou bibliothèque bloqué : l'étape faits complets s'arrête avec un avertissement, mais UNESCO/Kristals/Spek continuent sans feindre d'avoir importé les déclarations.
- Index qui retourne un autre QID : la fiche est rejetée, jamais reliée au mauvais concept.
- Les 134 correspondances P3916 ambiguës et 77 manquantes de ton dernier RUN **restent à réviser**. L'import vise seulement les candidats uniques, et ne fait aucune promotion canonique.
- Aucune réalisation GF/PGF qualifiée, aucun article encyclopédique scientifique approuvé, aucune publication automatique.

## Validation

`python -m unittest discover -s tests -v`: **16/16 PASS** (12 tests hérités + 4 tests ciblés du lecteur et de la provenance). Deux tests E2E intègrent le véritable Authoring Kit v9 et Spek. Test ciblé sur un dump synthétique non compressé et un localisateur factice; transfert BZIP2 simulé pour vérifier la provenance. **La combinaison Windows + vrai `.bz2` + vrai bloc-index Skope devra être confirmée par le prochain RUN utilisateur**. Aucun test ne prétend avoir lu ton dump local dans cet environnement de développement.
