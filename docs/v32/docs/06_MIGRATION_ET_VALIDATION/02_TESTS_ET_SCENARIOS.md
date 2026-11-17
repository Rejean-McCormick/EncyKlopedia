# Contrats minimaux et scénarios de validation pragmatiques

**V32.1 — nouveaux tests prioritaires :** lecture Education/Soil sans mutation; QID sans création d’îlot; préservation qualifiers Soil; admission unique via Kit vérifié puis reprise après crash; snapshot parent qui conserve l’ancien état d’un enfant; deux modes de lecture provisoire/admis; Kompiler qui indique les omissions. [Critères complets](../09_FEDERATION_KRISTAL/07_LOTS_A_E.md).


## Philosophie

Ne pas imposer une vérification SHA de tous les fichiers ni des manifestes avant chaque déplacement de code : cela immobiliserait le refactor sans améliorer le débit encyclopédique. **Mais** l'absence de procédure administrative lourde n'autorise pas les erreurs d'identité, les doublons silencieux ou les citations inventées. Vérifier ce qui protège directement le résultat : clés, révisions, contenu importé, transaction, récupération après arrêt.

## Tests incontournables par tranche (petites fixtures synthétiques)

| Scénario | Attendu | Preuve suffisante |
|---|---|---|
| QID direct P3916 unique | Relation `concept → QID → enwiki:page_id` identifiable | Requête indexée + identités stables |
| P3916 ambigu (plusieurs QID) | Plusieurs candidats, statut d'ambiguïté, aucune fusion forcée | Comparaison des clés et provenance |
| Concept sans P3916 | Branche utilisable par graphes SKOS, lexical ou revue ciblée | Aucun blocage global |
| Sujet présent dans deux branches | Une identité de sujet réutilisée, plusieurs relations; **pas de création forcée d’îlot** | Query SQL |
| Même article sans QID | Sujet provisoire par page_id, plus tard fusionnable si preuve | Clé provisoire explicite |
| Relations P31/P279 orientées | Candidate avec chemin et direction; pas d'APPROVE auto | Chemin de provenance conservé |
| Packs passe 1 | `candidate_id` complet et verdict récupérable | 100/100 lignes traçables ou 90 + 10 réparables |
| Packs passe 2 | Article complet par révision, claims spécifiques et citations | Vérification d'échantillon + couverture par article |
| Retour ZIP deux fois | Aucun nouveau fait lors du deuxième import | Compteurs inchangés |
| 0 PENDING + DEFERRED > 0 | Les DEFERRED ne sont pas ignorés | Au moins un pack créé si source disponible |
| Crash avant fin d'import | Reprise sans duplicata | Redémarrer fixture au point de faute |
| Absence index Wikidata | UI et imports existants fonctionnent | Dégradation localisée |
| Skope et Kristalizer | Aucune écriture ni import forcé dans dépôts externes | Chemins de configuration/adaptateurs |
| Fin de première branche | Aucun verrou de « clôture » imposé aux suivantes | Ouvrir deux branches en parallèle |

## Tests de performance utiles

- Chronométrer des jointures **indexées** sur 4 289 QID (pas le XML) et le premier enrichissement de quelques centaines de sujets. Suivre p50/p95 SQL/ZIP et mémoire réelle.
- En expansion P31/P279, mesurer candidates distincts, fraction avec article `enwiki`, ratio acceptés, coût par chemin; arrêter/différer les routes très bruyantes.
- Pour l'extraction ChatGPT, mesurer le rapport `claims_accepted / source_articles`, le nombre d'articles couverts, le nombre de retours partiels et la qualité des extraits. Un score de « temps de conversation » ne remplace pas ces observations.
- Les 10 lanes ne sont pas un SLA de remplissage. Mesurer plutôt le nombre de **packs utiles prêts** et la progression réelle.

## Conformité sans triple vérification

Une vérification programmatique d'identifiants/source et un échantillonnage raisonnable des citations suffisent pour la première production. Le delta doit être réparable : un seul champ invalide ne doit pas rendre automatiquement inutilisables 70 articles conformes. Les cas critiques (citation fabriquée, mauvais article, mauvais QID, falsification de révision) restent bloquants **pour l'item**, non nécessairement pour l'intégralité du lot.

## Tests d'interface dérivés du codex UX

- Arrivée sur l'écran : une action dominante « préparer », état des sources et jobs compréhensible.
- Sélection de branche, retour d'un ZIP et renouvellement d'une lane sans perte de contexte.
- Aucun deuxième bouton concurrent lançant la même opération dans une autre GUI.
- Pas de scan lourd lancé à l'ouverture.
- Les états `ready`, `sent`, `importing`, `done`, `partial`, `unknown` sont réellement distingués.
- Les opérations avancées (backup, logs, audit) restent accessibles sans encombrer la vue principale.

## Contre-exemples utiles

Un test « les fichiers ont le bon hash » ne prouve **ni** que le paquet a été construit avec les bonnes pages **ni** que l'IA a extrait assez de connaissances. Un bilan de « 41/41 concepts avec candidats » ne prouve pas une couverture encyclopédique complète. Un test d'import de 5 claims n'est pas une preuve de débit sur 87 branches. Ne pas surinvestir l'infrastructure de validation symbolique au détriment de ces essais réels.
