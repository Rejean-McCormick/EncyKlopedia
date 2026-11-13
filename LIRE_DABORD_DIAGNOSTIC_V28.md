# Diagnostic UNESCO v28 — test sur copie isolée

Un test d'écriture SQLite générique a réussi, mais le moteur v28 refuse toujours les vrais retours. Ce diagnostic exécute **le vrai import v28 sur une copie cohérente du catalogue**, pas sur la base originale. Les décisions et les files v30 ne sont pas modifiées. Le fichier `wikipedia_en.sqlite` reste en lecture seule. Le script identifie l'instruction fautive, le code d'erreur SQLite détaillé et la pile Python si l'import échoue.

1. Fermer la fenêtre PowerShell du poste v30.
2. Extraire le ZIP à la racine du dépôt `C:\mycode\EncyKlopedia\EncyKlopedia`.
3. Exécuter :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\DIAGNOSTIQUER_IMPORT_UNESCO_V28.ps1"
```

Le test utilise le retour complet `v28_ac43a56fc32867_530dee66` déjà conservé dans `D:\EncyKlopedia\30_working\poste_chatgpt_v30\returns`. Le dossier de diagnostic, avec une copie d'environ 2 Mo et d'éventuels exports tests, est `D:\EncyKlopedia\30_working\DIAGNOSTICS_IMPORT_V28`. Aucun échange de fichiers ni modification du code existant ne sont effectués.

**Important** : ne pas appliquer soi-même les changements d'une copie de test à la base originale. Si le test réussit, le moteur fonctionne sur une copie et le problème concerne les accès à l'original ou son environnement. S'il échoue, le code d'erreur et la pile indiquent l'étape exacte.
