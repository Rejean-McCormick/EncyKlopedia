# Prompts opérationnels V32 — spécifications à intégrer aux futurs ZIP

**V32.1 :** toutes les sorties d’enrichissement décrites ici sont des **propositions EncyK**, consultables en mode exploratoire. Une admission dans un état Kristal est séparée et ne sera activée qu’après qualification de l’auteur; voir [modèle fédéré](../09_FEDERATION_KRISTAL/00_DECISIONS_V321.md).


**Statut : [CIBLE].** Les champs et formats V32 doivent être implémentés avant usage. Les textes ci-dessous expriment les objectifs et la charge de travail souhaitée; ils ne remplacent pas `INSTRUCTIONS_CHATGPT.md` des packs v27 actifs. Le manager génère automatiquement les IDs, chemins et bornes depuis la tâche; un utilisateur n'a pas à recopier des identifiants à la main.

## Template A — Revue de pertinence par concept/sujet

> **Mission : SELECTION ENCYCLOPEDIQUE V32, lot `{JOB_ID}`.**
>
> Tu reçois un paquet de candidats **déjà découverts par nos bases locales UNESCO, Wikidata et Wikipédia**. Les alignements et relations de graphe donnent une raison de les examiner, pas une conclusion. Ton rôle est de décider si le sujet et/ou l'article constituent une source réellement utile pour enrichir un Kristal rattaché au concept UNESCO indiqué.
>
> **Traite toutes les lignes assignées.** Organise le lot en sous-ensembles internes si nécessaire. Pour chaque `candidate_id`, rends exactement une décision `SELECT`, `REJECT` ou `HOLD` et une justification spécifique. Ne change jamais `candidate_id`, QID, `concept_id` ou la page. Un sujet peut convenir à plusieurs concepts : juge chaque paire séparément.
>
> **Sois favorable à une couverture large mais raisonnable.** Sélectionne un article qui apporte une connaissance significative, même si le concept n'occupe qu'une section substantielle. Rejette les rapprochements accidentels, homonymies et sujets réellement hors champ. Un lien Wikidata seul n'est pas une preuve suffisante. Réserve `HOLD` aux ambiguïtés concrètes, plutôt que d'en faire le résultat par défaut.
>
> **Reste efficace** : pas de dissertation par ligne, pas de recherche web inutile, pas de triple vérification; réponds avec des décisions complètes et des justifications brèves. Tu dois terminer **le volume effectif du lot**, pas fournir seulement un exemple ou les premiers candidats.
>
> **Sortie unique** : un ZIP avec `SELECTION_{JOB_ID}.csv` (champs exacts du contrat V32). Aucun commentaire prose hors du ZIP. Si une partie du lot est réellement impossible à examiner, indique son état **explicitement**; n'invente pas de décisions et ne prétends pas que l'analyse est complète.

## Template B — Production encyclopédique intensive par Kristal

> **Mission : CONSTRUCTION DE KRISTALS V32, lot `{JOB_ID}`.**
>
> Tu reçois **uniquement des sujets sélectionnés** et leurs sources locales : fiches Wikidata originales lorsqu'elles sont disponibles, et **textes intégraux de révisions Wikipédia**. Chaque sujet doit produire une base de connaissances privée très riche et réutilisable dans plusieurs branches UNESCO.
>
> **Travaille en profondeur et en quantité utile.** Pour chaque sujet, examine toutes les grandes sections pertinentes du texte. Cherche de nombreuses connaissances distinctives : identité, définition, typologies, caractéristiques, mécanismes, chronologies, événements décisifs, acteurs, institutions, lois, controverses attribuées, résultats, limites, relations et changements dans le temps. Les articles riches justifient nettement plus que quelques généralités; augmente le nombre de claims jusqu'à couvrir leur matière importante. Une petite page peut soutenir très peu de faits : ne gonfle pas artificiellement le résultat.
>
> **Utilise Wikidata comme structure**, et Wikipédia comme récit documentaire. L'index compact Skope n'est pas un registre de preuves : seuls les extraits de la révision Wikipédia et les déclarations Wikidata originales reçues peuvent soutenir des faits détaillés. Ne déduis pas automatiquement une vérité d'un P31/P279 ou d'une relation UNESCO.
>
> **Une vérification utile, pas trois rituels** : chaque claim doit avoir le bon sujet `kristal_id`, un prédicat/valeur intelligible, une phrase autonome, la source exacte, la révision ou l'identifiant de déclaration et, pour une source Wikipédia, un passage littéral retrouvé dans le wikitext. Si le texte est ambigu ou contradictoire, exprime l'incertitude ou conserve des variantes. Ne fabrique aucune citation, date ou institution pour remplir la quantité.
>
> **Couvre toutes les unités du lot** : inclure un bilan par sujet/source, y compris pour une source ayant peu de matière. Ne termine pas après quelques exemples simplement parce qu'une synthèse rapide semble plausible. Privilégie l'extraction de connaissances denses et distinctes, puis une courte revue de cohérence; aucun long rapport narratif séparé.
>
> **Sortie unique** : ZIP contenant `KRISTAL_DELTA_{JOB_ID}.json` selon le contrat V32, aucune publication, aucune admission canonique. Ne rends pas de messages intermédiaires prose comme résultat final. Si le budget empêche de couvrir le lot, signaler explicitement l'incomplétude plutôt que feindre un traitement intégral.

## Template C — Réparation ciblée d'un retour invalide

> Le job `{JOB_ID}` a été refusé **uniquement** pour les erreurs identifiées dans `ERRORS.json` : `{SUMMARY}`. Réutilise le contenu déjà produit dans `ORIGINAL_RETURN` sans recommencer les articles corrects. Corrige les lignes listées, préserve leurs identifiants et leurs véritables sources, puis fournis le **ZIP complet corrigé**. Ne modifie ni les autres jobs, ni les sources, ni la base locale. N'ajoute aucun fait non étayé pour combler une erreur de citation.

## Variables à renseigner automatiquement

`JOB_ID`, `SCHEMA_VERSION`, liste des `candidate_id`/`kristal_id`, chemins internes, langues de sortie, nombre de pages/sections et budget de texte. Le gestionnaire ne doit pas demander à ChatGPT de « choisir ses propres IDs ».

## Pourquoi nous n'imposons pas 5, 10 ou 60 minutes

Un modèle ne promet pas une durée de calcul et la durée mesurée par l'utilisateur inclut la manipulation des ZIP. **La charge est spécifiée par les objets et la profondeur d'extraction**, vérifiables dans le retour. Le but reste de donner une mission assez substantielle pour exploiter la capacité disponible sans induire une génération interminable, répétitive ou trompeuse.
