# Prévisualisation Botanique mondiale (Skope v0.13.10)

- Le moteur actuel accepte les profondeurs 0 à 8 et un budget maximal de **10 000 entités**.
- L'interface donne accès à ces huit niveaux, y compris par branche.
- Le profil automatique Botany choisit Embryophyta `Q192154`, P171 (entrant), profondeur 6,
  plafond 10 000, convergence 14,6%, support 8, expansion 0.
- Les changements de ce grand profil ne déclenchent pas des calculs lourds à répétition.
  L'utilisateur déclenche l'exploration avec « Calculer le périmètre ».
- Le Wizard est toujours facultatif ; le simulateur quantifié compare au plus 1 500 entités,
  signalées comme sous-échantillon borné.
- `Troncature : Oui` signifie scope incomplet. `Non` ne prouve PAS l'exhaustivité de Wikidata.
- Une extraction mondiale de toutes les espèces nécessite un pipeline de lots incrémentaux
  avec checkpoints, pagination, résolutions de synonymes et alignement entre sources.
- Skope reste en lecture seule sur l'index, ne touche pas au dump ni au canon Kristal.
