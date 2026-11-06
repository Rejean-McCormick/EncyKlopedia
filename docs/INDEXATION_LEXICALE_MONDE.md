> **Complément v0.3 :** correction ciblée via `Reparer_Dictionnaires_UI.pyw` et `docs/REPARATION_UNIMORPH_V03.md`. Les fichiers `no_data` se réparent sans réexécuter toutes les sources.

# EncyKlopedia — Indexation mondiale des sources lexicales existantes (candidate v0.2)

## À installer sur C:, à exécuter sur D:

Cet overlay **cumulatif** inclut tout le Dictionary Harvester v0.1.1, plus le module d'indexation massive v0.2.
L'extraire **à la racine du dépôt EncyKlopedia sur C:**, là où se trouve `package.json` ; remplacer les fichiers existants. **Ne rien extraire sur `D:\EncyKlopedia`.** L'index sera produit sur D: automatiquement.

Après extraction : double-cliquer sur `Start_Indexation_Dictionnaires.cmd` ou exécuter depuis la racine du dépôt C: :

```powershell
node tools/dictionary-harvester/cli.mjs index-plan
node tools/dictionary-harvester/cli.mjs index-run
node tools/dictionary-harvester/cli.mjs index-status
node tools/dictionary-harvester/cli.mjs index-lookup --query chat --language fr
node tools/dictionary-harvester/cli.mjs index-lookup --query vais --language fr --match form
```

Nécessite **Node.js >=22 et Python >=3.10** sur le PC (Python n'utilise que la bibliothèque standard). Aucun logiciel supplémentaire, compte cloud, scraping ou accès réseau ne sont requis. La commande `index-plan` ne modifie rien ; `index-run` écrit seulement ses résultats dans `30_working` sur D:.

## Ce que fait exactement l'indexeur

1. **Découverte locale**, sans téléchargement :
   - `10_sources/lexical/wiktionary/kaikki/raw-editions/*/*.jsonl.gz` : les 21 extractions Kaikki téléchargées.
   - `10_sources/lexical/wiktionary/kaikki/enwiktionary/**/*.jsonl` : l'extraction albanaise déjà présente, si elle existe encore.
   - `10_sources/lexical/unimorph/repos/*.zip` : les 187 archives UniMorph, analysées **sans extraction** ; sélection du fichier principal sans extension, nommé selon le code de langue (`fra`, `eng`, etc.).
   - `10_sources/lexical/wikidata/lexemes/dumps/current/*lexeme*.json.bz2` : dump lexical Wikidata `L`/`F`/`S` déjà présent.
2. **Analyse en flux** du JSONL compressé, des paradigmes UniMorph et du dump bz2 Wikidata. Aucune copie décompressée des fichiers source n'est créée.
3. **SQLite candidat** : une ligne par observation de lemme Kaikki, par forme UniMorph, ou par lexème Wikidata (avec identifiant `L…`). Préserve le fichier source et le numéro de ligne, et les comptes de sens, formes et traductions observés. Les formes et traits UniMorph sont interrogeables.
4. **Reconciliation de code candidate** ISO 639 alpha-3 vers alpha-2 quand la correspondance est explicite (`fra → fr`, `eng → en`). Le code original est conservé dans `source_language_code`. Il ne s'agit **pas** d'une certification BCP 47 ou d'une décision KQ/KP.
5. **Checkpoints transactionnels** par groupe de 2500 lignes. Relancer la même commande reprend le travail (il faut relire les flux compressés jusqu'à la ligne sauvegardée, sans réindexer les données déjà enregistrées).
6. **Rapports par source et par langue** et manifeste candidat de passage à diK, sans modification des schémas Kristal, des identités canoniques ou du graphe sémantique.

## Emplacements de sortie (créés automatiquement)

```text
D:\EncyKlopedia\
  10_sources\lexical\                            Sources préexistantes conservées strictement en lecture seule
  30_working\lexical\harvester\index-v1\
    lexical.sqlite3                             Index candidat (peut devenir volumineux)
    lexical.sqlite3-wal / lexical.sqlite3-shm    Fichiers techniques SQLite temporaires
    lexical-index.lock                          Verrou de traitement automatique
    latest.json                                 État et totaux
    RAPPORT_LEXICAL.md                         Résumé lisible pour inspection humaine
    languages.csv                               Couverture observée par code de langue
    sources.csv                                 État individuel des archives et erreurs
    dik-source-handoff.candidate.json           Proposition de handoff — PAS un export diK normatif
```

Les métadonnées d'acquisition de `10_sources` et les preuves `20_evidence` ne sont **ni effacées ni modifiées**. Le lecteur et `src/server.mjs` ne sont pas modifiés. Le moteur de lecture n'obtient aucune route HTTP d'écriture.

## Interprétation correcte des résultats

- `lemma_observations` = **nombre de lignes lexicales observées** ; ce n'est pas un nombre global de lemmes uniques. Des entrées peuvent être présentes dans plusieurs éditions Wiktionary et dans UniMorph.
- `sense_observations`, `form_observations`, `translation_observations` = tailles des tableaux observés (ou nombres de formes morphologiques UniMorph), **pas** des sens/représentations dédupliqués ou vérifiés.
- Wikidata : les lexèmes conservent `L…` ; les formes et sens sont comptés, mais **les identifiants individuels `F` et `S` ne sont pas indexés séparément** dans v0.2. Le dump original reste accessible.
- UniMorph : les ZIP sans fichier linguistique principal, y compris ceux contenant seulement une README, obtiennent `no_data`, pas `complete` ou `exploitable`.
- L'index est **candidat, non révisé, non canonique et non publiable**. Aucune licence n'est implicitement approuvée ; aucune correspondance Wikidata `exactMatch` n'est attribuée ; aucun identifiant Kristal n'est créé.
- `stale` signifie que la taille ou la date de modification d'une source a changé. L'index existant est préservé ; seul `--refresh-changed` permet de reconstruire les **lignes dérivées** de cette source.
- Aucune empreinte officielle distante n'est validée par le seul traitement local. Les SHA-256 des précédentes captures doivent être qualifiés séparément.

## Résilience et gestion du disque

- `index-run` vérifie au démarrage qu'il reste au moins **5 Gio** sur le disque des données, et contrôle à nouveau cet espace avant chaque archive. En cas de manque de place, la progression déjà validée reste enregistrée. L'index SQLite peut être **nettement plus gros** que les archives compressées : vérifier l'espace réel avant de lancer l'ensemble.
- L'interruption (`Ctrl+C`) ou une erreur source ne détruit pas les autres sources indexées. Les transactions SQLite évitent les doubles insertions à la reprise.
- Il n'y a **aucune suppression automatique**. Pour les sources modifiées :

```powershell
node tools/dictionary-harvester/cli.mjs index-run --refresh-changed
```

La commande ci-dessus supprime et reconstruit **uniquement les entrées de l'index dérivé** associées aux fichiers modifiés, pas les archives sources.

Pour un pilote plus petit avant une indexation globale :

```powershell
node tools/dictionary-harvester/cli.mjs index-run --only unimorph --max-lines-per-source 1000
```

Cette limite est **par fichier** et marque l'état `partial`. Un lancement ultérieur sans limite reprend les fichiers.

## Tests

```powershell
node tools/dictionary-harvester/verify-overlay.mjs
npm run verify
py -3 -m unittest discover -s tests -p test_lexical_indexer.py -q
```

## Handoff vers diK

`dik-source-handoff.candidate.json` donne les chemins de la base et des rapports, et signale explicitement : `status=unreviewed_candidate`, `requires_license_review=true`, `requires_identity_crosswalk_review=true`, `may_be_published=false`.

**Le connecteur canonique vers le catalogue diK v11 est encore une étape distincte.** Ce nouveau module prépare le catalogue mondial, mais ne prétend pas avoir intégré ou approuvé les dictionnaires dans diK.
