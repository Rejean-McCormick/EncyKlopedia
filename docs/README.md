# Documentation Konstellation

Cette arborescence est la **référence documentaire du repo**. Voir aussi le [Manifeste documentaire](DOCS-MANIFEST.md) pour le statut normatif de chaque fichier. Elle décrit deux choses distinctes :

- **implémentation courante : **Konstellation 1.0 RC (`1.0.0-rc.2`)**, alignée sur les contrats 1.0 ;
- **qualification finale : Konstellation 1.0.0**, obtenue seulement lorsque tous les gates de release sont verts.

La documentation 1.0 est normative. `IMPLEMENTATION.md` décrit l’état réel du code et `VALIDATION-v1.0-RC.md` distingue ce qui a été exécuté dans ce snapshot de ce qui reste à qualifier dans l’environnement de release.

## Principe directeur

> Le Kristal définit ce qui est connaissable. La Lens définit l'angle. Konstellation reconnaît la structure visible, construit un plan de navigation explicable et la représente avec des renderers contrôlés. Une vue n'ajoute jamais de vérité au Kristal.

## Parcours de lecture

### Architecture et sémantique

1. [Décisions et invariants](00-decisions.md)
2. [Architecture système](01-architecture.md)
3. [QuerySpec, Lens, Reader Policy et état](02-query-model.md)
4. [Navigation adaptative](03-navigation.md)
5. [Autorité, sémantique et projections](04-knowledge-semantics.md)
6. [Exécution et Renderer Registry](05-execution.md)
7. [Intégrations et contrats externes](06-integrations.md)

### Production

8. [Plan de livraison 1.0](07-delivery-plan.md)
9. [Migration v0.7 -> 1.0](08-migration.md)
10. [Audit des sources et références](09-source-audit.md)
11. [Stratégie de validation](10-validation-report.md)
12. [Renderer Registry](17-renderer-registry.md)
13. [Performance et scalabilité](18-performance-scalability.md)
14. [Sécurité](19-security.md)
15. [Observabilité et fiabilité](20-observability.md)
16. [Tests et golden corpus](21-testing-golden-corpus.md)
17. [Déploiement](22-deployment.md)
18. [Extension à de nouveaux Kristals](23-extension-guide.md)
19. [API et contrats publics](24-api-contracts.md)
20. [Critères de release 1.0](25-release-1.0.md)
21. [Glossaire](26-glossary.md)
22. [Comportement attendu par famille de Kristal](27-behavior-by-kristal.md)
23. [Anti-patterns interdits](28-anti-patterns.md)
24. [Séquences de référence](29-reference-sequences.md)

### Alignement Kristal et navigation

- [Navigation adaptative — spécification détaillée](15-adaptive-navigation.md)
- [Alignement Kristal v6](16-kristal-v6-alignment.md)
- [État d'implémentation](IMPLEMENTATION.md)
- [Validation 1.0 RC](VALIDATION-v1.0-RC.md)
- [Import Kristal](IMPORT.md)
- [Intégrations](INTEGRATIONS.md)
- [Collections GitHub Kristal v10](30-kristal-v10-github.md)
- [Lecteur local v10 et Manager alpha.14](33-kristal-v10-local-reader.md)
- [Opérations](OPERATIONS.md)

### Exemples et historiques de domaine

- [Astrolabe](11-astrolabe.md)
- [Biblical Graph](12-biblical-graph.md)
- [Playwright](13-playwright.md)
- [Théophile enrichment](14-theophile-enrichment.md)

Ces documents illustrent l'architecture mais **ne définissent pas le modèle universel**.

## ADRs

Les décisions structurantes sont figées dans `docs/adr/` :

- [ADR-0005 — Bounded selection tree](adr/ADR-0005-bounded-selection-tree.md)
- [ADR-0006 — Kristal v6 reste l'autorité canonique](adr/ADR-0006-kristal-v6-authority.md)
- [ADR-0007 — Affordances de navigation dérivées](adr/ADR-0007-navigation-affordances.md)
- [ADR-0008 — Séparation planner / projection / renderer](adr/ADR-0008-planner-renderer-separation.md)
- [ADR-0009 — Actionability n'est pas une autorité d'exécution](adr/ADR-0009-actionability-not-authority.md)
- [ADR-0010 — Registry fermé de renderers](adr/ADR-0010-controlled-renderer-registry.md)

## Guides par rôle

- [Guide utilisateur](guides/USER.md)
- [Guide intégrateur Kristal](guides/INTEGRATOR.md)
- [Guide développeur](guides/DEVELOPER.md)
- [Guide opérateur](guides/OPERATOR.md)

## Statut des versions

`VALIDATION-v1.0-RC.md` est le rapport courant. Les fichiers `VALIDATION-v0.x.md` sont historiques et ne remplacent ni les critères de release 1.0 ni l’état d’implémentation courant.
