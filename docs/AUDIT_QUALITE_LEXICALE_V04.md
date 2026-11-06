# EncyKlopedia — Audit de qualité lexicale v0.4 (local, candidat)

## But

Analyser le catalogue lexical existant **sans** le réindexer ni recopier les
archives. Le travail est séparé : **code sur C:** dans le dépôt moteur,
**sources et bases de travail sur `D:\EncyKlopedia`**.

L'audit ne constitue **pas** une réconciliation sémantique, un nettoyage automatique
du dictionnaire diK ou une publication EncyKlopedia. Les identités Kristal KQ/KP
et les identifiants externes Wikidata ne sont jamais créés, fusionnés ou promus.

## Installation

Extraire **l'overlay cumulatif v0.4** à la racine du dépôt EncyKlopedia sur C:,
à côté de `package.json`, en remplaçant les fichiers. Ce ZIP contient les
correctifs v0.1.1–v0.3 ; ne pas l'extraire sur D:.

Python 3.10+ avec Tkinter (installation Windows standard) est nécessaire.
L'application n'utilise aucune bibliothèque Python externe.

Double-cliquer sur **`Audit_Qualite_Lexicale_UI.pyw`** ou sur
`Start_Audit_Qualite_Lexicale.cmd`. Vérifier que les données pointent vers
`D:\EncyKlopedia`, puis :

1. **Diagnostiquer pib + sdh** : lecture des petits ZIP `pib.zip` et `sdh.zip`,
   aperçu d'un échantillon de 2 000 lignes par archive et état `no_data` dans
   la base source. `sdh` peut contenir des lignes valides même si le statut index
   est `no_data` : signaler le décalage, ne rien corriger automatiquement.
2. **Audit pilote (fr/en)** : vérifier les lemmes normalisés français/anglais et
   produire un rapport **PARTIEL** ; les résultats sont conservés.
3. **Lancer / reprendre l'audit complet** : calculer les lemmes distincts,
   les répétitions et les homographies communes à plusieurs sources pour **toutes**
   les langues indexées, avec checkpoints par langue.

Pour l'exécution en console :

```powershell
node tools/dictionary-harvester/cli.mjs quality-diagnostic
node tools/dictionary-harvester/cli.mjs quality-audit --languages fr,en
node tools/dictionary-harvester/cli.mjs quality-audit
node tools/dictionary-harvester/cli.mjs quality-status
```

Alternativement, sans Node :

```powershell
py -3 tools/dictionary-harvester/quality_audit.py diagnostic --data-root D:\EncyKlopedia
py -3 tools/dictionary-harvester/quality_audit.py audit --data-root D:\EncyKlopedia
```

## Définitions : interpréter correctement les résultats

- `observation_rows` : nombre de lignes réellement présentes dans `entries`.
- `distinct_lemma_keys` : nombre de **paires (code langue normalisé, `lemma_key`)**
  dans les langues auditées. `lemma_key` est une normalisation NFKC, casse ignorée,
  tronquée à 300 caractères lors de l'indexation v0.3. Il ne s'agit donc ni du
  nombre de sens uniques ni du nombre de lexèmes canoniques.
- `extra_observation_rows` : occurrences au-delà d'une observation par clé.
  Les nombreuses flexions d'un lemme UniMorph peuvent être légitimement répétées.
- `repeated_inside_one_source_keys` : clés vues plusieurs fois dans le même
  fichier source.
- `shared_across_files_keys` : clés vues dans au moins deux fichiers sources.
- `shared_across_families_keys` : clés vues dans au moins deux **familles**
  Kaikki / UniMorph / Wikidata. Ce sont des homographes candidats, **pas**
  des `owl:sameAs`, `skos:exactMatch`, des synonymes ou des sens comparables.
- `kaikki_unimorph_keys`, `kaikki_wikidata_keys`, `unimorph_wikidata_keys` :
  nombres de clés présentes dans les deux familles correspondantes.

Les compteurs globaux valent uniquement pour les langues **auditées**. Le rapport
est marqué PARTIEL jusqu'à ce que la totalité du catalogue ait été balayée.
Une longue exécution complète parcourt potentiellement plus de 87 millions de
lignes, avec lectures importantes sur D:. Éviter de lancer une indexation / une
réparation en parallèle. Garder suffisamment d'espace libre sur D:.

## Destinations des fichiers dérivés

**Entrée en lecture seule** :

- `D:\EncyKlopedia\30_working\lexical\harvester\index-v1\lexical.sqlite3`
- `D:\EncyKlopedia\10_sources\lexical\unimorph\repos\pib.zip` et `sdh.zip`

**Sorties indépendantes** :

- `D:\EncyKlopedia\30_working\lexical\harvester\quality-v1\DIAGNOSTIC_PIB_SDH.md`
- `D:\EncyKlopedia\30_working\lexical\harvester\quality-v1\UNIMORPH_PIB_SDH.json`
- `D:\EncyKlopedia\30_working\lexical\harvester\quality-v1\runs\<empreinte-source>\quality.sqlite3`
- `...\RAPPORT_QUALITE_LEXICALE.md`
- `...\languages_quality.csv`
- `...\overlap_examples.csv` (avec identifiants de fichiers et chemins sources)
- `...\source_issues.csv` (statuts incomplets ou rejets d'au moins 5 %)
- `...\latest.json`
- `D:\EncyKlopedia\30_working\lexical\harvester\quality-v1\latest.json`

Le stockage des résultats se fait **uniquement dans `quality-v1`**. L'index
`index-v1` n'est ni modifié, ni compacté, ni réparé par l'audit.

Les checkpoints sont validés **par langue** dans `quality.sqlite3`. `Ctrl+C` ou
le bouton Interrompre conserve les langues déjà terminées. Un lancement ultérieur
reprend les langues non terminées ; un changement du catalogue source crée une
nouvelle empreinte et donc un nouveau dossier d'audit. Les anciens rapports
restent disponibles. Aucun ancien résultat n'est supprimé.

## Limitations et garde-fous

- Le traitement n'effectue pas une comparaison des sens : il repère seulement des
  clés orthographiques identiques pour une même langue normalisée.
- L'égalité n'est pas déduite de l'écriture phonétique, d'un lien externe,
  d'une traduction ou de caractères semblables dans des écritures différentes.
- L'état des ZIP `pib` / `sdh` est déterminé par heuristique et échantillonnage;
  seule une analyse de tout le corpus justifierait une assertion exhaustive.
- Les 210 sources n'ont pas de vérification SHA-256 contre un manifest éditeur
  et leur statut juridique reste en attente. La présence d'un fichier ne donne
  aucun droit de publication.
- L'audit n'écrit pas dans diK, GF/SemantiK, Médiathèque kOA, Kristal ni dans
  le lecteur public ; aucune porte C2/C4 n'est franchie.

## Diagnostic d'un arrêt

Consulter le journal de l'interface et le dernier message `ERREUR`.
Le niveau d'espace libre minimum est **2 Go** sur D: (ajustable seulement via
la CLI). Si un autre outil modifie `lexical.sqlite3` pendant un audit, la
phase active est arrêtée pour éviter de mélanger deux versions du catalogue.
