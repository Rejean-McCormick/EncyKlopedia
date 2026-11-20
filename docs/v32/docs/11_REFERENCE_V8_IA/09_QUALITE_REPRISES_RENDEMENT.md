# 09 — Qualité des faits, erreurs, PARTIAL, et mesures de productivité

## Trois niveaux de qualité, à ne pas confondre

1. **Validation structurelle** : la réponse correspond au job, au type de données et à l'identifiant de source, citation littérale présente.
2. **Validation probante** : la citation soutient réellement l'énoncé, les unités, dates et hypothèses sont correctement attribuées.
3. **Admission canonique** : processus d'autorité séparé, via le Kit et les îlots cibles.

Aucun niveau ne doit être présenté comme ayant accompli le suivant. Le volume de propositions n'est ni une mesure de vérité ni une preuve de couverture totale.

## Règles de rédaction documentaire

- Privilégier **un fait autonome, utile, précis, attribué à la bonne entité** plutôt qu'une phrase vague.
- Distinguer faits mesurés, projections conditionnelles, théories, expériences et récits historiques.
- Associer chaque nombre à son unité, période, lieu, population et contexte quand le texte les présente.
- Privilégier les citations factuelles courtes et exactes plutôt qu'un long préambule bibliographique contenant le passage accessoirement.
- Ne pas combler les sections manquantes par supposition; `incomplete` permet un futur complément.
- Conserver la structure `source_coverage` et notes d'incomplétude pour éviter les réanalyses inutiles.

## Retours partiels

Un ENR de 60 articles peut inclure 705 faits corrects sur le plan technique mais déclarer 52 articles `incomplete`. C'est un **succès partiel utile**, non une preuve de complétude. Le moteur conserve les faits valides et peut reprendre les articles lorsque la politique l'autorise. Chaque complément doit tenir compte de `prior_propositions`, de la couverture antérieure et, idéalement, des sections non traitées.

## Erreurs d'import

Les journaux historiques Météorologie ont indiqué **379 + 47 + 80 = 506 lignes refusées** sur trois jobs. Ces refus ne doivent pas être attribués à une cause précise sans lecture de `import_errors.error` et du payload.

Procédure de récupération :

1. Identifier `job_id`, retour archivé, ordinal et code/message d'erreur.
2. Comparer le payload refusé au **pack source original** et au contrat du moteur installé.
3. Catégoriser : citation absente, mauvaise révision, mauvais sujet, objet typé incorrect, doublon, formulation non probante, dépassement de limite.
4. Distinguer **réparation d'une ligne jamais acceptée** de **remplacement d'un fait déjà accepté via `supersedes`**.
5. Reconstruire un nouveau flux de travail ou retour correct seulement quand le contrat d'importation l'autorise.
6. Mesurer les faits sauvés, ne pas réimporter aveuglément le même ZIP.

## KPI pour 88 branches

| KPI | Numérateur / indicateur | Pourquoi |
|---|---|---|
| Couverture documentaire | `COUNT(DISTINCT page_id)` traité par branche | Évite de confondre candidats conceptuels et pages |
| Couverture thématique | Concepts UNESCO avec ≥1 article pertinent traité | Réduit l'inégalité entre concepts dominants et niches |
| Rendement des transports | Faits nouveaux acceptés / transferts ChatGPT | Réduit les manipulations |
| Densité de connaissances | Faits distinctifs par section/article complet | Évite le résumé superficiel |
| Fidélité aux sources | Proportion de faits soutenus réellement par citation | Complète le contrôle d'existence littérale |
| Taux de perte | Lignes invalides / lignes soumises | Guide le diagnostic des prompts et du validateur |
| Taux de reprise utile | Nouveaux faits / mission PARTIAL supplémentaire | Empêche les boucles sans gain |
| Réemploi interbranches | Documents/révisions réutilisés sans nouvelle analyse | Économise la capacité IA |
| Durabilité | Retours idempotents, reprises après interruption | Assure aucun travail perdu à cause d'un crash |
| Canon | Propositions admises via Kit réel, **séparées** du cumul | Empêche les faux « publiés » |

## Tests d'acceptation d'une optimisation

Comparer à une ligne de base V8 sur un échantillon de concepts riches/pauvres et d'articles longs/courts : taux SELECT par route, coût en mots, propositions acceptées, qualité probante, pages distinctes couvertes, temps humain. Une automatisation qui augmente le nombre de candidats mais diminue la précision et sature les postes n'est pas une amélioration prouvée.
