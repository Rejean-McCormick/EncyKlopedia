## Démarrage documentaire officiel — édition enrichie du 17 novembre 2026

**Pour une nouvelle IA ou pour comprendre le système actuel :** [guide opérationnel V8/IA](11_REFERENCE_V8_IA/00_INDEX.md) ; [workflow de bout en bout](11_REFERENCE_V8_IA/05_WORKFLOW_DE_BOUT_EN_BOUT.md) ; [contrats de mission SEL/ENR](11_REFERENCE_V8_IA/07_CONTRATS_ZIP_ET_PROMPTS.md) ; [écosystème et responsabilités](11_REFERENCE_V8_IA/02_ECOSYSTEME.md) ; [inventaire massif V7](10_SYSTEME_MASSIF_20261117/00_INDEX.md).

Les paragraphes historiques ci-dessous décrivent **l'architecture documentaire V32.1/V32.2** et restent consultables. La V8 autonome est une distribution distincte, à vérifier sur son ZIP réel.

---

# Index de la documentation avancée

**Révision V32.1 :** commencer par [l’arbitrage fédération](09_FEDERATION_KRISTAL/00_DECISIONS_V321.md), [le modèle des cinq objets](09_FEDERATION_KRISTAL/01_MODELE_IDENTITES_ET_GRANULARITE.md), [la construction en deux passes](09_FEDERATION_KRISTAL/03_PIPELINE_IA_PROPOSITIONS.md) et [le plan A–E](09_FEDERATION_KRISTAL/07_LOTS_A_E.md). La documentation du 15 novembre est conservée comme inventaire et source de réemploi; les règles V32.1 priment lorsqu’elles diffèrent.

**Décision prioritaire V32.2 :** [workflow de cumul privé et d’intégration différée](09_FEDERATION_KRISTAL/09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md) — séparation stricte production ChatGPT / préparation des lots / auteur Kristal.


**Statut du paquet : architecture de transition V32, documentation fondée sur les snapshots fournis.** Le système actuel v25/v27/v28/v30/v31.x et les 88 dossiers UNESCO sont décrits comme observés; le futur manager et les modèles V32 sont des propositions à implémenter.

## Parcours de lecture

| Besoin | Commencer ici | Approfondir |
|---|---|---|
| Comprendre le but en 3 minutes | [Brief IA](00_DEMARRAGE_IA/01_BREVE_LECTURE.md) | [Décisions](00_DEMARRAGE_IA/02_PRINCIPES_ET_COMPROMIS.md) et [recettes agent](00_DEMARRAGE_IA/04_RECETTES_DE_CODAGE.md) |
| Trouver un module existant | [Carte des dépôts](01_ECOSYSTEME/01_DEPOTS_ROLES.md) | [Matrice de réemploi](01_ECOSYSTEME/02_MATRICE_REEMPLOI.md), [atlas des 488 modules](07_INVENTAIRES/ATLAS_MODULES.md) et [117 interfaces CLI repérées](07_INVENTAIRES/ATLAS_CLI.md) |
| Savoir où vivent les données | [Sources et index](02_SOURCES_ET_INDEX/01_CHAINE_UNESCO_WIKIDATA_WIKIPEDIA.md) | [Chemins et bases](02_SOURCES_ET_INDEX/04_CHEMINS_ET_SQLITE.md) |
| Coder le noyau V32 | [Topologie](03_ARCHITECTURE_V32/01_VISION_ET_TOPOLOGIE.md) | [Modèle](03_ARCHITECTURE_V32/02_MODELE_DOMAINES_ET_KRISTALS.md), [ports](03_ARCHITECTURE_V32/03_PORTS_ET_ADAPTATEURS.md) |
| Reprendre le moteur de production | [Moteur actuel](04_MOTEUR_CHATGPT/01_MOTEUR_EXISTANT.md) | [Passe 1](04_MOTEUR_CHATGPT/03_PASSE_1_SELECTION.md), [Passe 2](04_MOTEUR_CHATGPT/04_PASSE_2_ENRICHISSEMENT.md) |
| Concevoir launcher et UI | [Manager](05_MANAGER_ET_UX/01_MANAGER_FONCTIONNEL.md) | [Pyw](05_MANAGER_ET_UX/02_LAUNCHER_ET_INTERFACE.md) |
| Préparer le déplacement de code | [Plan de migration](06_MIGRATION_ET_VALIDATION/01_PLAN_DE_CONSOLIDATION.md) | [Compatibilité](06_MIGRATION_ET_VALIDATION/02_TESTS_ET_SCENARIOS.md) |
| Distinguer acquis et hypothèses | [Registre des preuves](08_REFERENCES/01_PREUVES_ET_STATUTS.md) | [Inconnues](06_MIGRATION_ET_VALIDATION/04_INCONNUES_MESURABLES.md) et [sources étudiées](08_REFERENCES/06_LISTE_DES_SNAPSHOTS.md) |

## Table des domaines

- [`00_DEMARRAGE_IA/`](00_DEMARRAGE_IA/) : orientation, compromis, glossaire IA, comment utiliser la documentation.
- [`01_ECOSYSTEME/`](01_ECOSYSTEME/) : cartographie des repos/apps, propriétaires, réemploi, historiques et frontières.
- [`02_SOURCES_ET_INDEX/`](02_SOURCES_ET_INDEX/) : UNESCO/LinkedDataHub, Wikidata/Skope, Wikipédia et index locaux, SQLite, chemins, provenance.
- [`03_ARCHITECTURE_V32/`](03_ARCHITECTURE_V32/) : architecture finale, modèle de sujet/Kristal, ports, graphes, stratégies de branche, stockage et performances.
- [`04_MOTEUR_CHATGPT/`](04_MOTEUR_CHATGPT/) : fonctionnement prouvé du moteur historique, deux passes, spécifications de prompts, lots, reprises et import.
- [`05_MANAGER_ET_UX/`](05_MANAGER_ET_UX/) : manager unique, launcher `.pyw`, parcours utilisateur, opérations, affichage des états.
- [`06_MIGRATION_ET_VALIDATION/`](06_MIGRATION_ET_VALIDATION/) : stratégie de consolidation, scénarios minimaux, archivage, questions ouvertes.
- [`07_INVENTAIRES/`](07_INVENTAIRES/) : CSV machines des 11 dépôts, 488 modules et 88 branches + tables SQL déclarées dans le code.
- [`08_REFERENCES/`](08_REFERENCES/) : sources précises, statut des observations, codex et [rapport utilisateur du 16 novembre](08_REFERENCES/07_RAPPORT_DECISION_20261116.md).
- [`09_FEDERATION_KRISTAL/`](09_FEDERATION_KRISTAL/) : **architecture V32.1 prioritaire**, autorités, modèle îlots/états/sujets, admission, reprise, Kompiler et plan A–E.

## Convention de lecture

- `[OBSERVÉ CODE]` : fichier/fonction vérifié dans un snapshot nommé.
- `[OBSERVÉ DONNÉES]` : objet ou chiffre présent dans les données de snapshots ou dans le rapport transmis.
- `[CIBLE]` : décision de conception V32, **pas** une fonctionnalité déployée.
- `[À MESURER]` : dépend de l'environnement Windows vivant, de la fraîcheur de l'index, d'une mesure de performance ou d'une validation documentaire.
- `[HISTORIQUE]` : ancienne fonctionnalité ou procédure conservée comme source de réemploi, pas comme mode opératoire recommandé.

### Interdiction de confusion

Le mot « Kristal » est aujourd'hui utilisé pour **un espace UNESCO de branche** et pour **une structure de connaissances**. V32.1 distingue **espace de branche**, **sujet**, **îlot Kristal**, **état**, **assertion/proposition**; un QID ne crée aucun îlot par défaut. Le nombre 88 ne signifie pas 88 sujets, et 4 500 concepts UNESCO ne signifient pas 4 500 articles encyclopédiques déjà écrits.

## Cartographie exhaustive pour les agents IA

- [Liste des 11 ensembles sources](07_INVENTAIRES/DEPOTS_INVENTAIRE.md), incluant leurs rôles, tailles et décomptes.
- [Atlas de tous les modules Python inventoriés](07_INVENTAIRES/ATLAS_MODULES.md) et [CSV des fonctions, classes, CLI et appels](07_INVENTAIRES/inventaire_modules.csv).
- [Atlas des entrées CLI](07_INVENTAIRES/ATLAS_CLI.md) repérées dans 117 modules (indices, non commandes garanties).
- [Liste intégrale des 88 branches](07_INVENTAIRES/BRANCHES_88.md) et [CSV machine](07_INVENTAIRES/unesco_88_branches.csv).
- [Atlas des schémas SQL statiques](07_INVENTAIRES/ATLAS_SCHEMAS_SQL.md) : 59 sources avec DDL repéré, et [JSON machine](07_INVENTAIRES/schémas_sql_statiques.json).
- [Cartographie des sources et fonctions](08_REFERENCES/03_CARTE_SOURCES_ET_FONCTIONS.md), [application des deux codex](08_REFERENCES/02_CODEX_ARCHITECTURE_ET_UX.md).
- [Leçons concrètes des incidents V31](08_REFERENCES/05_INCIDENTS_ET_LECONS.md), [moteur ChatGPT et prompts V32](04_MOTEUR_CHATGPT/05_PROMPTS_TEMPLATES.md).
- [Plan de consolidation et d'archivage](06_MIGRATION_ET_VALIDATION/01_PLAN_DE_CONSOLIDATION.md), [tests de flux](06_MIGRATION_ET_VALIDATION/02_TESTS_ET_SCENARIOS.md), [risques](06_MIGRATION_ET_VALIDATION/05_RISQUES_ET_DECISIONS.md).

**Convention impérative :** les inventaires décrivent les archives remises, pas l’état actualisé de `D:`. Le code cible V32 n’est pas inclus dans cette livraison documentaire.
