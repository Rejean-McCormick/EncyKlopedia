# EncyKlopedia → diK : qualification lexicale massive v0.5 (candidate)

**Statut : staging non canonique, aucune publication, aucun `exactMatch`.**

## Frontière et installation

- **Code** : dépôt EncyKlopedia sur **C:**, près de `package.json`.
- **Données** : `D:\EncyKlopedia` sur **D:**. Le pack ne migre aucun dump et ne réindexe pas les archives originales.
- **Entrée en lecture seule** : `30_working/lexical/harvester/index-v1/lexical.sqlite3` (v0.3), contenant les observations Kaikki, UniMorph et Wikidata L.
- **Sortie dérivée** : `30_working/lexical/harvester/dik-reconciliation-v1/`.

Démarrer par double clic sur `Concilier_Dictionnaires_diK_UI.pyw` ou `Start_Conciliation_diK.cmd` ; Python 3.10+ et Tkinter sont nécessaires.

### Parcours recommandé

1. **Voir le plan** : confirme la racine de données, les familles et le nombre de langues.
2. **Pilote français + anglais** : produit des candidats contrôlables, sans traiter toutes les langues.
3. **Explorer les candidats** : chercher un code de langue et un préfixe ; inspecter les sources, graphies et IDs externes en lecture seule.
4. **Lancer / reprendre les 6 848 langues** : un checkpoint transactionnel par langue ; le pilote est conservé.
5. **Vérifier les exports** : recalcule SHA-256 et nombre de lignes de chaque JSONL (peut prendre du temps sur le corpus mondial).
6. Transmettre `RAPPORT_RECONCILIATION.md`, `dik-review-queue.candidate.json` et `source_license_review_queue.csv` pour qualification des licences, des graphies et des identités.

En console (optionnel) :

```powershell
py -3 tools\dictionary-harvester\dik_reconciliation.py plan --data-root D:\EncyKlopedia
py -3 tools\dictionary-harvester\dik_reconciliation.py run --data-root D:\EncyKlopedia --languages fr,en
py -3 tools\dictionary-harvester\dik_reconciliation.py run --data-root D:\EncyKlopedia
py -3 tools\dictionary-harvester\dik_reconciliation.py verify --data-root D:\EncyKlopedia
```

## Livrables

- `reconciliation.sqlite3` : clés inter-familles candidates seulement, provenance et exemples bornés.
- `candidates/<lang>.jsonl` : shards UTF-8 par langue, avec SHA-256 et compte de lignes dans le manifeste.
- `languages_staged.csv` : statistiques et manifestes SHA par langue.
- `source_license_review_queue.csv` : sources non vérifiées, statut du parseur, licences à qualifier.
- `dik-review-queue.candidate.json` : pointeurs de transfert **candidat**, non conforme à un import normatif de dictionnaire curaté.
- `latest.json` / `RAPPORT_RECONCILIATION.md` : avancement et état. **Partiel** tant que toutes les langues ne sont pas traitées.

Toutes les sources à une seule famille restent dans `index-v1`, pas dans la file de rapprochement. Les candidats sont des clés `(langue, graphie NFKC/casefold)` qui apparaissent dans **au moins deux familles**. Le nombre de candidats devrait être proche du nombre de chevauchements de l'audit v0.4 lorsque l'index est identique ; le moteur n'invente ni score de confiance sémantique ni traduction.

Par candidat, on conserve des graphies d'origine en **NFC**, POS exemplaires, nombre d'observations, familles, jusqu'à quatre fichiers sources représentatifs par famille, chemin et numéro de ligne source, et si disponible ID lexical `L...`, Q de langue et membre ZIP. Cela n'équivaut **pas** à la preuve d'un même sens ; les unités Wikidata S/F et les définitions complètes ne sont pas encore projetées dans `index-v1`.

## Contrats existants : ne pas les contourner

- **LEX-003 / LEX-004 / LEX-005** : couches, versions, graphies NFC, variantes sans fusion abusive ; le catalogue ne devient pas automatiquement curaté.
- **XW-001 / XW-002 / XW-003** : recherche candidate, revue humaine avec décision et preuve KS pour une acceptation, licences et provenance par source ; aucune équivalence sur la seule graphie.
- **DIK-LEX-1 / 28_WIKIDATA_LEXEMES_GF_PIPELINE** : IDs L/S/F externes séparés, mapping Q des traits grammaticaux → GF nécessitant une revue ; aucun KQ/KP ne dérive d'une ligne lexicale.
- **DIK-LEX-1 / 29_ROADMAP_COLLECTION_MONDE** : source licence/hash, qualité et couverture mesurée, acceptation et publication comme étapes distinctes.

**Non réalisé dans v0.5** : compatibilité garantie avec les schémas diK/Framework, relecture intégrale des définitions/sens S, décisions humaines, revue des licences, contrôle SHA externe contre éditeur, attribution KS, crosswalk KQ/KP ou compilation GF. Cela exige d'autres qualifications explicites ; aucune exportation n'est automatiquement injectée dans le dépôt diK sur C:.

## Risques, performance et reprise

Le corpus courant représente environ 87 millions d'observations et jusqu'à ~1,55 million de clés multiesources candidates selon l'audit v0.4. La première exécution peut prendre du temps et produire de nombreux Go de fichiers dérivés : vérifier l'espace libre sur D:. Le moteur traite les lignes SQLite en streaming et n'écrit **qu'une langue à la fois** dans une transaction. Une langue interrompue est annulée, les langues précédentes restent validées. Les exports JSONL sont atomiques : ils se reconstruisent après interruption.

Un fingerprint de **catalogue** basé sur les sources/statistiques est vérifié en début et fin de parcours ; il ne garantit pas l'intégrité du contenu SQLite. Ne pas modifier l'index pendant le traitement. Si l'index change, conserver l'ancien snapshot et créer un dossier de staging versionné pour le nouvel index, ne pas les fusionner.

**Tests automatiques sur fixtures** ; aucune exécution sur le corpus réel de 87 millions de lignes depuis l'environnement de préparation.
