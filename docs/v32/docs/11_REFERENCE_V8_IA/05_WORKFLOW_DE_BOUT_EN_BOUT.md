# 05 — Workflow de bout en bout : de la source au cumul privé

## Pourquoi plusieurs étapes ?

Une **correspondance lexicale ou Wikidata** n'implique pas que la page Wikipédia traite réellement un concept UNESCO. Inversement, un article pertinent peut ne pas porter le mot exact du concept. La sélection permet de vérifier cette pertinence, puis l'enrichissement transforme la **source entière** en faits distinctifs et sourcés. L'importateur garantit la cohérence technique et le suivi des propositions; la publication reste distincte.

## Séquence opérationnelle complète

| Étape | Entrées | Action | Sorties et contrôle |
|---|---|---|---|
| 0. Initialiser | 88 références UNESCO versionnées | Importer branches, concepts, alias et mappings candidats | Registre privé **vierge** (pour V8 neuf), sans missions V31 |
| 1. Découvrir | Skope compact, titres, liens, ontologie UNESCO | Explorer par budgets et curseurs, enregistrer routes | `candidates`, `candidate_routes`, curseurs ; pas auto-SELECT |
| 2. Diversifier | Concepts/branches et priorité | Éviter que les concepts dominants monopolisent chaque pack | Échantillonnage de paires article/concept |
| 3. Sélectionner | `SEL_...zip` et instructions internes | ChatGPT décide `SELECT`,`REJECT`,`HOLD` pour chaque identifiant | `selection_decisions.csv` dans un retour ZIP |
| 4. Importer choix | ZIP + mission et manifeste original | Vérifier IDs, décisions, justification, doublons | `decisions`, `decision_history`, états candidate |
| 5. Préparer source | Pages sélectionnées, index direct, XML original | Résoudre texte exact, révision, hash, lecture/sections | `ENR_...zip` incluant sources et descriptions |
| 6. Enrichir | Wikitext, QID, concepts, profils, prior_propositions | Décomposer en faits FR distincts et citations EN verbatim | `kristal_delta.json`, `source_coverage` par page |
| 7. Importer faits | Delta + pack d'origine | Vérifier format, portée, citations exactes; enregistrer erreurs | `proposals`, citations, occurrences, `source_results`, reçus |
| 8. Réutiliser | Une page/révision déjà traitée | Vérifier profil et concepts avant de réexploiter la source | Pas de retravail inutile ni de fausse fusion conceptuelle |
| 9. Reprendre | PARTIAL, erreurs, nouvelles routes | Compléments ciblés; futur flux de réparation | Couverture plus riche sans effacer les valides |
| 10. Fenêtre suivante | Nouvelles pages sélectionnées, budget | Parcourir les liens/catégories et remplir les postes libérés | Nouveau lot **figé**, découverte toujours ouverte |
| 11. Admission différée | Propositions mûres et auteurs autorisés | Contrats du Kit, revue/transaction contrôlée, reçu | État Kristal seulement après admission **explicite** |

## Deux passes, mais pas deux sciences isolées

L'étape SEL juge **la pertinence d'une relation entre page et concept**. L'étape ENR analyse **le contenu du document** et peut servir plusieurs concepts, sous réserve que le rattachement soit démontré. Dans une future optimisation, certaines relations suffisamment sûres pourraient être examinées et enrichies dans une même interaction, mais **ce n'est pas le contrat général V32** et cela demande une expérimentation de qualité.

## Pourquoi ne pas « tout découvrir et figer » définitivement ?

Les liens Wikipédia sont explorés à partir de pages déjà retenues; des concepts ou sujets peuvent apparaître après la première passe. Un inventaire de départ peut être **figé par fenêtre** pour la reproductibilité, pas pour prétendre avoir trouvé tous les articles. On privilégie donc une boucle progressive, bornée, observable et réversible.

## Logique des dix postes

Les dix lanes sont un **plafond de missions concurrentes**, pas une définition du nombre total de candidats ni d'une branche complète. Le moteur crée `SEL` et `ENR` selon des priorités et des réservations; il conserve les retours importés, libère les postes et peut réapprovisionner. Les ZIP doivent rester associés au `job_id` attendu. Un ZIP `SEL` ne peut pas être transformé en retour `ENR` sans nouvelle mission.

## Qualité et rendement

Les indicateurs fondamentaux sont : pages Wikipédia **uniques**, paires article/concept, concepts UNESCO couverts, décisions SELECT/REJECT/HOLD, propositions nouvelles, taux d'erreurs, couverture `PARTIAL`, propositions par transfert et nombre d'interventions humaines. **10 606 propositions** historiques ne prouvent pas 10 606 faits scientifiquement indépendants et complets.

## Exemple de reprise

Un article de 35 000 mots reçoit 50 assertions mais est déclaré `incomplete`. L'import conserve les 50 faits valides. La prochaine mission cible les sections non couvertes et signale les propositions antérieures pour éviter des paraphrases. On n'efface pas l'article et on n'emploie pas `processed` uniquement pour faire disparaître les PARTIAL.

Lire [campagnes](06_CAMPAGNES_V8.md), [contrats](07_CONTRATS_ZIP_ET_PROMPTS.md), [qualité](09_QUALITE_REPRISES_RENDEMENT.md).
