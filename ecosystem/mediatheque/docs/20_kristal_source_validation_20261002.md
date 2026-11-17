# Validation du système de sources Kristal — snapshot 2026-10-02

> **Note historique.** Cette validation précède le schéma v4. Les mesures restent utiles, mais l'autorité source courante est désormais `source_*`; Kristal est représenté comme un consumer binding.

Validation effectuée contre `SmartSnap(20261002-122632)` dans une base Médiathèque kOA jetable.

## Librairies canoniques détectées

| Kristal | Sources déclarées | Snapshots | Représentations déclarées dans source-store |
|---|---:|---:|---:|
| Kristal-HistoryTech | 200 | 200 | 564 |
| Kristal-HumanBody | 119 | 0 | 0 |
| Kristal-Math | 22 | 6 | 24 |
| Kristal-ScolQc | 122 | 0 | 0 |

`FoodBrands/external-source-library` ne contient actuellement qu'un README, donc aucun `source-store.json` à importer.

`HospitalOps/knowledge-sources` et les dossiers `canonical-corpus`/`knowledge-base/corpus` ont été laissés hors migration automatique : ils contiennent des connaissances/corpus internes, pas la même classe de téléchargements externes.

## Résultat d'import réel

- Kristals enregistrés : **4**
- liens Kristal ↔ source : **463**
- sources logiques uniques après normalisation URL : **461**
- snapshots enregistrés : **206**
- snapshots disponibles : **125**
- représentations effectivement liées : **588**
- fichiers physiques uniques dans la Médiathèque : **582**
- volume physique copié pour ce test : **243 418 083 octets**
- fichiers réutilisés par déduplication SHA-256 : **6**
- incohérences SHA-256 : **0**

## Fichiers référencés mais absents du snapshot fourni

Le catalogue source référence des fichiers qui ne sont pas présents dans le ZIP de snapshot :

- HistoryTech : **120** absents (116 `rendered_pdf`, 4 `original`)
- Math : **5** absents

Le migrateur ne crée pas de faux fichiers. Les sources et snapshots sont conservés dans le catalogue; seules les représentations physiquement présentes et valides sont copiées.

## Vérification après import

`KoaKristalSources.py verify` :

- fichiers physiques vérifiés : **582**
- fichiers manquants dans le stockage kOA : **0**
- SHA-256 incohérents dans le stockage kOA : **0**
- état final : **OK**

Des manifests de bindings ont aussi été générés pour les quatre Kristals importés avec des locators `koa-media://version/<version_uuid>`.
