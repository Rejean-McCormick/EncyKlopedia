# 18 — Alignement Médiathèque ↔ DaaT ↔ Kristal/Kristall

**Projet :** Médiathèque kOA / instances spécialisées  
**Interaction Kernel :** `2.0.0-dev.2`  
**DaaT :** nom humain `DaaT`, identifiant machine `daat`  
**Contrat Kristal portable :** `kristal_state/6.0`  
**Baseline Kristal/Kristall :** `7.0.0-draft.3.2`

## Décision d’architecture

La Médiathèque est l’autorité persistante des octets, versions, SHA-256, droits et locators physiques. Kristal/Kristall reste l’autorité du sens interne d’un Kristal. Un Kristal peut référencer du contenu de la Médiathèque et le fichier qui matérialise ce Kristal peut lui-même être versionné dans la Médiathèque.

```text
Médiathèque
  contenus / sources / médias
  + fichiers de Kristals versionnés
          │
          │ ArtifactRef / locator propriétaire
          ▼
Interaction Kernel
          │
          ▼
DaaT (`daat`)
  admission + mapping de contrat explicite
          │
          ▼
Kristal portable (`kristal_state/6.0`)
          │
          ▼
Kristall v7
  identité sémantique / Mesh / axes / cristallisation
```

DaaT ne stocke pas les sources, n’acquiert pas les médias, ne crée pas les identités KQ/KP/KA/KS et ne possède pas les décisions de cristallisation.

## Deux identités à ne jamais confondre

Pour un Kristal stocké dans une Médiathèque :

```text
kristal_ref   = identité sémantique stable (Kristal/Kristall)
media_uuid    = identité de l’artefact stocké (Médiathèque)
version_uuid  = version physique immuable (Médiathèque)
sha256        = intégrité de cette version
```

Ces identités sont reliées mais ne sont jamais interchangeables.

## Références de contenu

Un Kristal peut pointer vers une version média par locator opaque :

```text
koa-media://version/<version_uuid>
```

Les chemins locaux ne quittent pas la Médiathèque. Une nouvelle version d’un média ou d’un Kristal produit une nouvelle identité de version physique sans changer l’identité sémantique du Kristal.

## UCKK

L’instance UCKK utilise ce modèle pour stocker :

```text
1 Kristal UCKK
10 Kristals de voies
100 Kristals de cours
64 médias Korpus au bootstrap
```

Le catalogue Moodle `uckkarchive_kartifact` lie l’identité sémantique `kristal_ref` au média stocké, et `uckkarchive_kversion` lie chaque publication à une version physique immuable. L’ancien `uckkarchive_kristal` reste un objet historique d’insight/archive Moodle et n’est pas utilisé comme autorité des Kristals canoniques.

## Limite volontaire

La Médiathèque stocke, versionne et sert les artefacts. Elle peut indexer leur hiérarchie pour l’accès, mais elle ne devient jamais l’autorité du contenu sémantique d’un Kristal.
