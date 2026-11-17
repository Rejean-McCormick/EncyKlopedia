# Kristal Local Kit 3.2.4 — Validation Report

## Portée

Cette version garde inchangés `kristal.local-workspace/3.2.0`, les profils de Logical Commitment et le State Commitment. Elle réaligne uniquement la couche de lecture dérivée avec l'objectif GitHub à grande échelle : une IA recevant `kristals/<slug>/` doit disposer d'un entrypoint compact, d'un index déterministe et des représentations physiques localement disponibles.

## Garanties visées

- le build sémantique v9 reste indépendant du hosting et de la read surface ;
- `read-surface` est read-only et produit `kristal.github-read-surface/1.0` ;
- la surface possède un digest opérationnel déterministe distinct de tout commitment sémantique ;
- `AI_START_HERE.md`, `AI_MANIFEST.json`, `ai/*`, canon/provenance/docs utiles et l'état exact sont projetables sans miroir complet du workspace ;
- les Materialization Manifests sont visibles dans `ai/INDEX.json` ;
- les blobs workspace-locaux explicitement référencés sont vérifiés et décrits comme objets de transport séparés, sans être injectés automatiquement dans Git ou `pack-ai` ;
- locators externes/manquants restent visibles comme disponibilité partielle et ne sont jamais fetchés implicitement ;
- une modification d'un fichier indexé après `build-ai` rend la read surface non prête jusqu'à reconstruction ;
- `pack-ai` réutilise la même projection de lecture, en ajoutant seulement l'enveloppe workspace locale.

## Compatibilité

Le workspace reste `kristal.local-workspace/3.2.0`. `kristal.local-inspection/1.0` est conservé avec une extension additive `github_read_surface`. Le nouveau contrat `kristal.github-read-surface/1.0` est opérationnel et non sémantique.

## Limites

Le Local Kit décrit et vérifie les bytes locaux disponibles. Il ne télécharge pas les matérialisations distantes, ne maintient pas le catalogue global d'une collection GitHub et n'effectue pas le push : ces responsabilités appartiennent respectivement au runtime/exchange, au Manager et à la couche hosting.

## Validation de cette build

Exécuté sur cette archive avant packaging :

- compilation Python des outils/scripts/tests : PASS ;
- parse de tous les JSON : PASS ;
- liens Markdown locaux : PASS ;
- `check` + `check-ai` + `read-surface --require-ready` sur `demo-open`, `demo-v9-small` et `demo-hosted-v10` : PASS ;
- test ciblé d'une matérialisation locale : manifest dans la read surface, blob séparé en `materialization_objects`, disponibilité/digest corrects : PASS ;
- test ciblé de staleness : modification d'un fichier canonique après `build-ai` rend `read-surface.ready=false` : PASS.

La suite `tests/test_tools.py` a aussi été étendue avec les deux cas de régression correspondants. Dans cet environnement d'exécution, la suite complète par sous-processus est anormalement lente ; la validation ci-dessus couvre directement les nouveaux chemins 3.2.4 sans revendiquer un run complet de toute la suite.
