# Overlay pilote UNESCO / Kristal / Spek / SemantiK / Wordbench

- **Racine de dépôt** : `C:\mycode\Kristal\Kristal_UNESCO_Factory`
- Déposer ce ZIP **dans cette racine**, en conservant `tools/unesco_gf_pilot/`.
- Lancer `tools/unesco_gf_pilot/LANCER_UI.cmd` ou `py -3.12 tools/unesco_gf_pilot/pilot.py`.
- Installer **les 4 overlays** avant de lancer le pilote ; tous les chemins sont préremplis.
- Le compilateur référencé est **`C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe`** (Wordbench), pas un fichier PGF.

## Garanties / limites

Ce script lit le dernier RUN, ses libellés UNESCO et les instances Spek. Il crée dans Téléchargements un **nouveau** dossier de travail et un ZIP. Il appelle Wordbench pour compiler un PGF **candidat**, SemantiK pour rendre la demande en utilisant le vrai moteur GF, puis l'Orchestrator pour vérifier les preuves. Si toutes les étapes passent, il rend une page Wiki **privée** avec le moteur Spek déjà embarqué.

La grammaire candidate est volontairement **minimale** : elle concatène des segments de la source UNESCO dans l'ordre. Elle sert à démontrer GF/PGF réel, **pas** une validation de style/morphologie encyclopédique. Elle ne synthétise ni définition ni fait scientifique. Le pilote existant exige un concept sans définition et les deux champs Spek `claim` et `scope`; sinon, il refuse explicitement. `concept10` est le cas ciblé par défaut, mais n'est pas supposé compatible sans lire le RUN local.

Aucune compilation de 4 500 concepts, aucune modification des RUN, des dépôts, ni des RuntimeSets, aucune promotion ni publication. Les logs et les fichiers source du dossier de résultat peuvent révéler des chemins locaux; vérifier avant de partager.

Pour test statique : `py -3.12 -m unittest discover -s tools/unesco_gf_pilot/tests -v`.
