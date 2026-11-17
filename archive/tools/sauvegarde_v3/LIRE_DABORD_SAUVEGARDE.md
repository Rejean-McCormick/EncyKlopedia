# EncyKlopedia — Sauvegarde **DES RÉSULTATS** (v3 — correction WAL/SHM)

Cet outil est **indépendant** des overlays logiciels et ne touche à aucune base d'origine. Il est conçu à partir du dépôt v31.9 et des chemins de la station connus au 15 novembre 2026. Il peut être extrait dans un dossier extérieur au dépôt (par exemple `E:\Outils\Sauvegarde_EncyKlopedia`).

## Correction v3 — erreur de vérification `-shm`

La v2 pouvait produire une **copie autonome du contenu** tout en conservant le *mode journal WAL* de la base SQLite source. En la relisant pour les contrôles, SQLite créait alors un fichier temporaire `-shm` dans le dossier de destination ; la validation stricte le rejetait comme « fichier supplémentaire non déclaré ». C'est le cas de la base `DECOUVERTE_ARTICLES_RELIES_V28.sqlite` signalé par le journal utilisateur.

La v3 conserve les mêmes cinq bases de résultats, les mêmes chemins, les exclusions et les contrôles. Elle :

1. Sauvegarde chaque **source en lecture seule** avec l'API SQLite `backup()`, en tenant compte d'un éventuel WAL.
2. Convertit **uniquement la copie** au mode `journal_mode=DELETE` avant sa validation, afin que les journaux temporaires soient intégrés/fermés et que le fichier `.sqlite` soit autonome.
3. Exige l'en-tête SQLite journal classique (version 1/1), contrôle le `quick_check` en mode strictement `immutable=1` sur la copie, puis SHA-256 et absence de fichiers non déclarés.
4. Refuse toujours les journaux `-wal` ou `-shm` résiduels, les copies divergentes et les fichiers inattendus. Aucun contournement de contrôle.

**Après l'échec de la v2 :** le répertoire `_INCOMPLETE_ENCYK_RESULTATS_...` n'est **pas** une sauvegarde validée. Refaire une nouvelle sauvegarde avec v3, vérifier `SUCCES`, puis supprimer manuellement l'ancien `_INCOMPLETE_` si vous le souhaitez. Il ne sera ni réparé automatiquement ni supprimé par l'outil.

## Contenu inclus par défaut

Uniquement les **bases SQLite portant les résultats et l'état durable** :

| Base | Utilité |
|---|---|
| `30_working/poste_chatgpt_v30/station_v30.sqlite` | 431 tâches importées (selon la station), décisions de revue, historique, mises à jour, file persistante |
| `30_working/production_kristals_v27/KRISTAL_CUMULATIF_PRIVE_V27.sqlite` | Connaissances privées et citations Kristal cumulées |
| `80_search_indexes/EncyKlopedia/catalogue_global_unesco_wikipedia_v25.sqlite` | Catalogue et décisions UNESCO importées |
| `30_working/decouverte_articles_relies_v28/DECOUVERTE_ARTICLES_RELIES_V28.sqlite` | Découvertes, preuves et progression des graines |
| `30_working/production_kristals_v27/FILE_PACKS_V27.sqlite` | Registre de suivi des articles déjà produits (si présent) |
| `30_working/qualification_multibranche_v31/qualification_multibranche_v31.sqlite` | Qualification multibranche (si présente) |
| `30_working/preuves_xml_cibles_v31/PREUVES_XML_CIBLES_V31.sqlite` | Vérifications ciblées documentées (si présentes) |

Une option distincte ajoute `80_search_indexes/EncyKlopedia/inventaire_categories_wikipedia_v26.sqlite`, index calculé d'environ 1,3 Gio dans les anciens relevés. C'est facultatif, car il est généralement reconstructible.

**Exclus, sans option pour les ajouter par erreur :** 110 Go de Wikipédia décompressé, dumps XML bruts, index directs du corpus Wikipédia, ZIP des packs, retours ChatGPT, deltas de production, code et dépôt source, anciens snapshots, exports intermédiaires, journaux transitoires `-wal`/`-shm`.

Cet outil n'est **pas** une sauvegarde intégrale capable de réinstaller le logiciel depuis zéro. Il conserve les résultats essentiels. Il faut conserver séparément le dépôt logiciel dans Git ou un snapshot de code et les corpus source nécessaires pour reconstituer les index. Les fichiers de réponse et packs en transit ne sont pas récupérables si une restauration survient pendant une vague active : sauvegarder de préférence entre deux vagues.

## Procédure Windows

1. **Avant de lancer un nouveau batch**, fermer complètement EncyKlopedia et tous ses producteurs/importateurs. Zéro poste occupé dans l'interface est favorable, mais ne remplace pas la fermeture des processus.
2. Décompresser le ZIP de l'outil dans un dossier hors de `C:\mycode\EncyKlopedia\EncyKlopedia` et hors de `D:\EncyKlopedia`.
3. Double-cliquer `SAUVEGARDER_ENCYKLOPEDIA.cmd`.
4. Choisir `1` (résultats uniquement), puis la destination (par défaut `D:\EncyKlopedia_SAUVEGARDES`). Préférer un disque externe distinct de `D:`.
5. Confirmer `OUI` après fermeture de tous les processus. Attendre le message `SUCCES` et la vérification SHA-256 + SQLite ; les dossiers `_INCOMPLETE_` ne sont **pas** des sauvegardes valides.
6. Copier le dossier `ENCYK_RESULTATS_...` sur un disque externe distinct et lancer `VERIFIER_SAUVEGARDE.cmd` pour vérifier son intégrité indépendamment.
7. Relancer EncyKlopedia, puis seulement ensuite démarrer la prochaine vague.

## Vérification et limites

- Capture SQLite via `sqlite3.Connection.backup`, lecture seule de la source ; les transactions WAL sont intégrées dans une base autonome de destination.
- Contrôle `PRAGMA quick_check` et SHA-256 de chaque base ; inventaire détaillé dans `MANIFEST_RESULTATS.json`.
- Les bases obligatoires (station, Kristal privé, catalogue et découverte) doivent être présentes, sinon le programme refuse de déclarer une sauvegarde réussie.
- Les bases optionnelles absentes sont énumérées dans le manifeste.
- Les bases SQLite sont cohérentes individuellement, **mais pas atomiquement entre elles** : la fermeture de la station et des producteurs est indispensable à une copie interbases cohérente.
- Aucune suppression, réinitialisation, import, canonisation ou publication.
- Pas de restauration automatique destructive. Pour restaurer, vérifier la sauvegarde, fermer tous les processus, protéger les fichiers existants puis restaurer chaque base selon `source_path` du manifeste. Les `-wal` et `-shm` de la sauvegarde sont volontairement absents.

En PowerShell avancé :

```powershell
python -I .\encyk_sauvegarde.py preflight --data-root 'D:\EncyKlopedia' --destination 'E:\Sauvegardes'
python -I .\encyk_sauvegarde.py backup --data-root 'D:\EncyKlopedia' --destination 'E:\Sauvegardes' --station-fermee
python -I .\encyk_sauvegarde.py verify --backup-dir 'E:\Sauvegardes\ENCYK_RESULTATS_...'
```
