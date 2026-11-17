# Révision des compositions Wiki — 127 Kristals

**Statut : étude éditoriale, NON publiable.** Les métadonnées de cinq Kristals et leurs états portables v8 ont été inspectés dans l’archive remise. Le canon source n’a pas été qualifié. Les 122 autres restent basés sur les métadonnées du rapport Manager.

## Résultats vérifiables

- 127 propositions conservées ; 5 réétudiées sur un instantané portable v8, 122 sans fichiers canoniques détaillés.
- 2277 occurrences d’assertions parcourues sur les cinq ; classement exhaustif par section, sans doublon de position.
- Les positions d’assertions et quelques identifiants sont enregistrés dans `kristal-structure-reviews.json` : **ce ne sont pas des assertions sélectionnées pour publication**.
- Les SHA-256 correspondent aux octets du ZIP inspecté, **pas à une attestation canonique JCS**.
- Les 8 layouts historiques étaient insuffisants. **Depuis la mise à jour de l'atelier**, 19 layouts supplémentaires disposent de contrats typés et de rendus HTML/PDF/TeX/Markdown à partir d'unités explicites ; **aucune réalisation SemantiK n'a été produite automatiquement** et la validité structurelle des graphes/écritures n'est pas attestée.
- Les assignations de publication sont toujours vides : `kristal-assignments.json`.

## Analyse individualisée

### Kristal-AI

Modèle à sept axes dont les relations transversales et les rétroactions empêchent une présentation strictement linéaire.

Assertions portables v8 : **360** occurrences, **360** identifiants uniques.

| Partie | Occurrences inspectées | Présentation proposée (non implémentée) |
|---|---:|---|
| Données | 60 | `stage-interaction-network` |
| Représentation | 38 | `stage-interaction-network` |
| Modèles | 57 | `taxonomy-tree` |
| Apprentissage | 55 | `process-interface-map` |
| Inférence | 44 | `process-interface-map` |
| Évaluation | 51 | `evidence-constraint-matrix` |
| Propriétés transversales et rétroactions | 55 | `relation-network` |

**Écueils à éviter :** Ne pas transformer les étapes de navigation en pipeline causal strict. Ne pas remplacer les sept dimensions par un parcours pédagogique.

### Kristal-Accounting

Graphe événement → document source → écriture → comptes → période → états; la distinction entre événements, écritures, preuves et agrégation comptable est structurelle.

Assertions portables v8 : **581** occurrences, **580** identifiants uniques.

| Partie | Occurrences inspectées | Présentation proposée (non implémentée) |
|---|---:|---|
| Concepts, catégories et règles | 134 | `taxonomy-tree` |
| Événements et pièces justificatives | 196 | `event-document-chain` |
| Écritures, comptes, débits et crédits | 206 | `double-entry-ledger` |
| Périodes, états et rapprochements | 35 | `period-rollup-matrix` |
| Interfaces et autres faits | 10 | `source-provenance-index` |

**Écueils à éviter :** Une période comptable n’est pas automatiquement une chronologie d’événements datés. Le débit/crédit exige une vue équilibrée et une provenance distincte du journal. Un identifiant d’assertion dupliqué interdit un rattachement unique sans occurrence.

### Kristal-Aerospace

Système de mission comprenant phases, véhicules, environnement, trajectoire et opérations; les phases déclarées ne sont pas des dates.

Assertions portables v8 : **717** occurrences, **717** identifiants uniques.

| Partie | Occurrences inspectées | Présentation proposée (non implémentée) |
|---|---:|---|
| Architecture de mission, phases et opérations | 166 | `mission-phase-map` |
| Véhicules, systèmes et ressources | 241 | `system-interface-map` |
| Trajectoires, environnement et mesures | 220 | `trajectory-constraints-map` |
| Interfaces et frontières du domaine | 79 | `boundary-relation-map` |
| Taxonomies transversales | 11 | `taxonomy-tree` |

**Écueils à éviter :** Ne pas présenter des phases abstraites comme des événements historiques datés. Ne pas assimiler une interface système à une relation de causalité démontrée.

### Kristal-Aging

Modèle multi-échelles distinguant âge chronologique, mécanismes biologiques, fonction, résilience, fragilité et trajectoires de vie.

Assertions portables v8 : **228** occurrences, **228** identifiants uniques.

| Partie | Occurrences inspectées | Présentation proposée (non implémentée) |
|---|---:|---|
| Mécanismes et systèmes | 136 | `multiscale-relations-map` |
| Fonction, réserve et compensation | 49 | `functional-trajectory-map` |
| Mesures et indicateurs | 10 | `evidence-constraint-matrix` |
| Trajectoires observées | 8 | `functional-trajectory-map` |
| Limites, éthique et invariants | 13 | `source-provenance-index` |
| Nuances entre échelles et autres thèmes | 12 | `crossscale-distinctions-map` |

**Écueils à éviter :** Ne pas présenter les thèmes de vieillissement comme une chronologie individuelle. Ne pas assimiler vieillissement, maladie, fragilité et âge chronologique. Les vues comparatives exigent un critère explicite et des formulations complètes.

### Kristal-Agriculture

Graphe agroécologique organisé par sol, organisme cultivé, intrants, pratiques et rendement avec interactions contextuelles non linéaires.

Assertions portables v8 : **391** occurrences, **391** identifiants uniques.

| Partie | Occurrences inspectées | Présentation proposée (non implémentée) |
|---|---:|---|
| Sol | 79 | `agroecosystem-network` |
| Organisme cultivé | 75 | `agroecosystem-network` |
| Intrants | 66 | `inputs-practices-matrix` |
| Pratiques | 91 | `practice-interface-map` |
| Rendement | 62 | `evidence-constraint-matrix` |
| Interfaces transversales | 18 | `relation-network` |

**Écueils à éviter :** La navigation en cinq étapes ne signifie pas causalité linéaire. Ne pas confondre interactions, influences documentées et pratiques prescriptives. Ne pas le traiter comme la même composition que Kristal-AI.

## Optimisation et limites

- **Couverture observée :** 100 % des positions d’assertions v8 rangées dans des catégories de revue, non 100 % des faits éditoriaux garantis.
- **Fidélité :** choix de structures en fonction des axes/namespace réels; validations humaines et vérification de sources encore requises.
- **Articulation :** plan des sections prévu; le moteur Spek ne compile pas les templates marqués `DESIGN_ONLY`.
- **Traçabilité :** empreintes brutes, indices et identifiants d’échantillon fournis. Pas de rendu linguistique SemantiK vérifié.
- **Lisibilité :** concept de hiérarchie document/petites pages prêt à implémenter, non publié.

## Pour compléter les 122 restants

Il faut les états de lecture portables et/ou les graphes structurés. Le rapport Manager seul ne permet pas de contrôler les relations internes. L’exporteur local `scripts/exporter_sources_pour_analyse_ia.py` prépare un manifeste, puis un bundle d’artefacts sur demande explicite, après revue de confidentialité.

## Intégration à Spek

Le registre des 127 reste dans `template_library/wiki/kristal-ai-proposals.json`. Les cinq revues détaillées sont dans `kristal-structure-reviews.json`, et le registre des 19 layouts spécialisés dans `specialized-template-designs.json`. **Aucune règle de choix n’est ajoutée au runtime Spek**.
