# EncyKlopedia — Référence enrichie d'écosystème, workflow et instructions IA

**Édition documentaire : 17 novembre 2026 · Overlay additif V8 / noyau V32.2 · Aucune modification de production.**

Ce dossier est le **point d'entrée opérationnel pour un humain ou une IA**. Il complète les chapitres historiques V32 et l'inventaire V7, sans effacer leur provenance. Il ne prétend pas que les fonctions cibles sont déjà implémentées.

> **Précision de vérification.** Le snapshot `znapshot_EncyKlopedia_11172030.zip` contient le dépôt V32.2 et l'inventaire V7, mais **pas l'archive exécutable autonome V8**. Les contrats V32.2 ci-dessous ont été confrontés au code du snapshot. Le fonctionnement V8 est décrit à partir de la livraison antérieure et doit être **requalifié sur le ZIP V8 réellement installé**. Une IA ne doit jamais convertir cette description en preuve d'installation Windows.

## Parcours de lecture

| Besoin | À lire | Ce qui est établi |
|---|---|---|
| Reprendre le projet en 5 minutes | [01_PRISE_EN_MAIN_IA](01_PRISE_EN_MAIN_IA.md) | Mission, règles de lecture, actions défendues |
| Comprendre les projets et responsabilités | [02_ECOSYSTEME](02_ECOSYSTEME.md) | Autorités, interfaces, frontières, historique |
| Comprendre les données et les index | [03_SOURCES_ET_INVENTAIRE](03_SOURCES_ET_INVENTAIRE.md) | UNESCO, Wikidata compact/full, Wikipédia XML/SQL |
| Voir les logiciels et modules disponibles | [04_PROGRAMMES_ET_CAPACITES](04_PROGRAMMES_ET_CAPACITES.md) | Fonctions existantes, historiques, cibles |
| Suivre une campagne de bout en bout | [05_WORKFLOW_DE_BOUT_EN_BOUT](05_WORKFLOW_DE_BOUT_EN_BOUT.md) | Découverte→sélection→enrichissement→cumul privé |
| Piloter les campagnes et les dix postes | [06_CAMPAGNES_V8](06_CAMPAGNES_V8.md) | Hypothèses V8, budgets et arrêts |
| Produire des retours ChatGPT valides | [07_CONTRATS_ZIP_ET_PROMPTS](07_CONTRATS_ZIP_ET_PROMPTS.md) | Noms des fichiers, identifiants, statuts |
| Comprendre identités, base et provenance | [08_MODELE_TECHNIQUE](08_MODELE_TECHNIQUE.md) | Branches, candidats, propositions, états |
| Améliorer sans diluer la qualité | [09_QUALITE_REPRISES_RENDEMENT](09_QUALITE_REPRISES_RENDEMENT.md) | Contrôles, erreurs, PARTIAL et métriques |
| Installer ou diagnostiquer | [10_INSTALLATION_SECURITE](10_INSTALLATION_SECURITE.md) | Chemins, dépendances, sûreté et vérifications |
| Décider la prochaine évolution | [11_ROADMAP_ET_DECISIONS](11_ROADMAP_ET_DECISIONS.md) | Alternatives, priorités, critères d'acceptation |
| Transmettre le projet à une autre IA | [12_PASSATION_IA](12_PASSATION_IA.md) | Message de passation, fichiers requis, checklists |
| Vérifier contradictions/autorités | [13_REGISTRE_DES_PREUVES](13_REGISTRE_DES_PREUVES.md) | Matrice affirmations ↔ sources et lacunes |
| Lire exemples et diagnostics | [14_EXEMPLES_ET_RECETTES](14_EXEMPLES_ET_RECETTES.md) | Missions SEL/ENR, incidents et gestes opérateur |
| Instructions locales pour agents | [AGENTS.md](AGENTS.md) | Contrat opérationnel pour IA travaillant dans ce dossier |

## Continuité avec les documents existants

- [Inventaire massif V7](../10_SYSTEME_MASSIF_20261117/00_INDEX.md) : 15 chapitres et inventaires CSV, **archives inspectées en 2026**, pas une lecture vivante des volumes D:.
- [Architecture V32](../03_ARCHITECTURE_V32/01_VISION_ET_TOPOLOGIE.md) : noyau et principes de stockage.
- [Moteur ChatGPT](../04_MOTEUR_CHATGPT/02_CONTRATS_PACKS_ET_RETOURS.md) : référence historique ; pour les noms de fichiers du retour, le **code installé et le `INSTRUCTIONS_CHATGPT.md` du ZIP** prévalent.
- [Fédération Kristal](../09_FEDERATION_KRISTAL/09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md) : frontière canonique non franchissable automatiquement.
- [Catalogue historique](../07_INVENTAIRES/ATLAS_MODULES.md) : anciens modules, non inventaire de la V8 installée.

## Vérités d'architecture

1. EncyK est **un producteur de propositions encyclopédiques privées**; ce n'est pas une forge de Kristals canoniques.
2. Les 88 branches sont des **espaces thématiques UNESCO**, non 88 articles ni 88 QID ni 88 îlots à créer.
3. Un candidat est une **association branche × concept × page Wikipédia**, et non nécessairement un article unique.
4. Un QID est une **référence externe**, jamais une preuve suffisante de pertinence ou d'admission.
5. Une citation Wikitext **exactement présente** n'est pas automatiquement une preuve que l'assertion est juste ou bien attribuée.
6. La découverte est **progressive et bornée par fenêtres** ; une fenêtre terminée ne signifie pas une branche exhaustive.
7. Les ZIP de mission sont des **instantanés contractuels** : IDs, révisions, textes et hash ne se changent pas pendant leur traitement.
8. `PARTIAL` peut contenir de nombreuses propositions valides. Les reprises doivent cibler les lacunes, pas effacer le passé.
9. Une IA doit agir dans le périmètre du *dossier réellement fourni*, pas réécrire Skope, Kristalizer ou des index mondiaux.
10. Tout statut « opérationnel » doit indiquer sa **version, sa source et son niveau de preuve**.

## Deux générations à ne pas fusionner fictivement

| Noyau V32.2 présent dans snapshot | Station V8 antérieure, non incluse dans ce snapshot |
|---|---|
| `encyk_v32/`, registre SQLite schéma `/2`, API de sélection/enrichissement et import | Copie autonome corrigée du moteur + UX dix postes + campagne progressive V8 décrite auparavant |
| Contrats vérifiés dans `pipeline.py` du ZIP courant | API, chemins et tests réels **à confirmer sur la distribution V8** |
| Documentation V7 déjà installée | Documentation V8 éparpillée dans la livraison antérieure, à rattacher lors du prochain snapshot du code |

En cas de désaccord, **vérifier le code déployé et le pack de mission effectif**. Cette référence enrichie évite de faire passer une aspiration de conception pour une fonctionnalité disponible.
