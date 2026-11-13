# EncyKlopedia — Mise à jour cumulative V31.1.1

Ce ZIP reprend **tout** le méga-update V31.1 et corrige les 6 échecs `WinError 32`
observés sur Windows après la copie des scripts. La cause était la non-fermeture de
connexions SQLite temporaires, pas un problème du catalogue EncyKlopedia.

## Installation (PowerShell 7)

Placez le ZIP dans Téléchargements puis exécutez :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -Command '$z=Join-Path $HOME "Downloads\EncyKlopedia_MEGA_MAJ_CUMULATIVE_V31_1_1_WINDOWS_SQLITE.zip"; $d=Join-Path $env:TEMP "ENCI_MEGA_MAJ_V3111"; Expand-Archive -LiteralPath $z -DestinationPath $d -Force; & (Join-Path $d "INSTALLER_MEGA_MAJ_V3111.ps1")'
```

Le lancement précédent a **déjà copié les fichiers V31.1** avant d'échouer aux tests.
Ce nouvel installeur peut se superposer sans recréer les bases. Il vérifie la syntaxe,
le manifeste et les empreintes, installe les scripts et exécute les tests.

Succès attendu : `MEGA_MAJ_ENCYKLOPEDIA_V31_1_1_OK` et `Ran 17 tests ... OK`.

Aucune commande de restauration ni reconstruction n'est requise pour le journal reçu.

Détails : `docs/architecture/09_CORRECTIF_CONNEXIONS_SQLITE_WINDOWS_V3111.md`.
