# EncyKlopedia — Fondation documentaire du futur manager V32

**MISE À JOUR ARCHITECTURALE V32.1 — 16 novembre 2026.** [Synthèse autonome du nouveau plan](PLAN_V321.md). Le [nouveau plan fédéré](docs/09_FEDERATION_KRISTAL/00_DECISIONS_V321.md) corrige le modèle antérieur. [Lire le plan des lots A–E](docs/09_FEDERATION_KRISTAL/07_LOTS_A_E.md). Les 55 fichiers du paquet initial restent présents; de nouveaux chapitres et les points d’entrée ont été adaptés. Documentation uniquement.

**Décision de workflow V32.2 :** [accumulation massive dans EncyK puis intégration différée par lots dans les Kristals](docs/09_FEDERATION_KRISTAL/09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md). Cible architecturale, non admission déjà codée.


**Livraison du 15 novembre 2026 — DOCUMENTATION UNIQUEMENT.** Ce dossier n'est pas un nouveau moteur, un installateur ni un dépôt réorganisé. Il ne contient ni bases SQLite de production, ni XML Wikipédia, ni dump Wikidata, ni modifications de Skope/Kristalizer.

## Ce que nous construisons

Un **manager local unique**, lancé ultérieurement par `EncyKlopedia.pyw` à la racine, orchestrera les index et fonctions existantes : UNESCO, Wikidata, Wikipédia, sélection ChatGPT, **production de propositions sourcées**, suivi des tâches et **lecture fédérée des états Kristal existants**. EncyK ne devient pas un second canon. Les îlots sont créés selon une responsabilité, **pas automatiquement par QID**.

**Décision de cadrage :** le pilote UNESCO `unesco.mt1.10` peut rester archivé et non migré; le V32 est construit pour les 87 autres branches. Les gros index locaux, en revanche, sont préservés et utilisés directement en lecture seule. Les dépôts Skope et Kristalizer sont **hors périmètre de modification**.

## Pour commencer

- Agent IA ou nouveau développeur : lire [AGENTS.md](AGENTS.md), puis [`docs/00_INDEX.md`](docs/00_INDEX.md) et [`docs/00_DEMARRAGE_IA/01_BREVE_LECTURE.md`](docs/00_DEMARRAGE_IA/01_BREVE_LECTURE.md).
- Architecture cible : [`docs/03_ARCHITECTURE_V32/01_VISION_ET_TOPOLOGIE.md`](docs/03_ARCHITECTURE_V32/01_VISION_ET_TOPOLOGIE.md).
- Moteur ChatGPT, priorité majeure : [`docs/04_MOTEUR_CHATGPT/01_MOTEUR_EXISTANT.md`](docs/04_MOTEUR_CHATGPT/01_MOTEUR_EXISTANT.md).
- Localisation du code existant : [`docs/07_INVENTAIRES/inventaire_modules.csv`](docs/07_INVENTAIRES/inventaire_modules.csv) (488 modules) et [`docs/01_ECOSYSTEME/02_MATRICE_REEMPLOI.md`](docs/01_ECOSYSTEME/02_MATRICE_REEMPLOI.md).
- Incertitudes ouvertes : [`docs/06_MIGRATION_ET_VALIDATION/04_INCONNUES_MESURABLES.md`](docs/06_MIGRATION_ET_VALIDATION/04_INCONNUES_MESURABLES.md).

Ce paquet peut ensuite être **copié comme `/docs` du méga-repo**; il ne fait aucun déplacement du code existant. Les noms de chemin utilisés dans les documents désignent les dépôts d'origine et resteront référencés jusqu'au déplacement réel.

## Profondeur de cette livraison

Le dossier `/docs` contient un parcours de lecture IA, l’architecture V32, les interfaces des sources et index, le modèle d’identité des Kristals, la chaîne de découverte, les **deux passes ChatGPT**, les spécifications de prompts et ZIP, les états/transactions, les parcours UX, la migration et les scénarios de validation. Il comprend aussi des atlas générés à partir des sources : **11 ensembles, 488 modules Python et leurs fonctions, 88 branches UNESCO, 117 modules à options CLI, 59 fichiers contenant du DDL SQL**. Ce sont des inventaires des snapshots étudiés, **pas** des scripts à lancer aveuglément.

**Commencer par [l’index complet](docs/00_INDEX.md)**; les agents qui codent une fonction précise peuvent consulter les [recettes de navigation](docs/00_DEMARRAGE_IA/04_RECETTES_DE_CODAGE.md).

### Ce qui manque encore au futur méga-repo

Le launcher racine `EncyKlopedia.pyw`, les modules V32, les adaptations P3916, le registre des propositions/fédération V32 et les tests end-to-end n’ont **pas encore été développés**. Cette livraison n’installe rien et ne modifie pas Skope, Kristalizer ou la production.
