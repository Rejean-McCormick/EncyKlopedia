# Intégration — Skope 0.2 → EncyK, Arketype 1.4

## Ce qui a été migré

- Sélection déterministe par branche, profondeur, relation entrante/sortante et convergence ; code original adapté depuis Skope standalone 0.2.
- UI Web locale, API de recherche et de prévisualisation.
- Recette `Skope scope recipe (PROPOSAL)` et fixture JSONL de démonstration.

## Ce qui n'est PAS migré

- `skope/ingest.py`, importeur SQLite et base autonome `entities/edges` : duplicata de l'acquisition et de l'index EncyK.
- L'export JSON brut Skope n'est pas transposé : l'index EncyK est **perdant** et ne contient pas le JSON Wikidata. L'export contient maintenant une **proposition de collecte**, jamais des preuves.
- Skope standalone, ses lanceurs et ses fichiers de dépôt n'ont pas été effacés : c'est un dépôt externe à EncyK.

## Passage vers EncyK

1. Choisir un index global EncyK finalisé (`meta.complete=1`).
2. Construire la recette Skope et vérifier branches et convergences.
3. Exporter le ZIP `skope-encyk-proposal/1.0` et examiner la liste sélectionnée.
4. Comparer l'empreinte source indiquée à l'index actuel. Si une mise à jour du dump/index intervient, refaire la découverte et relire la sélection.
5. Copier les deux fichiers sous `staged/` en retirant ce préfixe, seulement après accord humain explicite.
6. Exécuter `harvest.ps1 -Scope <scope_key> -DiscoveryBackend index` avec le dump correspondant. La configuration fixe exactement les QID sélectionnés comme racines et désactive toute expansion automatique.
7. Valider la source intégrale et le handoff avec les outils EncyK habituels ; ne pas substituer le graphe de prévisualisation aux preuves.

## Arketype

La référence est `arketype.scope-guidance/1.0` (v1.4). Une proposition structurelle n'est pas un scope de collecte ni `state_scope`. Le JSON de guidage accompagne la proposition à titre documentaire uniquement et ne modifie ni Arketype, ni Kristal, ni Authoring Kit. En particulier Skope v0.2 ne met pas en œuvre le contrat de proposition Kristal attribué à une future version 0.3.

## Nettoyage

Aucun fichier préexistant de ce snapshot EncyK 0.12 n'a été déplacé ou supprimé. Le script racine `Nettoyer_Fichiers_Obsoletes.pyw` lit une liste explicite de migrations (actuellement vide), vérifie les empreintes et propose un nettoyage manuel sécurisé. **Il n'accède pas aux dépôts Skope externes.**
