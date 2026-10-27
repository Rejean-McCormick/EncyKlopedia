## 2026-10-17 — Accessible French semantic presentation (experimental)

- Kristal v10 local reader: derived graph relation labels resolve grounded French names for known Wikidata properties (including P138) and a bounded set of explicitly interpreted Catho predicates; unknown P IDs remain explicit, never guessed.
- Astrolabe: word-aware search instead of arbitrary substring matches, improved result diversity without merging identities, and correct entity-type labels.
- Exploration: empty/technical facets hidden unless actively filtered, epistemic state labels rendered in French, and advanced inspector retains original identifiers and provenance.
- Constellation: derived node-kind metadata excluded from leading relationship groups, still visible in inspector.
- No canonical Kristal mutation, no new permissions, no changes to configured local Kristal directories or stored reader policies. Full Windows/browser regression is pending.

## 2026-10-16 — Sélecteur local neutre expérimental
- Un lanceur principal `Konstellation.cmd`, choix du Kristal dans l'interface.
- Catalogue local privé au format interne `kristal-local-catalog-v10` (répertoire explicitement configuré).
- Démarrage sans corpus présélectionné, démonstration Théophile non chargée par défaut.
- Les anciens scripts sont rangés sous `tools/legacy-root`; migration contrôlée et réversible.

## Correctif du 16 octobre 2026 — domaines de relations du lecteur Catho

- Répare le plantage au démarrage `relation-registry: /relations/1/domain must NOT have more than 10 items`.
- Partitionnement déterministe des relations dépassant dix types de domaine, sans affaiblir le schéma ni perdre d'assertions.
- Test de non-régression pour plus de dix types de nœuds et pour les liens intertypes.
- Voir `docs/36-correctif-registre-relations-catho.md`.

## 2026-10-16 — Parcours de lecture des Kristals (correctif expérimental)

- Types de nœuds dérivés convertis en perspectives de lecture séparées,
  avec relations typées et conservation intégrale des métadonnées d'origine.
- Entrée Personnes (Catho) plutôt que `V9 state`, avec six parcours rapides.
- Libellés de présentation locaux facultatifs et limités aux types/prédicats
  réellement présents dans le graphe; aucune promotion sémantique.
- Suppression de la qualification erronée « Corpus de démonstration » pour
  les vraies données locales; avertissement de projection non canonique.
- Aucune mutation du Kristal, aucune modification Manager / Interaction Kernel / Daat.
- 9 tests ciblés du lecteur réussis. Build Astro/Windows non qualifiés ici.


## Correctif local Catho — 2026-10-16

- Launchers: local Catho path preserved at `C:\mycode\Kristal\locals\A-Kristal-Catho`.
- Main launcher honors optional `config/active-reader.json` ahead of the legacy Theophile pack.
- Added explicit `Ouvrir_Theophile_demo.cmd` and path-specific instructions; no changes to Daat, Manager, Kernel or Catho canon.

## Unreleased — Lecteur local Kristal v10 et Manager alpha.14 (2026-10-16)

- Ajout expérimental de `kristal-local-v10` : état sémantique v9 sous Framework v10, vue locale structurelle et modèle dérivé optionnel, strictement en lecture seule.
- Contrôle des ressources, états exporté/construit, empreintes canoniques des graphes et diagnostic Discovery périmé.
- Consommation minimisée des résultats opérationnels de Manager alpha.14 avec politique d'accès distincte. `READY` reste `not_checked` du point de vue de la qualification.
- Ajout d'un exemple Catho et lanceur local Windows; aucune modification de Manager, Framework, Interaction Kernel ou Daat.
- Statut : expérimental; aucune validation de release finale n'est revendiquée.

# Unreleased — Manager candidate + Discovery 3.3 consolidation (2026-10-13)

- Local-only My Kristals now reads `kristal.manager-local-inventory/0.1-candidate` **with a separate explicit, default-deny operator access policy**; no implicit access from the Manager inventory itself.
- Enforces state_ref and state commitment matching, rejects duplicate identities, local paths and sensitive data. Hosted and local observations stay separate.
- Optional bounded local `konstellation.discovery-projections/0.1` catalog from Authoring Kit 3.3; classification, reader hints and measured bytes remain advisory, noncanonical and non-authorizing.
- `scripts/project-discovery.mjs` projects explicitly selected Kit manifests without scanning or accessing any network.
- My Kristals remains loopback-only. Legacy synthetic preview still supported but its fixture moved to `examples/fleet/legacy/`.
- Added `Nettoyage_Konstellation.pyw` for manual deletion of the superseded local fixture only after SHA-256 verification and GUI confirmation.
- Manager, Authoring Kit, canonical Kristals, remote services, and C2/C4 publication gates are unchanged.

# Working tree — KNAV My Kristals preview (unreleased, 2026-10-12)

- Opt-in local-only `GET /api/fleet` with per-principal ACL filtering and a bounded experimental Manager-preview JSON consumer (not an official Manager API).
- Svelte My Kristals navigator and separate inventory/detail view with source/readiness/verification distinctions and return to existing Explorer.
- Preserve the existing GitHub v10 checkout adapter, claims, and strict reader checks; no generic v9 concept decoding.
- Legacy Kollection launch mode now requires explicit opt-in; portable Node 24 and an explicit v10 backend config are respected; existing listeners on the configured port are not killed.
- Test coverage for permissions, unknown states, collisions, path safety, and deployment profiles. **Not a qualified release**; full UI build and E2E on Node >=24.15 remain required.

# Changelog

## 2026-10-08 — Patch d’intégration GitHub Kristal v10 sur 1.0 RC

- Adaptateur opt-in `kristal-github-collection-v10` pour les collections synchronisées.
- Vérification des index et manifestes de synchronisation, hashes SHA-256, budgets et arborescences exactes.
- Navigation technique dérivée vers les membres v9 et fichiers hébergés ; aucune nouvelle autorité sémantique.
- Conservation des adaptateurs v6, des Lens et des renderers existants.
- Tests autonomes v10 et documentation d’intégration ; numéro RC inchangé tant que les gates complets ne sont pas qualifiés.

## 2026-10-03 — Sélecteur de Kristals

- ajout du sélecteur `KRISTAL` dans l’interface pour les backends `kristal-kollection-v1` ;
- découverte des domaines lisibles et affichage désactivé des domaines sans état exploitable ;
- sélection isolée par requête via `X-Konstellation-Kristal`, avec cache de runtime par Kristal et rôles ;
- conservation du Kristal dans le navigateur et dans `ExplorationState.kristalRef` ;
- `Konstellation_Launcher.cmd` active automatiquement le mode collection quand `../kristals/domains` existe.

## Kristal-Kollection compatibility — 2026-10-03

- Ajout de `kristal-kollection-v1` pour sélectionner directement un domaine `Kristal-*` dans une collection.
- Profil v6 de compatibilité en lecture pour les variantes de collection (`content_hash.algorithm`, provenance optionnelle, rôles additionnels), avec diagnostics explicites sans promotion en canon.
- Projection des valeurs JSON/boolean/nombre non entier vers une représentation JSON canonique lorsque le registre local ne possède pas de type natif équivalent.
- Gestion déterministe des `assertion_id` upstream dupliqués avec identifiants locaux uniques et `projectionWarnings`.
- Découverte des états dans les dispositions `knowledge-base/corpus/` et `knowledge-base/`.

## 1.0.0-rc.2 — 2026-10-02

- Durcissement final du contrat `navigation-projection` 1.0 : formes internes strictes par famille, liaison `projectionKind`/renderer/recipe, `nextCursor`/`totalCandidates` explicites et fixtures positives/négatives hors-ligne.
- Sanitization des DTOs publics : `actionability`, `lineage`, `valuations` et `coordinates` n’exposent plus les payloads upstream bruts ou champs internes inutiles.
- Correction des producteurs Traceability et StateFlow pour respecter les DTOs stricts.
- Réparation du validateur Python hors-ligne avec registry URN JSON Schema ; 62 contrôles passent sans accès réseau.
- Améliorations accessibilité : Tree avec navigation clavier type ARIA tree, noms accessibles sur SVG interactifs, structure Timeline/Matrix/Traceability corrigée.
- Compatibilité CSP publique renforcée : suppression des `style=`/`style:` Svelte, transformations SVG natives, classes d’indentation déterministes et `build.inlineStylesheets=never`.
- Nouveau gate statique `check:svelte-structure`, intégré au preflight, couvrant structure Svelte, interactions SVG et styles inline interdits.
- Nouveau gate `check:frontend-security` contre raw HTML/dynamic code, styles/scripts inline et imports CSS distants ; headers HTTP de défense en profondeur ajoutés.
- Découplage de `AppError`/`fail()` vers `server/errors.mjs` afin que auth/config soient testables sans charger Ajv ; 5 tests sécurité dependency-free passent.
- Benchmark complet requalifié jusqu’à 1M assertions, tous les scénarios sous baseline.
- Documentation d’implémentation/validation mise à jour avec les résultats réellement exécutés.

## 1.0.0-rc.1 — 2026-10-02

- Implémentation complète de la navigation adaptative 1.0 : profils global/type/result-set/focus, NavigationPlan 1.0 et registre fermé de renderers.
- Ajout des renderers/projections `timeline-lineage`, `tree`, `dag-proof`, `flow-path`, `causal-feedback`, `matrix-profile`, `state-flow`, `traceability`, `multiscale-layer` et `spatial`.
- Alignement Kristal v6 : coordinates, valuations, record_role, actionability, conflits, succession, lineage, evidence/provenance restent des signaux dérivés sans changer l’autorité canonique.
- Reader Policy appliquée à toutes les surfaces secondaires, y compris introspection, recommandations et projections ; indexes d’entités/assertions policy-scoped.
- Auth multi-principal rôles/scopes, profils de déploiement, rate limiting, CSP publique, health/readiness/version, logs JSON et métriques.
- ExplorationState 1.0 avec migration 0.2 ; `navigationHints` 1.0 avec compatibilité legacy.
- Golden corpus 1.0 étendu (24 tests dependency-free), tests sécurité/policy/Lens et benchmark 10k/100k/1M + dense/timeline/DAG profond/multi-échelle/forte cardinalité.
- Contrats de projection 1.0 stricts par famille avec 10 fixtures officielles ; fallback frontend piloté par `accessibilityFallback` du Renderer Registry.
- Renderers spécialisés enrichis avec visualisations natives déterministes (timeline, DAG, flow, feedback, multi-échelle, spatial) et fallback textuel accessible, sans dépendance graphique externe.
- Bootstrap, validation QuerySpec, Lens/facettes et navigation sont désormais policy-scoped jusque dans le schéma exposé, supprimant les oracles type/ID/relation.
- Cache des scopes Reader Policy, préchauffage readiness, détection de cycles itérative et suppression fail-closed des labels/préférences de navigation sous policy.
- Manifest source SHA-256, SBOM CycloneDX, checks de synchronisation et checksums exposables par `/api/version`.
- Runbooks threat model et backup/restore ajoutés aux opérations de production.
- Release gates automatisés (`release:preflight`, `release:check`) et vérification des liens docs.
- Le package reste RC tant que Node 24 + lockfile + build/Vitest/Playwright n’ont pas été qualifiés dans l’environnement de release.

## Documentation 1.0 — 2026-10-02

- Ajout d'une documentation complète native au repo dans `docs/`.
- Réécriture des docs cœur comme spécification normative Konstellation 1.0.
- Ajout Renderer Registry, performance/LOD, sécurité, observabilité, golden corpus, déploiement, API, extension guide et gates de release.
- Ajout ADR-0006 à ADR-0010 et guides utilisateur/intégrateur/développeur/opérateur.
- Clarification permanente de la distinction baseline v0.7 / cible production 1.0.

# v0.7.0 — 2026-10-01

Alignement natif sur Kristal Standard 6.0 : lecteur direct `kristal_state`, vérification d’identité `kristal.v6:jcs-rfc8785`, projection locale explicitement dérivée et pertes déclarées, introspection des `coordinates`, `valuations`, `record_role`, `actionability`, conflits, succession, lineage, évidence et provenance. La terminologie du planner devient **affordances structurelles** pour ne pas confondre ses scores UI avec les capability manifests de runtime. Ajout des recettes États, Évolution, Divergences, Traçabilité et Décisions & action. `actionability` reste strictement distincte d’une autorité d’exécution.

# v0.6.0 — 2026-10-01

Konstellation devient un navigateur adaptatif de Kristals : profil structurel indépendant du domaine, Navigation Planner, recettes Chronologie/Hiérarchie/Dépendances/Parcours/Boucles/Preuves/Positions/Comparer, endpoints `/api/navigation/plan` et `/api/navigation/project`, projection adaptative bornée, interface pilotée par le plan et Astrolabe générique. Ajout de `navigationHints` déclaratifs validés pour permettre aux Kristals de publier leurs affordances sans code UI. Les anciennes vues Liste/Tableau/Constellation et les états v0.2 restent compatibles.

## Correctifs Graphe biblique / recherche — 2026-09-30

- Le pack Théophile + graphe biblique devient le corpus local par défaut du serveur et du lanceur; aucun repli silencieux vers un ancien corpus externe.
- L’Astrolabe recherche explicitement les personnages bibliques et affiche jusqu’à 12 homonymes directs.
- Les homonymes bibliques reçoivent une désambiguïsation lisible; les 12 Joseph sont distingués (fils de Jacob, époux de Marie, d’Arimathie, Barsabbas/Justus, Barnabé, etc.).
- La barre de recherche de la liste cherche maintenant dans tout le catalogue chargé, et pas seulement dans la page courante.
- Les libellés désambiguïsés sont réutilisés dans les listes, l’inspecteur et les sélections.
- Les tests Playwright ciblent le pack enrichi et couvrent la recherche « Joseph ».

## Théophile semantic enrichment — 2026-09-30

- Embedded an enriched Théophile + Biblical Graph pack.
- Added explicit question → position, question → theme and question → author navigation.
- Added author-to-author dialogue projections derived only from existing position relations.
- Added Théophile lenses for authors, questions, positions and themes.
- Added readable constellation labels for the new semantic relations.
- Launcher now prefers the embedded enriched pack and local lenses.

## Biblical Graph v1 — 2026-09-29

- Added `person`, `tradition`, `event`, `group` and `term` graph types.
- Authorship is now modeled through historical, traditional, disputed, pseudepigraphic and attributed relations.
- Added contextual canon relations and biblical/apocryphal work seed.
- Added BibleData importer for all named biblical figures, aliases and person relationships.
- Added Biblical People and Biblical Works lenses.
- Astrolabe now searches aliases and French biblical forms.
- Launcher merges the update onto the local Theophile pack when available and caches the generated pack.
- Added `Update_Biblical_Corpus.cmd` for explicit corpus refresh.


## 0.5.1 — Playwright QA harness

- Ajoute `Test_Konstellation.cmd` avec modes rapide, Astrolabe, complet, UI et rapport.
- Tests E2E du démarrage, des API, du corpus biblique, de l’Astrolabe, de la navigation, de l’inspecteur, des sauvegardes et du responsive.
- Capture automatique des `Failed to fetch`, erreurs console, requêtes échouées et réponses 5xx.
- Rapports HTML avec screenshots, vidéos et traces conservés en cas d’échec.
- Instance de test isolée sur le port 4323, sans perturber le launcher normal sur 4321.

## Astrolabe

- Ajout d’une couche d’orientation sémantique avant le catalogue.
- Recherche tolérante aux accents, traits d’union et petites fautes.
- Caps sémantiques pour des termes non indexés directement (eudiste, Saint-Esprit, parousie, iconoclaste).
- Bouton « Cap au hasard » et navigation depuis un cap vers un QuerySpec Konstellation normal.
- Distinction visible entre correspondance du corpus et piste voisine.

# v0.5.0 — 2026-09-28

Nouvelle vue **Constellation** : navigation sémantique centrée sur une entité, groupes déclaratifs optionnels dans les Lens, projection de qualificatifs et sources sans créer de nouvelles assertions, classement de saillance déterministe et diversifié, budget utilisateur de 3 à 25 satellites, fil d’Ariane restaurable, et rendu lisible des qualificatifs dans l’inspecteur. Le Query Service expose `/api/constellation`; le frontend reste Astro + Svelte + SVG natif, sans bibliothèque de graphe supplémentaire.

# v0.4.1 — 2026-09-28

Intégration SA alignée sur `konstellation-explorer-2`. Konstellation reste strictement semantics-only : aucun hint de planification/lexicalisation n’est injecté dans les `CommunicationRequest`; toute réalisation linguistique reste propriété de SemantiK Architect.

# v0.4.0 — 2026-09-27

Lecture Kristal Parquet/JSON et HTTP complète, contrôles d’intégrité/signatures, ReaderPolicy v5, capacités par relation, adaptateur SA avec couverture vérifiée, panneau de communication et exemple Parquet reproductible. 29 tests serveur et 6 tests DOM.

# Changelog

## 2026-10-08 — Patch d’intégration GitHub Kristal v10 sur 1.0 RC

- Adaptateur opt-in `kristal-github-collection-v10` pour les collections synchronisées.
- Vérification des index et manifestes de synchronisation, hashes SHA-256, budgets et arborescences exactes.
- Navigation technique dérivée vers les membres v9 et fichiers hébergés ; aucune nouvelle autorité sémantique.
- Conservation des adaptateurs v6, des Lens et des renderers existants.
- Tests autonomes v10 et documentation d’intégration ; numéro RC inchangé tant que les gates complets ne sont pas qualifiés.

## 0.2.0 — 2026-09-26

Refonte de conception : arbre de sélection et pivots bornés, politique de lecture épinglée, séparation état visuel/requête, sémantique explicite des absences et exclusions, qualification du lecteur Kristal avant choix RDF, témoins de correspondance, schémas stricts et vecteurs synthétiques. Documentation et plan réécrits. Origine v0.1 préservée dans legacy.

Aucune application ou intégration de production n’est livrée dans cette révision.

## 0.3.0 — 2026-09-26

Application Astro/Svelte et service Node implémentés. Moteur QuerySpec, politiques normalisées, pivots corrélés, compteurs, curseurs signés, cache, témoins, trois vues, inspecteur, historique, sauvegardes/import/export et partage. Pack de démonstration autonome et importeur SES strict. Tests moteur/API/import et composants Svelte, suite Playwright fournie. Runtime Pack natif et SA/GF non qualifiés; limites détaillées dans docs/IMPLEMENTATION.md.
