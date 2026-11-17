# Exploitation quotidienne et cadence pour 87 branches

**V32.1 :** toutes les sorties d’enrichissement décrites ici sont des **propositions EncyK**, consultables en mode exploratoire. Une admission dans un état Kristal est séparée et ne sera activée qu’après qualification de l’auteur; voir [modèle fédéré](../09_FEDERATION_KRISTAL/00_DECISIONS_V321.md).


## Routine principale

**[CIBLE]** Choisir le périmètre et lancer la préparation; envoyer les ZIP dans les conversations ChatGPT; déposer les retours; consulter les gains; relancer quand le stock utile est disponible. Le manager maintient la file, mais **ne crée pas de conversations ChatGPT et n'effectue pas d'upload vers elles**. Les prompts doivent être visibles et adaptés au pack effectivement téléchargé.

## Campagnes de branches

- Une branche est un **périmètre de concepts** et peut réutiliser des Kristals partagés avec d'autres branches. Il n'est pas obligatoire de clôturer intégralement la précédente avant la suivante.
- Démarrage rapide : construire les ancrages P3916 déjà présents, rejoindre `wiki_qid`, puis quelques traversées graphes pertinentes. Ne pas démarrer d'emblée un parcours exhaustif de toutes les catégories Wikipédia.
- Première sélection généreuse mais justifiée; enrichir les sujets acceptés, publier les claims dans le magasin privé. Alimenter la branche suivante à partir des mêmes sujets et claims sans relire les mêmes articles.
- Reprise/complétion : budgets indépendants pour cas sans QID, ambigus, liens entrants larges, lexique, HOLD, articles orphelins. Ne pas interrompre 87 branches pour perfectionner une seule.
- La finition sémantique exhaustive est reportée à une campagne d'agent ultérieure; V32 conserve l'historique utile pour pouvoir la mener.

## Principaux indicateurs, non trompeurs

| Compteur | Sens | Faux sens à éviter |
|---|---|---|
| `concepts_mapped_qid_candidate` | Ancrages P3916 candidats | Correspondances revues et approuvées |
| `qid_with_enwiki_page` | QID rejoignant une page anglaise locale | Toutes les pages Wikipédia pertinentes |
| `candidate_pairs` | Routes `(concept,page)` proposées | Paires approuvées ou stock exhaustif |
| `selection_accepted` | Couples jugés pertinents, provisoirement | Faits canoniques |
| `subject_kristals` | Sujets distincts, indépendamment des branches | Quantité de connaissances |
| `claims_with_source` | Assertions enrichies et sourcées | Couverture complète du monde |
| `zip_ready / awaiting_return` | Travail préparé et remis | Temps IA réellement écoulé |
| `source_missing / import_partial` | Travail à réparer | Perte irréversible |

Un objectif pertinent est le **débit de connaissances utiles sourcées par vague** et leur diversité, pas une barre artificielle de couverture à 100 %.

## Dimensionnement des sessions ChatGPT

Le guide utilisateur insiste sur la productivité des sessions, pas sur une durée magique. Une réponse en 5 minutes peut être excellente pour 100 cas très simples, mais médiocre si le ZIP contient 70 articles longs et que seuls cinq ont été exploités. Mesurer donc le taux réel de couverture et la densité : articles ayant un bilan, sections importantes traitées, claims contextualisés, sources citées, erreurs de forme. **Ne pas écrire dans les prompts « travaille exactement X minutes »** : l'interface n'a pas de chronomètre fiable du raisonnement, et une durée n'est pas une preuve de substance. Demander un traitement consciencieux de toute la capacité utile offerte par le pack.

## Sauvegardes et rétention

Le V3 de sauvegarde des résultats sait copier les SQLite de travail avec l'API SQLite et contrôles de cohérence; ne pas recopier les 125 Go d'index à chaque vague. Le V32 doit conserver une stratégie légère : snapshot des petites bases **avant opérations structurantes ou migration**, et éventuellement périodique par défaut. Les gros index sont des dépendances externes recensées, pas des artefacts à réingérer dans les ZIP de code.

## Journal minimum utile

Un événement par transition importante : découverte préparée, pack prêt, ZIP téléchargé/affecté (si observable), import accepté/refusé, incréments de Kristals/claims, source indisponible et reprise. Afficher l'état réel, pas le dump verbeux du moteur au milieu de la page. Logs détaillés accessibles en avancé.
