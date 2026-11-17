# Manager unique V32 — responsabilité, parcours principal et frontières

**V32.1 — manager fédéré :** le manager inventorie et lit les îlots existants; il **n’en devient pas le propriétaire**, sauf des propositions, tâches et vues EncyK. Il pilote la collecte à haut débit même quand l’admission Kit n’est pas encore activée. Voir [autorités](../09_FEDERATION_KRISTAL/02_AUTORITES_FEDERATION_ET_LECTURE.md).


**[CIBLE]** Le manager n'est pas un orchestrateur de microservices : c'est l'application de travail locale qui coordonne les opérations de construction de l'encyclopédie et rend leur état lisible. Une fenêtre, un moteur de jobs, des adaptateurs vers les index existants. Les autres dépôts pourront être archivés par étapes, sauf Skope et Kristalizer, **externes et intouchables**.

## Une phrase de besoin (guide UX)

« Choisir des branches UNESCO, récupérer des sujets déjà reliés par Wikidata et Wikipédia, faire sélectionner puis enrichir ces sujets via dix conversations ChatGPT, importer les réponses, constater le gain réel et reprendre. »

## Les cinq actions normales — visibles ensemble

1. **Choisir le périmètre** : branches (une, plusieurs ou ensemble), état de préparation, compte de concepts, disponibilité des index, mode découverte ou consolidation.
2. **Préparer la prochaine vague** : exécuter les *étapes manquantes* : alignements, candidats par jointures, paquets de sélection, paquets d'enrichissement. Montrer combien de travail est disponible **avant de lancer**, sans importer ni recalculer silencieusement les index gigantesques.
3. **Travailler sur les 10 postes** : un poste affiche son rôle (sélection/enrichissement), son ID de job, son nombre réel d'items, ses fichiers ZIP, son prompt copiable et l'action suivante.
4. **Importer les retours** : dépôt groupé de ZIP, détection du job, contrôle léger des champs essentiels, résultats détaillés (items intégrés, reportés, à réparer), poste renouvelé si le travail existe.
5. **Consulter les résultats** : nouveaux sujets, Kristals enrichis, faits ajoutés et sourcés, branches ayant progressé, alertes **actionnables**; reprendre ensuite.

Ne pas disperser cette séquence en « poste », « file », « outils », « construction », « import » et « accueil » concurrents. La vue de travail peut afficher plusieurs sections en défilement naturel, mais un seul bouton principal par intention.

## Intention distincte : consulter l'encyclopédie

Le lecteur public expérimental (`src/server.mjs`, `src/catalog.mjs`) ne doit pas voler l'espace de travail de production. Le manager peut fournir une action secondaire « Voir un Kristal » ouvrant une lecture privée locale. Le module de **publication officielle** n'est pas implicitement activé par l'enrichissement et n'entre pas dans la refonte du cœur de production.

## Responsabilités et non-responsabilités

| Propriété | Manager | Reste ailleurs |
|---|---|---|
| État des jobs, lanes, imports, reprises | **Autorité unique** | Aucun deuxième scheduler concurrent |
| Enregistrement concepts/QID/sujets candidats | V32 local | Sources UNESCO restent dans leurs snapshots |
| Accès à l'index Wikipédia, XML | Adaptateur lecture seule | Importeur et fichiers SQL/XML existants |
| Graphe et extraction Wikidata | Port/adaptateur | **Skope externe**, non modifié |
| Kristalizer | Port/adaptateur éventuel, seulement contrat observé | **Kristalizer externe**, non modifié |
| Registre privé de propositions V32 | Manager et moteur de construction | Aucun second canon indépendant; admission par Kit qualifié uniquement |
| Backups, diagnostics, stats | Actions avancées intégrées | SQL/dumps sources inchangés |
| Workflow humain de ChatGPT | Instructions + ZIP + import | Le manager n'envoie pas les fichiers dans dix chats à ta place |

## Structure logique du manager

- `workspace`: profil local (chemins et disponibilités) ; aucun des 125 Go n'est déplacé.
- `registry`: concepts UNESCO, relations SKOS, P3916 avec statut de mapping.
- `discovery`: candidates `(branch_id, concept_id, qid, page_id, path)` dédupliqués, curseurs et budgets.
- `selection`: passerelle ChatGPT passe 1 et import APPROVE/REJECT/HOLD provisoire.
- `islands`: inventaire des îlots et états, capacités et rattachements N:N; aucun nouveau workspace par QID par défaut.
- `proposals`: propositions sourcées privées distinctes des états admis, lues dans le mode exploratoire.
- `admission`: auteur Kit optionnel après qualification, décision et reçu liés à l’état réellement observé.
- `federation`: snapshots épinglés et lecture Kompiler avec omissions explicites.
- `enrichment`: passerelle ChatGPT passe 2, textes wiki et déclarations Wikidata ciblées, **création cumulative de propositions EncyK**.
- `scheduler`: jobs persistants + lanes; priorités, débits, réparations et reprise après redémarrage.
- `monitor`: écarts utiles, production cumulée, limitations des sources, journaux.
- `desktop`: UI pyw; jamais propriétaire de l'état ni des transactions.

## Démarrage, durée de vie, non-régression

Un redémarrage du manager recharge les jobs et les lanes depuis SQLite, **sans** les reconstruire ni modifier les ZIP déjà préparés. « Reprendre » signifie *reprendre des états*, pas redécouvrir. Une revue envoyée conserve sa source et son contrat jusqu'à import ou annulation volontaire. Les analyses de disponibilité restent rapides et read-only. Les opérations de découverte et d'extraction demandent une action explicite.

## Pourquoi les dix postes restent un maximum

Si le stock donne quatre lots de travail utiles, afficher « 4/10, aucune réserve prête » et la raison. Il serait trompeur de fabriquer six micro-packs dupliqués. Inversement, si PENDING=0 et DEFERRED>0, le scheduler ne doit pas déclarer « rien à faire ». La fonction multibranche `routage_branches_v311.prepare()` observée dans le snapshot comporte une telle voie de sortie précoce : **test de régression obligatoire lors du réemploi**, pas supposition qu'elle est corrigée par la station historique v31.12.
