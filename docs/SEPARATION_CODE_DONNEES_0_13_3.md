# EncyK 0.13.3 — Code Git séparé des données locales

## Deux emplacements, deux responsabilités

- **Dépôt Git** : ton clone EncyK, par exemple `C:\mycode\EncyKlopedia\EncyKlopedia` ; contient `00_system`, Skope, scripts, `10_sources/seeds`, tests, schémas.
- **Données** : `D:\EncyKlopedia` ; contient les originaux Wikidata, l'index global 124,94 Gio, l'index rapide ~2,16 Gio, les bases lexicales, snapshots d'acquisition et archives métier.

**Ne pas installer le dépôt Git, Skope ou les scripts exécutables dans `D:\EncyKlopedia`.** Ce répertoire n'est pas un dépôt incomplet.

## Configuration sous PowerShell 7

Depuis la racine de TON dépôt EncyK (pas D:), avec les traitements Wikidata arrêtés :

```powershell
pwsh -NoProfile -File .\configure_data_on_D.ps1
pwsh -NoProfile -File .\configure_data_on_D.ps1 -Apply
```

Le script se base sur `$PSScriptRoot`, pas sur un chemin C: codé en dur. Si tes données sont ailleurs : `-DataRoot 'E:\MesDonneesEncyK'`.
Il crée seulement les jonctions suivantes sur le dépôt :

| Chemin relatif du dépôt | Cible du dossier de données |
|---|---|
| `10_sources\lexical` | `D:\EncyKlopedia\10_sources\lexical` |
| `10_sources\wikidata\dumps` | `D:\EncyKlopedia\10_sources\wikidata\dumps` |
| `20_evidence` | `D:\EncyKlopedia\20_evidence` |
| `30_working` | `D:\EncyKlopedia\30_working` |
| `90_runtime` | `D:\EncyKlopedia\90_runtime` |

**Attention** : une jonction est un accès direct aux fichiers sur D:, pas une copie. Supprimer un fichier via la jonction le supprime aussi sur D:. Le configurateur refuse de remplacer un répertoire C: non vide ou une liaison existante différente.

Si tu mets à jour un ancien clone C: où `20_evidence/`, `30_working/` ou `90_runtime/` contiennent encore des fichiers suivis par Git, fais d'abord une mise à jour propre / commit de la version 0.13.3. **Ne les efface pas à la main.** La version source 0.13.3 archive les anciens README et manifestes d'exemple sous `docs/historical-*` pour ne plus bloquer ces jonctions. Si un blocage subsiste, l'outil s'arrête et affiche le chemin exact.

## Nettoyeur pour D:

Lancer **`Nettoyer_Donnees_EncyK.pyw`** depuis le dépôt de code (Python 3, Tkinter). Il accepte un chemin de données distinct et fonctionne en mode audit par défaut.

1. **Analyser** : aucun changement ; compare les fichiers protégés et l'arborescence historique.
2. **Préparer D:** : crée `20_evidence/` et `90_runtime/` sans toucher aux anciens dossiers.
3. **Copier l'ingestion historique** : copie et vérifie `20_ingest/` sous `20_evidence/legacy-ingest/`. Les originaux restent dans `20_ingest/`, notamment pour conserver les chemins de provenance.
4. **Archiver l'ancien 40_kristal** : uniquement si le dossier contient *exactement* le README historique connu, sans fichier caché ni lien ; copie vérifiée dans `D:\EncyKlopedia_Archives_Legacy/` avant suppression de l'original. Confirmation explicite et journal.

Les données des dossiers `10_sources`, `30_working`, `20_ingest` et `50_mediatheque` ne sont **jamais supprimées** par cet outil. En particulier, la base SQLite 124,94 Gio et le catalogue de 533 œuvres candidates sont protégés.

## Décisions de migration

- `20_ingest` : zone héritée mais **non supprimable** ; les snapshots (1 123 entités) et handoffs ont de la valeur. Copie optionnelle vers `20_evidence/legacy-ingest`; suppression ultérieure requiert un audit des références absolues.
- `40_kristal` : l'audit du 2026-10-13 ne relève qu'un README. Archivage conditionnel, jamais un dossier contenant de vrais Kristals.
- `50_mediatheque` : catalogue candidat à préserver ; sa migration éventuelle vers Médiathèque kOA est **un chantier métier séparé**, pas un nettoyage de cache.
- `30_working/wikidata/wikidata.compact.sqlite` : index possiblement incomplet (`checkpoint complete=false` historique) ; ne pas supprimer, ne pas reconstruire sans audit et place disque disponible.

## Limitations

Les scripts PowerShell de jonction Windows n'ont pas été exécutés sur le PC cible. La copie d'historique et l'archivage conditionnel peuvent être testés hors Windows sur des dossiers de simulation. L'opération ne convertit pas les anciens Kristals en v9 et n'enrichit pas les Kristals avec Wikidata.
