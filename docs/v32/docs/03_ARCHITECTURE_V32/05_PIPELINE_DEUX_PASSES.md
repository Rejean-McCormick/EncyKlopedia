# Pipeline V32 — deux passes documentaires, un seul graphe de sujets

**CORRECTION V32.1 :** « sujet/Kristal retenu » veut dire **sujet sélectionné comme cible possible**, pas création d’îlot. La sortie de passe 2 est un [registre EncyK de propositions provisoires](../09_FEDERATION_KRISTAL/03_PIPELINE_IA_PROPOSITIONS.md); l’[admission](../09_FEDERATION_KRISTAL/04_ADMISSION_KIT_REPRISE.md) dans un état Kristal est distincte. Les étapes ci-dessous décrivent les entrées et le débit, mais la phrase « upsert direct dans le Kristal » est historique.

**DÉCISION V32.2 :** la cadence de travail est désormais explicitement `sélection → extraction → cumul privé`, répétée à grande échelle. La [promotion dans les Kristals UNESCO préparés](../09_FEDERATION_KRISTAL/09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md) intervient par campagne/vague mûre, **pas par pack ZIP**. La consolidation/assignation privée précède toute opération d’auteur.


## Objectif opérationnel

Ne plus mettre indistinctement 4 000 correspondances titre/concept devant ChatGPT puis lire tous les articles catalogués. V32 fabrique des candidats structurés à partir du graphe, fait choisir **ceux qui méritent un enrichissement documentaire**, et réserve le travail d'extraction coûteux aux sources sélectionnées. La sélection est une décision **contextuelle par concept**, et l’enrichissement est une production **réutilisable de propositions contextualisées**; le périmètre d’auteur de chaque îlot est indépendant.

### Passe 0 — préparation locale (sans IA)

- Charger les 88 branches et leurs concepts, notes/relations et P3916 candidates.
- Pour les QID uniques, joindre les pages EN indexées, construire des routes Wikidata de premier niveau et, au besoin, des routes fallback.
- Grouper par article/QID pour éviter de faire lire plusieurs fois le même texte.
- Calculer les marqueurs : un QID ancré direct, une instance/sous-classe, une relation SKOS, un fallback lexical, un article EN absent, etc.
- Préparer des paquets ayant assez de contexte pour une décision; **pas de long wikitext de toutes les pages** tant que la sélection ne l'exige pas.

### Passe 1 — sélection de pertinence ChatGPT

Entrées : `(concept, labels/scope_notes, sujet QID + label/description, page_id/titre, route de graphe, extrait Wikipédia court si disponible)`, plus contexte de branche. **Une réponse par paire unique**, même si le lot a regroupé plusieurs paires d'un même article.

Sorties : `SELECT`, `REJECT`, `HOLD`; raison brève et précise, niveau de confiance si utile, marqueurs d'ambiguïté. Un article à faible lien ne doit pas être inventé comme pertinent; `HOLD` permet de reporter sans geler la production entière. Tous les retours restent privés et révisables.

Éviter les faux négatifs : lorsqu'un article traite substantiellement un concept dans une sous-section, il peut être **sélectionné même si ce concept n'est pas le thème unique de l'article**. En revanche, partager uniquement un mot générique ou une relation Wikidata lointaine ne suffit pas.

### Passe 2 — enrichment Kristal ChatGPT

Entrées : les **sujets sélectionnés** et leurs articles entiers (wikitext à la révision disponible), plus les entités Wikidata complètes lorsque l'extraction ciblée est accessible, et les `concept_id`/branch scopes de la passe 1.

Sorties : un delta de **propositions structurées par sujet et domaine**, avec un grand volume de faits **distinctifs et non redondants** selon la richesse de l'article : définitions, typologies, mécanismes, étapes historiques, personnes/institutions, événements, décisions, nombres pertinents, controverses attribuées, variantes, relations. Ajouter une citation/localisateur authentique pour chaque fait; aucun quota fixe par article et aucune exigence de triple audit des mêmes phrases.

Le fait peut concerner un sujet QID différent du titre de l'article si le passage est explicite. Dans ce cas, conserver la source de page et l'identité du bon sujet. Les liens aux concepts UNESCO hérités de la sélection **n'impliquent pas** que tous les faits sont pertinents pour toutes les branches; les vues filtrées restent possibles.

### Import local et cumul

- Vérifier seulement que le retour se rapporte au job attendu, n'est pas déjà appliqué, que les clés et révisions existent et que les citations présentées apparaissent dans les sources reçues.
- Créer/récupérer les sujets référencés et propositions EncyK; conserver citations et conditions. **Aucune écriture automatique dans un état Kristal.**
- Enregistrer les passages incertains et contradictions plutôt que les convertir en assertions certaines.
- Mettre la tâche à `done` et réapprovisionner les postes à partir des files **sans redécouvrir systématiquement**.
- Continuer d'autres branches, même si certains articles sont `HOLD` ou si un worker a échoué.

## Ce que les deux passes apportent

Le coût de lecture longue de Wikipédia n'est payé que pour des sujets utiles; les mêmes pages et faits sont réutilisés entre branches; la construction n'est plus prisonnière d'un ancien catalogue `article-first`. **Les deux décisions ne doivent pas être confondues** : choisir une page est une décision de classement documentaire; la passe 2 est un acte d’extraction et de proposition de connaissances. **Admettre** dans un état Kristal constitue une opération séparée.

## Stratégies de progression

- Priorité de travail : branches actives, candidats directs P3916, puis graphes à rendement élevé, puis stratégies complémentaires.
- Au niveau de la branche : afficher nombre de sujets sélectionnés, connaissances nouvelles, articles lus, QID sans page, tâches ouvertes, principales lacunes.
- Une fois le stock immédiatement rentable traité, passer à une autre branche; laisser des queues de rappel, ambiguïtés et HOLD pour l'agent de finition en 2027.
