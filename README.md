# EncyKlopedia (EncyK) — 0.13.14

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


## Skope Wizard (0.13.9)

Le bouton **✦ Wizard** dans la barre supérieure ouvre un assistant facultatif,
sans modifier la mise en page de Skope. Il explique les paramètres (direction,
propriétés PIDs, profondeur, budget, convergence, exceptions par branche),
propose des valeurs contextuelles Botany (PRF-03), représente leurs effets
par des graphes pédagogiques **non chiffrés**, et ne renseigne les champs
qu'après un clic explicite sur **Appliquer**. Le mode **Mesurer** interroge
`/api/preview` en lecture seule pour afficher des comptes réels et la troncature ;
ces résultats ne sont pas des preuves Wikidata. Le canon Kristal et les fichiers
sur D: ne sont pas modifiés. L'extraction automatisée reste une étape séparée.


## Skope · Botanique mondiale (0.13.10)
Le choix `Kristal-Botany` préremplit automatiquement Q192154, P171 entrant, profondeur 6
(UI jusqu’à 8, backend jusqu’à 8), plafond d'aperçu 10 000, convergence 14,6 %,
minimum 8, extra 0. Le Wizard propose la même configuration et une mesure comparative
bornée explicitement à 1 500 QID. La grande exploration ne se recalcule plus
automatiquement à chaque changement : utiliser `Calculer le périmètre`.
**Ce mode reste un aperçu non exhaustif et non canonique.** Il n'extrait pas des millions
de taxons ; la collecte mondiale partitionnée est une évolution séparée.

## Définir un scope géographique (Skope 0.13.12)

Dans Skope, conserver les réglages taxonomiques, puis ouvrir **Wizard → 5 · Géographie**.
La recommandation Botany : région `Q49` (Amérique du Nord), priorité `Q16` (Canada),
mode « Prioriser sans exclure les taxons mal documentés ». Les QID peuvent être changés
pour d'autres projets. La couverture est **mesurée seulement après** « Calculer le périmètre ».
L'option stricte ne constitue pas une flore du Canada exhaustive : Wikidata manque de données
de répartition, et la traversée de la taxonomie précède le filtre. Voir
`00_system/tools/skope/docs/SCOPE_GEOGRAPHIQUE_AMERIQUE_DU_NORD_0_13_11.md`.

## Skope 0.13.12 : zone secondaire visible

Dans l'interface principale, sous le Kristal, les deux champs QID
**Zone prioritaire** (Canada `Q16`) et **Zone secondaire** (Amérique du Nord `Q49`)
sont directement modifiables. Choisir le mode d’application et cliquer sur
**Appliquer les zones**, puis **Calculer le périmètre**. Le Wizard partage
les mêmes valeurs et les deux zones sont sauvegardées dans le ZIP de scope.

Ce sont des signaux géographiques Wikidata incomplets : la région ne peut pas
rendre exhaustive une traversée tronquée, ni prouver l'absence des espèces.

## Skope 0.13.13 — scopes sans plafond logique

Un objectif `max_entities=0` demande un inventaire sans plafond global. La prévisualisation HTTP reste **bornée à 10 000 QID**, mais le bouton explicite « Collecter les QID par lots » emploie un état SQLite sur disque sous `D:\EncyKlopedia\30_working\skope-large-scopes`. Le parcours est interruptible, reprenable à paramètres inchangés et n’écrit jamais dans la source SQLite ni dans le canon Kristal. Le ZIP exporté avec un scope supérieur à 10 000 QID est un **plan**, pas une liste exhaustive ; les QID complets sont écrits dans un `.jsonl` une fois le travail terminé. Pas d’extraction de JSON Wikidata complet dans cette étape.

## v0.13.15 — Skope consolidation
The current user interface retains the density graph (three layers, filters, magnifier, inspect) while restoring the full English 0.13.14 collection results dialog and ZIP actions.


## Verified full Wikidata records in Skope 0.13.16

After a completed batch QID inventory, use **05 · Full Wikidata Records** in the
existing browser UI. Select the bundled extraction profile, check sources, then
explicitly confirm **Extract Full Wikidata Records**. The preflight validates the
existing completed QID job, verified source manifest, matching fast locator,
compression index, and disk space. It never scans the 96 GiB dump or builds an
index. Chunks are gzip JSONL with per-entity SHA-256; work remains under
`D:/EncyKlopedia/30_working/skope-extractions` until a verified snapshot is
promoted by a same-volume rename into `20_evidence/scope-snapshots` on D:.
No Kristal canon is modified. Pause/resume works at completed batch boundaries.
The profile file is under `00_system/tools/skope/config/extraction-profiles`.
Preflight blockers must be resolved before the Start button unlocks.
