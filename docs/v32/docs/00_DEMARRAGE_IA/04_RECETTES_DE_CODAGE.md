# Recettes de contribution : ce qu'un agent IA doit ouvrir selon sa tâche

Ce guide permet de travailler sur le futur méga-repo **sans redécouvrir chaque ancien projet**. Avant de coder, lire le document métier et au moins la fonction source citée. Si l'ancien outil possède une règle métier utile, l'intégrer par adaptateur; si c'est un prototype périmé, le noter comme tel.

## « Je dois préparer les 87 prochaines branches »

1. Lire `02_SOURCES_ET_INDEX/02_UNESCO_LDH_88_BRANCHES.md` et `07_INVENTAIRES/BRANCHES_88.md`.
2. Ouvrir `UNESCO_Kristals/branches/*/canon/domain/unesco-source.json` et `*/derived/wikidata-p3916-candidates.json` : statut et identifiants existent déjà.
3. Ouvrir `generer_branches_unesco_v25.py:run` et `catalogue_global_v25.py:load_branch`. Les 88 manifestes ont déjà été acceptés en test sur snapshots, mais P3916 n'est pas automatiquement transporté.
4. Écrire un **lecteur/adaptateur** de registre UNESCO, pas un nouveau parseur RDF complet.
5. Tester QID directs, ambigus, absents sur trois branches; ne pas exiger la résolution de tous les cas.

## « Je dois rejoindre Wikidata à Wikipédia »

1. Lire `02_SOURCES_ET_INDEX/03_WIKIDATA_SKOPE.md` et `02_SOURCES_ET_INDEX/05_WIKIPEDIA_ET_MEDIATHEQUE.md`.
2. Localiser `wiki_qid` et `wiki_pages` dans l'importeur de `mediatheque-references` et `source_by_qid` dans le catalogue v25.
3. Ne pas réextraire les dumps : requêter `wiki_qid` avec `QID` paramétré, vérifier que la page existe et sa langue/source.
4. Enregistrer `no_enwiki_sitelink` ou `index_missing` sans inventer de page. Conserver ces cas pour le rappel lexical.
5. Ne pas modifier le code source Skope; utiliser son API/adaptateur.

## « Je dois créer un Kristal de sujet »

1. Lire `03_ARCHITECTURE_V32/02_MODELE_DOMAINES_ET_KRISTALS.md`.
2. Ne pas appeler la branche `unesco-mt1-10` un sujet : l'espace UNESCO est un périmètre, le Kristal sujet est une entité ou thème stable.
3. Déterminer une identité réutilisable `wd:QID`, sinon provisoire `enwiki:page_id` avec statut explicite.
4. Ajouter liens N:N vers concepts/branches et références sources, dédupliquer les faits à portée logique, préserver les contradictoires.
5. Tester un QID dans deux branches et deux articles : un seul sujet, plusieurs relations.

## « Je dois produire des packs ChatGPT »

1. Lire **en entier** `04_MOTEUR_CHATGPT/01...` à `04_MOTEUR_CHATGPT/07...`.
2. Étudier `poste_chatgpt_v30.py` + `production_kristals_v27.py` avant tout nouveau sérialiseur ZIP : il existe déjà une mécanique éprouvée de 10 lanes, retours, retries et import cumulatif.
3. **Passe 1** : candidats `(concept, sujet/page, preuve de route)`, contexte discriminant, décision pour chacun.
4. **Passe 2** : sujets retenus, textes complets des révisions et déclarations originales pertinentes, consigne d'extraction dense, couverture par source.
5. Adapter taille des packs à la **matière réelle**, sans attente arbitraire et sans découper systématiquement les articles complets en extraits insuffisants.
6. Un retour ZIP incomplet doit pouvoir être réparé; ne pas recréer les jobs anciens.

## « Je dois créer le manager `.pyw` »

1. Lire `05_MANAGER_ET_UX/01_MANAGER_FONCTIONNEL.md`, `02_LAUNCHER_ET_INTERFACE.md`, `05_UX_AUDIT_ET_NAVIGATION.md`.
2. Ouvrir `poste_chatgpt_v30.html/js` et `CENTRE_PILOTAGE_ENCYK_V314.pyw` pour relever les actions réelles avant de dessiner.
3. Créer une **composition root** pour GUI et CLI, stateful services indépendants de Tk et de la station HTML.
4. Les cinq actions normales restent ensemble; technique/maintenance en avancé; aucune opération lourde au démarrage.
5. Tester une mission complète avec redémarrage du manager, cinq ZIP et un retour importé deux fois.

## « Je dois archiver un dépôt »

1. Lire `01_ECOSYSTEME/01_DEPOTS_ROLES.md` et `06_MIGRATION_ET_VALIDATION/03_ARCHIVAGE_ET_REPRISE.md`.
2. Chercher le remplacement dans `01_ECOSYSTEME/02_MATRICE_REEMPLOI.md`.
3. Tester le scénario utilisateur qui utilisait l'outil. Conserver la référence au code ancien et une sortie consultable des données utiles.
4. **Arrêter** si le chemin cible se trouve sous Skope, Kristalizer ou une médiathèque partagée non exclusivement EncyK : ce n'est pas un dépôt à déplacer d'office.
5. Ne pas lancer un travail de documentation/manifest SHA de chaque fichier déplacé par simple réflexe.

## « Je dois vérifier un bug de production »

1. Décrire l'écart **observé** et la preuve attendue, pas une théorie sur la saturation.
2. Lire `08_REFERENCES/01_PREUVES_ET_STATUTS.md` et `08_REFERENCES/05_INCIDENTS_ET_LECONS.md`.
3. Faire une reproduction sur un petit SQLite temporaire. Préférer un correctif de l'item, du curseur ou de l'adaptateur plutôt que reconstruire la base.
4. Vérifier qu'une branche concurrente continue de produire et qu'aucun ancien job n'est modifié.
5. Mettre à jour la documentation du propriétaire V32 quand le module est réel; ne jamais faire passer le comportement souhaité pour un test exécuté sur D:.
