# Dictionary Harvester — code C: / données D: — correctif v0.1.1

## Emplacement impératif

Le ZIP d'overlay s'extrait **dans la racine du dépôt EncyKlopedia SUR C:**, là où se trouve `package.json`. **Ne jamais extraire ce ZIP sur `D:\EncyKlopedia`.** Le chemin exact du dépôt C: n'est pas établi par le snapshot; utiliser l'emplacement réel de ton clone du moteur.

Le collecteur est un outil de préparation privé, sans route HTTP. Son code reste sous `tools/dictionary-harvester/`; `src/server.mjs` demeure inchangé. Skope/EncyK reste responsable de l'acquisition institutionnelle, Médiathèque kOA de la conservation durable, diK de la curation lexicale. Ce petit collecteur ne remplace aucun de ces composants.

Les données sont stockées exclusivement dans le lac de données existant :

```text
D:\EncyKlopedia\
  10_sources\lexical\                  # archives lexicales existantes, intouchées
    wikidata\lexemes\dumps\current\latest-lexemes.json.bz2  # déjà présent selon index du 2026-11-04
    wiktionary\kaikki\enwiktionary\Albanian\...jsonl       # déjà présent selon index
    harvester\raw\<source>\<snapshot>\...  # NOUVELLES captures uniquement
  20_evidence\                       # preuves existantes, non modifiées ici
  30_working\lexical\harvester\      # observations candidates du collecteur
  50_mediatheque\                    # catalogues existants, non modifiés ici
```

Le manifest `capture.json` d'une nouvelle acquisition est conservé **à côté du fichier source**. Il n'est pas automatiquement promu dans `20_evidence` ni dans `50_mediatheque`. Le statut reste `unreviewed` et `public_release=false`.

## Installation

1. Conserver le ZIP précédent non installé : il est **remplacé intégralement** par cet overlay corrigé.
2. Sauvegarder le dépôt **C:** EncyKlopedia.
3. Extraire **l'overlay v0.1.1 dans la racine du dépôt C:**, accepter les remplacements.
4. Ne déplacer ni effacer aucun fichier de `D:\EncyKlopedia`.
5. Exécuter `Verify_Dictionary_Harvester.cmd` depuis C:.

Le script utilise `D:\EncyKlopedia` par défaut sous Windows. Si la racine diffère, définir explicitement `ENCYK_DATA_ROOT` ou passer `--data-root`. Les commandes qui écrivent vérifient que `10_sources/lexical`, `20_evidence`, `30_working` et `50_mediatheque` existent avant toute création : une faute de chemin ne créera pas un faux nouveau dépôt de données.

## Exemples (depuis la racine du dépôt C:)

```powershell
node tools/dictionary-harvester/cli.mjs layout
node tools/dictionary-harvester/cli.mjs inventory-existing
node tools/dictionary-harvester/cli.mjs sources
node tools/dictionary-harvester/cli.mjs status
```

`inventory-existing` est **en lecture seule** : il répertorie les `.jsonl`, `.bz2` et `.gz` dans `D:\EncyKlopedia\10_sources\lexical` sans les télécharger, les déplacer ou les valider. Les fichiers existants ne sont **pas** des captures effectuées par le harvester : `status` ne les comptabilise donc pas.

Pour exploiter le Kaikki albanais **déjà présent** sans le télécharger une seconde fois :

```powershell
node tools/dictionary-harvester/cli.mjs ingest-kaikki --source kaikki-en --snapshot albanian-existing-20261104 --file "D:\EncyKlopedia\10_sources\lexical\wiktionary\kaikki\enwiktionary\Albanian\kaikki.org-dictionary-Albanian.jsonl" --limit 1000
```

La sortie candidate est créée automatiquement sous `D:\EncyKlopedia\30_working\lexical\harvester\kaikki\kaikki-en\albanian-existing-20261104.jsonl`. Cette observation doit rester non publiée et l'origine du fichier doit être vérifiée séparément; `--source` indique seulement le profil de parseur sélectionné. Le dump Wikidata `latest-lexemes.json.bz2` n'est pas accepté par le parseur Kaikki : utiliser diK pour les lexèmes Wikidata L/F/S.

Pour un **nouveau** petit téléchargement explicite (IANA, ce n'est pas un dictionnaire) :

```powershell
node tools/dictionary-harvester/cli.mjs fetch --source iana-subtags --snapshot iana-20261104
```

Cela crée `D:\EncyKlopedia\10_sources\lexical\harvester\raw\iana-subtags\iana-20261104\registry.txt` et un `capture.json`. Aucun téléchargement, déménagement ni publication automatique n'est déclenché à l'installation ou aux tests. Les conditions de licence des sources externes doivent être vérifiées individuellement.

## Limitations

- Aucun scraping HTML général; seules les sources listées et explicitement activées peuvent être téléchargées.
- Pas de reprise partielle dans cette version et pas de vérification des énormes archives déjà présentes sans action spécifique.
- `inventory-existing` ne prouve ni intégrité ni droits de réutilisation.
- Pas de décision de crosswalk exactMatch, pas de création KQ/KP, pas de publication.
- Les ports/public routes du lecteur ne changent pas.

## Indexation massive candidate v0.2 (nouveau)

Le module reprend automatiquement les dictionnaires déjà téléchargés dans le lac D: et produit une base SQLite et des rapports **sans déplacer les archives**. Voir [guide d'indexation mondiale](INDEXATION_LEXICALE_MONDE.md). Depuis la racine C:, lancer `Start_Indexation_Dictionnaires.cmd`, ou `node tools/dictionary-harvester/cli.mjs index-run`.
