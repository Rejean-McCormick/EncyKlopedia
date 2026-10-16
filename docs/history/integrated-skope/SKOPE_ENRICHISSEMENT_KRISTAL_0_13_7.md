# Enrichir un Kristal depuis EncyK — 0.13.7

1. Dépôt C: : ouvrir `Lancer_Skope.pyw`.
2. Choisir `Kristal-Botany` ou un autre Kristal (manifest `kristal.workspace.json`).
3. L'index Wikidata sur D: est déjà proposé. Pour Botany, le guide
   `config/arketype/botany.scope-guidance.json` (PRF-03) est renseigné.
4. `Ouvrir Skope`, rechercher *Embryophyta*, confirmer le QID, calculer puis exporter.
5. Le ZIP téléchargé contient la proposition EncyK et la cible déclarée ;
   il ne contient pas le JSON source original ni ne modifie le canon Kristal.
6. Dans le lanceur, choisir `tools/kristal.py` du Kit 3.3.1, puis **Vérifier le Kristal**
   ou **Générer Discovery** (ce dernier bouton modifie uniquement les données dérivées
   après confirmation). La classification proposée n'est pas déclarée automatiquement.

**Limites** : absence d'ingestion canonique automatique ; la chaîne
EncyK → extraction complète → admission → adaptation → Authoring Kit doit
être qualifiée séparément. Aucun dump/index de D: n'est écrit par Skope.
