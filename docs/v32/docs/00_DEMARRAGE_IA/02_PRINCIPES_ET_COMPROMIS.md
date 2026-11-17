# Décisions durables et compromis de vitesse

**V32.1** : l’encyclopédie à grand débit produit d’abord des propositions dans EncyK. La lecture peut fédérer des états Kristal existants dès le lot A. La **promotion vers un état Kristal** passe par un auteur supporté et une décision versionnée, sans second canon; voir [décision](../09_FEDERATION_KRISTAL/00_DECISIONS_V321.md).


## Résultats privilégiés

1. **Réemploi maximal** du code et surtout des index; consolidation des fonctions dans un manager, sans recopier les outils externes.
2. **Débit utile** : nombreuses connaissances sourcées par lot, efforts IA sur les articles riches; le tri préalable évite de lire des milliers de pages non pertinentes.
3. **Couverture raisonnablement large** : plusieurs voies de rappel sans chercher la preuve impossible d'un index encyclopédique complet en 2026; poursuivre plus tard avec un agent de finition.
4. **Itérabilité** : des décisions/recherches peuvent être reprises sur nouveaux signaux; un HOLD est un dossier à revoir, pas une erreur bloquante.
5. **Economie opérationnelle** : Windows local, un manager, fichiers sur D:, sources volumineuses lues là où elles sont, dix conversations ChatGPT possibles mais non forcées.

## Séparation de responsabilités

- **UNESCO** désigne les concepts et leur hiérarchie; le rattachement d'un sujet à un concept est distinct de l'identité du sujet.
- **Wikidata** apporte identité QID, labels, propriétés et graphe. Sa vérité éditoriale ne se substitue pas à la preuve documentaire.
- **Wikipédia** fournit les articles et les révisions, le matériau principal de l'enrichissement. Un sitelink/QID est une **jointure**, pas une décision de pertinence pour toutes les branches.
- **ChatGPT** rend les décisions de sélection et extrait une grande quantité de faits utiles dans les articles retenus.
- **EncyK V32** conserve les sujets référencés, propositions et décisions provisoires; les **états Kristal propriétaires** conservent les assertions qui leur sont admises. Aucun QID ne devient automatiquement un îlot.
- **Skope/Kristalizer** restent externes, sans modification.

## Gardes légers plutôt que barrières

**Garder** : clés stables (`QID`, `page_id`, `concept_id`), distinction QID direct/voisin de graphe, trace de la révision, une citation ou un passage source pour les faits nouveaux, import idempotent, refus des fichiers ZIP exécutables/inattendus, reprise de lots.

**Ne pas imposer dans V32** : manifeste SHA pour chaque sous-produit, hash obligatoire de tout le dump avant une simple requête indexée, approbation humaine de chaque ligne, scan de complétude Wikipédia avant chaque branche, quota universel de faits, répétition de trois vérifications identiques, migration totale du pilote avant premier résultat.

**Nuance** : l'absence de blocage administratif n'autorise pas les citations inventées, les faux sujets ni les publications automatiques. Une erreur d'extraction peut être corrigée plus tard si l'origine de la phrase et la page restent disponibles.

## Choix de design à favoriser

Modular monolith local (un process orchestrateur/worker Python, SQLite de travail); ports/adaptateurs pour les corpus; file de jobs persistante et idempotence; batch/claim-check par chemins de fichiers et ZIPs; métriques opérationnelles; UX pilotée par tâches. Éviter microservices, bus distribué, event sourcing exhaustif, enchaînements de revues qui n'apportent pas de valeur.
