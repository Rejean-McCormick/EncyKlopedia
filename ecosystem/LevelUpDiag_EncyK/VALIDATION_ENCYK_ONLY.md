# Validation de LevelUpDiag EncyK dédié v1.2.0

- Un seul manifeste (`levelupdiag_manifest.json`), une seule configuration (`levelupdiag.config.json`).
- Niveau N00–N14 : état EncyK, code, topologie, Wikidata, lecteur, preuves, Kristal, pont EncyK ← Skope.
- Aucun Orgo, navigateur générique, suite Playwright, collecte Skope ou test du dépôt Skope.
- La configuration refuse explicitement un dépôt cible n’étant pas EncyK v0.14.x avec pont d'importation.
- Les rapports sont confinés à `.levelupdiag/encyk`; les diagnostics sont en lecture seule.
- Les contrôles en direct de D: et Windows devront être effectués dans l'installation locale.
