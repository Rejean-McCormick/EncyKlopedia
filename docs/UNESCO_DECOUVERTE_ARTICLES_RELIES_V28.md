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
