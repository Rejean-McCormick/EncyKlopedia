# Skope — outil interne d’EncyKlopedia (dépôt unique)

**Statut :** Skope n’a plus de dépôt autonome actif. Le code maintenu, la CLI, l’interface et les tests résident uniquement dans `00_system/tools/skope/` du dépôt EncyK.

**Provenance historique :** algorithme de navigation par branches, convergence, interface locale et recette inspirés de Skope standalone v0.2 ; adaptateur SQLite, contrat d'export et pipeline modifiés pour EncyK.

- L'index **global compact EncyK** est la seule base de découverte en production (`30_working/wikidata/wikidata.compact.sqlite`). Ouverture **en lecture seule** et vérification `meta.complete=1`.
- La visualisation des arêtes vient des **agrégats** `entity_edge`. Elle ne représente pas les statements, qualifiers, references ou JSON Wikidata intégraux.
- Les parcours par branche, seuils de convergence, ajouts explicitement approuvés et profondeur supplémentaire restent non canoniques.
- L'export ZIP contient un rapport et **deux fichiers proposés** (registre de QID + configuration Scope Builder `encyklopedia-scope/v3`) en `staged/`. Il n'écrit **jamais** dans les scopes actifs.
- Relecture humaine obligatoire, puis copie manuelle des deux fichiers vers les emplacements correspondants et exécution du pipeline EncyK existant. L'extraction complète revient à EncyK, puis handoff inchangé à Médiathèque (`encyk.source-evidence-handoff/2.0.0`).
- Guide `arketype.scope-guidance/1.0` facultatif : **conception seulement**, jamais injection dans `state_scope`, aucune autorisation de lecture, activation ou publication.

## Démarrer

À partir de la racine EncyK sous Windows : double-cliquer `Lancer_Skope.pyw` (sélection facultative d’un guide Arketype) ou utiliser :

```powershell
python -m skope serve --db 'D:\wikidata\wikidata.compact.sqlite'
```

La commande ci-dessus se lance depuis `00_system/tools/skope`, ou avec `PYTHONPATH=00_system/tools/skope`.
Le service HTTP est local à `127.0.0.1:8767` (pas d'écoute publique).

```powershell
python -m skope preview --db <index-encyk> --recipe fixtures/demo.recipe.json
python -m skope export --db <index-encyk> --recipe <scope-recipe.json> --out <proposal.zip> --scope-key mon-projet --guidance <guide-arketype.json>
```

La recette demo ne concerne que la fixture synthétique, pas un vrai dump. Pour un scope réel, choisir une racine existante dans l'index EncyK complet.

## Limites

- L'index compact omet les statements individuels et peut être incomplet du point de vue du graphe original. Aucun paquet de « preuve source » n'est fabriqué par Skope.
- `max_entities=10 000` maximum dans la recette Skope ; les budgets Scope Builder d'EncyK sont distincts.
- Une base incomplète, une recette tronquée ou un guide Arketype accordant des droits sont rejetés.
- Après extraction, EncyK et Médiathèque restent les seules étapes qualifiées pour les sources. Aucun Kristal v9/v10 n'est construit par cet outil.

Documentation de migration : `docs/MIGRATION_SKOPE_ARKETYPE.md`.

## Déduplication 0.13.1

L'ancienne livraison d'intégration 0.12 ajoutait ses propres modules d'`ingest`,
le stockage SQLite `entities/edges`, des lanceurs indépendants et des nettoyeurs
pour un dépôt autonome. Ces chemins ne font **pas** partie de la version
consolidée. L'index compact `entity/name/entity_edge/meta` d'EncyK est
l'unique index de consultation Skope ; les artefacts bruts restent extraits
par le Scope Builder officiel.

En cas de superposition d'une ancienne archive intégrée, utiliser
`Nettoyer_Fichiers_Obsoletes.pyw` **à la racine EncyK** après sauvegarde.
La liste blanche cible uniquement les copies obsolètes de l'ancien snapshot,
contrôlées par SHA-256, sans accès au dépôt autonome que l’utilisateur
supprime séparément.

Attribution de Skope original : voir `LICENSE` (MIT), maintenu dans le dossier intégré.


## Sélection du Kristal destinataire (0.13.7)

Le lanceur racine `Lancer_Skope.pyw` parcourt `C:\mycode\Kristal\locals` (ou
`KRISTAL_LOCALS_ROOT`) et lit les `kristal.workspace.json` sans les modifier.
Pour `Kristal-Botany`, le guide Arketype 1.4 PRF-03 (`taxonomie-nature`) est
prérempli. Le chemin du guide est dans `config/arketype/`, à l'intérieur du repo.
Le ZIP de proposition contient `review/target-kristal.json` (métadonnées sans
chemin local, ni écriture canonique). Extraction EncyK, revue et construction
Kristal restent des étapes distinctes.
