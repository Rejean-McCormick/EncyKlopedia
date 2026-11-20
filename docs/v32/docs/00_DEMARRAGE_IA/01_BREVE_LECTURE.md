## Actualisation de lecture — 17 novembre 2026

**La vision actuelle porte sur 88 branches UNESCO neuves**, et non « les 87 branches restantes » du pilote. L'archive de code présente dans le snapshot est V32.2 ; la V8 autonome a été livrée séparément. Commencer par [la passation officielle IA](../11_REFERENCE_V8_IA/12_PASSATION_IA.md), [l'écosystème](../11_REFERENCE_V8_IA/02_ECOSYSTEME.md) et [le workflow](../11_REFERENCE_V8_IA/05_WORKFLOW_DE_BOUT_EN_BOUT.md). L'architecture historique ci-dessous est conservée pour ses sources et compromis, pas comme preuve que toutes les fonctions ciblées sont opérationnelles.

---

# Brief opérationnel pour agent IA entrant

**Lire la décision V32.1** : [fédération et admission](../09_FEDERATION_KRISTAL/00_DECISIONS_V321.md). Le schéma initial plus bas décrit encore le pipeline de découverte mais sa dernière étape se termine désormais par des **propositions EncyK**. Les écritures dans les états Kristal requièrent un chemin d’auteur distinct et qualifié.


## Intention utilisateur

Construire une encyclopédie privée **titanesque** à partir de sources locales déjà indexées, pour les 87 branches UNESCO restantes, avec **beaucoup de connaissances utiles par vague ChatGPT**. La finition éditoriale exhaustive sera ultérieure. La réussite ne se mesure ni à « 10/10 postes remplis » ni à une preuve impossible de 100 % de rappel Wikipédia, mais à la **production de sujets bien alignés et densément enrichis par unité de travail**.

## Ce qui existe déjà

[OBSERVÉ DONNÉES] `UNESCO_Kristals/branches/` : 88 workspaces, 4 500 concepts distincts, 4 289 `SINGLE_P3916_CANDIDATE`, 134 `REVIEW_AMBIGUOUS_P3916`, 77 `NO_P3916_MAPPING` dans les fichiers fournis. Les 88 snapshots présentent `source_scheme_modified: 2026-08-31`.

[OBSERVÉ CODE] `catalogue_global_v25.py` sait joindre les QID au Wikipedia anglais via `wiki_qid JOIN wiki_pages`; `mediatheque-references/.../import_dumps.py` construit ces tables. `Skope/skope/db.py` lit un index Wikidata `entity_edge` en entrée/sortie et `Skope/skope/extraction.py` sait extraire les déclarations complètes. `production_kristals_v27.py` construit les packs de wikitext intégral et cumule les retours structurés. `poste_chatgpt_v30.py` pilote dix conversations humaines, l'import et les reprises.

[À MESURER] Nombre réel de QID UNESCO possédant une page `enwiki` dans l'index **installé sur D:**; politique de traversée graphes selon type de concept; performance de requêtes P31/P279 par branche; qualité de rappel des candidats sélectionnés.

## Architecture cible en une minute

```
88 branches UNESCO ── concepts + SKOS + P3916 candidats
                 │
          index d'alignements commun
                 │
Skope (EXTERNE) ── Wikidata QID + arêtes typées
                 │
Wikipedia index ── wiki_qid ── enwiki:page_id
                 │
         candidats avec ROUTES de preuve
                 │
       PASSE 1 : ChatGPT SELECT / REJECT / HOLD
                 │
          sujets retenus (N:N concept/branche)
                 │
       PASSE 2 : Wikidata complet + Wikipédia intégral
                 │
       propositions privées sourcées EncyK
                 │
          manager et lecture fédérée
                 │
  admission Kit distincte (après qualification)
```

## Trois pièges majeurs

1. **Ne pas réindexer** les dump Wikidata/Wikipédia (les index déjà construits sont l'investissement). Requêtes indexées, lecture seule, caches de travail séparés.
2. **Ne pas recopier Skope ni Kristalizer**. Ce sont des producteurs/consommateurs externes ; EncyK V32 définit des ports adaptés, sans modifier leurs dépôts.
3. **Ne pas sur-gouverner la construction**. L'intégrité minimale des IDs/révisions/citations protège le résultat; les cérémonies de validation, manifestes globaux obligatoires et triple lecture ralentiraient inutilement les 87 branches.

## Parcours utilisateur cible

Ouvrir `EncyKlopedia.pyw` → sélectionner une branche → constater les candidats et les sources → préparer/transmettre les packs **sélection** → importer les décisions → préparer/transmettre les packs **enrichissement** → importer les faits et voir les Kristals → poursuivre la branche suivante. Les écrans de diagnostics/gestion avancée restent accessibles, pas au cœur du parcours.
