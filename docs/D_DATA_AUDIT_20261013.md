# Inventaire D:\EncyKlopedia — audit reçu le 13 octobre 2026

Audit en lecture seule de 42 fichiers, zéro erreur de parcours signalée. Valeurs extraites de l'index fourni par l'utilisateur (non vérifiées directement sur le disque D:).

| Zone | Observations | Décision 0.13.4 |
|---|---|---|
| `10_sources` | Dump entités Wikidata 103 222 517 992 octets ; lexical Wikidata et Wiktionary | PROTÉGER |
| `30_working/wikidata` | `wikidata.compact.sqlite` 134 155 157 504 octets (124,94 Gio) | PROTÉGER ; vérifier `meta.complete` avant Skope |
| `30_working/wikidata-fast` | `qid-locator.bin` 2 264 725 264 octets, index bzip2 55 177 801 octets | PROTÉGER |
| `30_working/lexical` | Deux SQLite lexicales, fichier WAL/SHM inclus | PROTÉGER ; WAL/SHM jamais supprimés automatiquement |
| `20_ingest` | Snapshots, provenance, checkpoints, handoffs historiques ; environ 5,7 Mio | DÉPLACER vers `20_evidence` / `90_runtime`, dédupliquer l’ancienne copie `legacy-ingest` si SHA-256 identique |
| `40_kristal` | Un seul README historique de 201 octets | SUPPRIMER le README vérifié et les dossiers vides uniquement |
| `50_mediatheque` | Catalogue de 533 œuvres candidates ; fichier `.works.jsonl` 2 364 399 octets | DÉPLACER les candidats sous `20_evidence/mediatheque-candidates` ; admission kOA ultérieure indépendante |

Le checkpoint de septembre de l'index global est déclaré incomplet dans le fichier historique. Cela n'établit pas l'état actuel de `meta.complete` ; le cleaner ne finalise pas la base de 125 Gio.

## Ce que cet audit ne démontre pas

- L'état présent des fichiers au moment où le cleaner s'exécutera.
- L'admission canonique des sources vers Médiathèque kOA.
- La compatibilité des anciens handoffs vers Kristal v9/v10.
- La validité des chemins historiques internes après réorganisation ; les manifestes de provenance restent immuables.

Le cleaner 0.13.4 agit uniquement sur les 17 fichiers reconnus par empreinte et refuse les fichiers modifiés. Les données utiles sont déplacées directement, sans backup ; les fichiers inconnus restent en place.
