## Point d'entrée IA actualisé — référence enrichie, 17 novembre 2026

Commencer par [la référence V8/IA](docs/11_REFERENCE_V8_IA/00_INDEX.md), [ses règles d'agent](docs/11_REFERENCE_V8_IA/AGENTS.md) et [la matrice des preuves](docs/11_REFERENCE_V8_IA/13_REGISTRE_DES_PREUVES.md), puis consulter ce guide V32 comme contexte historique et technique. **Le registre V8 neuf comprend 88 branches** ; les anciennes formulations « 87 branches restantes » parlent d'une phase de pilote, pas du système retenu. La distribution autonome V8 doit être vérifiée séparément du snapshot V32.2.

---

# Guide de lecture IA — EncyKlopedia V32

**À LIRE EN PRIORITÉ — V32.1 (16 novembre 2026) :** [décisions fédération](docs/09_FEDERATION_KRISTAL/00_DECISIONS_V321.md), [cinq objets](docs/09_FEDERATION_KRISTAL/01_MODELE_IDENTITES_ET_GRANULARITE.md), [plan A–E](docs/09_FEDERATION_KRISTAL/07_LOTS_A_E.md). Cette révision prévaut sur les anciennes formules « un QID = un Kristal » et « fact_claim V32 est le canon ».


## Ordre utile, non rituel

1. Lire `docs/00_INDEX.md`, le brief, les décisions et le glossaire de `docs/00_DEMARRAGE_IA/`. Utiliser `04_RECETTES_DE_CODAGE.md` pour sa tâche concrète.
2. Pour une tâche précise, consulter le chapitre métier et **les sources existantes citées**, pas les noms de fichiers seuls.
3. Vérifier si la fonction existe déjà dans le catalogue de modules et la matrice de réemploi avant de la réécrire.
4. Travailler sur une tranche verticale visible, livrable et réversible; éviter de coupler d'emblée les 87 branches.
5. Distinguer systématiquement les quatre étiquettes : **[OBSERVÉ CODE]**, **[OBSERVÉ DONNÉES]**, **[CIBLE]**, **[À MESURER]**. Un document cible ne prouve pas que le code est installé.

## Décisions utilisateur à respecter

- Priorité : une encyclopédie **très vaste**, construction rapide, revue approfondie par agents ultérieurs; **pas** un audit de complétude à 100 %.
- Wikidata, ses QID et les liens Wikipédia sont **la première voie de structuration**; l'index lexical/graphique est une voie de rappel complémentaire.
- Deux passes IA explicites : **sélection de pertinence** puis **production intensive de propositions sourcées**. L’admission dans un état Kristal est **une troisième frontière distincte**; un QID n’impose pas un nouveau Kristal.
- Le système de conversations ChatGPT ↔ packs ZIP ↔ retours locaux est un **actif à conserver**, particulièrement la reprise et l'intégration cumulative. Les prompts doivent solliciter un volume substantiel de travail utile, pas s'arrêter après un résumé rapide.
- Aucun APPROVE, fait canonique, publication ni attribution sémantique officielle automatique à partir d'un simple lien Wikidata.
- Ne pas modifier, déplacer ni empaqueter le code source de **Skope ou Kristalizer**. Consommation de leurs outils/interfaces en tant que composants externes uniquement. Ne pas créer de fork interne.
- Archiver *plus tard* les anciens dépôts devenus redondants, après que la fonction correspondante soit dans le manager. Pas de déplacement de données/logiciel à cette étape documentaire.
- **Éviter les freins artificiels** : pas d'obligation universelle de manifestes, de hachages de tous les fichiers, de triple relecture ou de revues humaines pour chaque minuscule opération. Les vérifications légères restent là où elles protègent la provenance d'une connaissance, une reprise ou un import de résultat.

## Règles d'implémentation simples

- Une autorité par catégorie de donnée et par périmètre; EncyK possède propositions/tâches, les îlots leurs états admis. Des adaptateurs en lecture seule pour les gros index.
- Identité par `concept_id`, `QID`, `enwiki:page_id` et révision; jamais uniquement par titre.
- Les relations de graphe produisent des **candidats**, la passe IA produit des décisions puis des **propositions privées sourcées**; une politique et un auteur qualifiés pourront éventuellement les admettre dans un îlot.
- Idempotence par identité logique et statut durable des jobs; reprise sur curseur; petits composants et une interface de pilotage unique.
- Les checkpoints et quelques exemples de citations précises coûtent peu; ne pas en faire des barrières procédurales supplémentaires.
- Les travaux importants sont non atomiques entre corpus; indiquer l'incertitude au lieu de bloquer le pipeline entier.

## Ce que cette livraison ne fait pas

Elle n'exécute pas le refactor, ne teste pas les bases D: en direct et ne crée pas le futur launcher Python. Toute promesse de couverture Wikidata → Wikipédia dans la base locale reste **à mesurer**.
