# Le moteur de construction ChatGPT existant : à conserver et renforcer

## Pourquoi c'est un actif majeur

Depuis v27/v28/v30, EncyK a résolu une partie difficile : des bases gigantesques restent locales; la station crée des **packs autonomes**; les dix conversations ChatGPT travaillent indépendamment; les fichiers de retour sont importés dans des SQLite persistants. Le système reprend après fermeture/erreur et ne doit pas réécrire les preuves d'une tâche déjà envoyée.

**V32 ne doit pas jeter ce moteur pour développer un simple prompt ad hoc.** On veut une production industrielle : missions suffisamment volumineuses pour un travail riche, visibilité des statuts, import de plusieurs ZIP à la fois, déduplication et enrichissement cumulatif.

## Fonctionnement vérifié dans les sources

### Kristal v27 / synthèse v31.8

`EncyKlopedia/tools/unesco_pilot/production_kristals_v27.py` :

- `synchronize` prend des pages cataloguées et leur statut de queue.
- `page_from_index` / `VerifiedXmlResolver` lisent le XML local via index v21; chaque pack contient **le texte source entier** des pages, pas une fenêtre coupée à arbitrairement 4 000 caractères.
- `make_pack` construit `MANIFEST_PACK_V27.json`, `DOSSIER_PRIORITAIRE_KRISTAL_V316.jsonl`, `MODELE_DELTA_KRISTAL_V27.json`, `INSTRUCTIONS_CHATGPT.md` et `articles/enwiki-ID.wikitext.txt`.
- `validate_delta` vérifie identifiants/révisions, structure de claims et, pour les packs v31.8, une citation exacte dans le wikitext et un bilan `coverage_note` **par article**.
- `import_delta` alimente `claims`, `citations`, `claim_concepts`, `claim_branches`, `article_visits`, `delta_imports`, `text_variants` dans le SQLite privé. Le réimport du même delta ne redouble pas les faits.

**Exemple réel fourni** : `PACK_V27_000289.zip` contient 64 articles et `RETOUR_KRISTAL_PACK_V27_000289.zip` contient un JSON avec **305 claims**. C'est un exemple de forme, pas une norme de quantité ni une preuve d'exhaustivité.

### Station ChatGPT v30/v31.x

`poste_chatgpt_v30.py`: `LANES=10`, revue UNESCO à 4 000 lignes maximum, `QUEUE_BUFFER=20`, limite de décompression et préchargement des ZIPs. `Station._batch()` lance la production v27 puis la découverte v28 sauf si une revue UNESCO est ouverte; `_prepare` alimente la file; `bundle`, `mark_sent`, `receive`, `_process_returns`, `_import_one`, `_complete` gèrent le cycle d'une tâche. Le serveur HTTP local et ses fichiers `poste_chatgpt_v30.html/.js` rendent les postes visibles.

La station connaît les états `WAITING`, `READY`, `SENT`, `IMPORTING`, `NEEDS_CONFIRMATION`, `ERROR`, `DONE`, `SKIPPED`. Les imports UNESCO sont reliés au moteur officiel v28, pas directement réécrits par le retour du modèle.

### Revue UNESCO v28

Un pack contient `REVUE_<task_id>.csv`, un prompt et éventuellement des contextes documentaires. Réponse attendue : trois colonnes `candidate_id,decision,justification` avec `APPROVE/REJECT/HOLD`. Les décisions publiées restent **provisoires**; les exemples et chemins ont été gelés pendant une revue active.

## Réglages historiques à comprendre, non à idolâtrer

La station actuelle lance Kristal avec jusqu'à **120 articles, 400 000 mots cibles et 60 MiB de texte cible** par pack. Les lots UNESCO visent **4 000 propositions**. Ce sont de gros volumes mais de coût IA très différent selon la densité des articles.

L'ancien flux stocke une grande part des claims avec `subject_ref=enwiki:page_id`. V32 doit déplacer l'identité vers **le sujet Wikidata/Kristal**, et stocker la page comme source. L'ancien moteur fait **de la classification documentaire et de l'enrichissement dans deux files assez indépendantes**; V32 les reliera explicitement : passe 1 `SELECT`, puis passe 2 *seulement des sélectionnés*.

## Ce qu'il faut copier comme principes de conception

- Un **job durable** a une identité propre et une entrée source; ne pas le recréer pendant un refresh.
- Les retours sont **fichiers de données**, jamais du code.
- Une tâche importée ne crée pas de doublons si renvoyée deux fois.
- Les cas incomplets sont visibles; un article à zéro fait peut avoir un motif honnête.
- L'interface présente la prochaine tâche au lieu d'imposer des commandes shell multiples.
- La source volumineuse demeure sur le poste, et les packs sont construits par lecture locale.

## Ce qu'on changera

- Lier les deux passes à un registre de **sujets et propositions** (pas un îlot par QID), avec `selected_candidate_ids` au lieu d'un catalogue d'articles entier.
- Remplacer les prompts v31.8 trop axés sur « ne pas trop extraire » par une politique de **forte couverture factuelle utile**, sans inventer une phrase ni multiplier les relectures lourdes.
- Corriger structurellement la réserve de travail : `PENDING` et `DEFERRED` ne deviennent pas des exclusions, les dix slots sont alimentés par **une file commune V32**.
- Organiser les packs par **coût du texte/sujet**, pas seulement par compte d'articles; conserver un budget souple et la capacité de continuer une mission très volumineuse.
