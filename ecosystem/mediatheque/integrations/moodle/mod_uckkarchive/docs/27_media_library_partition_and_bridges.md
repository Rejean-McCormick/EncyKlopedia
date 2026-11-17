# Médiathèques autonomes et bridges inter-Univers-Cités

## Décision d'architecture

Les médiathèques publiques d'Univers-Cité sont **séparées par défaut**.

Un média n'est jamais rendu commun à toutes les Univers-Cités simplement parce qu'il est public. Chaque média et chaque collection possède un **fonds d'origine** (`libraryid`). La recherche publique d'un site résout d'abord sa médiathèque primaire puis limite les résultats à ce fonds et aux bridges entrants explicitement actifs.

Cette décision remplace l'ancien comportement où la recherche publique pouvait parcourir un catalogue global commun.

## Trois formes de partage

### 1. Fonds autonomes

Cas normal : chaque site utilise sa propre médiathèque primaire.

- `uckk` → Médiathèque UCKK
- `ucc` → Médiathèque chrétienne
- `math` → Bibliothèque mathématique

Sans bridge, un média du fonds `ucc` n'apparaît pas dans `math`, et inversement.

### 2. Même médiathèque pour plusieurs Univers-Cités

Plusieurs sites peuvent pointer vers **le même `libraryid`**. Ils utilisent alors réellement le même fonds : mêmes médias, mêmes collections, mêmes UUID et mêmes révisions.

Ce cas est représenté par `uckkarchive_library_site`. Un site n'a qu'une médiathèque `primary`; ses anciens rattachements primaires sont conservés comme `shared` lorsqu'un nouveau fonds devient primaire.

### 3. Bridge partiel ou complet

Les médiathèques restent distinctes, mais un bridge directionnel peut rendre visible dans la médiathèque cible :

- toute la médiathèque source (`library`);
- une collection précise (`collection`);
- un média précis (`media`).

Le bridge ne copie jamais le média. L'objet conserve son fonds d'origine, son UUID, sa provenance et son historique de versions.

## Direction des bridges

Un bridge `UCC → Math` ne crée pas automatiquement `Math → UCC`.

Les bridges sont volontairement à sens unique. Un partage bidirectionnel se représente par deux bridges explicites.

Les bridges sont actuellement **à un seul saut** : un média reçu par bridge n'est pas automatiquement retransmis par les bridges de la médiathèque cible. Cette règle évite les propagations implicites de corpus.

## Provenance publique

Lorsqu'un média est visible dans une médiathèque via un bridge, le DTO public indique :

- le nom et le slug du fonds d'origine;
- `isbridged = true`;
- le type de bridge (`library`, `collection`, `media`);
- le libellé du bridge lorsqu'il existe.

L'interface peut donc expliquer pourquoi le média est visible sans le présenter comme une copie locale.

## Migration des données existantes

À l'installation de cette architecture :

1. les trois fonds par défaut (`uckk`, `ucc`, `math`) sont créés;
2. chaque site reçoit son fonds primaire distinct;
3. les médias et collections existants sans `libraryid` sont rattachés à la Médiathèque UCKK pour préserver leur accessibilité sans deviner leur appartenance;
4. UCC et Math démarrent donc isolés et ne voient que les contenus explicitement rattachés à leur fonds ou reçus par bridge.

Ce choix de migration évite d'attribuer automatiquement d'anciens contenus à une Univers-Cité spécialisée sur la base d'une heuristique.

## Création de nouveaux contenus

Les appels modernes peuvent préciser `libraryslug` lors de la création d'un média ou d'une collection. Pour compatibilité, les anciens appels sans ce paramètre utilisent le fonds UCKK comme fonds d'origine.

La sélection explicite d'un fonds spécialisé via les services externes requiert la capacité système `mod/uckkarchive:managelibraries`.

## Sauvegarde et restauration Moodle

Les médiathèques et bridges sont une configuration de site, pas une propriété portable d'une activité Moodle. Les sauvegardes d'activité ne transportent donc pas les identifiants de fonds ni les bridges. Lors d'une restauration, les médias et collections restaurés sont rattachés au fonds UCKK de l'installation de destination; un administrateur peut ensuite les réaffecter explicitement. Cette règle évite qu'un identifiant numérique provenant d'une autre installation donne accès au mauvais fonds.

## Administration

La page :

`/mod/uckkarchive/library_admin.php`

permet de :

- créer une médiathèque;
- rattacher le même fonds à plusieurs sites;
- réaffecter un média par UUID;
- réaffecter une collection par UUID;
- créer des bridges complets, de collection ou de média;
- désactiver un bridge sans supprimer son identité d'audit.

La gestion requiert `mod/uckkarchive:managelibraries` au contexte système.

## Tables

- `uckkarchive_library` : identité des fonds;
- `uckkarchive_library_site` : rattachement site ↔ fonds;
- `uckkarchive_media.libraryid` : fonds d'origine du média;
- `uckkarchive_media_collection.libraryid` : fonds d'origine de la collection;
- `uckkarchive_library_bridge` : règles explicites de partage.

## Invariants

1. Un média a un seul fonds d'origine.
2. Une collection a un seul fonds d'origine.
3. Un site public a un seul fonds primaire.
4. Deux sites peuvent partager exactement le même fonds primaire.
5. Le partage entre fonds distincts est explicite et directionnel.
6. Aucun bridge ne duplique un média ou son UUID.
7. La recherche publique échoue fermée si le site n'a pas de fonds résolu.
8. Les bridges ne sont pas transitifs.
