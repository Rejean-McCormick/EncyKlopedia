# Validation v0.13.4 — nettoyer sans backup

- `python 00_system/tools/validate_repo.py` : PASS
- Tests cleaner : 7 PASS (réexécution, collisions, fichier modifié, dossier inconnu, lien, racine code).
- Tests Skope : 9 PASS.
- Tests Scope Builder : 5 PASS.
- Simulation sur une copie des 17 fichiers de l'inventaire historique avec les 12 copies initiales `20_evidence/legacy-ingest` : 14 fichiers déplacés, 15 doublons/README supprimés, 28 dossiers vides retirés ; seconde passe sans action.
- Source 10_sources et index 30_working inchangés dans la simulation.
- Aucune sauvegarde ni archive créée.
- Environnement de validation : Python sur Linux, sans GUI Windows. Interface Tkinter et jonctions Windows à vérifier sur le poste de destination.
- Limitation connue : les anciens manifestes de provenance ne sont pas réécrits ; des références de chemin historique demeurent et les nouveaux manifestes doivent être générés via le pipeline courant.
