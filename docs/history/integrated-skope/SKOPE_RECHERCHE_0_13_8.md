# Skope : correctif recherche sur l’index EncyK

Constat sur SQLite 121 780 373 entités : `/api/node?qid=Q192154` répond en 7 ms,
`/api/search?q=Q192154` et `q=Embryophyta` dépassaient 30 s. La cause est la requête
`SELECT DISTINCT e.wid ... WHERE n.norm LIKE ? ORDER BY e.wid LIMIT ?`, susceptible
de parcourir/trier de grandes portions de `name`.

Correctif :
- QID/PID/LID : `node(entity.id)` directement, sans requête textuelle.
- Noms : égalité puis intervalle de préfixe sur `name INDEXED BY idx_name_norm`, LIMIT borné,
  dédoublonnage Python après collecte ; aucun tri SQL global.
- Le client montre Recherche… et relâche le bouton après réponse/erreur/timeout.
- Pas de modification de D:, ni de migrations ni de création d'index.

Sur le poste Windows, remplacer le code du dépôt, fermer Skope dans le lanceur,
relancer Skope, et presser Ctrl+F5 dans le navigateur.

Vérifier avec PowerShell :
```powershell
Invoke-RestMethod 'http://127.0.0.1:8767/api/search?q=Q192154'
Invoke-RestMethod 'http://127.0.0.1:8767/api/search?q=Embryophyta'
```

Le nom peut retourner plusieurs taxons/alias ; sélectionner l'entité
`Q192154`, puis examiner les branches et périmètres avant export.
