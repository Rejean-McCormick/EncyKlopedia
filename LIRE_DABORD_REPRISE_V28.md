# EncyKlopedia — reprise des imports UNESCO v28 apres restauration Bitdefender

1. **Fermer la fenêtre PowerShell qui exécute `LANCER_POSTE_CHATGPT_V30.ps1`**, et les outils v28 éventuels. Ne pas supprimer l'état des postes.
2. Extraire ce ZIP à la **racine du dépôt** `C:\mycode\EncyKlopedia\EncyKlopedia`.
3. Exécuter la commande suivante dans PowerShell 7 :

   ```powershell
   pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\REPARER_ECRITURE_UNESCO_V28.ps1"
   ```

L'outil vérifie le catalogue restauré et sauvegarde sa **vue SQLite cohérente** sous
`D:\EncyKlopedia\30_working\SAUVEGARDE_CATALOGUE_V25_RESTAURE\AVANT_REPRISE_V28_*`.
Il effectue ensuite un `BEGIN IMMEDIATE` suivi d'un `ROLLBACK`, sans importer de décisions.
Si l'écriture fonctionne, il n'effectue aucun remplacement. Si l'original échoue
mais qu'une copie saine **dans le même dossier** fonctionne, il propose une réparation.
**Il ne remplace rien sans que tu tapes `REPARER`.** Les originaux et leurs `-wal` / `-shm` sont archivés.

L'outil **ne supprime aucun retour ChatGPT, ne touche pas aux 117 Gio de Wikipédia, ne
reconstruit aucune base et ne réinitialise pas v27/v28/v30**.

Après un résultat OK, relancer le poste v30 avec la commande habituelle puis redéposer
**un seul** ZIP UNESCO v28 qui avait échoué. Si une erreur persiste, communiquer le nouveau
journal : cela identifiera une autre cause que le simple accès en écriture du catalogue.
