# Catalogue global EncyKlopedia v25 — Architecture UNESCO × Wikipédia

## Objet et limites

Le **catalogue** sert à décider *quels articles traiter* et *dans quelles familles de sens les ranger*. Ce n'est ni une bibliothèque d'articles complets, ni le Kristal canonique. L'identité globale des articles en anglais est `enwiki:<page_id>`. Les rattachements sont une relation N:N : un article peut appartenir à plusieurs concepts, et un même concept peut appartenir à plusieurs branches UNESCO. Le lecteur affiche des titres et exemples, pas le texte encyclopédique.

Le moteur ne parcourt **pas** le dump XML et ne recopie **pas** la base SQL Wikipédia. Il ouvre celle-ci en lecture seule et lance uniquement des recherches sur les index existants. La base dérivée v25 contient seulement les articles découverts et leurs rattachements candidats. Aucun acte canonique, aucune publication et aucune traduction ne sont effectués.

## Changements par rapport à v24

| v24 | v25 |
| --- | --- |
| Un seul microthésaurus et 41 concepts codés en dur | Manifestes de branches réutilisables, nombre variable de concepts |
| Tous les articles en mémoire avant export final | Insertion SQLite par lots, consommation mémoire bornée |
| Plafond global de 25 000 articles | Pas de plafond global codé; budgets contrôlés par exécution et catégorie |
| Exploration interrompue = nouvelle génération | File de catégories persistante, reprise par `rowid` et transactions |
| Sortie unique v24 | Un catalogue global persistant; snapshots de lecteurs et exports immuables |
| Attribution unique privilégiée pour l'affichage | Relations N:N entre article, concept et branche avec preuves de classement |

## Schéma simplifié

- `articles(wiki, page_id)` : identité unique de la page Wikipédia EN.
- `branches(branch_id)` : identité et version du microthésaurus, empreinte de son manifeste.
- `concepts(vocabulary, concept_id)` : identité stable du descripteur UNESCO.
- `branch_concepts(branch_id, concept_id)` : sous-ensembles des concepts par branche.
- `assignments(branch_id,wiki,page_id,concept_id)` : rattachements documentaires candidats, score heuristique, chemin de découverte, nombre d'indices rencontrés.
- `category_tasks(task_id)` : catégorie, racine, profondeur, curseur `rowid`, statut et compteur des membres déjà examinés.
- `audit_events` : refus et extensions explicites des budgets.

Ces tables sont indexées. Les tâches avancent **par lots transactionnels**. Si la machine s'arrête au milieu d'un lot, les écritures du lot et son curseur reviennent ensemble au dernier état validé.

## Stratégie de classement

1. **Ancrages directs candidats** : titre anglais UNESCO = titre d'article, et correspondances Wikidata P3916 candidates lorsque fournies.
2. **Racines exactes de catégories** : catégories dont le nom correspond au libellé anglais UNESCO ou à une variante simple. Par défaut, recherche sur les membres directs seulement (profondeur 0).
3. **Ponts de familles explicitement revus** : fichier CSV (`concept_id,category_title,status,justification,depth_limit`). Seules les lignes `ACTIVE_REVIEWED_AI` avec justification sont parcourues. Ce statut indique une revue de routage documentaire, pas une vérité canonique.
4. **Filtrage des familles** : certaines catégories de maintenance Wikipédia et grandes classes géographiques hors sujet sont ignorées. Les catégories parcourues ne doivent jamais être considérées automatiquement équivalentes à un concept UNESCO.
5. **Unicité** : plusieurs rattachements, mais une ligne par page dans le registre global `articles`.

Un score 96 (ancrage QID), 90 (égalité du titre), 78 (catégorie revue), 64 (catégorie automatique), diminué selon la profondeur, sert uniquement au **tri**. Il ne représente ni une probabilité, ni une approbation de vérité.

## Déploiement Windows

Dézipper le pack dans un dossier temporaire puis, dans PowerShell :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\INSTALLER_CATALOGUE_GLOBAL_V25.ps1'
```

L'installateur valide les SHA-256 et les collisions avant de copier le code. Il vérifie la source SQL `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite` en lecture seule. Il refuse de réutiliser une destination SQLite étrangère ou d'altérer le contenu d'un fichier de code existant.

**Le premier lancement exécute 50 lots de 1 000 liens au maximum**, puis produit un snapshot de consultation. Ce n'est pas une indexation totale ni une couverture annoncée de Wikipédia.

Catalogue dérivé :

`D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite`

Exports et lecteurs versionnés :

`D:\EncyKlopedia\30_working\catalogue_global_unesco_wikipedia_v25\snapshots\<sequence>\`

`LATEST.json` indique le lecteur et l'export les plus récents. Transmettre `EXPORT_V25_POUR_CHATGPT.zip`, pas la base SQLite ni les dumps.

### Reprendre

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\mycode\EncyKlopedia\EncyKlopedia\CONTINUER_CATALOGUE_GLOBAL_V25.ps1' -MaxBatches 250 -BatchSize 2000
```

Les catégories sont reprises au dernier curseur validé. Une relance déjà terminée n'ajoute pas de doublons. Pour produire seulement un nouveau rapport : `-ReportOnly`.

### Étendre une catégorie plafonnée

L'état `CAPPED` indique une limite atteinte, **pas** une catégorie entièrement parcourue. Pour augmenter de façon explicite les budgets de la branche existante :

```powershell
$py = 'C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'  # Adapter si nécessaire
& $py 'C:\mycode\EncyKlopedia\EncyKlopedia\tools\unesco_pilot\catalogue_global_v25.py' extend --extend-branch-id unesco.mt1.10 --new-max-members 200000 --new-max-tasks 30000
```

Puis reprendre normalement. Les tâches limitées sont réactivées à leur curseur antérieur; le fichier de configuration de la branche ne doit pas être modifié sur place.

## Extension à d'autres microthésaurus UNESCO

Le ZIP inclut un générateur qui partitionne un export JSON de concepts UNESCO contenant `microthesaurus_ids` en manifestes indépendants. Exemple à partir d'un futur export complet :

```powershell
& python 'C:\mycode\EncyKlopedia\EncyKlopedia\tools\unesco_pilot\generer_branches_unesco_v25.py' --source 'D:\EncyKlopedia\10_sources\unesco\unesco_complet.json' --dest 'D:\EncyKlopedia\30_working\unesco_branches_v25_2026' --revision snapshot2026
```

Cette commande ne suppose **pas** que l'export complet existe déjà. Si la source ne contient que MT 1.10, elle ne crée qu'un manifeste MT 1.10. Le moteur peut recevoir plusieurs `--branch <manifest.json>` en une exécution, y compris des branches différentes qui partagent le même article. Le manifeste d'une branche enregistrée est immuable : une révision de taxonomie exige un nouvel identifiant de branche ou une nouvelle base dérivée, avec réconciliation éditoriale explicite.

**Important :** pour reprendre une file comportant plusieurs branches, repasser tous leurs manifestes via `-Branches` à la commande `CONTINUER...`, même si l'on n'en ajoute pas de nouveaux.

## Conditions pour le déploiement mondial

- **Donnée manquante** : le ZIP ne contient que les 41 concepts MT 1.10; il ne prétend pas inclure les 88 microthésaurus. Un export UNESCO plus complet sera nécessaire pour instancier les autres branches.
- **Contrôle de qualité** : les ponts catégories Wikipédia ↔ concepts UNESCO doivent être revus. Sans eux, la couverture reste limitée aux correspondances exactes et aux ancrages.
- **Données de catalogue** : la base SQL source doit être complète, et les index SQL attendus doivent être présents. Aucune reconstruction SQL d'office.
- **Limites de volumétrie** : l'architecture supporte le traitement incrémental; elle n'a pas été testée ici sur les 126 Go de base SQL de l'utilisateur, ni sur l'ensemble du Wikipédia anglais. Il faut mesurer les performances sur D: avant d'étendre les budgets.
- **Contenu encyclopédique** : les textes ne sont pas encore extraits ni convertis en connaissances. C'est le deuxième chantier après validation de la couverture de catalogue.
- **Licence** : toute réutilisation ultérieure de texte Wikipédia doit conserver l'attribution et les conditions de licence applicables.

## États d'intégrité

`V25_PREFLIGHT_OK` : vérifications source, aucune écriture.

`V25_RUN_OK` : état et snapshot produits (pas nécessairement catalogue complet).

`V25_SNAPSHOT_OK` : fichiers de sortie SHA-256 conformes.

`V25_REFUS` : refus explicite, par exemple source ou manifeste modifié.

`V25_INSTALLATION_COMPLETE_OK` : installation Windows et premier lot validés; cela n'affirme **pas** que la classification globale est achevée.

## Préparer les lots du futur moteur sémantique

Le catalogue peut exporter en **lots bornés** des identifiants de pages, titres, QID, révisions et rattachements de concepts, sans aucun texte Wikipédia. Ces lots sont destinés au futur moteur d'extraction des textes et de construction des Kristals. Exemple :

```powershell
$script = 'C:\mycode\EncyKlopedia\EncyKlopedia\tools\unesco_pilot\catalogue_global_v25.py'
& python $script export-batch --export-branch-id unesco.mt1.10 --after-page-id 0 --batch-limit 1000
```

La commande renvoie un chemin `batches/*.jsonl` et `next_after_page_id`. Pour la tranche suivante, utiliser cette dernière valeur dans `--after-page-id`. Les lots sont horodatés par le numéro de séquence du catalogue, versionnés et pourvus d'empreintes SHA-256. Les articles sont uniques au sein d'une branche; leur réutilisation entre branches reste possible et doit être dédupliquée par `article_id` dans l'étape sémantique.

Le lecteur fournit également `PONTS_A_REVOIR_V25.csv` : ce sont des catégories Wikipédia découvertes sur les articles-ancrages, **non activées automatiquement**. Une fois examinées, elles peuvent être recopiées dans un fichier de ponts d'une **nouvelle version de branche** avec justificatif. Cela évite d'introduire silencieusement des millions d'articles à partir de familles inadaptées.
