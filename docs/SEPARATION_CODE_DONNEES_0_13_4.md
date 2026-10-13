# EncyK 0.13.4 — Code Git séparé des données locales

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

Si tu mets à jour un ancien clone C: où `20_evidence/`, `30_working/` ou `90_runtime/` contiennent encore des fichiers suivis par Git, fais d'abord une mise à jour propre / commit de la version 0.13.4. **Ne les efface pas à la main.** La version source 0.13.4 archive les anciens README et manifestes d'exemple sous `docs/historical-*` pour ne plus bloquer ces jonctions. Si un blocage subsiste, l'outil s'arrête et affiche le chemin exact.

## Nettoyeur pour D: sans sauvegarde

Fermer les outils qui accèdent aux anciennes zones, puis lancer `Nettoyer_Donnees_EncyK.pyw` depuis le dépôt de CODE.

1. **Analyser** : aucune écriture ; affiche chaque déplacement/suppression envisagé, plus les conflits et inconnus.
2. **Déplacer et nettoyer** : après avertissement et saisie de `EFFACER`, déplacer les originaux vérifiés par SHA-256 vers leur destination définitive, supprimer les copies strictement identiques de l'ancienne action « Copier 20_ingest » et retirer les dossiers vides.

Aucun backup, aucune archive, aucun duplicata intentionnel n'est créé.

- `20_ingest/manifests` → `20_evidence/manifests`.
- `20_ingest/scope-snapshots` → `20_evidence/scope-snapshots`.
- `20_ingest/snapshots/wikidata` → `20_evidence/acquisition-snapshots/wikidata`.
- `20_ingest/provenance` → `20_evidence/provenance`.
- `20_ingest/checkpoints` → `90_runtime/checkpoints`.
- Ancien handoff DaaT v5 → `20_evidence/legacy-handoffs/daat` (conservé comme pièce historique non active, une seule copie).
- `50_mediatheque/catalog/candidates` → `20_evidence/mediatheque-candidates` (ne constitue pas une admission canonique dans Médiathèque).
- `40_kristal` → suppression du README historique reconnu et des dossiers vides uniquement, jamais de vrais Kristals.

**Seuls les 17 fichiers reconnus par l'audit fourni sont éligibles**. Tout fichier différent, nouveau ou non reconnu est laissé en place ; un conflit de SHA-256 bloque le nettoyage.

Ne pas toucher au dump Wikidata ~96 Gio, à l'index SQLite ~125 Gio ni aux bases lexicales. `20_evidence/legacy-ingest` peut être retiré s'il ne contient que des copies identiques de ces fichiers ; il ne faut pas le supprimer à la main.

**Chemins historiques dans les manifestes :** certains anciens JSON font encore référence à `20_ingest/`, `50_mediatheque/` ou à un chemin de code sous D:. Pour préserver leurs empreintes de provenance, le cleaner ne réécrit pas les originaux. Ces anciens pointeurs ne sont pas des destinations actives ; les nouveaux manifestes doivent être régénérés par EncyK quand le pipeline est relancé.

## Décisions de migration

- Les sources et les index restent exclusivement sur D:.
- Les données historiques utiles sont **déplacées**, non sauvegardées dans un autre répertoire.
- Les droits de publication et la migration effective vers Médiathèque kOA restent des processus externes explicites.
- Aucun ancien état n'est implicitement promu en Kristal canonique.

## Limitations

Les scripts PowerShell de jonction Windows n'ont pas été exécutés sur le PC cible. La copie d'historique et l'archivage conditionnel peuvent être testés hors Windows sur des dossiers de simulation. L'opération ne convertit pas les anciens Kristals en v9 et n'enrichit pas les Kristals avec Wikidata.
