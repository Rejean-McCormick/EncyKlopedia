# Runbook — Startup / readiness

1. Vérifier Node `>=24.15.0` et checksum de l’artefact.
2. Charger les secrets hors repo.
3. Exécuter `npm run release:preflight` sur l’artefact qualifié.
4. Démarrer le processus.
5. Vérifier `/api/health` puis `/api/ready`.
6. Vérifier `/api/version` et le `buildId` attendu.
7. Faire une requête de lecture représentative sous un principal réel.
8. N’ouvrir le trafic qu’après ces vérifications.

Si le pack, une policy ou une Lens est invalide, le processus doit échouer au démarrage plutôt que passer ready.
