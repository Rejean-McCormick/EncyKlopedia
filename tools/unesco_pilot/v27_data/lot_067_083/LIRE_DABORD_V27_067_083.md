# Import cumulatif des 17 deltas 067–083

1. Decompresser le ZIP overlay directement a la racine `C:\mycode\EncyKlopedia\EncyKlopedia` (conserver les chemins internes).
2. Lancer **une seule commande**, depuis PowerShell a la racine du depot :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\IMPORTER_DELTAS_KRISTAL_V27_067_083.ps1"
```

Le script verifie d'abord les 17 packs sources et les empreintes des deltas, copie uniquement les nouveaux JSON dans le dossier de travail sur D:, importe les 17 deltas avec le moteur v27 existant puis affiche le statut. Un delta identique deja importe n'ajoute pas de doublons.

Message attendu : `V27_LOT_067_083_OK`.

Avant import, le statut rapporte 66 deltas / 877 articles / 2 735 connaissances candidates. Apres ce lot, le total attendu est de **83 deltas, 1 049 articles et 3 254 connaissances candidates**, si les 66 precedents sont les seuls deja importes.

Les 519 nouvelles connaissances sont **des propositions non canoniques** selectionnees en partie de maniere automatisee et revues ponctuellement dans les textes complets. Leurs references sont fondees sur Wikipedia; elles ne sont pas verifiees contre des sources primaires et l'extraction n'est pas exhaustive. Le code source du moteur v27, le catalogue v25/v28, les anciens deltas et la base canonique ne sont pas remplaces.
