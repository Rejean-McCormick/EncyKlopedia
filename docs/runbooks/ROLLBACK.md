# Runbook — Rollback

1. Retirer la version fautive du trafic.
2. Identifier `buildId`, corpus/config et première version saine.
3. Restaurer atomiquement code + lockfile + build + schémas + configuration.
4. Ne pas restaurer une projection dérivée comme canon.
5. Redémarrer et vérifier health/readiness/version.
6. Rejouer un parcours query + plan + projection sous Reader Policy représentative.
7. Documenter l’incident et ajouter un test de non-régression.

Les cursors d’un contexte/fingerprint incompatible doivent expirer naturellement.
