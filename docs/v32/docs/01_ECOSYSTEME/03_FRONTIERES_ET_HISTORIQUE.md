# Historique, conflits de versions et limites des snapshots

## Quatre générations qui se superposent

1. **v11–v23 :** recherches UNESCO privées, Workbench, crosswalk P3916 candidat, revue de preuves, premières identités Kristal. Ces objets sont utiles pour comprendre la provenance mais ne constituent pas une encyclopédie finale.
2. **v25–v28 :** catalogue global concept×page, recherches catégories/liens, packs d'articles complets, décisions UNESCO et cumul Kristal.
3. **v30–v31.x :** station à dix conversations, routage, synthèse approfondie, découvertes étendues, états `DEFERRED`, rappel ontologique et audits.
4. **V32 [CIBLE] :** orienter le système vers **sujets Kristal** d'abord, sélectionner les articles pertinents et enrichir les sujets ensuite.

## Attention aux collisions de noms

`v31.1`, `V311`, `V3111`, `v31.11` et `v31.12` sont employés différemment dans l'historique. Le titre d'un script n'est pas une preuve de son état installé. `Production v30` est la base du serveur de station; ce libellé est demeuré pendant les overlays. La future documentation doit nommer *composant + fonction* en priorité, non numéro historique seul.

## État des sources utilisées ici

- `SmartDump_20261115_173446.zip` est un snapshot **de code et de données de référence**, pas une copie transactionnelle des bases D:.
- Le dépôt `architecture_deep/EncyKlopedia` reconstitué depuis les snapshots inclut certains correctifs dans le corps des moteurs (`DEFERRED`, découvertes, relations). Cela **n'établit pas** leur SHA exacte dans le Windows actuel.
- Les archives Skope fournies permettent de documenter une interface **externe**; aucun changement n'y est fait.
- `UNESCO_Kristals` contient des dossiers `canon/` dans la structure des workspaces, mais les données UNESCO sont marquées `imported_source_snapshot_not_semantically_reviewed` et `not_canon`. Ne pas interpréter le nom de dossier comme une validation sémantique.
- `LinkedDataHub-UNESCO/demo/unesco-thesaurus` est une démonstration comparative RDF/SKOS **plus ancienne (2025)**; privilégier les snapshots UNESCO 2026 pour les prochaines branches.

## Ce qui est déjà prouvé vs ce qui ne l'est pas

**Prouvé dans le code/données fournis :** 88 branches, 4 500 concepts, 4 289 QID uniques *candidats*, `wiki_qid` pour la jointure EN, arêtes `entity_edge`, extraction Wikidata ciblée, extraction Wikipédia par offsets, file ZIP/import de ChatGPT, cumul privé.

**Non prouvé par les snapshots :** disponibilité de chaque QID dans l'index D:, présence d'une page Wikipédia EN pour chaque QID, coût des jointures à l'échelle de toutes les branches, qualité du classement par relation, nombre de Kristals enrichissables, état exact et intégrité des données de production après 19:00, taux de rappel encyclopédique.

## Autorité future

Un seul registre de **paramètres du manager** doit pointer vers des corpus situés sur D:, une branche active et des files de travail V32. Les autres apps peuvent continuer de fonctionner le temps de la migration. Les anciens tableaux de bord ne deviennent pas de nouvelles sources d'état : ils *lisent* l'état propriétaire, jusqu'à archivage.
