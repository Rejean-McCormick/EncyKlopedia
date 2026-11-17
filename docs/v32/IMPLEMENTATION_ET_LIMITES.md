# État d'implémentation du méga-repo V32.1

> Date du paquet : 16 novembre 2026. **Source ≠ test sur D: ≠ admission Kristal.**

## Inventaire d'actifs réutilisés

- Repo principal historique : sources `tools/unesco_pilot`, GUI/JS/HTML, scripts, tests et docs, avec superposition des correctifs disponibles v31.8→v31.12.
- UNESCO_Kristals : 88 espaces de référence, 4 500 concepts, mappings P3916 : 4 289 uniques, 134 ambigus, 77 sans mapping; contenus dans `ecosystem`.
- LinkedDataHub-UNESCO : RDF/SKOS historique, pas le crosswalk QID à lui seul.
- Wikidata compact Skope **externe** : table `entity_edge(subject_id,property_id,target_id,...)`; P+1 milliard, Q sans offset, sources en lecture seule.
- Wikipédia local **externe** : `wiki_qid.qid` → `wiki_pages.page_id`, lecteur direct XML indexé v21 réutilisé dans la passe 2.
- Anciennes Fabrique, Workbench, médiathèque, diagnostics : sources archivées pour transition et analyse, sans lancement automatique de centres concurrents.

## Modules V32 implémentés

| Chemin | Statut | Frontière |
|---|---|---|
| `config.py` | Codé | Chemins des sources externes et travail privé |
| `sql.py` | Codé | Base V32 SQLite locale indépendante |
| `sources.py` | Codé/testé sur fixtures | Import UNESCO et découverte QID/graph/fallback lexical par curseurs |
| `pipeline.py` | Codé/testé sur fixtures | Deux passes ZIP, validations, postes, idempotence, retours partiels |
| `federation.py` | Codé/testé sur fixtures | Lecture des `canon/state.index.json`, vue dérivée |
| `ui.py` + `EncyKlopedia.pyw` | Codé | Interface Tkinter locale, non testée sur Windows vivant |
| `doctor.py`, `cli.py` | Codé/testé | Diagnostics, orchestration CLI |
| `tools/unesco_pilot` | Historique réutilisé | Moteurs V31 et lecteur de révision, pas réimplémentés |

## Tests réellement effectués ici

- Index des **88 branches** des sources incluses → 4 500 concepts et 4 289 QID candidats.
- Pipeline local synthétique : découverte directe et graphe, 2 passes, ZIP, sources intégrales, import de propositions, réimport idempotent, retour partiel et refus de citation inventée.
- Lecture d'îlots : inventaire sans modifier le `canon` et admission volontairement désactivée.
- Tests ciblés des anciens correctifs v31.8, v31.9 et v31.12 : voir `tests/` et les rapports de test de livraison.

## Limites bloquantes pour « production finale »

1. **Framework / Authoring Kit externes** : dépôts et contrats d'écriture non tous présents. Aucun appel d'admission universel imaginé. Il faut qualifier une écriture sur Education puis Soil, avec état attendu, verrou, reçu, reprise.
2. **Kompiler / fédération épinglée** : lecture d'index canonique et projection dérivée possibles; création d'un état parent publié par Framework non intégrée.
3. **Mesures réelles D:** : les index de 125 Go et Wikidata local ne sont pas contenus dans le ZIP. Plans de requête, temps, capacité de 87 branches et fidélité des révisions doivent être validés sur le poste cible.
4. **Sélection sémantique** : les prompts et corpus sont prêts, mais l'agent ChatGPT et la qualité des décisions ne sont pas simulés par les tests. Les contraintes d'utilisation de ChatGPT restent manuelles.
5. **Graphes de propriétés** : P31/P279/P921/P361 sont des routes configurables; les taux de sélection et faux positifs restent à mesurer selon les familles de concepts. Pas de saturation prétendue.
6. **Reprise distribuée très concurrente** : file SQLite locale testée sans plusieurs processus écrivains simultanés; une qualification sous forte concurrence est encore nécessaire.

Le paquet peut servir de base de développement fonctionnelle. **Il serait incorrect de le qualifier d’encyclopédie finale complète, validée ou publiée** à partir des seules archives fournies.

## Procédure de qualification Windows

1. Décompresser le dépôt dans un nouveau dossier, **sans remplacer le programme v30 vivant**.
2. `python encyk_cli.py doctor`; vérifier que Wikipédia SQL, Wikidata compact, XML et index direct sont visibles.
3. `python encyk_cli.py index-unesco` et `python encyk_cli.py discover --branch unesco.mt1.05 --budget 5000` sur la base V32 propre.
4. Confirmer le total d'articles joignables, les plans de requête indexée et les performances, avant les 87 branches.
5. Produire un petit pack sélection; importer un vrai retour ChatGPT; vérifier les décisions et routes.
6. Produire un pack enrichissement; vérifier les citations et la taille avant d'augmenter à 60 articles / 200k mots.
7. Étudier les dépôts Framework/Kit réels pour une intégration séparée et des tests d'écriture sur copies de workspaces, puis seulement activer l'admission par profil validé.

### Ancienne suite de tests

Les tests historiques comprennent de nombreuses générations d'interface et des ressources qui ne figurent pas dans ce snapshot. Les tests du vieux mode « 880 candidats », par exemple, n'expriment pas les règles `REVIEW_SIZE=4000` des correctifs actuels. Conserver les échecs consignés comme **limitations historiques**; ne pas abaisser le moteur à 880 ni fabriquer les ressources absentes pour rendre les chiffres verts.
