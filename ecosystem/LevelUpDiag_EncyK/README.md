# LevelUpDiag — EncyK seulement (v1.2.0)

Diagnostic externe et indépendant **exclusivement pour EncyKlopedia v0.14.x**.
Ce n'est pas un framework générique, ni un analyseur Orgo, ni un serveur Skope.

Installer dans `C:\mycode\LevelUpDiag-EncyK` (jamais dans EncyK).
Ouvrir `LEVELUPDIAG_ENCYK.pyw` pour choisir la campagne.

En PowerShell :

```powershell
Set-Location C:\mycode\LevelUpDiag-EncyK
python -B .\levelupdiag.py --target 'C:\mycode\EncyKlopedia\EncyKlopedia' doctor
python -B .\levelupdiag.py --target 'C:\mycode\EncyKlopedia\EncyKlopedia' run quick
```

Campagnes : `quick`, `repository`, `reader`, `bridge`, `standard` (15 niveaux N00–N14).
Elles concernent uniquement les opérations d'EncyK ; les requêtes Skope (API locale
en lecture seule) servent **uniquement au diagnostic de l’interface de collecte et du pont
d’importation EncyK ← Skope**. Aucun audit du dépôt Skope ni de son sélecteur Kristal.
Aucune collecte, aucune extraction et aucune écriture sur D: ou dans les canons.

Réglages : `levelupdiag.config.json`; overrides locaux (non livrés) :
`levelupdiag.config.local.json`.
Rapports : `.levelupdiag/encyk/runs/` à l'intérieur de cette application.

**Mise à niveau depuis v1.1.0** : ne pas superposer par-dessus l'ancien dépôt
Orgo/EncyK polyvalent : installer en dossier neuf. Voir MIGRATION_ENCYK_ONLY.md.
