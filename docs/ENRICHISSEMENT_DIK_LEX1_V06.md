# DIK-LEX-1 v0.6 — Enrichissement des preuves source, candidats uniquement

**Statut : non normatif, non approuvé, pas de correspondance sémantique automatique.**

## Où installer et comment lancer

Extraire le ZIP **à la racine du moteur EncyKlopedia sur C:** (`package.json` au même niveau), en écrasant les fichiers homonymes. Le ZIP est **cumulatif** et contient l'overlay v0.5 complet. Ne jamais extraire sur le disque D: des données.

Pré-requis : Python 3.10+, Tkinter, index lexical v0.3/v0.4 et conciliation candidate v0.5 terminée, exports v0.5 déjà vérifiés. Sur Windows : double clic sur `Enrichir_Dictionnaires_diK_UI.pyw`. Autre accès `Start_Enrichissement_diK.cmd` ou :

```powershell
py -3 tools\dictionary-harvester\semantic_enrichment.py plan --data-root D:\EncyKlopedia
py -3 tools\dictionary-harvester\semantic_enrichment.py run --data-root D:\EncyKlopedia --languages fr,en
py -3 tools\dictionary-harvester\semantic_enrichment.py run --data-root D:\EncyKlopedia
py -3 tools\dictionary-harvester\semantic_enrichment.py verify --data-root D:\EncyKlopedia
```

## Contrat de lecture/écriture

- **Entrées en lecture seule** : `30_working/lexical/harvester/index-v1/lexical.sqlite3`; `30_working/lexical/harvester/dik-reconciliation-v1/reconciliation.sqlite3` ; toutes les archives originales dans `10_sources/lexical`.
- **Sorties isolées** : `30_working/lexical/harvester/dik-enrichment-v1/` sur D: exclusivement.
- `enrichment.sqlite3` : ancrages `(source_id,source_line,candidate_id)`, lignes d'archives relues, checkpoints par source/lot et langues préparées.
- `evidence/<lang>.jsonl` : une fiche par **graphie candidate**, contenant seulement les observations ancrées en v0.5, leur texte utile limité, les IDs externes et une étiquette *non approuvé*. Manifestes avec SHA-256 local.
- `sources_enrichment.csv`, `RAPPORT_ENRICHISSEMENT.md`, `latest.json`, `dik-enriched-handoff.candidate.json` : état, anomalies et handoff candidat.

**Le logiciel ne modifie pas la v0.5, l'index initial, les ZIP sources, diK, Framework, GF ou les KQ/KP.** Aucun réseau ni scraping pendant l'enrichissement. Aucune correspondance `exactMatch` automatique.

## Ce que la v0.6 récupère réellement

1. **Kaikki/Wiktextract** : les sens et gloses textuels d'un enregistrement source ancré, POS, formes, traductions et étiquettes, avec leur langue d'origine. Maximum 24 sens, 24 formes, 24 traductions et 4 gloses par sens par ligne ; les nombres bruts et troncatures sont conservés.
2. **Wikidata Lexemes** : l'ID externe `L...`, les IDs externes `L...-S...`, `L...-F...`, gloses, représentations, Q de langue, catégorie et traits morphologiques Q. Ces Q ne deviennent pas automatiquement des propriétés Kristal ou des traits GF.
3. **UniMorph** : ligne de paradigme avec lemme, forme et traits, dans les ZIP d'origine, y compris certaines variantes de format corrigées en v0.3. Ce n'est **pas une définition**.

## Limitation fondamentale : échantillons ancrés, pas extraction exhaustive

L'index v0.5 conserve **un petit ensemble d'observations témoin** par famille, et non la totalité des occurrences et des sens de chaque lexème. La v0.6 relit précisément ces témoins (`source_id` + `source_line`), et non toutes les entrées partageant la même graphie. Si un lemme possède 30 sens ou plusieurs sources non sélectionnées, le dossier n'est **pas exhaustif**. Il est interdit de déduire une équivalence sémantique de la seule graphie, du POS ou de deux gloses similaires. Cette v0.6 sert à **qualifier les preuves et préparer les revues**, pas à finaliser les dictionnaires.

Les sources avec une seule famille ne sont pas ajoutées à la v0.5; elles restent dans l'index-v1 et pourront être traitées séparément après adaptation aux contrats diK. La v0.6 n'est pas un import diK/Framework v11 normatif.

## Reprise, performance, intégrité

- Stage transactionnel **par langue**. Si tu commences par `fr,en`, les autres langues s'ajoutent ensuite sans perdre les preuves déjà enregistrées. Les sources avec nouveaux ancrages sont rescannées, mais les enregistrements de preuve sont dédoublonnés.
- Lecture compressée **en flux** (Kaikki gzip, Wikidata bz2, UniMorph ZIP/XZ). Checkpoint transactionnel des nouvelles preuves + curseur **toutes les 25 000 lignes sources** par défaut, reprise après interruption. Pour gzip/XZ/bz2, une reprise doit redécompresser le début de l'archive jusqu'au curseur : les étapes passées ne sont pas réécrites, mais le coût CPU de ce saut existe.
- Un contrôle vérifie la taille et l'heure de modification de chaque archive contre son enregistrement dans l'index; toute divergence bloque sa lecture. Un fingerprint de catalogue vérifie la cohérence index-v1 avec la v0.5. Ces contrôles ne remplacent pas une signature officielle des éditeurs.
- Une transaction ne valide pas silencieusement des sources incomplètes. Les statuts `error`, `partial`, `unresolved` restent visibles dans `sources_enrichment.csv` et `latest.json`.
- Les exportations JSONL sont écrites temporairement puis renommées de façon atomique; leur SHA-256 est recalculable par l'interface. Le total de lignes et la couverture des ancrages sont mesurés.
- Pour une base de millions de candidats, la préparation et l'export peuvent prendre du temps et consommer plusieurs Go. Prévoir de l'espace sur D: et ne pas modifier les sources ou l'index pendant l'opération.

## Gouvernance diK / Framework

Les règles DIK-LEX-1 et les contrats diK de conciliation, de curation, de revue et d'identités restent **en amont**. Les dossiers générés portent `manual_sense_review_required=true`, `source_license_review_required=true`, `semantic_equivalence=null`, `may_be_published=false`. Les flags de licence ne se changent pas automatiquement.

La prochaine étape est la qualification de la preuve, puis **des propositions de rapprochement de sens soumises à revue**. Aucune publication EncyKlopedia, aucune modification du registre Kristal et aucun alignement Q/P ou grammatical GF n'en découlent.
