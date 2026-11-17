# 24 — Catalogue de dépôts GitHub

## But

La Médiathèque peut exposer des dépôts GitHub comme **références externes navigables** sans les confondre avec des contenus stockés.

## Source UCKK 0.5.0

Le bootstrap UCKK utilise `Kristal-kOA-Ecosystem v0.6.3` comme source de cartographie :

```text
views/public-repository-directory.md
source-registry/source-registry.json
        ↓
bootstrap/repositories/github-repositories.json
        ↓
mod_uckkarchive --mode=repositories
        ↓
uckkarchive_media (external_reference)
        + sourceurl=https://github.com/...
        + metadata boundary / role / commit
        ↓
collection « Référentiels GitHub — écosystème kOA »
```

## Autorité

GitHub reste l’hôte externe du dépôt. Médiathèque conserve seulement :

- le lien observé;
- le rôle/boundary fournis par le Kristal d’écosystème;
- l’état d’observation locale du snapshot;
- le commit épinglé lorsque le source registry le déclare, avec un lien direct `.../commit/<sha>`;
- la provenance du snapshot ayant fourni ces faits.

Un lien GitHub **n’est pas** traité comme une version locale du dépôt. Pour obtenir une version immuable, il faut importer un snapshot/fichier avec SHA-256 séparé.

## UI

Les médias `external_reference` possédant une URL `github.com` affichent un badge GitHub et un bouton direct. La page détail conserve l’URL externe et les métadonnées de provenance.

## Idempotence

Chaque URL reçoit un `media_uuid` et un `source_uuid` UUID5 déterministes. Réimporter le même catalogue met à jour la fiche au lieu de créer un doublon.

## Répertoire humain

`mediatheque-uckk/bootstrap/repositories/GITHUB_LINKS.md` fournit la liste lisible des 58 dépôts avec liens directs et, pour les 12 références épinglées, un lien vers le commit observé.
