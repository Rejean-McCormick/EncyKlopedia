# EncyKlopedia — stabilisation de l'import UNESCO v28

Le diagnostic a montré que `BEGIN IMMEDIATE` pouvait réussir sur le catalogue
restauré alors que le **premier INSERT dans `reviewed_article_links_v28`** échouait
avec `SQLITE_READONLY (8)`. Le même import réussissait sur une copie saine.

Cette intervention ne change aucun code de classement UNESCO ni aucune règle
d'import. Elle ne modifie ni les bases source Wikipédia ni Kristal v27, ni la
station v30, ni les retours ChatGPT.

## Utilisation

1. **Fermer complètement la station v30 et tout programme EncyKlopedia.**
2. Extraire le ZIP dans `C:\mycode\EncyKlopedia\EncyKlopedia`.
3. Depuis PowerShell 7 :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\STABILISER_IMPORT_UNESCO_V28.ps1"
```

## Protections

- Lecture du catalogue existant et `PRAGMA integrity_check`.
- Sauvegarde cohérente avec l'API SQLite `backup` dans
  `D:\EncyKlopedia\30_working\SAUVEGARDE_CATALOGUE_V25_RESTAURE\STABILISATION_V28_...`.
- **Véritable INSERT dans la même table que v28**, systématiquement annulé
  par `ROLLBACK` : aucune revue test conservée.
- En cas d'échec uniquement, création et test d'une copie saine **dans le même
  dossier**, donc sur le même disque et sous les mêmes contraintes de dossier.
- Si cette copie accepte l'insertion, archivage du fichier d'origine et de ses
  éventuels `-wal`/`-shm`, puis installation de la copie saine.
- Si le `-wal` d'origine n'est pas vide, la procédure refuse toute substitution.
- Si la copie saine échoue elle aussi, aucun remplacement n'est effectué.
- Contrôle final `integrity_check`, nombres d'articles/rattachements/séquence,
  et nouvelle insertion annulée sur la base installée.
- En cas d'échec lors du remplacement, tentative de remise en place des fichiers
  originaux ; les sauvegardes restent disponibles.

**Ne pas supprimer le dossier de sauvegarde.** Si la commande signale une
impossibilité de remettre un fichier, ne pas redémarrer v30 avant examen.

Après réussite, ouvrir le poste v30 et déposer **un seul** ZIP de retour UNESCO
v28 précédemment refusé, sans réexécuter les conversations ChatGPT.
