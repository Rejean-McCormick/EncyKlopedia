# Découverte V32 — identifiants avant heuristiques

**V32.1 :** toutes les sorties d’enrichissement décrites ici sont des **propositions EncyK**, consultables en mode exploratoire. Une admission dans un état Kristal est séparée et ne sera activée qu’après qualification de l’auteur; voir [modèle fédéré](../09_FEDERATION_KRISTAL/00_DECISIONS_V321.md).


## Ordre de recherche par concept

**Niveau A, direct** : mapping P3916 candidat unique → QID → `wiki_qid` → page EN → candidature. Le lien direct est le plus fort signal d'identité mais la pertinence contextuelle du concept reste une décision de sélection.

**Niveau B, graphe** : voisins Wikidata du QID ancré avec propriétés et **direction explicites**. Examiner les propriétés utiles selon la nature du concept; privilégier d'abord les P31/P279 entrantes pour les notions véritablement classifiantes, et des relations de thème/partie/rôle quand elles sont pertinentes et réellement indexées.

**Niveau C, thésaurus** : relations UNESCO `broader`, `narrower`, `related` pour proposer des QID déjà ancrés à des concepts voisins, avec une route différente et une priorité moindre. Éviter les boucles/tours de graphe illimités; code v31.11 fournit déjà un exemple de curseur.

**Niveau D, Wikipédia** : catégories, liens, titres, indices lexicaux pour candidats sans QID ou absents du graphe; réutiliser les modules v25/v28/v31.10 plutôt qu'un nouveau scan plein texte de 125 Go.

## Typage minimal de concept

| Famille indicative | Pistes de parcours initiales | Risque à éviter |
|---|---|---|
| Classe d'organisations / établissements | P31 entrant, P279 entrant puis P31 sur sous-classes | Candidats associés à des catégories trop génériques |
| Discipline / domaine de connaissance | Sous-domaines, objets/sujets, liens d'articles spécialisés | P31 « instance de discipline » peu utile |
| Personnes / métiers | P106 et relations de rôle/occupation *si indexées* | Confondre la profession avec tout le sujet d'une biographie |
| Événements / politiques | Sujet, partie de, période, lieu, institutions impliquées | Partager une date/lieu n'est pas une pertinence substantielle |
| Concept normatif / droit | Liens notionnels/thésaurus, jurisprudence associée via recherche | Traiter une notion abstraite comme classe d'objets |
| Lieu / région / patrimoine | Localisation, taxons/objets régionaux selon le domaine | Boule de neige de relations sans lien éducatif ou sémantique |

**Les exemples de propriétés autres que P31/P279 sont des hypothèses à valider sur le corpus local.** Le moteur doit lire un `discovery_policy` éditable par grande famille, pas des règles universelles codées en dur pour 4 500 concepts.

## Route et déduplication

Une `CandidateRoute` précise : `branch`, `concept`, `anchor_qid`, `candidate_qid`, `page_id`, `property_path` (PID + direction + profondeur), `origin`, `priority`, `discovery_run`, `status`. Plusieurs routes vers la même paire `(concept,page)` sont **fusionnées en un candidat à examiner**, tout en conservant les chemins dans l'explication.

L'absence de score élevé **ne supprime pas** la route; elle peut être traitée en priorité secondaire. La sélection documentaire tranche lorsque les passages utiles sont disponibles.

## Cursors et budgets [CIBLE]

- Pagination persistante par `(concept,ancre,propriété,direction,dernière clé)`; éviter les parcours qui recommencent depuis zéro à chaque vague.
- Définir **un budget par vague**, non un plafond définitif. Si un concept a 1 million de voisins, le moteur peut s'arrêter à 10 000 candidats par phase et continuer plus tard, ou changer de stratégie si le rendement est faible.
- Mesurer `qids_examined`, `pages_found`, `pairs_new`, `pairs_already_decided`, `routes_by_property`, `selected_ratio`, `unexplored_routes`.
- Eviter une explosion combinatoire de 87 branches × chaque article × 4 500 concepts. Commencer par les QID et leurs arêtes indexées.

## Cas importants

- QID sans page EN : conserver sujet `wikidata_only`, pas fausse page.
- Plusieurs QID pour un même concept P3916 ambigu : candidats d'alignement à départager; pas de blocage de toutes les branches.
- Redirect/désambiguïsation : suivre la résolution de page avec une route explicite, pas fusion silencieuse de deux identités différentes.
- Éventuel article pertinent sans QID : fallback de catégorie/texte, sujet local en attente d'identité Wikidata.
- Doublon interbranche : conserver une seule collecte de contenu et plusieurs scopes; le fait n'est pas recopié 87 fois.
