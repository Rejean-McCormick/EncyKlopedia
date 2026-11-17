# EncyKlopedia V32.2 — moteur privé corrigé

Mise à jour du dépôt V32.1 : isolation des branches, réservations exclusives, retours archivés, propositions contextualisées, corrections versionnées, réutilisation des extractions et reprise explicite.

**Commencer par [MISE_A_JOUR_V32_2.md](MISE_A_JOUR_V32_2.md)** : installation Windows, migration sauvegardée, commandes, validation et limites. Ce document prévaut sur les descriptions historiques de V32.1 pour le comportement du noyau livré.

## Lancer

Python 3.10+ avec Tkinter, bibliothèque standard uniquement pour le noyau V32. Copier `config/settings.example.json` vers `config/settings.json` et adapter les chemins des index D:. Les références UNESCO internes sont localisées automatiquement dans le dépôt. Pour un pilote indépendant, configurer un nouveau `work_root` local.

```powershell
python encyk_cli.py doctor
python encyk_cli.py index-unesco
python encyk_cli.py discover --branch unesco.mt1.05
python encyk_cli.py prepare --branch unesco.mt1.05
python EncyKlopedia.pyw
```

Les dix conversations ChatGPT restent manuelles : packs ZIP → réponses ZIP → import. Les propositions restent privées et provisoires.

## Vérifier

```powershell
python -m unittest discover -s tests_v32 -v
python -m compileall -q encyk_v32
python encyk_cli.py recover
```

30 tests V32 et 15 tests historiques ciblés ont réussi sur les fixtures Linux. Les index Windows vivants et la GUI modifiée n’ont pas été qualifiés sur Windows. La CI ajoutée permettra une vérification Windows supplémentaire.

## Périmètre

- `encyk_v32/` : moteur et manager actualisés ; schéma local `/2` avec sauvegarde avant migration de `/1`.
- `tests_v32/` : tests du flux et des défauts corrigés.
- `tools/unesco_pilot/`, `ecosystem/`, `archive/` : sources historiques conservées ; aucune migration de canons.
- `docs/v32/` : architecture et historique ; consulter le guide V32.2 pour les changements effectifs.

**L’admission dans Kristal reste fermée jusqu’à qualification du Kit.** La fédération n’est pas encore une composition canonique d’états. Skope et Kristalizer restent externes. Le dépôt est prêt pour un pilote de validation, pas une promesse de production industrielle sur 87 branches.
