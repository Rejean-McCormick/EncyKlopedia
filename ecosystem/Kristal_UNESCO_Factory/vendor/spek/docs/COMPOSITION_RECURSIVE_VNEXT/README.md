# Spek vNext — Composition récursive et templates rhétoriques

**Statut : architecture vNext partiellement implémentée (aperçus privés et tests).**  
**Mise à jour : 2026-11-03.**  
**Périmètre :** architecture des templates documentaires, rhétoriques et visuels ; intégration SemantiK ; rendu ; validation ; migration.  
**Le moteur de composition et les templates rhétoriques sont ajoutés au code. Les registres des 127 propositions et les autorisations de publication sont inchangés.**

## Décision de produit

Une **seule grammaire de templates composables** organise la totalité d'un document. Un template peut :

- accueillir des **sous-templates** de toute famille compatible ;
- répéter un sous-template un nombre **explicitement prescrit** de fois ou pour une collection d'éléments **explicitement fournie** ;
- contenir des **feuilles linguistiques** dont Spek prescrit la fonction et la place ;
- prescrire un **rendu rhétorique** : fusion visuelle de plusieurs petites réalisations, promotion d'une phrase-thèse en élément principal, suppressions de titres décoratifs, disposition comparative, etc. ;
- être utilisé à l'intérieur d'un template Wiki, scientifique, éducatif, de rapport ou de livre.

La catégorie `rhetorical/` est une **catégorie de templates**, et non un moteur linguistique parallèle ni un système d'inférence. SemantiK Architect réalise les **petites unités linguistiques** à partir d'obligations sélectionnées en amont ; Spek les agence **sans réécriture artistique**.

> Formule courte : **IA choisit la composition pour chaque Kristal → Manager approuve les contenus → Spek déroule le graphe de templates et commande les formes → SemantiK réalise les unités → Spek rend le document → publication contrôlée séparément.**

## Base historique préservée et nouvelle extension

- Des layouts typés `kristal.editorial-layout/0.1`, avec `slots`, `allowed_kinds`, `min`, `max` (`layouts/*.json`).
- Un article plat `kristal.layout-article-source/0.1` : `sections[]` pointant vers un layout et des unités.
- La couche `spek/slot_dialogue.py` produisant `spek.slot-dialogue/1.0` et ajustant certaines contraintes des requêtes SemantiK sans en modifier graphes ni obligations.
- Les compositions IA du registre Wiki et les propositions pour 127 Kristals, **non équivalentes à des assignations approuvées**.
- Des adaptations de rendu pour les 27 layouts historiques, **et maintenant** un interpréteur récursif distinct pour HTML/Markdown privés.

**La partie exécutable** utilise `spek.template-graph/1.0` et `spek.composition-instance/1.0` ; voir les commandes dans [11](11_ETAT_DU_CODE_LIVRE.md). Les phases de qualification et publication restent à réaliser.

## Parcours de lecture

| Document | Sujet |
| --- | --- |
| [01 — Frontières et invariants](01_VISION_ET_FRONTIERES.md) | Qui décide quoi, standardisation, prohibitions |
| [02 — Modèle composable](02_MODELE_COMPOSABLE.md) | Définition, instanciation, sous-arbres, répétitions et validation |
| [03 — Templates rhétoriques](03_CATALOGUE_RHETORIQUE.md) | Familles proposées, composition à plusieurs échelles |
| [04 — Dialogue SemantiK](04_DIALOGUE_SEMANTIK.md) | Contrat d'unités linguistiques, contraintes et compatibilité réelle |
| [05 — Rendu](05_RENDU_ET_ACCESSIBILITE.md) | Titres logiques vs hiérarchie visuelle, typographie, HTML/PDF/Wiki |
| [06 — Sécurité et preuve](06_SECURITE_ET_VALIDATION.md) | Refus déterministe, audit, fuite d'informations, publication |
| [07 — Patterns retenus](07_PATTERNS_RETENUS.md) | Adaptation critique du ZIP *senior-architecture-patterns* |
| [08 — Migration et livraison](08_MIGRATION_ET_PLAN.md) | Étapes sans rupture du moteur actuel |
| [09 — Exemples commentés](09_EXEMPLES.md) | Argument ×3, comparaison en prose, imbrication |
| [10 — Critères d'acceptation](10_TESTS_ACCEPTATION.md) | Tests fonctionnels, sécurité, compatibilité, documents |
| [ADR — Décision](ADR-0001-COMPOSITION_UNIFIEE.md) | Décision enregistrée et alternatives rejetées |
| [11 — État du code](11_ETAT_DU_CODE_LIVRE.md) | API, CLI, contrats pris en charge et limites restantes |
| [Exemples JSON exécutables](exemples/) | Instances explicites pour tests privés ; les phrases de démonstration sont fictives |

## Démarcation indispensable

Le dépôt *senior-architecture-patterns* est une **source d'inspiration pour l'architecture logicielle**. Ses modèles (hexagonal, ACL, monolithe modulaire, idempotence, etc.) ne sont **pas des templates rhétoriques** et ne constituent pas des règles éditoriales. Voir [07](07_PATTERNS_RETENUS.md).

## Références locales examinées

- `../DIALOGUE_SPEK_SEMANTIK_SLOTS_2026-11-02_FR.md`
- `../LAYOUT_DESIGN.md`, `../CONTRACTS.md`, `../SECURITY_MODEL.md`
- `../REVUE_EDITORIALE_127_SOURCE_FIDELITY.md`
- `spek/core.py`, `spek/slot_dialogue.py`, `spek/render.py`, `spek/wiki.py`
- Snapshot SemantiK Architect : `docs/04_COMMUNICATION_SEMANTICS_LOCK.md`, `docs/05_LANGUAGE_PLANNING_LOCK.md`, `docs/10_PORTS_ADAPTERS_LOCK.md`

## Implémentation disponible

Le moteur récursif vNext, les dix templates rhétoriques, le plan de dialogue et les aperçus privés HTML/Markdown sont maintenant codés. **Cela ne remplace ni SemantiK GF/PGF ni le pipeline de publication.** Voir [11 — État réel du code livré](11_ETAT_DU_CODE_LIVRE.md).


- [12 — Inventaire scientifique de la rhétorique](12_INVENTAIRE_SCIENTIFIQUE_RHETORIQUE.md) — modèles fondés sur la RST, le PDTB, Toulmin, Walton, CARS et DITA, et déclarations éditoriales requises.

- [Catalogue visuel des 62 templates](CATALOGUE_RHETORIQUE.html) — recherche locale par famille et relation, avec les précautions de chaque adaptation.

- [14 — Grammaire du discours](14_GRAMMAIRE_DU_DISCOURS.md) — 62 modèles avec mouvements, liens, groupes de paragraphes, contraintes de cohésion, CLI d’audit.
- [15 — Sources réelles et SemantiK](15_SOURCES_REELLES_ET_LIMITES_SEMANTIK.md) — contrôle d’un ancrage Agriculture et limites d’exécution GF/PGF.
