# v1.4 — Import de faits Wikidata complets (try big → fix → validate)

**Nouvelle fonction substantielle :** extraction ciblée des *entités originales* Wikidata pour les seuls QID associés sans ambiguïté à un concept UNESCO. Réutilise le lecteur Skope fourni dans ton `Kristal-Wikidata-Workflow` sans créer d'index ni parcourir le dump entier.

## Un lancement

Décompresser à `C:\mycode\Kristal\Kristal_UNESCO_Factory`, démarrer `LANCER_FABRIQUE.cmd`, conserver « Importer les entités Wikidata complètes » actif, lancer **TOUT CONSTRUIRE + VALIDER**. Le champ source peut rester vide : la fabrique cherche automatiquement le dump dans `D:\EncyKlopedia\10_sources\wikidata\dumps\current` (en dérivant le volume depuis le chemin de l'index). On peut aussi indiquer :

- **Fichier de fiches préextraites** `*.jsonl` / `*.jsonl.gz`, par exemple un export Skope.
- **Dossier Skope** contenant `snapshot-manifest.json` et `part-*.jsonl.gz`.
- **Dump original** `*.json`, `*.json.gz` ou `*.json.bz2`, **uniquement** avec le localisateur et l'index de compression Skope existants. Jamais de scan global implicite.

Si le localisateur est absent, la version déclare précisément **FAITS COMPLETS NON IMPORTÉS** et continue le parcours UNESCO/Spek ; elle ne fabrique pas des données manquantes. Pour les archives `.gz` / `.bz2`, le Python de la Fabrique doit disposer du lecteur d'accès rapide adapté (`rapidgzip` ou `indexed_bzip2`). Le lecteur est récupéré du snapshot de Skope et sa licence MIT est conservée dans `vendor/wikidata_skope/LICENSE-MIT.txt`.

## Sorties complémentaires

- `02_WIKIDATA/FAITS_COMPLETS/raw_entities.jsonl.gz` : entités complètes telles que reçues, conservées sans modification de leur contenu ; les lignes sont réencodées sous forme JSONL compressée.
- `02_WIKIDATA/FAITS_COMPLETS/facts.jsonl` : assertions typées, rangs, valeurs, **qualificatifs et références**, plus une empreinte de chaque entité.
- `02_WIKIDATA/FAITS_COMPLETS/manifest_full.json` : nombre de QID demandés/présents/manquants, nombre de déclarations, groupes de références, qualificatifs et empreintes des sorties.
- `02_WIKIDATA/FAITS_COMPLETS/faits_consultables.html` : visualiseur hors-ligne des QID et faits, recherche et lien vers Wikidata.
- `03_KRISTALS/*/derived/wikidata-full-facts-index.json` : correspondances d'entités et aperçus pour les microthésaurus, **non canoniques**.
- `04_SPEK/` : aperçu enrichi avec quelques propriétés Wikidata **P-ID**, valeurs, rangs et compte de références. Ce n'est pas une interprétation scientifique certifiée.
- `RAPPORT_FINAL.json` : nouveaux champs `wikidata_full_claims_import`, `wikidata_full_evidence` et compteurs `full_entities`, `wikidata_statements`, `wikidata_reference_groups`.

La fenêtre contient **Ouvrir faits WD**, et le catalogue local intègre un lien vers ce navigateur lorsque l'import a produit des données.

## Garanties et limites

- **Aucune promotion canonique** des QID ou déclarations ; seuls les snapshots de source UNESCO existants sont dans `canon/domain`.
- **Aucune publication** ; chaque RUN reste indépendant et local.
- Les 134 ambiguïtés P3916 et les 77 identifiants sans P3916 de la précédente exécution restent hors de l'extraction comme identités approuvées.
- Une preuve de lecture du dump n'est pas une **révision scientifique** des assertions. Les rangs et références Wikidata sont conservés, non validés.
- Les propositions IA Ollama utilisent désormais aussi des aperçus des faits locaux quand ceux-ci existent ; elles restent séparées et non canoniques. IA désactivée par défaut.
- SemantiK Architect / GF **n'est pas encore raccordé** à la réalisation linguistique. Le contenu généré par Spek est un aperçu bilingue de données sources et non une encyclopédie de qualité éditoriale prête à publier.

**Objectif du prochain saut** : normaliser les propriétés et les entités en contrats sémantiques revus, améliorer les explications par IA avec contrôle de citations, puis brancher SemantiK/GF sur les mêmes kristals et qualifier les pages en langues multiples.
