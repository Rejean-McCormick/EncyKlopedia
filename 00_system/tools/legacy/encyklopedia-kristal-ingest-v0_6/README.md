# EncyKlopedia → Kristal ingest orchestrator v0.6

## But

Construire, à partir de la copie SQLite locale de Wikidata, un corpus de travail **centré sur les personnes du seed**, puis préparer un snapshot immuable pour le passage par **Da'at → Kristal v5**.

Le pipeline n'invente pas de schéma Kristal et ne produit jamais de Reference Exchange par lui-même.

```text
seed persons
   ↓ resolve local QID
people anchors
   ├── direct context (P101/P106/P135/P1142/P737/...)
   ├── authored works (reverse P50)
   ├── notable works (P800)
   ├── movements / ideologies (P135/P1142)
   ├── fields of work (P101)
   └── influence graph (P737)
        ↓
30_working/encyklopedia-harvest/runs/<run>
        ↓ freeze + hashes
20_ingest/snapshots/encyklopedia/<snapshot>
        ↓
20_ingest/handoffs/kristal/<snapshot>/daat-handoff.json
        ↓ Da'at + pinned Kristal v5
40_kristal/...
```

## Scripts

1. `01_resolve_people.py` — réutilise le resolver local existant et stabilise `qid-map.local.json`.
2. `02_extract_people.py` — profils-source Wikidata des personnes + toutes leurs signatures de relation N1.
3. `03_extract_works.py` — œuvres/documents via `P800` et surtout reverse `P50`.
4. `04_extract_intellectual_context.py` — courants (`P135`), idéologies (`P1142`), domaines (`P101`) et influence (`P737`).
5. `05_publish_mediatheque_candidates.py` — feed **candidat seulement** vers UCKK Médiathèque.
6. `06_build_source_snapshot.py` — fige l'export source et calcule SHA-256.
7. `07_prepare_daat_handoff.py` — prépare le handoff vers Da'at; vérifie facultativement une installation Kristal pinée.
8. `run_pipeline.py` — orchestre toute la chaîne.

## Commande PowerShell 7 — pipeline complet

Depuis `D:\EncyKlopedia` :

```powershell
python -u .\00_system\tools\encyklopedia-kristal-ingest\scripts\run_pipeline.py `
  --root .
```

Avec une copie locale du dépôt Kristal v5 pour vérifier le pin et le schéma :

```powershell
python -u .\00_system\tools\encyklopedia-kristal-ingest\scripts\run_pipeline.py `
  --root . `
  --kristal-root C:\mycode\Kristal
```

Ou double-cliquer :

```text
run_kristal_ingest.pyw
```

Le Wikidata Local Manager v0.6 contient aussi un bouton **Harvest → Kristal**.

## Commandes étape par étape

```powershell
$Root = (Get-Location).Path
$RunId = "manual_$(Get-Date -Format yyyyMMdd_HHmmss)"
$Run = Join-Path $Root "30_working\encyklopedia-harvest\runs\$RunId"
New-Item -ItemType Directory -Force $Run | Out-Null
$Scripts = Join-Path $Root "00_system\tools\encyklopedia-kristal-ingest\scripts"

python -u "$Scripts\01_resolve_people.py" --root $Root
python -u "$Scripts\02_extract_people.py" --root $Root --run-dir $Run
python -u "$Scripts\03_extract_works.py" --root $Root --run-dir $Run
python -u "$Scripts\04_extract_intellectual_context.py" --root $Root --run-dir $Run
python -u "$Scripts\05_publish_mediatheque_candidates.py" --root $Root --run-dir $Run --snapshot-name $RunId
python -u "$Scripts\06_build_source_snapshot.py" --root $Root --run-dir $Run
python -u "$Scripts\07_prepare_daat_handoff.py" --root $Root
```

## Pourquoi P101 n'est pas rangé avec les courants

`P101` est un **field of work**. Il est conservé comme domaine intellectuel. Les courants utilisent `P135` (movement) et `P1142` (political ideology). Cela évite d'aplatir une discipline comme « mathématiques » en mouvement philosophique.

## Limite actuelle du compact index

Le compact index conserve :

- les labels et alias;
- la présence de toutes les propriétés;
- les arêtes dont la valeur est une entité Wikidata;
- P569/P570/P1317 pour la chronologie.

Il ne conserve pas encore les valeurs littérales génériques. Ainsi `P577` (date de publication), `P1476` (titre monolingue), ISBN, VIAF, Project Gutenberg IDs, URLs, etc. peuvent être détectés comme **présents** mais leurs valeurs ne sont pas encore dans SQLite.

La phase suivante pourra ajouter un `selected-literal index` ciblé sur les personnes/œuvres découvertes, sans gonfler l'index principal.

## Autorité

- `30_working` = reconstruction locale, dérivable, non canonique.
- `20_ingest/snapshots` = export source immuable + provenance.
- `20_ingest/handoffs/kristal` = contrat de passage Da'at.
- `40_kristal` = uniquement les artefacts réellement produits par la mécanique Kristal existante.
- `50_mediatheque/catalog/candidates` = candidats, pas catalogue autoritaire final.
