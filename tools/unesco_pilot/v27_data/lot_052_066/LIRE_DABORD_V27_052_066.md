# Lot EncyKlopedia v27 052–066 — installation simple

1. Decompresser le ZIP **a la racine** de `C:\mycode\EncyKlopedia\EncyKlopedia`.
2. Ouvrir PowerShell a cette racine et executer **une seule commande** :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\IMPORTER_DELTAS_KRISTAL_V27_052_066.ps1"
```

Le lanceur verifie les 15 ZIP sources sur D:, sauvegarde les 15 JSON dans
`D:\EncyKlopedia\30_working\production_kristals_v27\deltas`, refuse d'ecraser
un delta different, importe de 052 a 066 et montre le statut final.

Message terminal attendu : `V27_LOT_052_066_OK`.
Si les deltas 001–051 sont deja importes et qu'aucun autre n'a ete ajoute,
resultat attendu : 66 deltas, 877 articles visites, 2 735 connaissances candidates.
Le dossier `tools/unesco_pilot/v27_data/lot_052_066` est constitue de donnees de revue,
aucun changement au moteur ni aux Kristals canoniques.
