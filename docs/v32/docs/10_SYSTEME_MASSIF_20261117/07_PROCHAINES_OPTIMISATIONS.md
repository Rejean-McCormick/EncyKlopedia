# 07 — Plan concret d'optimisation, avec ordre, coût, bénéfices et critères

## Principe : ne pas ajouter de couches par réflexe

Une seule base privée V32; ports en lecture seule; missions ChatGPT immuables; reprise conservatrice. Une optimisation doit démontrer soit davantage de candidats pertinents, soit davantage de faits acceptés et nouveaux par transfert, soit moins de charge humaine.

| Lot | Modification envisagée | Code à réutiliser | Changements techniques | Qualification de réussite |
|---|---|---|---|---|
| **0 — livré** | Inventaire, docs, observateur RO | V32 SQL, snapshots V6/Skope/Kristalizer | Documents + script Python autonome | Rapport exact, aucune écriture à la base |
| **1 — ordonnanceur permanent** | Une campagne par branche, fenêtres et budget cumulatif, auto-remplissage après retours **(fenêtre CLI opt-in déjà fournie, permanence restante)** | `Station._perform`, `make_wave`, `discover_*`, curseurs | Petit coordinateur V32, table additive seulement si nécessaire, modes pause/reprise | 10 postes respectés, jamais de job dupliqué, aucun scan illimité |
| **2 — perte import** | Rendre les lignes `import_errors` réparables sans perdre les valides | `import_for_job`, `import_errors`, pack source | Générateur de mission de réparation; contrat retour distinct, reçu idempotent | 506 refus mieux catégorisés, taux de récupération mesuré |
| **3 — LONGS textes** | Décompresser l'analyse intra-article par sections | `_reading_guide`, `page_from_index`, XML index direct | sous-lots avec offsets de citation, garde-fou sur la taille IA | Plus de faits nouveaux sur source longue, citations exactes, peu de répétitions |
| **4 — PARTIAL** | File de compléments avec budget et seuil de gain | `source_results`, `retry_candidates`, `prior_propositions` | historique de tentatives et cooldown | Pas de boucle infinie, rendement positif calculé |
| **5 — couverture** | Préserver la diversité des 34 concepts (puis 88 branches) | planification V6, alias Skope, V28 liens, thésaurus | quotas souples par concept/route et exploration de catégories | Couverture conceptuelle progresse sans sacrifier les sujets riches |
| **6 — extraction Wikidata** | Source structurée lossless originale ciblée | Skope `extraction.py`, source evidence handoff | Prévol source, port d'import privé à provenance propre | Qualifiers/références vérifiées, aucun faux `source_quote` |
| **7 — mémoire documentaire** | Cache `(page_id,revision,sha,profil,segments)` interbranches | `source_results`, `article_sources`, `candidate_extractions` | table/artefact additionnel content-addressed, liens vers concepts séparés | Réduction des analyses répétées sans faux rattachement |
| **8 — admission** | Lots mûrs pour Kristals indépendants | Kristalizer staging + Kit réel | Contrat externe qualifié, autorisations, reçus | **Zéro admission non autorisée**, pas de QID→Kristal automatique |

## Qualification minimale avant de lancer une mise à jour en production

1. **Capture de base V32 avec SQLite Backup API**, sur chemin de sauvegarde séparé; garantir les jobs et les propositions; ne pas arrêter la station pendant un import.
2. Jeu synthétique de 88 branches, 10 lanes, états `PENDING`,`READY`,`PARTIAL`,`SOURCE_BLOCKED`, réponses valides et mixtes; démontrer idempotence à import doublé.
3. Comparer à V6 **le nombre de candidats uniques** et leurs routes, puis les faits acceptés par article (pas uniquement par mission).
4. Fixer le poids des sources dans une **politique versionnée** et pouvoir l'annuler; ne pas modifier `Skope`, `Kristalizer` ni `mediatheque`.
5. Prévol des vraies bases D: RO, sans `COUNT(*)` mondial sur 134 Go ni `VACUUM` des sources.
6. Première campagne pilote sur Météorologie avec nombre de tours et budget bornés; scanner les journaux de refus.
7. Généraliser aux autres branches **après une mesure**, pas parce que la console affiche simplement 0 erreur.

## Décisions pour la production massive

- **Volume :** préférer des fenêtres de découverte jusqu'à quelques milliers de candidats utiles; réajuster selon le bruit par concept. Ne pas imposer un seuil fixe mondial.
- **Coût IA :** sélectionner par lot large si extraits courts; découper les grands enrichissements selon les textes. Prompts six passes utiles, mais leur longueur seule ne garantit pas une analyse exhaustive.
- **Faits invalides :** récupérer les erreurs utiles; ne pas bloquer toute la campagne pour quelques rejets.
- **Réutilisation :** partager le document/révision entre branches, mais conserver les rattachements conceptuels et QID séparés.
- **Publication :** entièrement différée; de la collecte privée au canon, passage par **véritable Kit** avec audit et autorisation.

## Ce que nous n'avons PAS vérifié

- Temps réel d'une campagne de 20 000 voisins sur toutes les branches; la V6 a été confirmée seulement sur Météorologie.
- Disponibilité opérationnelle du dump Wikidata lossless + index random-access sur le poste.
- Qualité scientifique indépendante des 10 606 propositions privées.
- Existence actuelle et contenu de toutes les tables de catégories V25 sur D:.
- Réussite d'un futur ordonnanceur robuste sous concurrence Windows/station; il **reste à coder** après validation de l'architecture.
