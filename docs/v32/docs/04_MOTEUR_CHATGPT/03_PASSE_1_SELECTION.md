# Passe 1 — sélection documentaire large mais pertinente

## Responsabilité

ChatGPT doit choisir **quels sujets/pages valent la construction d'un Kristal dans le scope UNESCO donné**, sans encore extraire tout le contenu encyclopédique. Les indications P3916, le type Wikidata, une relation `P31/P279`, une relation SKOS ou un score lexical ne sont **jamais des APPROVE automatiques**. Elles fournissent la liste des candidats et le contexte.

## Unités de décision

La décision porte sur la **paire `(concept_id, sujet QID/identifiant local, enwiki:page_id?)`**. Un même sujet ou article peut être sélectionné pour plusieurs concepts et branches. Si le QID n'a pas de page Wikipédia, il peut être retenu pour un Kristal Wikidata seul ou marqué `HOLD_ENRICHMENT`, plutôt qu'ignoré.

## Critères de SELECT

- Sujet intrinsèquement pertinent pour le concept ou pour une sous-dimension substantielle du concept.
- Article où l'on trouvera une matière encyclopédique exploitable : histoire, propriétés, rôle, mécanismes, enjeux, exemples importants, institutions/œuvres/personnes pertinentes.
- Relation de graphe claire et appuyée par le libellé, la description et, lorsqu'utile, un extrait de l'article.
- Ne pas exiger que 100 % de l'article porte sur le concept; une **section importante et réellement pertinente** suffit.

## Critères de REJECT et HOLD

- `REJECT` : homonymie, relation incidente, simple partage de mot, sujet manifestement hors périmètre, page non encyclopédique.
- `HOLD` : correspondance identitaire ambiguë, manque de résumé, statut de redirection confus ou nécessité d'un examen plus profond. **HOLD ne gèle pas toutes les autres branches.**
- L'absence de la preuve de pertinence **dans une métadonnée** ne signifie pas nécessairement que l'article n'est pas pertinent; si un court extrait serait décisif, demander le contexte avant de rejeter.

## Pack et sortie

Le pack peut regrouper 1 000/4 000 lignes ou plus selon sa taille réelle, mais il doit **produire une décision pour chaque candidate_id assigné**. Il n'est pas valide de renvoyer 25 exemples simplement parce que le lot contient 4 000 candidats. Pour les cas trop longs à couvrir dans la même mission, le manager prépare des **lots plus petits à l'avance**, avec leur propre job. Ne pas faire passer 3 975 omissions silencieuses pour HOLD.

## Critères de qualité proportionnés

Une justification de sélection peut rester courte mais spécifique au couple. Éviter les paragraphes répétitifs et le faux détail. Un contrôle léger du nombre d'IDs retournés et de la cohérence du format suffit; aucun rapport de triple revue n'est demandé. Utiliser les informations du ZIP, ne pas chercher sur le Web pour refaire les associations déjà indexées.

## Prompt opérationnel proposé

Voir [`05_PROMPTS_TEMPLATES.md`](05_PROMPTS_TEMPLATES.md). Le prompt ne doit pas exiger une réévaluation exhaustive de tout Wikipédia : **il demande la couverture du lot reçu**, avec des décisions fiables et une tolérance de rappel raisonnable.
