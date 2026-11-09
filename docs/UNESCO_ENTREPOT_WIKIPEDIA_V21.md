# EncyKlopedia / Wikipédia EN — entrepôt à accès direct v21

## Objectif

Préserver l'archive Wikimedia d'origine (`.xml.bz2`) et le XML **déjà décompressé** de **109,75 Gio** sur le SSD Crucial X10 Pro `D:`. Construire **un seul index dérivé** des positions de pages : `(page_id, byte_offset, byte_length, namespace, title, revision_id, is_redirect)`.

Le XML contient les wikitextes. Le SQLite existant `wikipedia_en.sqlite` contient déjà pages, QID et liens. L'index direct v21 ne duplique **aucun wikitexte**. La Médiathèque reste responsable de la provenance documentaire et des enregistrements admis; l'outil écrit seulement un **catalogue candidat**, sans import dans sa base. Kristal reste inchangé.

## Installation

Décompresser le ZIP dans `C:\mycode`, en conservant les répertoires. Prérequis : v19 et v20 déjà installés, Python 3.11+, Windows PowerShell 7, XML décompressé existant. L'overlay est **additif** : pas de remplacement des scripts v19/v20.

Exécuter dans PowerShell :

```powershell
C:\mycode\EncyKlopedia\EncyKlopedia\LANCER_WIKIPEDIA_ENTREPOT_V21.cmd
```

Le lanceur vérifie l'intégrité de son propre code, vérifie le XML, indexe toutes les pages (avec transactions par paquets), contrôle l'index, écrit le **candidat de source Médiathèque**, puis extrait les **25 articles** du lot 002.

Pour voir la progression sauvegardée :

```powershell
C:\mycode\EncyKlopedia\EncyKlopedia\AUDITER_WIKIPEDIA_ENTREPOT_V21.cmd
```

En cas d'arrêt volontaire : `Ctrl+C`, puis **relancer le même lanceur**. Le dernier paquet d'index non validé peut être relu; les autres sont conservés. Ne jamais lancer deux indexeurs simultanés : un verrou système empêche cela. Le fichier `.writer.lock` peut subsister, mais n'empêche pas une reprise si aucun processus n'en détient le verrou.

## Répertoires et fichiers

| Rôle | Chemin |
|---|---|
| XML source lecture seule | `D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml` |
| Archive `.bz2` source | `D:\EncyKlopedia\10_sources\wikipedia\enwiki\2026-10\enwiki-latest-pages-articles-multistream.xml.bz2` |
| Index direct v21 (créé) | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite` |
| Candidat de provenance (créé) | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.source-candidate.json` |
| Graphe de liens SQL v19, **inchangé** | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite` |
| Index comprimé v20 partiel, **inchangé** | `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_multistream_offsets_v20.sqlite` |
| Lot 002 v21 | `D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41\atlas_documentaire_v19_LOT_002_CHATGPT_V21.zip` |

## Fonctionnement et limites

- **Première indexation :** lecture séquentielle du XML complet, donc coûteuse mais effectuée une seule fois pour cette version exacte du dump.
- **Après l'indexation :** récupération de chaque article par `seek(byte_offset)` et lecture de `byte_length` octets. Aucun scan global ni décompression BZip2.
- **Source :** identifiée par chemin absolu, taille, date de modification et SHA-256 des **premier et dernier Mio seulement**. C'est un contrôle de cohérence, **pas une empreinte cryptographique intégrale du XML**.
- **Reprise :** checkpoint et enregistrements validés dans la même transaction SQLite; en cas d'interruption, le travail validé est réutilisé.
- **Intégrité :** contrôle d'échantillons d'articles à leurs offsets exacts et refus si les métadonnées du XML divergent.
- **Lot 002 :** les 25 page_id de la sélection existante sont obligatoires; la version v21 **ne produit aucun ZIP final si un texte manque**, si une page est une redirection ou si un texte dépasse la limite de sécurité de 5 Mio.
- **Versions :** les décalages de révision entre la base SQL/atlas et le XML sont **signalés**, pas effacés. Les textes restent privés et requièrent attribution Wikipédia et respect des licences applicables.
- **Écriture :** la base de provenance Médiathèque, la base des liens, les fichiers XML et tous les Kristals sont laissés inchangés. Le catalogue candidat ne prétend pas être un `source_registry` admis.
- **Sécurité :** source `XML` lu en mode binaire (`rb`); base de liens jamais ouverte dans l'indexeur; sortie ZIP versionnée, vérifiée avec reçu `.v21.json`.
- **Capacité :** l'index et son journal WAL exigent de l'espace supplémentaire sur D:. Le lancement à grande échelle et sa performance restent à valider sur le vrai SSD.

## Commandes avancées (directement en PowerShell)

```powershell
$base = 'C:\mycode\EncyKlopedia\mediatheque-references\tools\wiki\atlas'
python "$base\index_xml_v21.py" status
python "$base\index_xml_v21.py" lookup --page-id 2287044
python "$base\index_xml_v21.py" audit --require-complete
python "$base\extraire_lots_xml_v21.py" audit
```

Pour un autre lot, préparer un CSV de **1 à 100 pages** avec `selected,page_id,title,revision_id,qid`, où les pages sont présentes dans l'atlas v19, puis :

```powershell
C:\mycode\EncyKlopedia\EncyKlopedia\EXTRAIRE_UNESCO_LOT_LIBRE_ENTREPOT_V21.cmd "D:\chemin\selection_003.csv" "D:\chemin\LOT_003_CHATGPT.zip"
```

Chaque nouvelle version de dump Wikimedia doit avoir **un nouvel index**, pas une écriture dans la base v21 existante. Si on veut un index texte intégral (FTS) plus tard, le créer dans une **nouvelle couche dérivée**, séparée du registre des sources et du Kristal.
