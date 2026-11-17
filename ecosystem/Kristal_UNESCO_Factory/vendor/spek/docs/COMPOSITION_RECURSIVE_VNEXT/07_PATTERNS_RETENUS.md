# 07 — Patterns d'architecture retenus et écartés

**Base examinée :** archive fournie `senior-architecture-patterns(6).zip` (33 fiches numérotées, regroupées par thème). Cette source concerne l'**architecture logicielle**, pas le contenu rhétorique. Les choix ci-dessous sont **des adaptations proposées à Spek**, pas des affirmations selon lesquelles ils seraient déjà implémentés.

## Patterns réellement utiles maintenant

| Pattern de l'archive | Où l'utiliser dans Spek | Pourquoi / limites |
| --- | --- | --- |
| **10 — Hexagonal Architecture** (`02-structural-and-decoupling/10-hexagonal-architecture.md`) | Port `RealizationPort` pour SemantiK ; `TemplateStore` ; `RenderPort` par format | Moteur de composition pur, testable sans Tkinter, GF/PGF ou GitHub |
| **08 — Anti-Corruption Layer** (`02-structural-and-decoupling/08-anti-corruption-layer.md`) | Adaptateur versionné `CommunicationRequest/Result ↔ feuilles Spek` | Empêcher les formats de requête SA et états Kristal de polluer le modèle du template |
| **31 — Modular Monolith** (`08-emerging-and-specialized/31-modular-monolith.md`) | Modules locaux `composition`, `rhetorical`, `semantik_adapter`, `renderer`, `publication_gate` | Spek reste un outil local Python ; pas de microservices ni de bus obligatoire |
| **15 — Idempotency** (`03-data-management-consistency/15-idempotency.md`) | Calcul d'identité de compilation, sortie staging, ré-essais sûrs et publication externe | Évite productions contradictoires ou doublons après relance ; ne remplace pas les approbations |
| **07 — Strangler Fig** (`02-structural-and-decoupling/07-strangler-fig.md`) | Coexistence du compilateur plat et du nouveau moteur récursif pendant migration | Activation par version de format explicite ; pas de basculement brutal des 27 layouts |
| **04 — Graceful Degradation** (`01-stability-and-resilience/04-graceful-degradation.md`) | Afficher le plan privé quand SA est indisponible | **Jamais** remplacer une phrase requise par un triplet ou une paraphrase ; refus de publication |
| **06 — Timeout Budgets** (`01-stability-and-resilience/06-timeout-budgets.md`) | Appels locaux SemantiK multiples lors d'une composition à N feuilles | Budget total borné et erreurs explicites ; pas nécessaire d'inventer une orchestration réseau |

## Patterns utiles de manière limitée ou conditionnelle

- **12 — CQRS :** séparer en code le *modèle de lecture de l'atelier* de la *commande d'édition/validation* ; **ne pas** imposer un bus d'événements ni deux bases de données. Le pattern source prévient que CQRS est excessif pour les CRUD simples.
- **26 — Distributed Tracing :** non justifié pour un moteur Spek purement local ; des identifiants internes de build et journaux structurés expurgés suffisent. Une traçabilité distribuée n'a de valeur que si la chaîne est distribuée.
- **01 — Circuit Breaker / 03 — Exponential Backoff & Jitter :** éventuellement pour un service SemantiK réellement distant et temporairement défaillant ; aujourd'hui, un adaptateur local avec timeout et erreurs typées suffit.
- **16 — Transactional Outbox / 14 — Saga :** non adaptés au rendu local. À discuter seulement dans une architecture de publication distribuée avec effets de bord persistants ; le Manager conserve l'autorité de publication.
- **17 — Sharding / 21 — Pub-Sub / 30 — Cell-Based Architecture / 32 — Sidecarless Service Mesh / 33 — Data Mesh :** **non retenus** : aucune justification à cette complexité pour Spek local et la collection visée.

## Architecture résultante

```text
[Tkinter atelier] [CLI] [Tests]
       |            |      |
       +--------> [CompositionUseCase] <-------------------------+
                         |                                      |
        +----------------+------------------+                   |
        |                |                  |                   |
   [DefinitionStore] [SemantiKPort]     [RendererPort]           |
        |                |                  |                   |
  JSON versionnés   Adaptateur ACL     HTML/PDF/TeX/Wiki         |
                    (SA 1.0)                 |                   |
                          [Publisher externe: Manager C1/C2/C3]-+
```

La figure est un **découpage de code proposé** ; elle ne prétend pas que le Publisher appelle le moteur en boucle. La flèche schématique indique une intégration par contrats, pas un flux de publication implicite.

## Garde-fous contre le surdimensionnement

1. Implémenter une API **in-process**, pas une couche HTTP entre chaque module Spek.
2. Tester d'abord les validateurs, l'expansion de templates et le rendu par fixtures.
3. Réutiliser le format et le moteur plats existants pendant la migration.
4. Garder la publication et l'autorisation **hors de Spek**.
5. Ne pas assimiler une architecture *hexagonale* à une structure de templates *fractalement imbriqués* : les deux servent des objectifs différents.

## Sources précises dans l'archive

Chemins relatifs à la racine `senior-architecture-patterns/` :

- `02-structural-and-decoupling/08-anti-corruption-layer.md`
- `02-structural-and-decoupling/10-hexagonal-architecture.md`
- `08-emerging-and-specialized/31-modular-monolith.md`
- `03-data-management-consistency/15-idempotency.md`
- `02-structural-and-decoupling/07-strangler-fig.md`
- `01-stability-and-resilience/04-graceful-degradation.md`
- `01-stability-and-resilience/06-timeout-budgets.md`
- `03-data-management-consistency/12-cqrs.md`
- `07-observability-and-maintenance/26-distributed-tracing.md`
