# Contrats, modèle de données logique et traçabilité v31

**Statut :** design cible — **aucune migration SQL autorisée par ce document**. Les noms ci-dessous sont des interfaces proposées, non des tables installées ni des contrats natifs prouvés. Revenir aux implémentations v25/v27/v28/v30 observées dans le code pour fixer les clés, contraintes et statuts finaux.

## 1. Séparation des domaines de données

| Domaine | Entité ou famille | Propriétaire autoritaire | Qui peut écrire ? |
|---|---|---|---|
| Corpus encyclopédique | Page, lien, catégorie, QID, révision | Index Wikipédia existants | Processus d'ingestion historique, **pas** le classificateur |
| Taxonomie | Branche, concept, hiérarchie | Catalogue v25 + ressources UNESCO contrôlées | Gestionnaire de branches compatible v25 |
| Profil | Type, sujets, signaux, version | Couche de qualification cible | Qualification seulement, après contrôle de source |
| Hypothèses | Association article–branche ; article–concept | Couche de qualification cible | Qualification seulement ; statut provisoire |
| Tâches et preuves figées | Job, ZIP, `candidate_id`, hash, état | **Station v30** | Station native uniquement |
| Décisions et affectations | APPROVE, REJECT, HOLD ; affectations documentaires | Import v28 / catalogue v25 | Importateur natif validé |
| Claims privés | Assertions, citations, visites | **Kristal v27** | Moteur Kristal natif |
| Observabilité | Statistiques, versions, performance, audits | Tableau de bord et exports | Rapporteur, journaux auxiliaires non canoniques |

**Le principe de propriété unique interdit d'avoir deux mécanismes d'attribution de `candidate_id` ou deux stations distributrices des tâches.** Le module de qualification n'a pas le droit de réécrire `review_index` sur des tâches scellées.

## 2. Identités et versions obligatoires

- **Page :** `wiki` (p. ex. `enwiki`) et `page_id`. Le titre est une étiquette mutable. Le QID enrichit la correspondance inter-projets et peut être absent.
- **Snapshot :** source du dump, empreinte/vérification, instant de collecte et, si disponible, métadonnées d'ingestion. Une révision précise est `revision_id`; pour un profil textuel ou une citation, sa présence est indispensable.
- **Branche :** `branch_id` natif ; éventuellement `branch_version`, `config_sha` ; ne pas inventer de nouveaux identifiants.
- **Concept UNESCO :** `(vocabulary,concept_id)`, plus version des libellés et notes de portée. `label_en/fr` seuls ne sont pas des identifiants.
- **Proposition de revue :** `candidate_id` natif ; une proposition correspond à un contexte conceptuel spécifique, pas seulement à un article.
- **Preuve :** provenance détaillée, origine, version/snapshot et `evidence_sha256` natif dès que scellée ; aucune mutation silencieuse.
- **Modèle :** `classifier_version`, `feature_version`, paramètres, méthode et `run_id` ; indispensable pour comprendre pourquoi un candidat a été priorisé.

## 3. Etats logiques : ne jamais les confondre

### 3.1 Article inventorié (hors revue)

`INVENTORIE → PROFILE → BRANCHES_PROPOSEES` ; possibilités parallèles `A_PRECISER` ou `SANS_BRANCHE_PROPOSEE`. Une page peut passer à un nouveau profil lorsque sa révision change ; le profil historique est conservé ou référencé.

### 3.2 Qualification de paire

`CANDIDAT_LIBRE → PRIORITAIRE | A_ENRICHIR | EXPLORATION_DIFFEREE` ; chaque état est recalculable et audité. `EXPLORATION_DIFFEREE` signifie *non sélectionné actuellement*, **pas REJECT**. Le candidat reste recherché et récupérable.

### 3.3 Revue v28

La station possède ses états natifs `review_index.state` / `jobs.status` (valeurs exactes à confirmer dans le code). Une fois le job créé, scellé ou envoyé, le classement externe ne modifie plus son contenu. Le retour importe des décisions `APPROVE/REJECT/HOLD` selon le contrat de la station. `HOLD` conserve l'incertitude et doit permettre une nouvelle preuve/revue conformément aux règles natives.

### 3.4 Canonique / Kristal

`APPROVE` qualifie une **affectation documentaire** ; l'admission canonique est un acte indépendant, jamais déclenché par simple classification ou import v28. Les claims privés Kristal conservent leurs preuves/versions et ne traversent pas cette frontière par défaut.

## 4. Objets d'échange proposés (illustratifs, hors contrat natif)

### 4.1 ArticleProfile

```json
{
  "schema": "encyklopedia.article_profile.v31/1",
  "wiki": "enwiki",
  "page_id": 123456,
  "snapshot_id": "snapshot-source-a-confirmer",
  "revision_id": 987654,
  "article_type": ["institution_educative"],
  "topics": ["enseignement_superieur"],
  "source_signals": [
    {"kind": "category", "source_key": "categorie-identifiee", "strength": "medium"}
  ],
  "text_verified": false,
  "profile_version": "profile-rules-v1",
  "status": "PROVISOIRE"
}
```

Les numéros sont des exemples de format, **pas des pages ou révisions attestées**. L'état `text_verified=false` empêche qu'on présente un rapprochement de catégorie comme preuve de contenu.

### 4.2 BranchProposal

```json
{
  "schema": "encyklopedia.branch_proposal.v31/1",
  "wiki": "enwiki",
  "page_id": 123456,
  "branch_id": "BRANCHE_EXISTANTE",
  "profile_version": "profile-rules-v1",
  "score": 0.76,
  "reason_codes": ["CATEGORY_SPECIFIC", "DIRECT_LINK_NEIGHBOURHOOD"],
  "status": "PROPOSEE_NON_VALIDEE",
  "classifier_version": "branch-routing-v1"
}
```

`score` ne doit pas être interprété comme probabilité calibrée avant une validation indépendante. Un même article peut générer plusieurs objets avec des branches différentes ; la liste peut être vide.

### 4.3 PairQualification

```json
{
  "schema": "encyklopedia.pair_qualification.v31/1",
  "candidate_id": "ID_CANDIDAT_NATIF",
  "branch_id": "BRANCHE_EXISTANTE",
  "wiki": "enwiki",
  "page_id": 123456,
  "vocabulary": "VOCABULAIRE_EXISTANT",
  "concept_id": "CONCEPT_EXISTANT",
  "evidence_sha256": "empreinte_native_si_figee",
  "concept_definition_version": "version-ou-empreinte",
  "features_version": "signal-v1",
  "classifier_version": "pair-ranker-v1",
  "priority_score": 0.62,
  "lane": "A_ENRICHIR",
  "reasons": ["NOTE_DE_PORTEE_NON_VERIFIEE", "EXTRAIT_ABSENT"],
  "locked_task": false,
  "run_id": "run-exemple"
}
```

Ce document ne prescrit **aucune réécriture** de l'empreinte source pour y ajouter ces champs. Ces données appartiennent à un registre auxiliaire ou à une interface de lecture/planification tant que le producteur n'a pas adopté un contrat versionné.

## 5. Stockage et anti-duplication

### 5.1 Principe d'hébergement

En premier, chercher les tables et les fonctions équivalentes dans les stades sémantiques v4/v6 et le catalogue v25. Si elles couvrent déjà le besoin, les réutiliser. Sinon, ajouter un **petit magasin dérivé** (pas un nouveau graphe Wikipédia ni un second catalogue canonique). Son emplacement exact sera décidé après examen du code et des flux de sauvegarde.

### 5.2 Schéma logique minimal si besoin

Ce sont des **noms de concepts**, pas du DDL prêt à exécuter :

- `profile_versions` : clé `(wiki,page_id,snapshot_id,revision_id,profile_version)`, signaux et provenance compressés, statut de vérification du texte.
- `branch_proposals` : clé du profil + `branch_id`, score, raisons, modèle et statut.
- `pair_qualifications` : clé métier `candidate_id` + version des preuves/règles, priorité, file, raisons, provenance.
- `selection_runs` : entrée, budget, modèle, seed d'exploration déterministe, quotas et hash de sortie.
- `selection_items` : candidats retenus, différés, motifs, décision de quota, ordre ; ne jamais perdre les différés.
- `evaluation_runs` : entraînement, test, protocole, résultats par concept, incertitude et indicateurs de rappel.
- `data_sources` / `lineage` : source du snapshot, hachages, fraîcheur, extraction et dépendances.

Les objets dérivés sont **supprimables/recalculables** sans perte de données canoniques ; leur reconstruction doit pouvoir être reproduite à partir des versions enregistrées. Pas de copie des textes complets ni des liens de la base de 125 Go.

## 6. Portes de compatibilité pour la station native

Avant qu'une nouvelle file de sélection alimente des tâches :

1. La proposition existe dans la source et ses identifiants sont inchangés.
2. La tâche est réellement **libre** selon la logique native ; ne jamais inférer le libre en utilisant seulement une colonne sans lire le code.
3. Le job n'est pas scellé, attribué ou importé, et la protection de génération n'est pas active.
4. La sélection déterministe ne change ni le contenu du CSV baseline, ni ses preuves, ni `source_sha256` ou `bundle_sha256` après scellement.
5. Le retour correspond exactement au nombre, à l'ordre/ensemble d'identifiants et aux décisions autorisées par le contrat natif.
6. Les erreurs sont visibles, l'import est transactionnel et rejouable ; la sauvegarde/rollback sont prêts.
7. Une option explicite permet de revenir au producteur d'origine (`qualification.mode=off`).

## 7. Gouvernance des preuves de lien

Types observés dans les packs : `WIKILINK`, `CATEGORY`, `SUBCATEGORY`. Ils servent au **repérage**. Un `WIKILINK` n'est pas automatiquement une preuve de correspondance substantielle. Pour les sections/passages, n'indiquer un localisateur que si un extrait a réellement été retrouvé et validé au bon `revision_id` ; sinon stocker `NOT_AVAILABLE` / `SIGNATURE_MISMATCH` sans citation simulée.

Il faut conserver la distinction entre source d'origine (`seed_page_id`) et page candidate (`page_id`) ; dans les packs enrichis, faire correspondre les contextes par `candidate_id`, jamais par ordre de fichier seul.

## 8. Définition des contrats à figer après revue de code

Les points suivants restent à préciser par inspection du dépôt natif :

- Types exacts de `branch_id`, contraintes uniques de `assignments`, stratégies de mise à jour de titres et versions.
- Enumérations natives `review_index.state` et `jobs.status`, et règles exactes de transition.
- Format/version du manifeste des packs, algorithmes de hash de chaque preuve et critères de collision.
- API des fonctions de génération / réserve / reprise, et point d'insertion sans migration invasive.
- Règles natives de réconciliation des pages Wikipédia par QID, redirect, title et namespace.
- Stratégie de snapshot d'une petite DB active et politiques de sauvegarde déjà implémentées.

**Aucune migration ne doit être lancée sur la base de contrats supposés.**
