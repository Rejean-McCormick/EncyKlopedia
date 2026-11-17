# EncyKlopedia — Diagnostic des goulets, rappel et occupation des postes

**Référence :** ENC-AUDIT-2026-11-15/1 — document d'analyse, **pas** une promesse de rendement.  
**Sources croisées :** `RAPPORT_DIAGNOSTIC_ENCYK.json`, `RAPPORT_GOULOTS_ENCYK_20261115T204019Z.json`, code v31.10, diff v31.11 et journal de production Windows communiqué.

## 1. La question « pourquoi seulement 3/10 lots ? »

Au diagnostic du 15 novembre à 20:40 UTC :

| Indicateur | Valeur constatée |
|---|---:|
| Postes | 3 occupés / 7 libres |
| Packs ouverts | Kristal 120 + Kristal 13 articles ; UNESCO 3 034 propositions |
| UNESCO `PENDING + DEFERRED` non affecté | **0** |
| Kristal à empaqueter (`PENDING`) | **0** |
| UNESCO en revue (`QUEUED`) | 3 034 |
| Concepts UNESCO configurés | 41 |
| Concepts encore sans candidat | 16 |
| Curseurs de recherche lexicale v31.10 inachevés | 0 |
| Couples historiques dans la découverte | 186 232 |
| Couple découvert absent du rapprochement historique/catalogue/station | 0 (dans l'audit) |
| Contrôle v31.10 | SHA des deux moteurs conformes |

**Diagnostic immédiat :** les 7 postes ne sont pas vides à cause d'une panne d'attribution ; **il n'y avait plus de stock préparé**. La revue UNESCO ouverte gèle volontairement la découverte. Le total historique `candidate_pairs` ne peut pas être converti en nombre de nouveaux lots.

**Diagnostic de couverture :** les recherches de préfixe v31.10 sont terminées pour les alias configurés mais **16 concepts** n'ont reçu aucune proposition. Un curseur « complet » ne veut pas dire que l'encyclopédie Wikipédia a été épuisée : il indique seulement que **ce parcours indexé particulier** est fini. Exemple : `Adult literacy` et `Illiteracy` disposent de titres ressemblants dans l'index, sans candidat produit dans ces concepts ; il faut analyser les critères de pages, les données source et les chemins alternatifs, pas affirmer que ces concepts sont introuvables.

## 2. Pourquoi les correctifs ont changé de nature

1. **v31.9** : ordonne correctement la découverte par rapport au réexamen HOLD et clarifie le diagnostic ; n'ajoute aucun article par lui-même.
2. **v31.10** : ajoute recherche indépendante par préfixes de titres et catégories et membres, de façon résumable ; produit des paires supplémentaires, mais laisse encore 16 concepts vides au diagnostic.
3. **v31.11 (livré, non attesté installé ici)** : ajoute, sous garde de gel, des **pistes à partir de relations officielles entre concepts UNESCO et affectations existantes**. Les candidats sont **provisoires** ; seul ChatGPT peut conclure APPROVE/REJECT/HOLD. Le rendement `relation_*` ne peut être connu **qu'après installation vérifiée et batch autorisé**.

## 3. Indicateurs à lire dans le bon ordre

- `jobs` / `lanes` : tâches prêtes, envoyées, terminées ; capacité sur dix postes.
- `review_index.state` : `PENDING`, `DEFERRED` = stock susceptible d'être préparé ; `QUEUED` = déjà engagé en tâche ; `DECIDED` = déjà revu ; `HOLD` = éventuel réexamen volontaire. `HOLD` n'est **pas** un stock libre de nouvelles revues.
- `v28_open_jobs` : tant que supérieur à 0 (statuts `WAITING`, `READY`, `SENT`, `ERROR`, `IMPORTING`, `NEEDS_CONFIRMATION`), la découverte est volontairement bloquée.
- `candidate_pairs` : total des **paires historiques** en découverte ; une page peut apparaître sur plusieurs concepts.
- `seeds_pending` : graines historiques restant à parcourir ; distinct de `PENDING` des candidats en station.
- `broadscan_new_pairs`, `broadscan_new_pairs_unseeded`, `broadscan_concepts_still_empty`, `broadscan_unfinished_probes` : apport du rappel lexical v31.10, pas une mesure de précision ni de rappel global.
- `relation_new_pairs`, `relation_pairs_by_concept`, `relation_unfinished_paths` : apport du rappel ontologique v31.11 **si présent dans le moteur et effectivement exécuté**.
- `catalogue.articles`, `kristal.claims_count`, `article_visits` : résultats historiques ; `PACKED` dans la file Kristal ne suffit pas à conclure qu'un delta a été importé.

### Exemple : deux chiffres à ne pas confondre

Le journal affichait « 21 906 candidats parcourus dans la découverte, 3 034 nouveaux dans la station ». **21 906 n'est pas une réserve de 21 906 à empaqueter.** Une partie correspond à des paires déjà décidées, HOLD ou présentes au catalogue. Seuls les **3 034 nouveaux** avaient été préparés en une revue et la réserve est revenue à 0.

## 4. Conduite d'un audit exploitable

1. **Ne rien supprimer et ne rien réinitialiser.** Prendre une sauvegarde des résultats avant un correctif, pas pour tenter de « corriger » une file vide.
2. Obtenir la capture `api/state` ou le journal ; vérifier `jobs` + `review_index` + statut de gel. Faire la distinction **stock, tâches et historiques**.
3. Exécuter l'outil d'audit des goulets **en lecture seule**, si son SHA et sa provenance sont connus. Surveiller les erreurs/avertissements et les colonnes `start_stat/end_stat` ; les SQLite lues séparément ne sont pas atomiques.
4. Comparer **par concept** : libellés, variantes existantes, affectations, paires de découverte, preuves, curseurs et état de synchronisation. Noter les concepts à zéro et les critères de pages appliqués.
5. Examiner le code du **moteur réellement installé**, et non une simple version de documentation. Exiger le SHA-256 des scripts impactés avant de fabriquer un overlay.
6. Tester sur une **copie isolée** les cas : concept sans graine, source lexicale sans correspondance, liens ontologiques, reprise après plafond, idempotence, gel d'une tâche UNESCO, vérification de révision, rollback SHA.
7. Après déploiement et redémarrage, mesurer les nouveaux compteurs et la qualité réelle des décisions. **Ne jamais fixer dix packs comme critère unique de succès.**

## 5. Hypothèses à ne pas présenter comme acquises

- « Les 16 concepts sans candidat sont impossibles à documenter » : **faux** (seuls certains parcours lexicaux ont été épuisés).
- « `candidate_pairs=186232` = autant d'articles disponibles à produire » : **faux** (paires historiques, déjà revues ou cataloguées).
- « Le patch v31.11 est forcément installé » : **non vérifié** au 15 novembre en l'absence de journal/empreinte du poste après livraison.
- « Un voisinage ontologique est une preuve d'APPROVE » : **faux** ; c'est un mécanisme de rappel, pas de décision documentaire.
- « Le nombre de tâches mesure la complétude encyclopédique » : **faux** ; il mesure un flux, pas un rappel démontré.

Voir [checklist de maintenance](13_CHECKLIST_MAINTENANCE_V31.md) avant toute nouvelle modification.
