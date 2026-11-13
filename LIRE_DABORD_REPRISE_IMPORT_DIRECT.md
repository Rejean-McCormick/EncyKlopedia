# EncyKlopedia — reprise contrôlée d'un import UNESCO v28

Cette reprise vise **un seul retour déjà refusé** : `v28_ac43a56fc32867_530dee66`.

1. Fermer complètement le poste v30 (fermer la console PowerShell qui le lance).
2. Extraire ce ZIP à la racine `C:\mycode\EncyKlopedia\EncyKlopedia`.
3. Lancer dans PowerShell 7 :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\REPRENDRE_UN_IMPORT_UNESCO_V28.ps1"
```

Le script vérifie la copie originale (intégrité et compteurs), valide les décisions sans écriture, crée une **sauvegarde SQLite cohérente**, puis applique exactement le retour préexistant sur le **catalogue original**. Si une opération échoue, il affiche la dernière instruction SQLite, un traceback et le code d'erreur. Aucun fichier original n'est remplacé par une copie. Le fichier `station_v30.sqlite` n'est pas modifié et la station reste à 11 retours intégrés jusqu'à ce que le même ZIP soit redéposé dans v30. Le moteur v28 conserve ses contrôles d'idempotence pour les décisions déjà enregistrées.

**Si succès :** relancer v30, puis redéposer le même ZIP `RETOUR_CHATGPT_v28_ac43a56fc32867_530dee66.zip` pour inscrire le succès dans la station. L'importeur v28 doit constater que les décisions sont déjà présentes et les accepter sans compter les articles deux fois. Tester d'abord sur ce ZIP avant d'en redéposer d'autres.

**Si échec :** transmettre la sortie PowerShell. Ne pas restaurer la sauvegarde automatiquement ; une panne pendant la création du snapshot peut survenir après un commit réussi, et une restauration aveugle ferait perdre des décisions.

Aucune grosse base Wikipédia ou Kristal n'est touchée ; aucun historique n'est réinitialisé.
