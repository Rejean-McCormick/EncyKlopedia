# EncyKlopedia — Méga-update V31.1 (13 novembre 2026)

**Statut** : implémentation cumulative, vérifiée sur des index et catalogues synthétiques ; l'exécution sur les fichiers de production Windows n'est pas attestée par le présent document.

## 1. Contrats de données

- La base source `wikipedia_en.sqlite` reste en **lecture seule** ; les liens sont résolus **wiki_pagelinks.target_id → wiki_linktargets.target_id → wiki_pages(ns,title)**. `target_id` n'est jamais pris pour un `page_id`.
- `qualification_multibranche_v31.sqlite` reste un **cache d'hypothèses** : profils d'articles ns=0, suggestions multibranches, scores, QID et indices conservés. Aucun article ni redirection n'est supprimé par le classificateur.
- Le catalogue `catalogue_global_unesco_wikipedia_v25.sqlite` demeure la source de vérité pour les branches, les concepts, les articles affectés et les décisions v28 ; pas de second catalogue canonique.
- Les découvertes v28 de branches nouvelles sont rangées dans `decouverte_articles_relies_v28/branches/b_<sha16>/DECOUVERTE_ARTICLES_RELIES_V28.sqlite`. La découverte historique continue dans son chemin d'origine.
- La station garde **une seule base de tâches**, avec une table additive `v311_job_routes` pour mémoriser la branche et la base v28 de chaque tâche nouvelle. Les retours sont importés avec l'**importeur officiel v28**, jamais en écrivant directement des APPROVE dans le catalogue.
- Les justifications, les `candidate_id` et les empreintes `evidence_sha256` restent inchangés. Toute revue créée avant la mise à jour garde sa route historique.
- Kristal v27 reste une production privée distincte, non canonique.

## 2. Priorisation et réserve

- Les candidats à preuve forte (liens directs, score pertinent) sont envoyés d'abord.
- Une proposition avec `priority < 15` **et zéro lien direct** est marquée `DEFERRED` tant qu'elle n'a pas été distribuée. Il s'agit d'une **réserve**, pas d'un `REJECT` ; les preuves et la proposition demeurent dans la base.
- Tant que des candidats prioritaires existent, environ 25 % des places des nouveaux packs sont réservés à l'exploration stratifiée d'autres priorités et de la réserve différée. Les packs gardent un objectif de 300 propositions (max. 500 par contrat natif, volume réduit si le budget documentaire l'exige).
- Si la file prioritaire est vide, la station ne transforme pas automatiquement toute la réserve en lots. La commande `OUVRIR_EXPLORATION_V311.ps1` permet de remettre explicitement un échantillon de cette réserve dans la file.
- Aucun score n'est jamais une décision APPROVE, REJECT ou HOLD. Les taux de rappel et la qualité des candidats devront être mesurés sur les retours futurs.

## 3. Qualification multibranche

- La normalisation lexicale conserve désormais les racines de `education`, `educational`, `school`, `university`, au lieu de les supprimer comme simples mots outils.
- Les termes des titres, catégories et liens sont combinés à un signal QID **uniquement si un crosswalk officiel local référence explicitement la correspondance candidate**. Le score QID reste provisoire et n'autorise aucune admission.
- Les manifestes et le crosswalk entrent dans la signature de la configuration : changer les termes ou les QID requalifie les profils conservés.
- La migration additive des caches du format `...v31/1` vers `...v31/2` est automatique. Les anciens profils sont reclassés sans relecture des textes, en exploitant les indices conservés.

## 4. Découverte sans index XML v21

- Le moteur v28 original demeure accessible lorsque l'index v21 et le XML concordent.
- En cas de **désaccord attesté** de signature entre l'index v21 et le dump XML, la station bascule vers `decouverte_relationnelle_v311.py` pour de nouveaux liens/catégories, à partir des tables SQL indexées.
- Les preuves sont typées `WIKILINK` ou `SHARED_CATEGORY`, avec détail `WIKILINK_SQL:`/`CATEGORY_SQL:` et une graine d'origine. Il n'y a **aucune fausse citation de passage XML**.
- Le cache d'extraits XML v31 demeure optionnel : seuls des passages conformes à la signature et à la révision sont présentés comme vérifiés ; l'absence de texte est indiquée.
- La découverte n'est pas relancée pendant que des revues v28 distribuées sont ouvertes, conformément à la protection native de la station.

## 5. Nouvelles branches

- Le catalogue peut déjà accueillir plusieurs branches ; le nouvel outil `ACTIVER_TOUTES_BRANCHES_V311.ps1` réutilise les **manifestes v25 réels** sous `tools/unesco_pilot/v25_data/` pour étendre le catalogue puis lancer les découvertes SQL par branche.
- Aucune branche absente du référentiel local n'est fabriquée. Un manifeste UNESCO issu d'une source officielle doit être installé avant sa création.
- La station détecte les découvertes de nouvelles branches, enregistre le rattachement exact de chaque tâche, regroupe les propositions d'une **même branche par ZIP**, et importe avec les options `--branch`/`--work` correspondantes.
- Les notes et libellés transmis dans les contextes enrichis sont lus du **manifeste réel de la branche du ZIP**, plutôt que d'un concept central codé en dur.

## 6. Statistiques

`GENERER_STATS_GLOBALES_V31.ps1` produit HTML/JSON avec les tables existantes et, en plus :

- propositions par branche **et état**, dont `DEFERRED` ;
- revues achevées par branche (`APPROVE`, `REJECT`, `HOLD`) lorsque la route est connue ;
- nombre de profils ns=0 traités et pourcentage sur un dénominateur mesuré ;
- graines en attente par branche pour la découverte v28 ;
- données historiques du catalogue v25 et de Kristal v27.

**Ne pas confondre** l'inventaire des pages connues, l'état des lots distribués, la couverture des concepts et l'achèvement global de toutes les branches. L'achèvement global reste `null` tant que les critères de complétude et le dénominateur ne sont pas établis.

## 7. Commandes opérationnelles

Depuis le dépôt :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\ACTIVER_TOUTES_BRANCHES_V311.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File .\LANCER_QUALIFICATION_GLOBALE_V31.ps1 -Tout
pwsh -NoProfile -ExecutionPolicy Bypass -File .\GENERER_STATS_GLOBALES_V31.ps1
pwsh -NoProfile -ExecutionPolicy Bypass -File .\OUVRIR_EXPLORATION_V311.ps1 -Propositions 300
```

La station se lance toujours avec `LANCER_POSTE_CHATGPT_V30.ps1`. Les scripts et bases de production restent sur leurs chemins EncyKlopedia existants.

## 8. Vérifications avant de déclarer la production validée

- Exécuter les tests unitaires installés sous `tests/`.
- Contrôler le premier lot de 300 et son contexte enrichi sur la station Windows.
- Tester un aller-retour complet pour une branche supplémentaire **réellement manifestée et enregistrée au catalogue**.
- Mesurer l'accès aux index et le débit de qualification sur l'installation de 125 Go.
- Vérifier les taux de `APPROVE`, `REJECT`, `HOLD`, et le rappel sur un échantillon de la réserve.

Aucune reconstruction massive d'index n'est imposée par cette mise à jour.
