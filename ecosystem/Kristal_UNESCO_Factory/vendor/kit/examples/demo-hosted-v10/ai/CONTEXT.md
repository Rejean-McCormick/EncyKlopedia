# AI Context — Demo Hosted v10 Kristal

This is a deterministic, derived orientation document for offline AI reading. It is not the canon.

- State ref: `urn:kristal:state:demo-hosted-v10`
- State Logical Commitment: `sha256:fe33e0d960d446681645ffac103685bf22a2f2fc34135a118fee84175662722b`
- Workspace profile: `open`
- Native model: `small_native_document`
- Canonical artifacts: `1`
- Sources: `1`
- External pinned references: `0`
- Materialization manifests: `0`
- Workspace-local materialization blobs: `0`

## Reading rule

Treat `canon/` and the exact `state/state-snapshot.json` as the semantic basis. Treat `ai/` as derived navigation. Use `sources/` for provenance. Materialization manifests describe physical representations and may point to local or external bytes without changing semantic identity. Do not require GitHub or any executable tool to read this package.

---

## Included orientation from `docs/00_INTENT_AND_SCOPE.md`

# Intention et scope

Démontrer le plus petit workflow v9 utile du Kristal Authoring Kit : un Logical Artifact JSON natif, un State Snapshot et une publication immuable locale.

---

## Included orientation from `docs/01_SEMANTIC_BOUNDARY.md`

# Frontière sémantique

## Subject / territoire

TODO

## Possède

TODO

## Ne possède pas

TODO

## Relations avec d'autres Kristals

TODO

## State identity v9

Le `state_ref` est défini dans `kristal.workspace.json`. Une référence externe doit être pinée à un Logical Commitment avant publication.

---

## Included orientation from `docs/02_NATIVE_MODEL.md`

# Modèle natif

Forme native : petit document JSON contenant des entités et relations. Aucune segmentation n'est nécessaire.

Logical Contract : `demo-v9-small.core/1.0`.

---

## Included orientation from `docs/03_EPISTEMIC_MODEL.md`

# Modèle épistémique

## Régimes d'information

TODO

## Provenance épistémique

TODO

## Autorité

TODO

## Incertitude / conflits / inconnus

TODO

## Provenance de build

TODO — séparer la derivation informatique de la provenance épistémique.

## Politique des sorties IA

Les sorties IA sont des propositions jusqu'à validation explicite.

---

## Included orientation from `docs/04_CANONICAL_DERIVED.md`

# Canonique et dérivé

## Source(s) de vérité

TODO

## Logical Artifacts canoniques

TODO — les enregistrer dans `canon/state.index.json`.

## Artefacts dérivés / Runtime

TODO

## Materializations

TODO — préciser ce qui est seulement représentation physique.

## Recettes de reconstruction

TODO
