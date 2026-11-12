# Revue UNESCO v28 — vague 2 (catalogue sequence 34)

Decompresser cette archive **a la racine** `C:\mycode\EncyKlopedia\EncyKlopedia`.

Lancer une seule commande depuis cette racine :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\APPLIQUER_REVUE_UNESCO_V28_VAGUE2.ps1"
```

Le lanceur verifie SHA-256, fait le DryRun, applique les decisions, affiche le statut.
Message attendu : `V28_VAGUE2_OK`.

- 1500 correspondances etudiees ; 101 APPROVE, 282 REJECT, 1117 HOLD.
- 99 pages distinctes concernees par les approbations. Ce nombre **ne predit pas** les nouveaux articles : certaines pages sont deja dans le catalogue.
- 616 correspondances HOLD deja vues dans la premiere revue. Elles restent ouvertes sauf reexamen explicite ; aucune approbation ancienne n'est dupliquee.
- Les décisions approuvent le classement **documentaire candidat** dans UNESCO MT 1.10, pas la veracite des textes, des faits ni les Kristals canoniques.
- Les bases SQLite et le XML sur D: **ne sont pas embarques** dans cette archive. Les sources sont en lecture seule ; la v28 peut ajouter des assignations dans la base du catalogue.
- Si le catalogue ou les preuves ont change depuis l'export (sequence 34), le precontrole doit pouvoir refuser l'operation ; ne pas reinitialiser les bases v28 ou v27.
