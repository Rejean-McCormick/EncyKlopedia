# Kristal UNESCO Factory v1.3 — correction automatique de l'environnement Python

**Incident corrigé :** une ouverture directe de `Fabrique_UNESCO.pyw` via l'association Windows pouvait lancer le `pythonw.exe` global, alors que `rdflib` avait été installé dans `C:\mycode\Kristal\.venv-unesco`. Le premier sous-processus échouait avec `ModuleNotFoundError: No module named 'rdflib'`.

## Correctif intégré

- Le démarrage de la fenêtre GUI appelle désormais `runtime_bootstrap.py` **avant** le pipeline.
- Recherche prioritaire de `.venv-unesco` au niveau du répertoire Kristal; vérifie `rdflib` et `tkinter`.
- Si cette venv n'est pas utilisable, cherche la venv privée de l'application; si aucune n'est prête, elle est créée et `rdflib` y est installé automatiquement. **Aucun pip dans le Python système.**
- Si Windows a ouvert le `.pyw` avec un mauvais `pythonw.exe`, la GUI est relancée automatiquement avec le bon environnement.
- Les subprocess (inventaire RDF, jointure, Kit, Spek) utilisent **python.exe de ce même environnement**, même lorsque la GUI utilise `pythonw.exe` pour ne pas afficher de console. Sous Windows, fenêtres de console cachées pour les sous-processus.
- Journal d'amorçage : `BOOTSTRAP_RUNTIME.log`, aussi accessible dans la liste des artefacts de la GUI (double-clic pour ouvrir; bouton de copie du contenu).
- Les runs existants ne sont jamais écrasés et les données UNESCO/SQLite ne sont jamais modifiées.

## Installation

Décompresser ce ZIP à `C:\mycode\Kristal\` en autorisant le remplacement des fichiers `Kristal_UNESCO_Factory\*`. Fermer l'ancienne fenêtre, puis double-cliquer `LANCER_FABRIQUE.cmd` ou directement `Fabrique_UNESCO.pyw`. L'environnement Python est vérifié dans les deux cas. Cliquer `TOUT CONSTRUIRE + VALIDER`.

Les fichiers `vendor/kit` et `vendor/spek` de la v1.2 sont conservés, ainsi que les fonctionnalités et limites de l'audit P3916. La v1.3 corrige **l'exécution**, pas encore l'importation des assertions Wikidata complètes ni la qualification GF.

## Validation de développement

- Python : syntaxe de tous les modules modifiés compilée.
- 2 tests d'intégration : Kristal v9 natif et compilation/validation Spek, plus ambiguïtés P3916.
- 4 tests d'amorçage : runtime valide, `pythonw.exe` vers `python.exe`, redémarrage sous le bon interpréteur et absence de relance en boucle.
- Tests réalisés sous Linux pour la logique d'amorçage et le pipeline; **la relance de GUI sur Windows doit être confirmée sur la machine cible**.
