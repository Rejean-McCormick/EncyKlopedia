# Skope 0.13.13 — vérifications

- Limite en RAM bornée à 10k pour la carte ; objectif 0 accepté pour l’inventaire complet.
- Traitement opt-in sur D: en lecture seule sur la base source.
- Job SQLite temporaire, stop/resume après interruption ; génération JSONL de QID non probants.
- Conditions : PIDs sélectionnés, sens unique, aucune exclusion géographique automatique.
- Limite connue : pas encore de données source complètes ni de vérification géographique.

Tests exécutés sur un index synthétique uniquement (pas les 125 Gio de D:). Suite Skope : 35 tests, API HTTP de lancement/statut : OK, interface Chromium simulée : OK.

**Restrictions** : la collecte massive est un inventaire de QID accessibles dans le graphe taxonomique à la profondeur choisie ; aucune déduction de présence botanique réelle ni de claims médicaux, aucun JSON source original extrait, aucune ingestion canonique.
