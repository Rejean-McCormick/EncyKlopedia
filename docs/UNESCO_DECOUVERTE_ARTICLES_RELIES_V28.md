# EncyKlopedia v28 — Découverte d'articles reliés, revue, cumul

## Périmètre

- **Entrée** : catalogue mondial v25 existant et approuvé comme *catalogue documentaire candidat* (les 782 articles du pilote MT 1.10), Wikipédia EN SQL en lecture seule, index v21 des offsets XML en lecture seule et fichier XML complet en lecture seule.
- **Sortie** : propositions d'articles supplémentaires, *pas* des connaissances canoniques ni une mise en correspondance UNESCO automatiquement validée.
- **Validation** : une décision `APPROVE` explicite, justifiée et liée aux preuves est nécessaire pour ajouter des pages au catalogue v25.
- **Suite** : le producteur v27 détecte automatiquement les nouvelles pages à la prochaine action `Packs`, car chaque application de décisions fait progresser la séquence du catalogue.

Il n'y a ni nouvelle copie des 110 Go du XML, ni import SQL, ni création de Kristal canonique, ni installation de services, ni accès réseau.

## Ordre de fonctionnement sur D:\

Depuis `C:\mycode\EncyKlopedia\EncyKlopedia` :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Preflight
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Discover -MaxSeeds 1000
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Export -MaxExport 1500
```

Récupérer dans le JSON de résultat le chemin `export_for_chatgpt` du ZIP `EXPORT_V28_POUR_CHATGPT_<sha>.zip` sous :

`D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\exports\`

**Envoyer ce ZIP dans ChatGPT pour une revue éditoriale des nouveaux articles, ou préparer un CSV de décisions soi-même.** L'export contient une table des candidats classés par *priorité heuristique*, leurs concepts suggérés, et des preuves. Il ne contient pas le texte des articles : ceux-ci restent intégraux dans le XML local et les futurs packs v27. Pour explorer le reliquat, relancer `Export` avec `-MaxExport 5000` ou plus (jusqu'à 20 000); le nombre total est indiqué.

Décider chaque ligne dans la colonne `decision` : `APPROVE` (avec justification de 20 caractères ou plus), `HOLD` ou `REJECT` ; ne modifier ni les identifiants ni les empreintes de preuve. `HOLD` est la valeur par défaut. **Ne jamais approuver tous les candidats en masse.**

Puis :

```powershell
$csv = 'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\exports\REVUE_ARTICLES_RELIES_V28_s0000000033_top1500.csv' # exemple seulement : utiliser le chemin réellement produit
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Apply -DecisionsFile $csv -DryRun
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Apply -DecisionsFile $csv
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\PRODUIRE_KRISTALS_V27.ps1' -Action Packs -MaxPacks 10 -MaxArticles 24 -TargetWords 35000
```

La commande `Apply` est **idempotente** pour un CSV et des décisions inchangées. Un changement de décision déjà enregistré est refusé au lieu d'effacer les antécédents. Les nouveaux articles sont uniques par `enwiki:page_id`; ils peuvent avoir plusieurs rattachements UNESCO. Les anciens 782 articles et le Kristal cumulatif de 2 420 connaissances ne sont ni effacés ni réimportés.

## Algorithme d'exploration

1. Synchronisation incrémentale des graines depuis les rattachements v25 ; reprise transactionnelle par page et par lot. Si de nouvelles pages/relations sont approuvées dans le catalogue, une nouvelle synchronisation intervient à la prochaine séquence.
2. Lecture intégrale de chaque **article graine** par offsets XML v21 : pas de scan global de l'XML. Extraction heuristique des wikiliens `[[...]]` sur l'ensemble du texte, avec échantillonnage réparti si le nombre de liens excède `MaxLinksPerSeed`. *Le texte source n'est jamais tronqué.*
3. Voisinage des catégories de la graine à l'aide des index `idx_wiki_catid_from` et `idx_wiki_catid_target`. Seules quelques catégories avec signal lexical UNESCO ou pont éditorial existant sont suivies. Les catégories dépassant `MaxCategorySize` sont ignorées au lieu d'être traversées sans borne.
4. Exploration optionnelle d'un niveau de sous-catégories compatibles lexicalement, sans traversée profonde incontrôlée.
5. Regroupement des preuves par identifiant unique d'article et concept : liens directs, catégorie partagée, sous-catégorie et graines indépendantes.
6. Priorité heuristique 40–90, **pas une probabilité de pertinence** et encore moins une preuve de véracité. L'interface CSV est un espace de revue.

Limites : les wikiliens syntaxiques peuvent inclure des éléments de modèles ou contextes périphériques. L'échantillonnage limite **les liens analysés**, jamais le texte original du futur pack. L'index Wikipédia local ne comprend pas de table `pagelinks` prête à l'emploi : lire les pages via les offsets v21 est donc plus sûr que prétendre l'utiliser. Les concepts du pilote ne couvrent pas encore tous les microthésaurus UNESCO.

## Garanties

- Métadonnées v25 et signature du manifeste de branche vérifiées ; la configuration figée n'est pas modifiée.
- Source SQL, index XML et XML toujours en lecture seule. Données découvertes dans `D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite`.
- Aucun candidat n'est intégré automatiquement. Toute application est transactionnelle, auditée, et provoque un snapshot v25.
- Reprises idempotentes : graines déjà parcourues non retraitées, preuves dédupliquées ; nouvelle séquence = synchronisation sans perdre l'historique.
- Aucun changement de la base `KRISTAL_CUMULATIF_PRIVE_V27.sqlite`. Les Kristals continuent d'être enrichis exclusivement via les deltas v27.

Pour une nouvelle passe limitée : `-MaxSeeds 200`. Pour modifier le seuil de catégories : `-MaxCategorySize 500`. Utiliser `-Action Status` pour connaître les graines déjà traitées et les candidats en attente de revue.

## Correctif de reprise v28.1 — revisions SQL / XML differentes

Le catalogue v25 vient de l'inventaire SQL Wikipedia; les articles lus par
le producteur v27 et la decouverte v28 viennent du dump XML via l'index v21.
Leurs `revision_id` peuvent differer pour un meme `page_id`, sans que cela
signifie une corruption. Le v27 accepte deja explicitement cette situation.

La v28.1 applique la meme regle : **le texte et sa revision XML (valides contre
l'index v21) font autorite pour la lecture des liens**, tandis que le numero
de revision SQL conserve dans le catalogue n'est ni modifie ni masque.
Les divergences observees sont enregistrees dans la table privee
`seed_revision_mismatches` (page, revision catalogue, revision XML, titre XML,
date d'observation) et resumees dans les reponses `Discover` et `Status`.

Ce changement n'affaiblit pas le controle des offsets XML, des IDs, des titres
et des revisions **entre l'index v21 et le dump XML** : toute incoherence a
ce niveau reste bloquante. Il ne change pas non plus les sources ni la base
de Kristals.

**Reprise apres le refus `Revision XML differente du catalogue` :** remplacer
les fichiers de l'overlay, puis relancer exactement la meme commande
`-Action Discover -MaxSeeds 1000`. La base v28 deja presente est conservee;
les graines `DONE` ne sont pas traitees a nouveau. La nouvelle table de suivi
est creee automatiquement par une migration additive et ne requiert aucun
script SQL manuel. `-Action Status` donne les compteurs et jusqu'a dix exemples
de divergences observees. Les graines traitees avant la correction ne sont
pas relues uniquement pour remplir ce registre d'audit.


---

# EncyKlopedia v31.10 — Découverte LARGE, sélection documentaire par ChatGPT

## Principes

- Le système **propose largement** des correspondances possibles entre Wikipédia et les concepts UNESCO; il ne décide **jamais** lui-même lesquelles ont une valeur encyclopédique.
- Les propositions sont réunies dans les revues habituelles v28, de 4 000 lignes **maximum par pack**, avec les vrais identifiants, les empreintes des preuves indexées et les contextes documentaires.
- **ChatGPT** lit la revue et la documentation dans le pack, puis retourne **APPROVE, REJECT ou HOLD pour chaque ligne**. Seule cette revue constitue une décision documentaire, provisoire et non canonique.
- Aucune admission canonique ni publication, aucun effacement de l'inventaire; les candidats non sélectionnés pour un pack restent dans la file.

## Pourquoi ce correctif

Le diagnostic du 15 novembre 2026 confirme que les 5 fichiers v31.9 sont en place, mais que 19 des 41 concepts configurés n'ont ni affectation initiale ni candidat découvert. La découverte v28 historique part des affectations existantes, ce qui empêche ces concepts d'amorcer leur propre recherche.

## Découverte indépendante (additive)

En plus de la découverte historique par liens et catégories, v31.10 interroge **les index SQLite de Wikipédia en lecture seule** sur les libellés UNESCO officiels et variantes explicites :

1. Les titres exacts **et ceux qui commencent** par ces libellés (pas uniquement l'égalité stricte).
2. Les catégories exactes et les catégories dont le titre **commence** par ces libellés, puis leurs pages membres, même lorsque le titre de l'article n'est pas semblable au nom du concept.
3. Tous les concepts de la branche, y compris ceux avec zéro graine et ceux déjà amorcés : aucune catégorie n'est définitivement écartée parce qu'un plafond est atteint.

La découverte reste bornée pour les performances (jusqu'à 800 **nouvelles paires par concept et par exécution** par défaut), avec curseurs SQLite **persistants** par libellé et catégorie. Les passages suivants reprennent au point atteint. Ce plafond n'est donc **pas un rejet**. Le moteur ne balaie pas les 110 Go de XML et n'invente ni libellé UNESCO ni texte cité. Les seules nouvelles preuves sont des **références indexées** (`SQL_TITLE_PREFIX`, `SQL_CATEGORY_MEMBER`), pas une validation de pertinence.

En v31.10, les correspondances de ces deux provenances reçoivent une priorité de planification minimale de 20 pour entrer dans `PENDING`, et non une décision de fond. Elles doivent toujours être vérifiées par ChatGPT sur le contexte documentaire réellement présent.

## Intégrité, installation et exploitation

- **Attendre l'absence de revues UNESCO ouvertes pour LANCER la découverte**, car les preuves envoyées sont figées. Le moteur refuse une découverte manuelle si de telles revues existent.
- L'overlay se dépose dans **Mises à jour logicielles**, avec préconditions SHA-256. Ne décompressez pas l'overlay directement sur le programme.
- Les modifications des tables de travail se limitent aux curseurs additifs `v3110_probe_cursor` et `v3110_category_roots`, créés lors de la prochaine découverte autorisée. Aucun fichier historique n'est reconstruit. Les candidats et les preuves **déjà enregistrés** ne sont jamais modifiés par l'amorçage.
- Les bases de production ne sont pas incluses dans le ZIP. La sauvegarde des résultats v3 reste indépendante et recommandée avant installation.
- Aucun quota de 10 postes n'est garanti : si les index ne présentent pas assez de candidats, ou si les libellés ne capturent pas des synonymes, le résultat peut rester partiel. Un audit indépendant du rappel reste nécessaire.

## Tests et limites

Des tests isolés vérifient la reprise des curseurs, la recherche préfixe et par catégorie, la couverture de concepts non amorcés, l'absence de décision locale, la non-modification des preuves existantes et le refus des découvertes quand une revue est ouverte. Le test Windows de production ne peut pas être réalisé depuis ce snapshot ; surveiller au prochain cycle les nouveaux indicateurs `broadscan_*` du journal.

## v31.11 — Rappel par relations UNESCO (additif)

### Problème mesuré par l'audit du 15 novembre 2026

Les deux fichiers v31.10 vérifiés sont conformes. L'audit local a constaté 186 232 couples
candidats tous présents dans le catalogue, le registre des décisions ou l'index station
(aucune paire perdue); zéro candidat PENDING et zéro article Kristal non empaqueté.
Les 334 curseurs de préfixe et les 67 parcours de catégories existants sont tous marqués
terminés, mais **16 concepts sur 41 n'ont toujours aucun candidat**. Ceci **n'établit pas**
que les concepts sont épuisés : seuls leurs préfixes littéraux ont été explorés.

### Nouveau chemin de découverte

Le nouveau parcours utilise uniquement les arêtes documentées **broader/narrower/related**
du référentiel UNESCO de cette même branche et les **affectations existantes** dans le
catalogue v25. Il propose les articles déjà rattachés à des concepts voisins comme candidats
à examiner pour un concept pauvre en propositions. Les chemins directs sont prioritaires;
un chemin de deux arêtes UNESCO est autorisé si une relation directe n'apporte pas de
propositions. **Une relation entre concepts n'est jamais une preuve de pertinence de
l'article pour le concept cible**. Le pack contient la provenance `UNESCO_RELATED_CATALOGUE`;
ChatGPT lit l'article et choisit APPROVE, REJECT ou HOLD.

Le parcours ne modifie ni les affectations, ni les décisions, ni les anciennes preuves. Il
utilise uniquement des identifiants de pages existants, en ignorant les redirections et
les namespaces non encyclopédiques. Aucun balayage du XML Wikipédia de 110 Go.

Le plafond initial est de **800 nouvelles paires par concept et par lancement autorisé**.
Il répartit le travail en vagues sans exclure définitivement les articles : la table additive
`v3111_relation_cursor` enregistre `last_page_id` et l'état de chaque chemin. Les relations
et les articles déjà épuisés ne sont pas retraités inutilement. Les concepts sans aucune
affectation peuvent continuer à être explorés au-delà de leur première vague.

### Sécurité et exploitation

- La protection de v31.10 reste active : **aucune nouvelle découverte si une revue UNESCO
  est ouverte**, y compris après une installation de l'overlay.
- Les packs et empreintes de preuves déjà exportés restent inchangés; aucun ACCEPT/REJECT
  ou admission canonique automatique. Les décisions passées ne sont jamais remises à zéro.
- Le journal ajoute `relation_new_pairs`, `relation_pairs_by_concept`,
  `relation_unfinished_paths`, `relation_auto_approvals: 0` pour diagnostiquer l'apport réel.
- Installation **par l'interface logicielle v30** avec préconditions SHA-256, puis fermeture
  et redémarrage complet. Ne pas décompresser le ZIP dans le dépôt.
- Sauvegarde v3 des **seuls résultats SQLite** avant installation, sans corpus Wikipédia.
- Les suggestions de voisinage peuvent être nombreuses et peu pertinentes : elles ne sont
  pas un indicateur de rappel prouvé, et dix postes ne sont jamais garantis.
- Tests automatisés sur bases miniatures et retour arrière sur copie isolée, **pas**
  d'exécution sur la base de production de l'utilisateur.
