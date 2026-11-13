# EncyKlopedia — Documentation d'architecture cible (v31)

**Date :** 13 novembre 2026  
**Version de la documentation :** `ENC-DOC-V31.1`  
**Version installée du logiciel :** **inchangée** (station v30, catalogue v25, UNESCO v28, Kristal v27).  
**Statut :** documentation d'architecture cible pour guider les futurs correctifs ; **non une déclaration de déploiement**.

## Ordre de lecture

1. [01 — Système final](01_SYSTEME_FINAL_ENCYKLOPEDIA_V31.md) — objectif, architecture réutilisée, flux global et frontières de sécurité.
2. [02 — Cartographie et écarts](02_CARTOGRAPHIE_EXISTANT_ET_GAPS_V30.md) — constats du diagnostic du 13 novembre 2026, chiffres historiques, incertitudes et modules existants.
3. [03 — Plan de réalisation et tests](03_PLAN_DE_REALISATION_ET_TESTS_V31.md) — étapes de codage, validations, canari, rollback et lots élargis.
4. [04 — Contrats et données](04_CONTRATS_ET_DONNEES_V31.md) — identités, versions, modèle logique, machines à états et compatibilité v30.
5. [05 — Statistiques](05_STATISTIQUES_ET_PILOTAGE_V31.md) — dénominateurs, indicateurs, estimation du rappel et tableau de bord.
6. [06 — Décisions d'architecture](06_DECISIONS_ARCHITECTURE_ADR_V31.md) — choix durables et alternatives refusées.

## Trois garanties à ne jamais perdre

- **Le patrimoine existant :** réutiliser les index Wikipédia/pages/liens/catégories/QID, les structures de branches/concepts et les modules sémantiques déjà présents avant d'ajouter de nouveaux composants.
- **Le patrimoine documentaire :** ne supprimer aucun article du corpus inventorié ; une paire de faible priorité est différée, pas rejetée ; un même article peut appartenir à plusieurs branches.
- **Le patrimoine de production :** ne modifier ni tâches v30 distribuées, ni preuves, ni `candidate_id`, ni empreintes. Kristal reste privé et non canonique ; aucune publication automatique.

## Lectures exigées avant le premier correctif de code

Le diagnostic a **vu les noms et signatures de fonctions**, pas le corps des modules natifs. Avant de modifier la production, examiner les scripts présents dans `tools/unesco_pilot/` et leurs tests : catalogue v25, générateur de branches, stades sémantiques v4/v6, pont Wikipédia local, découverte v28, enrichissement des preuves, poste v30 et Kristal v27.

**Ne pas relancer la reconstruction des bases Wikipédia** avant l'audit de couverture, d'ingestion et de compatibilité des snapshots.

## Installation documentaire

La livraison ajoute uniquement des fichiers versionnés sous `docs/architecture/`. Elle n'écrase aucun script natif, base SQLite, dump XML, pack distribué ou tâche. Les fichiers de documentation remplacés sont sauvegardés avant copie ; le script vérifie les empreintes du paquet. En cas d'erreur, il restaure les documents modifiés dans cette installation.

**Prochain livrable après validation de cette documentation :** audit ciblé du code natif, puis implémentation par étapes, avec mode `off/observe` par défaut.
