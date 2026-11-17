# EncyKlopedia — Changelog v31.4

- Centre autonome, réutilisant les moteurs d'audit v31.2 et de supervision v31.3.
- Nouveau moteur `encyk_triage_v314.py`, en lecture seule, rapprochement contrôlé
  des clés concept/article pour 3 sources, diagnostic des 667 écarts observés.
- Comptage de l'existence d'affectations historiques et des incohérences de
  provenance station/catalogue sans réparation automatique.
- Vue Tkinter de triage + 3 exports supplémentaires.
- 12 tests automatisés synthétiques : conservation des bases et des connaissances
  privées, erreurs sources explicites, export séparé, conformité de l'interface
  de collection et refus des écritures sur la base.
- **Aucune modification des moteurs d'exécution UNESCO/Kristal** ; gel probatoire
  et 6 197 HOLD restent hors du champ d'intervention de cette version.
