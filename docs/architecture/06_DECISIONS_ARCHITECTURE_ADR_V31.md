# Journal de décisions architecturales (ADR) — v31

**Date :** 13 novembre 2026  
**Portée :** choix documentaires proposés pour la future implémentation ; confirmation technique après lecture des scripts natifs.

## ADR-001 — Réutiliser le registre de pages et le graphe existants

**Décision :** ne pas dupliquer `wikipedia_en.sqlite` (~125,6 Go), les liens, catégories ou QID. Vérifier leur couverture, état d'ingestion et cohérence des références ; ajouter au besoin un **cache dérivé minimal**, jamais un second entrepôt encyclopédique complet.

**Alternatives écartées :** recréer tous les liens depuis le dump XML ; recopier les 25,9 millions d'entrées du direct index dans une nouvelle base propriétaire.

**Risque restant :** ingestion incomplète, instantanés différents, performances des jointures non confirmées.

## ADR-002 — Garder le catalogue v25 comme autorité des affectations

**Décision :** réutiliser `branches`, `concepts`, `branch_concepts`, `articles` et `assignments`. Le fait qu'un seul `branch_id` soit actuellement enregistré n'implique pas que le modèle ne supporte qu'une branche. Vérifier les contraintes et les tests multibranches déjà détectés.

**Alternative écartée :** nouveau catalogue UNESCO v31 parallèle à v25.

**Risque restant :** compatibilité des clés et migrations, à déterminer dans `catalogue_global_v25.py` et ses tests.

## ADR-003 — Ne jamais exclure définitivement une vraie page encyclopédique

**Décision :** conserver tous les articles de l'univers choisi. Distinguer `non classé`, `à préciser`, `différé` et **rejet d'une paire article–concept**. Les redirections restent conservées comme alias, les homonymies identifiées comme telles ; aucune catégorie d'articles n'est effacée pour améliorer artificiellement le taux d'APPROVE.

**Alternative écartée :** filtrer toutes les villes, organismes généraux, concepts abstraits ou pages courtes.

## ADR-004 — Séparer profil global et qualification article–concept

**Décision :** calculer le profil d'une page par révision, puis plusieurs branches plausibles et finalement la pertinence de chaque paire article–concept. Ne jamais inférer qu'une université convient à tous les concepts pédagogiques.

**Alternative écartée :** classifier chaque page une seule fois dans un unique domaine.

## ADR-005 — Maintenir la station v30 comme propriétaire des tâches

**Décision :** le classificateur agit **avant** scellement sur les tâches libres. Aucun reclassement de ZIP distribué, aucun contournement des protections de preuve gelée, aucune modification silencieuse des hash/candidate_id. Les dix conversations continuent selon les contrats en place.

**Alternative écartée :** second ordonnanceur ou découpage de packs déjà envoyés.

## ADR-006 — Privilégier les preuves à révision vérifiée

**Décision :** une catégorie partagée ou un lien direct n'est qu'un signal. Un extrait doit provenir du véritable article à la bonne révision. En cas de signature XML incompatible, laisser la preuve absente et proposer un enrichissement ciblé ; ne pas ignorer le verrou.

**Alternative écartée :** « forcer » les offsets v21 sur le dump actuel.

## ADR-007 — Privilégier la priorisation au filtrage dur

**Décision :** files `PRIORITAIRE`, `A_ENRICHIR`, `EXPLORATION_DIFFEREE` ; tous les candidats restent récupérables. Contrôle du rappel par échantillonnage probabiliste stratifié, y compris les cas à faible score.

**Alternative écartée :** ne transmettre que les 20 % du haut du classement, méthode susceptible de perdre beaucoup de bonnes paires selon le test historique.

## ADR-008 — Packs adaptatifs, activation graduelle

**Décision :** le mode production garanti reste 110 jusqu'à qualification ; essais 150–200 puis 300 selon les preuves et budget de sortie. 500 est un plafond théorique à tester, pas une recommandation de déploiement immédiat.

**Alternative écartée :** augmenter directement tous les lots des dix conversations à 500 ou 1 000.

## ADR-009 — Stats honnêtes, couverture distincte de rendement

**Décision :** chiffres par source, instantané, périmètre et qualité ; `unknown` si dénominateur absent. Ne jamais convertir « propositions revues / stock découvert » en pourcentage de connaissance mondiale terminée. Une approbation n'est pas un article nouvellement créé.

## ADR-010 — Kristal reste privé et non canonique

**Décision :** réutiliser ses `section_hint`/`source_quote` comme exemple de traçabilité, mais ne pas considérer ces citations comme index universel de paragraphes. Aucune promotion automatique des claims vers catalogue canonique ou publication.

## ADR-011 — Mode observation avant insertion native

**Décision :** auditer le code réel ; préférer intégrer les stades sémantiques v4/v6 plutôt que créer un moteur en double ; tout nouveau module commence `off/observe`, avec tests, sauvegarde et rollback. Les schémas vus en diagnostic ne suffisent pas à choisir un point d'insertion sûr.

## ADR-012 — La documentation précède le code

**Décision :** cette révision actualise uniquement les **documents**. Les modifications d'exécutables, bases, tâches, scripts de lancement et contrats d'import constituent des livraisons de code **ultérieures et distinctes**. La date et la version de cette documentation ne signifient pas « v31 installée ».
