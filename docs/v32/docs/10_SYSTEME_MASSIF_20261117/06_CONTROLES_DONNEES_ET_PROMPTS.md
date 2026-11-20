# 06 — Qualité, pertinence, prompts et exploitation du retour

## Notre objectif de qualité n'est pas une perfection impossible

Il faut maximiser les **faits nouveaux avec une preuve retrouvable et une attribution de sujet correcte**, en tolérant les incertitudes et `PARTIAL` documentés. Le système ne doit pas perdre 379 faits parce qu'un pack est imparfait; il doit **sauver le valide et rendre le reste réparable**. Mais il ne doit pas convertir artificiellement une citation exacte en démonstration de vérité scientifique.

## A. Passe 1 : SELECT / REJECT / HOLD

**Contenu du pack** : un candidat est une association exacte `{branch_id,concept_id,page_id,revision_id,subject_key,priority,route}`, plus titre/extrait et libellé du concept. Le contexte peut être `TITLE_AND_GRAPH_ONLY_NO_ARTICLE_TEXT`, ce qui doit provoquer plus de `HOLD` lorsqu'il manque de preuve.

**Règle d'arbitrage** : SELECT si le **sujet principal de l'article** documente substantiellement le concept; REJECT si simple lien marginal, homonyme, liste sans contenu ou mauvais sens de relation; HOLD si ambiguïté substantielle, texte manquant ou absence de contexte pour trancher.

**Une sélection généreuse est compatible avec une encyclopédie titanesque**, mais pas les liens grossièrement erronés. Mesurer SELECT par type d'origine : Skope P31, titre lexical, wikilink, relation UNESCO.

**Taille de mission** : 300 candidats est bon pour les données homogènes / extraits courts; si passages longs et incertains, une taille plus petite peut améliorer les justifications. Ne pas juger seulement à la taille du ZIP compressé.

## B. Passe 2 : extraction sourcée

Sont requis : énoncé français autonome, sujet exact du pack, concept(s) si pertinents, révision, citation texte **verbatim**, locator section, nature de l'objet, qualifications (date, lieu, unité, hypothèse, incertitude) lorsque le texte les prouve. Ne pas inventer de source absente, de référence Wikidata ou d'équivalence Kristal.

**Six passes V31.8** (V6 les restitue) :

1. Lire la carte des sections et repérer les dimensions riches.
2. Parcourir le texte complet : mécanismes, chiffres, lieux, dates, formes, nomenclatures, contextes et controverses.
3. Deuxième parcours pour omissions et passages minoritaires.
4. Décomposer en faits utiles **distincts**, sans paraphrases répétitives.
5. Vérifier chaque citation par rapport à la **bonne révision**, son sujet et sa portée probante; ne pas confondre notes bibliographiques avec preuves.
6. Déclarer `processed`, `incomplete`, `blocked` ou `no_relevant_claim`, avec une note informative et domaines non couverts.

**Ne pas confondre le dossier de lecture avec une source autonome** : les extraits du guide sont des aides, l'original complet et son SHA sont la vraie matière documentaire.

## C. Bon volume : davantage de connaissance, pas de contexte ingérable

- V6 cible souple 45 000 mots pour la **mission**; un article plus long est isolé jusqu'au plafond octets ferme 45 Mio.
- Un paquet de 60 articles courts peut convenir; 60 longs ne devrait pas être la règle. Les packs de 143 000 mots du début montraient le danger.
- **CIBLE NON IMPLÉMENTÉE** : fractionnement physique d'un même article par sections en missions ordonnées avec chevauchement limité, en conservant hash de l'article intégral + offsets/span citables.
- Pour limiter les copier-coller, grouper les **packs de sélection** est déjà possible. Les enrichissements trop volumineux méritent plutôt compression/optimisation des textes et dossier de lecture que collage d'un gigantesque ensemble à l'aveugle.

## D. Contrôles existants à l'import : ce qu'ils prouvent

V32 vérifie notamment :
- le `job_id`, la portée des `page_id`, `subject_key`, `revision_id` et `concept_ids` attendus;
- la conformité JSON et des types `text`, `date`, `number`, `entity`, `boolean`;
- les contraintes de taille/structure et la présence **littérale** de `source_quote` dans le texte d'origine;
- l'interdiction d'admission canonique ou de publication dans un retour;
- la déduplication exacte par identité de proposition et les occurrences, les retours idempotents.

**Il ne prouve pas** : qu'une citation démontre le fait; que les nombres ont la bonne unité; que la proposition est non controversée; qu'aucune paraphrase équivalente n'existe; que l'article a été exhaustivement traité; qu'une identité KQ est correcte.

## E. Les trois incidents d'import à traiter sans perdre le rendement

Selon journaux : `ENR_000007` 379 invalides / 463 soumis, `ENR_000018` 47 / 452, `ENR_000022` 80 / 566. **506 lignes invalides**, 975 lignes nouvelles acceptées sur ces lots. Les autres données restent dans le registre.

**Procédure recommandée (pas encore automatisée)** :
1. Lire `import_errors` avec l'identifiant job, le SHA du ZIP de retour, l'ordinal et le motif; ne **pas** réimporter le même retour en espérant une différence.
2. Regrouper les motifs par cause : mauvaise révision, citation non présente, cible étrangère, type incohérent, preuve non probante.
3. Préparer une **mission de correction** utilisant le pack original (non modifié) et les payloads refusés; ne corriger que les lignes vérifiables. Conserver ordinals et justification.
4. Si le contrat `--correction` du job original exige `supersedes` d'une proposition valide, **ne pas l'utiliser abusivement pour des lignes jamais acceptées**. Un nouveau flux de réparation est nécessaire pour ces cas. Rester honnête sur ce qui est supporté.
5. Soumettre un nouveau job de complément ciblé si requis et mesurer « lignes sauvées ».

**Ne jamais produire automatiquement une citation voisine au hasard** : elle risquerait de ne plus appuyer l'assertion.

## F. Reprise PARTIAL : politique anti-boucle

- Conserver les propositions déjà présentes (et leurs occurrences), les sections/notes déjà couvertes.
- Maximum provisoire : 1–2 compléments ciblés par `page_id/revision_id/profile`, puis mise en veille si gain faible; chiffre de politique à calibrer.
- Prioriser les grands documents scientifiquement riches, ou un concept peu couvert, plutôt qu'un ordre purement « plus ancien d'abord ».
- `source_results` donne un point de départ; une **mémoire d'offsets de sections** serait encore meilleure, mais est une extension future.
- Aucune tâche de complément auto sur un job actif ou sur un document dont la source a changé sans nouvelle identification.

## G. Déduplication prudente et réemploi

- Dédup exacte V32 : utile, conforme; une paraphrase d'une même information peut rester un autre `proposal_id`.
- **CIBLE** : regrouper *similarités candidates* pour revue, jamais supprimer de façon aveugle plusieurs sources indépendantes.
- Réutiliser des faits d'une même révision Wikipédia dans plusieurs branches si la correspondance de **concept et sujet** est attestée; préserver l'occurrence/route pour chaque concept. Le modèle V32 fait déjà des réutilisations strictes `source_results` `PROCESSED`.
- Les données structurées Wikidata originales (si accessibles) doivent entrer sous leur **propre type de provenance**, pas emprunter une fausse citation Wikipédia.
