# Audit UX existant → interface unifiée

## Constats concrets [OBSERVÉ CODE + UI utilisateur]

- `poste_chatgpt_v30.html/js` fournit le **Centre de production** avec dix postes, « préparer prochaine vague », import ZIP, prompt et historique; la structure métier est utile et constitue la meilleure base d'écran principal.
- `ENCYK_CENTRE_PILOTAGE_V313/V314` fournit d'autres dashboards, triages et bilans; l'utilisateur devrait éviter de les ouvrir comme applications concurrentes pour une opération normale.
- `EncykAudit` fournit une GUI Tk, un tableau de couverture, CSV/JSON, et une tâche planifiée facultative. Ses rapports ne mesurent pas la saturation réelle; conserver en diagnostics, pas en verdict de complétude.
- Le lecteur alpha Node (`src/server.mjs`) et le Workbench UNESCO sont d'autres intentions, pas des vues à empiler au centre de production.
- Skope et Kristalizer ont leurs propres interfaces et responsabilités. Le manager **n'imite pas** leurs écrans internes.

## Mapping ancien → nouveau [CIBLE]

| Ancienne action / fenêtre | Emplacement V32 | Réemploi |
|---|---|---|
| « Préparer toute la prochaine vague » v30 | Action principale « Préparer » | Scheduler et mécanisme de packs |
| Postes 01..10 v30 | Vue de travail principale | 10 lanes + ZIP + prompt |
| « Déposer des ZIP corrigés » v30 | Import groupé juste sous les postes | Détection et validation ciblées |
| Journal et retours v30 | Activité récente + historique détaillé | Tables persistantes |
| Mises à jour/rollback v30 | Avancé > Maintenance | Pas d'overlay imposé pour chaque refactor |
| Centre de pilotage V313/V314 | Avancé > Tableau de production | Statistiques sans second scheduler |
| Audit auto V312 | Avancé > Diagnostics par branche | Lire trois sources, corriger comptages |
| Workbench UNESCO | Avancé > Références UNESCO | Source, provenance, diff |
| Utilitaire sauvegardes | Avancé > Sauvegarde | SQLite backups |
| Recherche publique alpha | Accès secondaire « Consulter » | Garder privé tant que non qualifié |

## Navigation minimale

Une **vue de production** par défaut, un **explorateur de Kristals** pour revoir le résultat, un écran **branches/périmètre** si la sélection exige réellement une profondeur propre, et un espace **avancé** pour états techniques. La quantité d'onglets n'est pas un objectif; c'est l'absence de doublons qui compte. Les détails d'une mission s'ouvrent depuis son poste, pas comme une nouvelle application.

## Actions dangereuses, non automatiques

- L'UI ne doit pas lancer un scan de dizaines de Go à l'ouverture.
- « Reprendre » ne crée pas une deuxième mission identique.
- « Importer » affiche les items non conformes, n'efface pas la file.
- « Archiver un ancien dépôt » n'apparaît que dans la phase de consolidation après reprise et backup suffisants.
- Les travaux de publication/canonisation ne doivent pas avoir de bouton ambigu confondu avec « enrichir ».

## Parcours à tester sur la vraie interface

1. Démarrer depuis le `.pyw` racine; index Wikidata disponible, aucune tâche. Choisir trois branches → préparer → télécharger prompts/packs.
2. Retour d'un ZIP d'enrichissement, déposé deux fois : un seul import effectif, résultats identiques et poste renouvelable.
3. Redémarrage alors que cinq missions sont envoyées : retrouver les mêmes job IDs et ZIP, sans toucher aux preuves.
4. Absence de Skope : afficher « relation Wikidata indisponible » mais autoriser l'import de ZIP prêts et la consultation des Kristals.
5. Retour partiel valide : afficher 50/60 articles terminés, 10 à réparer, sans « tâche accomplie » trompeur.
6. 0 PENDING, 2 300 DEFERRED : en sélectionner réellement au lieu de conclure que les postes doivent rester libres.
7. 2 jobs seulement et huit postes libres : afficher cause métier et chemin vers le prochain travail, pas un avertissement de « panne 8 postes ».

## Indications codex

Le guide UX fourni (`AI_INGESTION.md`) impose une organisation par tâche utilisateur, non par module. Il interdit l'anti-pattern consistant à ajouter un onglet simplifié en maintenant tous les écrans concurrents. Les états locaux et inconnus doivent être distingués. La grille UX-01…UX-18 est **une ressource de conception**, pas dix-huit fonctions à ajouter à l'interface.
