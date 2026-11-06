# EncyKlopedia — Réparation ciblée UniMorph v0.3 (5 novembre 2026)

## Contexte vérifié

`DIAGNOSTIC_UNIMORPH_NO_DATA.csv`, généré sur le PC Windows : 16 ZIP marqués
`no_data`, ZIP lisibles dans les 16 cas. Les huit sources contenant des candidats
textuels sont `slk`, `fin`, `olo`, `ckb`, `vep`, `pbs`, `lud`, `sdh`. Les huit
autres (`pib`, `oss`, `zxx`, `pqm`, `pnb`, `epo`, `mon`, `grn`) n'ont pas de
membre de données reconnu dans ce diagnostic. Il n'est pas démontré que
l'ensemble des données de chaque ZIP est lexical ou sans doublons.

## Installer et lancer (C: code / D: corpus)

Extraire **tout le ZIP cumulatif** à la racine du dépôt du lecteur EncyKlopedia
sur **C:**, aux côtés de `package.json`, en remplaçant les fichiers. Ne pas
extraire sur `D:\EncyKlopedia`.

**Interface Windows** : double-cliquer sur `Reparer_Dictionnaires_UI.pyw`,
cliquer `Actualiser`, puis `Réparer uniquement les sources no_data`.
Python 3.10+ avec Tkinter est requis ; aucun module tiers n'est nécessaire.

**Alternativement** : dans le dépôt moteur sur C: :

```powershell
node tools/dictionary-harvester/cli.mjs index-repair
```

## Politique de réparation

- Examine uniquement les sources UniMorph déjà enregistrées `no_data`
  (`error` / `partial` peuvent aussi être reprises). Jamais de relecture ni de
  réécriture des 194 sources `complete` de la première indexation.
- Préserve les ZIP de `10_sources/lexical` en lecture seule.
- Écrit uniquement dans l'index SQLite **candidat**
  `D:\EncyKlopedia\30_working\lexical\harvester\index-v1`.
- Garde le `source_line` global aux membres de chaque ZIP ; `source_members.csv`
  précise le nom de membre interne et sa plage de lignes pour la provenance.
- Prend en charge `slk.xz` par décompression XZ **en flux**, sans extraction,
  `fin.1` + `fin.2`, les dialectes `olo`, `lud`, `vep`, et le CSV `pbs.csv`.
- Pour `ckb`, choisit les **deux transcriptions** arab et latn de la table
  « large » ; n'ajoute pas les fichiers d'entraînement, validation, test ni les
  anciennes tables. Les deux transcriptions peuvent contenir des doublons
  linguistiques : ce sont des **observations non dédupliquées**.
- Pour `fin`, les fichiers `.args`, `segmentations` et `derivations` sont
  volontairement **hors périmètre** de cette réparation ; ils nécessitent une
  modélisation distincte avant d'être ajoutés.
- Les huit ZIP sans paradigme reconnus restent marqués `no_data`; il n'y a
  ni téléchargement ni transformation artificielle en langues couvertes.
- Reprise par checkpoint SQLite. Un second lancement ignore les archives
  déjà réparées `complete`.

## Vérifier après traitement

Lire :

- `30_working/lexical/harvester/index-v1/latest.json`
- `30_working/lexical/harvester/index-v1/sources.csv`
- `30_working/lexical/harvester/index-v1/source_members.csv`
- `30_working/lexical/harvester/index-v1/RAPPORT_LEXICAL.md`

Si les huit sources récupérables deviennent `complete` et les huit sans données
restent `no_data`, le nombre de `complete` doit passer de 194 à **202** et les
`no_data` diminuer de 16 à **8**. Cette prévision dépend des vraies archives,
du disque et du traitement local : **ce n'est pas encore un résultat constaté**.

## Gouvernance

Aucune identité Kristal, aucun `exactMatch` Wikidata et aucun dictionnaire
canonique diK n'est créé. Les contenus demeurent `unreviewed_candidate` :
contrôle de licences, empreintes externes et curation restent nécessaires.
L'analyse des importants rejets Kaikki `ru` / `id` est un chantier séparé.
