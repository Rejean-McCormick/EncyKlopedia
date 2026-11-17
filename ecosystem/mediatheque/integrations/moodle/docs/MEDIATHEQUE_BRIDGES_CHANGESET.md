# Change set — Médiathèques autonomes et bridges

Cette version part du snapshot « Univers-Cité chrétienne » et ajoute la séparation réelle des médiathèques par Univers-Cité, le partage d'un même fonds et les bridges directionnels.

## Fichiers ajoutés

- `mod/uckkarchive/classes/local/media_library_scope.php`
- `mod/uckkarchive/db/install.php`
- `mod/uckkarchive/docs/27_media_library_partition_and_bridges.md`
- `mod/uckkarchive/library_admin.php`
- `mod/uckkarchive/tests/media_library_scope_test.php`

## Fichiers modifiés

- `local/uckk/amd/src/mediatheque_explorer.js`
- `local/uckk/classes/local/public_pages/math/mediatheque.php`
- `local/uckk/classes/local/public_pages/mediatheque.php`
- `local/uckk/classes/local/public_pages/ucc/mediatheque.php`
- `local/uckk/classes/local/public_pages/ucc/site.php`
- `local/uckk/mediatheque.php`
- `local/uckk/version.php`
- `mod/uckkarchive/backup/moodle2/restore_uckkarchive_stepslib.php`
- `mod/uckkarchive/classes/external/add_media.php`
- `mod/uckkarchive/classes/external/add_media_collection.php`
- `mod/uckkarchive/classes/external/search_mediatheque.php`
- `mod/uckkarchive/classes/local/media.php`
- `mod/uckkarchive/classes/local/media_collection.php`
- `mod/uckkarchive/classes/local/public_mediatheque_repository.php`
- `mod/uckkarchive/classes/local/public_mediatheque_service.php`
- `mod/uckkarchive/db/access.php`
- `mod/uckkarchive/db/install.xml`
- `mod/uckkarchive/db/upgrade.php`
- `mod/uckkarchive/docs/00_index.md`
- `mod/uckkarchive/lang/en/uckkarchive.php`
- `mod/uckkarchive/lang/fr/uckkarchive.php`
- `mod/uckkarchive/settings.php`
- `mod/uckkarchive/tests/public_mediatheque_repository_test.php`
- `mod/uckkarchive/version.php`

## Validation effectuée

- syntaxe PHP : OK sur `mod/uckkarchive`, `local/uckk` et `theme/ucc`;
- XMLDB `install.xml` : XML bien formé;
- JavaScript `mediatheque_explorer.js` : syntaxe OK;
- JSON Atlas : valides;
- clés de langue FR/EN : aucune duplication;
- tests PHPUnit ajoutés pour l'isolation, les bridges directionnels et le partage d'un même fonds.

Le snapshot ne contient pas une installation Moodle complète ni un exécutable PHPUnit, donc les tests PHPUnit n'ont pas été exécutés dans cet environnement.

## Extension UCC — maillage Médiathèque ↔ cours

La Médiathèque UCC dispose maintenant d'un manifeste sémantique explicite reliant les ressources historiques aux 110 cours canoniques.

### Ajouts

- `local/uckk/atlas/ucc_mediatheque_course_links.json` — autorité des liens cours–média;
- `local/uckk/classes/local/atlas/ucc_mediatheque_registry.php` — lecture et validation des deux registres;
- `local/uckk/tests/ucc_mediatheque_registry_test.php` — invariants de couverture;
- `UCC_MEDIATHEQUE_COURSE_LINK_AUDIT.md` — audit humain de la couverture.

### Contrat

- 110/110 cours reliés;
- 105/105 références de Médiathèque reliées à au moins un cours;
- 3 à 6 références par cours;
- liens `primary`, `supporting`, `anchor` ou `editorial_complement`;
- les liens sémantiques reposent sur l'intersection des `kristal_theme_refs`;
- les compléments non équivalents sémantiquement sont explicitement étiquetés;
- `get_ucc_course` projette maintenant les références Médiathèque du cours.
