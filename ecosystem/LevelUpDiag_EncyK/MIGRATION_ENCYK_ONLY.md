# Migration vers LevelUpDiag EncyK dédié v1.2.0

Installer le ZIP **complet** dans `C:\mycode\LevelUpDiag-EncyK` (nouveau dossier).
L'ancienne installation reste indépendante et intacte.
Le paquet ne fournit ni les outils Orgo ni leurs fichiers, et n'est pas un overlay
de l'ancienne installation multi-profils.

EncyK, Skope, Kristal et D: ne sont ni modifiés ni recopiés.

Les contrôles du service Skope restent uniquement des contrôles de la connexion
**d'EncyK** à ce service externe.

Les noms du profil EncyK deviennent les fichiers par défaut `levelupdiag.config.json`
et `levelupdiag_manifest.json`. Le mode `--profile` est supprimé.
Si tu avais des réglages personnalisés dans `levelupdiag.config.encyk.local.json`,
recopie uniquement les valeurs pertinentes manuellement dans
`levelupdiag.config.local.json` (ne pas importer les options Orgo).
