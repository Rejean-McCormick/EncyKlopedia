# UNESCO Educational Policy — v20 : déblocage de l'extraction Wikipédia EN

## Pourquoi

L'atlas documentaire v19 marche déjà sur les 20 000 pages explorées. Le lot éditorial 002 sélectionne 25 pages dont les textes ne sont pas disponibles dans les extractions antérieures. Le dump XML local `enwiki-latest-pages-articles-multistream.xml.bz2` existe d'après les étapes antérieures, mais son index officiel `...-multistream-index.txt(.bz2)` n'a pas été trouvé par v19.

La v20 apporte **le maillon manquant d'accès aux textes**, sans recréer l'atlas ni réimporter Wikipédia SQL :

1. Si l'index officiel existe à côté du XML, l'utiliser.
2. Sinon, lire une fois les flux indépendants BZip2 du XML, indexer l'offset compressé de chaque page en namespace 0 dans **un SQLite dérivé séparé**.
3. Sauvegarder une transaction/checkpoint après chaque flux compressé pour reprendre après fermeture, coupure ou arrêt.
4. Dès que les 25 pages demandées sont localisées, passer leurs offsets au **lecteur v19 déjà testé**, puis former le ZIP de recherche **uniquement si les 25 textes sont réellement extraits**.
5. Vérifier la SHA-256 de chaque texte et du ZIP; produire un reçu contenant les révisions XML, SQL et les éventuels écarts.

## Installation

Extraire le ZIP overlay **dans `C:\mycode`** en conservant les dossiers, fusion sans effacer les sources. Il ajoute des fichiers dans `EncyKlopedia\EncyKlopedia` et `EncyKlopedia\mediatheque-references`. Il ne remplace pas les programmes v19.

Exécuter :

```powershell
C:\mycode\EncyKlopedia\EncyKlopedia\LANCER_UNESCO_EXTRACTION_WIKIPEDIA_LOT_002_V20.cmd
```

En cas de source déplacée :

```powershell
C:\mycode\EncyKlopedia\EncyKlopedia\LANCER_UNESCO_EXTRACTION_WIKIPEDIA_LOT_002_V20.cmd --xml "D:\mon-dossier\enwiki-latest-pages-articles-multistream.xml.bz2"
```

En cas de fichier d'index officiel présent dans un autre dossier :

```powershell
C:\mycode\EncyKlopedia\EncyKlopedia\LANCER_UNESCO_EXTRACTION_WIKIPEDIA_LOT_002_V20.cmd --official-index "D:\mon-dossier\enwiki-latest-pages-articles-multistream-index.txt.bz2"
```

**Aucune connexion Internet ni installation Python supplémentaire** n'est requise. Fonctionne avec la bibliothèque standard de Python 3.11–3.14.

## Emplacements

- XML : `D:\EncyKlopedia\10_sources\wikipedia\enwiki\2026-10\enwiki-latest-pages-articles-multistream.xml.bz2` (lecture seule).
- Atlas v19 : `D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41\atlas_documentaire_v19` (lecture seule).
- Nouvel index local optionnel : `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_multistream_offsets_v20.sqlite`. **Ce n'est PAS `wikipedia_en.sqlite`.**
- Lot final : `D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41\atlas_documentaire_v19_LOT_002_CHATGPT.zip`.
- Reçu d'intégrité : le même nom, suffixé `.v20.json`.
- Si l'index est incomplet : `...LOT_002_CHATGPT.zip.v20_status.json`, aucun ZIP final incomplet.

## Gestion d'une longue première construction d'index

Sans l'index officiel, le logiciel **doit parcourir et décompresser séquentiellement les flux** du très gros dump local; aucun algorithme ne peut deviner des offsets absents. Cela peut coûter de nombreuses opérations disque et CPU, même si les pages ne sont pas toutes conservées en mémoire. Des messages `V20_INDEX_PROGRESS` affichent l'avancement. Le nouveau SQLite dérivé est extensible et réutilisable pour d'autres lots sans rescanner les flux déjà indexés. Arrêter avec `Ctrl+C` puis relancer **la même commande**; chaque flux terminé a son checkpoint. La signature stockée utilise la taille, date de modification et SHA-256 des 1er/dernier Mio, et **ne prouve pas l'identité intégrale du fichier**.

Pour un premier essai limité :

```powershell
C:\mycode\EncyKlopedia\EncyKlopedia\LANCER_UNESCO_EXTRACTION_WIKIPEDIA_LOT_002_V20.cmd --max-streams 500
```

Puis relancer sans l'option pour continuer. Le ZIP ne sera créé **qu'avec les 25 textes**. Si une page ne figure pas dans le XML, la v20 signale son ID et refuse d'annoncer un succès. Si un article dépasse la limite de 5 Mio du pack v19, le résultat est également incomplet et signalé.

## Frontières

- La sélection de 25 pages vient de l'analyse humaine assistée de l'atlas 001 et reste éditoriale, sans valeur canonique.
- Les 41 concepts UNESCO et leurs KQ restent **provisoires**; pas de nouveau KQ, KP, KA ou KS.
- Le graphe des liens Wikipédia reste **documentaire**; les liens ne prouvent pas les assertions.
- Les révisions HTML/XML/Wikidata doivent être distinguées. Le reçu indique les révisions XML qui divergent de la révision SQL de l'atlas.
- Réutilisation des textes Wikipédia : attribution, révision et obligations **CC BY-SA** avant toute publication.
- Aucun push GitHub, aucune réalisation GF ou publication d'articles.

## Diagnostic/audit

```powershell
C:\mycode\EncyKlopedia\EncyKlopedia\DIAGNOSTIC_UNESCO_SOURCE_XML_V20.cmd
C:\mycode\EncyKlopedia\EncyKlopedia\AUDITER_UNESCO_EXTRACTION_WIKIPEDIA_LOT_002_V20.cmd
```

Les tests sont dans `EncyKlopedia\mediatheque-references\tests\test_unesco_multistream_v20.py` et ne touchent pas aux données de `D:`.

## Lots suivants, sans nouvel overlay

Le moteur permet aussi de produire un lot 003, 004, etc. à partir d'un **nouveau CSV sélectionné dans l'atlas v19**, avec les champs `selected,page_id,title,revision_id,qid` (et, si utile, les colonnes de classement). Ne jamais modifier la sélection épinglée du lot 002. Pour un autre lot :

```powershell
py -3 "C:\mycode\EncyKlopedia\mediatheque-references\tools\wiki\atlas\extraire_lots_v20.py" build --future-lot --selection "D:\mon-dossier\selection_LOT_003.csv" --output "D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41\atlas_documentaire_v19_LOT_003_CHATGPT.zip"
```

De 1 à 100 pages sélectionnées sont admises dans ce mode. Le CSV doit respecter **les IDs, titres, QID et révisions de l'atlas**; les sources hors atlas sont refusées. Le SQLite dérivé des offsets est réutilisé en lecture/reprise, sans tout recommencer. Chaque ZIP possède un reçu d'intégrité propre. Pour un nouveau sous-graphe, produire d'abord un **nouvel atlas** via v19 : une découverte ne doit pas inventer les liens entre pages.

Les propositions ChatGPT issues de ces ZIP continuent à entrer via le récepteur privé v19, **sans écriture canonique automatique**. La qualification de chaque affirmation et de chaque source reste distincte.
