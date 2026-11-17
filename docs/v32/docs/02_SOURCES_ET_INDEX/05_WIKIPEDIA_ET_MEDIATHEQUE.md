# Wikipédia local, index SQL, récupération de révisions et médiathèque

## Trois représentations complémentaires

1. **Index SQL Wikimedia** : table `wiki_pages` pour les identités/versions/titres, `wiki_qid` pour la jointure Wikidata, `wiki_pagelinks` et catégories pour la découverte de rappel.
2. **Index d'offsets XML v21** : recherche directe du fragment XML correspondant à un `page_id`, sans scanner entièrement le fichier de plus de 100 Go à chaque requête.
3. **XML Wikipédia décompressé** : wikitext complet d'une révision précise, base documentaire du pack d'enrichissement.

Les pièces 1–3 **ne sont pas interchangeables**. Le classement/choix des articles peut se faire à partir de métadonnées et de courts extraits; l'enrichissement substantiel des faits dépend du texte complet. Le QID est un lien d'identité vers Wikidata mais la propriété P3916 appartient à la couche Wikidata, pas à `wiki_pages`.

## Réemploi exact du code

- `mediatheque-references/tools/wiki/dump_import/import_dumps.py` : import SQL complet et reprenable (`page`, `page_props`, `linktarget`, `pagelinks`, `categorylinks`), création d'index.
- `mediatheque-references/tools/wiki/atlas/atlas_wikipedia.py` : lecture indexée des pages, QID et liens pour les campagnes Atlas.
- `mediatheque-references/tools/wiki/atlas/extraction_multistream_v20.py` : historique de construction d'offsets; le contrat de lecture utilisé par EncyK est dans `production_kristals_v27.py`.
- `EncyKlopedia/tools/unesco_pilot/production_kristals_v27.py` : `validated_sources()`, `page_from_index()`, `VerifiedXmlResolver.read()`, `make_pack()`, `validate_delta()` et `import_delta()`.
- `EncyKlopedia/tools/unesco_pilot/contexte_revue_unesco_v28.py` : `MAX_EXCERPT_CHARS=3400`, synopsis nettoyé depuis le wikitext, contexte non exhaustif, cache de lecture locale.

## Opportunité spécifique à V32

Une page sélectionnée après la passe 1 ne doit être **lue/extraitée qu'une fois pour sa révision**, puis son résultat de lecture peut alimenter plusieurs concepts, plusieurs branches et éventuellement plusieurs sujets dérivés. Le cache est indexé par `(wiki,page_id,revision_id)` et reste un cache de source, non le lieu de la vérité sémantique.

Pour une page sans QID ou une notion UNESCO abstraite, les catégories, liens et recherche de titres peuvent générer des candidats supplémentaires. Garder une route `fallback_lexical` distincte de `P3916→QID→sitelink`; ne pas additionner des évidences de nature différente comme si elles étaient équivalentes.

## Relation à la médiathèque partagée

`mediatheque` possède un modèle de **source matérielle** (`source_uuid`, snapshot, version, représentation), et plusieurs consommateurs kOA. Il ne devrait pas être copié dans EncyK V32; un adaptateur de références source est suffisant si l'archivage des extraits au niveau de la médiathèque est utile. `mediatheque-references`, lui, comprend le code d'import de l'index Wikimedia; ses index sont le patrimoine de production à garder sur D:.

## Optimisations sans frein

- Préférer `wiki_qid.qid` et `wiki_pages.page_id`, jamais un `LIKE` global sur des millions de pages comme méthode principale.
- Faire un appel par lot de QID lorsque c'est avantageux et que l'index le supporte; éviter une nouvelle connexion SQLite pour chaque entité.
- Précharger les sections d'un article sélectionné, sans rogner le wikitext dans le ZIP source. La présentation peut avoir des extraits; **l'intégration ne doit pas se fonder uniquement dessus**.
- Dédupliquer les fichiers `articles/enwiki-ID.wikitext.txt` au niveau du pack; associer plusieurs concepts dans le manifeste plutôt que dupliquer le texte.
- Ne pas exiger un contrôle d'intégrité global de l'index SQL à chaque session. Savoir gérer les erreurs de lecture et signaler une révision introuvable suffit pour continuer d'autres tâches.
