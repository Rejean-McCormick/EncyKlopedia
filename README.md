# EncyKlopedia (EncyK) — 0.13.8

EncyK is the ecosystem's **source discovery, acquisition, extraction and handoff pipeline**.

> **EncyK finds and prepares source evidence. It does not store the canonical library and it does not decide the final semantic meaning.**

## Code séparé des données — installation Windows

- **Dépôt Git** : sur C: (ou n’importe quel autre disque), avec `00_system/`,
  `10_sources/seeds/`, les scripts et Skope intégré.
- **Données** : `D:\EncyKlopedia`, avec dumps, SQLite, preuves actives,
  volumes lexicaux et résultats d'acquisition. **Ce dossier n’est pas un dépôt.**
- Configuration en lecture seule d'abord : `pwsh -File .\configure_data_on_D.ps1` ;
  puis `pwsh -File .\configure_data_on_D.ps1 -Apply` une fois le plan vérifié.
- Nettoyeur : `Nettoyer_Donnees_EncyK.pyw`. **Les entités extraites, handoffs, scopes et 533 œuvres candidates sont protégés sans option de purge.** Le cleaner peut replacer quatre métadonnées de fonctionnement et retirer uniquement les copies strictement identiques laissées dans `20_evidence/legacy-ingest`. Pas de sauvegarde/archivage ; les fichiers inconnus et modifiés sont conservés.

La configuration crée des **jonctions uniquement pour les zones de données**.
Aucun dump n’est déplacé sur C: et aucun exécutable n’est installé dans D:.
L'ancien script `Migrer_EncyKlopedia.pyw` (v0.13.2) **ne doit pas être exécuté** :
il supposait à tort que le dépôt de code se trouvait sur D:.
Voir [le nettoyage respectueux des données](docs/NETTOYAGE_DONNEES_PROTEGE_WIKIDATA_0_13_6.md).

## Responsibility

```text
external sources
      ↓
EncyK
  discover
  acquire
  scope
  extract losslessly
  prepare external identity candidates
      ↓
Médiathèque kOA
  persistent source authority
      ↓
IK → DaaT (optional integration path)
      ↓
Kristal / Kristall
  semantic authority
      ↓
Kompiler
  read-only context compilation
```

## Repository zones

```text
00_system      code, contracts, configuration, architecture docs
10_sources     seeds + acquisition inputs/caches
20_evidence    outgoing lossless evidence + Médiathèque handoffs
30_working     rebuildable indexes, discovery state and caches
90_runtime     temporary/runtime status, reports and recovery
```

There is deliberately no `40_kristal` and no `50_mediatheque` in the active architecture.

## Scope pipeline

```text
configured roots
   ↓
resolve source identities
   ↓
discover project scope
   ↓
freeze exact external entity IDs + project roles
   ↓
extract COMPLETE selected source records
   ↓
prepare source-qualified external identity candidates
   ↓
content-addressed Médiathèque handoff
```

The engine is scope-rooted and domain-neutral. Existing intellectual scopes happen to use people as roots; other scopes may use works, installations, processes or other local role/kind hints.

## Lossless evidence invariant

Selection rules decide **which source records enter the scope**. They do not decide which fields are discarded.

For Wikidata, an admitted entity is retained as complete source JSON including claims, literal values, statement IDs/ranks, qualifiers, references, labels, aliases, descriptions, external identifiers and sitelinks.

The global SQLite, optional project SQLite, entity vault and random-access locator are derived accelerators only.

## External identity candidates

`06_prepare_identity_candidates.py` emits source-qualified identity hints such as:

```text
wikidata:Q8018
```

These are **not** Kristal/Kristall semantic identities. They do not mint KQ/KP/KA/KS identifiers and they are not assertions. Their purpose is to preserve source identity and useful external IDs through the handoff.

## Source authority

EncyK no longer maintains a mini-Médiathèque.

The canonical handoff target is:

```text
Médiathèque kOA >= 0.2.0
koa.source-catalog/2.0.0
```

Médiathèque owns durable Source → Snapshot → Representation identity, hashes, rights/access facts and stable source locators. `20_evidence/` can be retained for retry/audit, but it is not a second canonical library.

## DaaT / Kristal / Kristall

**DaaT** is the human name; `daat` is the machine identifier. DaaT is an optional external IK↔Kristal admission/contract-mapping boundary. It is not an EncyK stage.

Current compatibility baseline:

- Interaction Kernel `2.0.0-dev.2`;
- portable Kristal contract `kristal_state/6.0` / Standard `6.0.0`;
- Kristal/Kristall `7.0.0-draft.3.2`.

EncyK does not vendor those contracts and does not write Kristal/Kristall artifacts.

## Kompiler

Kompiler `0.5.0` is downstream and read-only. It compiles context from knowledge read surfaces. It is not a source normalization/acquisition stage and EncyK does not call it as part of harvest.

## Active handoff contract

```text
encyk.source-evidence-handoff/2.0.0
```

See:

- `00_system/contracts/knowledge-baseline.json`
- `00_system/contracts/source-evidence-handoff/2.0.0/`
- `00_system/docs/architecture.md`
- `00_system/docs/ecosystem-boundaries.md`

## Main commands

Default pipeline:

```powershell
.\harvest.ps1 -Scope catholic-pilot
```

Force raw discovery/extraction when explicitly desired:

```powershell
.\harvest_raw.ps1 -Scope catholic-pilot
```

Use the global discovery index as an accelerator:

```powershell
.\harvest.ps1 -Scope catholic-pilot -DiscoveryBackend index
```

Optionally build a per-project query SQLite:

```powershell
.\harvest.ps1 -Scope catholic-pilot -BuildQueryIndex
```

GUI:

```text
run_scope_manager.pyw
```

## Authority summary

- source discovery/acquisition/extraction: **EncyK**;
- persistent source bytes/snapshots/representations: **Médiathèque kOA**;
- IK↔Kristal admission/mapping when used: **DaaT**;
- semantic identity and epistemic/crystallization artifacts: **Kristal/Kristall**;
- context compilation over knowledge read surfaces: **Kompiler**.

## Skope (outil EncyK intégré) — 0.13.0

Le dépôt intègre maintenant **Skope** sous `00_system/tools/skope/` pour explorer les graphes de QID, régler les branches et proposer des candidats par convergence. Skope réutilise **en lecture seule** l’index global compact EncyK ; il ne reconstruit plus un second cache Wikidata.

- Double-cliquer `Lancer_Skope.pyw` et choisir l’index global finalisé, puis explorer l’interface Web locale.
- L’export produit une **proposition** `skope-encyk-proposal/1.0` contenant un registre de QID et un scope EncyK v3 sous `staged/`. Vérifier les QID, le dump et les contrôles de périmètre avant copie manuelle.
- Les JSON Wikidata complets ne figurent pas dans le pack Skope : l’extraction intégrale et le handoff Médiathèque restent du ressort d’EncyK.
- Guide `arketype.scope-guidance/1.0` (Arketype v1.4) acceptée en **lecture documentaire**, sans injection dans `state_scope` ni droit d’activation/publication.
- `Nettoyer_Fichiers_Obsoletes.pyw` : interface de nettoyage local sous contrôle SHA-256. **Aucun ancien fichier EncyK supprimable dans cette migration** (manifeste vide).

Détails : `00_system/tools/skope/README.md` et `00_system/tools/skope/docs/MIGRATION_SKOPE_ARKETYPE.md`.

## Consolidation Skope (0.13.1)

**Skope est un outil interne d’EncyKlopedia**, situé dans `00_system/tools/skope/`.
Le dépôt Skope standalone n'est plus une dépendance ni un dépôt actif :
ni importeur Wikidata concurrent, ni second registre de sources, ni export de preuves depuis Skope.
L'outil lit l'index EncyK complet **en lecture seule**, explore les scopes, puis
produit une **proposition non canonique** à vérifier avant le pipeline EncyK.

- Lancer : `Lancer_Skope.pyw` à la racine.
- Documentation : `00_system/tools/skope/README.md`.
- Si une ancienne installation EncyK contient des copies héritées de la première
  intégration, ouvrir `Nettoyer_Fichiers_Obsoletes.pyw` pour les examiner ;
  l'outil n'efface rien automatiquement, ne touche pas au repo Skope externe
  et refuse les fichiers dont l'empreinte a changé.
- **Ne jamais effacer** les répertoires locaux `10_sources`, `20_evidence`,
  `30_working`, `90_runtime`, ni les données ou fichiers inconnus.

Mettre à jour EncyK en sauvegardant le dépôt puis en superposant le contenu de
ce ZIP à sa racine ; ne pas créer de second dépôt Skope.

## Enrichissement d'un Kristal par Skope (0.13.7)

Depuis le dépôt **sur C:**, ouvrir `Lancer_Skope.pyw`. L'interface permet de choisir un
`kristal.workspace.json` sous `C:\mycode\Kristal\locals`, et préremplit
l'index `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite`.
Pour `Kristal-Botany`, le guide Arketype PRF-03 est proposé automatiquement (source
locale `00_system/tools/skope/config/arketype/botany.scope-guidance.json`,
non canonique). Skope exporte une **proposition** incluant la cible déclarée,
jamais une injection du canon botanique. Le lanceur peut aussi exécuter explicitement
`check` et `build-discovery` du Kit 3.3.1 choisi par l'utilisateur.
Aucune écriture dans les dumps, index, Kristals ou droits d'accès au démarrage.

## Skope v0.13.8 : recherche utilisable sur très gros index

- Les QID/PID/LID (par exemple `Q192154`) interrogent `entity.id` directement.
- Les noms/alias utilisent `idx_name_norm` en deux passes bornées : égalité puis préfixe.
- Pas de jointure-tri global sur les noms, pas de reconstruction de SQLite.
- Bouton Chercher : chargement visible, erreur explicite et délai d'attente.
- Après mise à jour du code C:, **arrêter puis relancer** le serveur Skope avant Ctrl+F5 dans le navigateur.
