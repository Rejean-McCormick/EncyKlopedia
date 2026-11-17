# Cartographie des dépôts, outils et applications

**Source** : inventaire statique du SmartDump `SmartDump_20261115_173446.zip`, du snapshot principal, des fichiers autonomes du centre v31.3/31.4, et du snapshot Skope transmis. Les décomptes portent sur les fichiers présents dans les snapshots, **pas** sur les systèmes Windows complets. Voir [`../07_INVENTAIRES/inventaire_depots.csv`](../07_INVENTAIRES/inventaire_depots.csv).

## Noyau de l'écosystème

| Dépôt (nom d'origine) | Ce qu'il contient réellement | Statut cible pour la consolidation |
|---|---|---|
| `EncyKlopedia` | Application vitrine/recherche Node, scripts de catalogue v25, découverte v28/v31, Kristal v27, station v30, multibranche v31, tests/docs, nombreux lanceurs CMD/PS1 | **Principal donneur de code** : porter fonctions de production, importer les sources sans copier le patrimoine historique inutile |
| `UNESCO_Kristals` | 88 workspaces, snapshots UNESCO 2026, relations SKOS, mapping candidates P3916, prévisualisations de faits Wikidata | **Données d'entrée réutilisables**, pas 88 moteurs à intégrer |
| `Kristal_UNESCO_Factory` | Fabrique GUI `.pyw`, pipeline d'extraction UNESCO, alignement P3916, lectures Wikidata, rapports | **Réutiliser l'import/normalisation/export** comme adaptateurs; une seule gestion d'espaces de branche |
| `UNESCO_Workbench` | Revue et comparaison privée de la branche pilote, ancien extrait LinkedDataHub, contrôles, documents et rapports | **Réutiliser fonctions utiles au diagnostic**, archiver les procédures répétées du pilote |
| `LinkedDataHub-UNESCO` | Démonstrateur RDF/SKOS LinkedDataHub 2025, ontologie, données Turtle, scripts d'installation Web | **Source comparative historique**, pas le moteur d'alignement P3916 ni un service nécessaire au V32 |
| `mediatheque-references` | Import SQL Wikipédia, `wiki_qid`, pages/liens/catégories, index offsets et outils atlas | **Préserver les index**, employer adaptateurs de lecture; ne pas relancer l'import massif sans besoin |
| `mediatheque` | Moteur partagé de préservation des sources, snapshots, sources UUID, intégration UCKK/Moodle | **Service partagé externe/logique**, réutiliser l'interface, ne pas copier le moteur commun dans EncyK |
| `LevelUpDiag_EncyK` | Diagnostics, vérifications reader/bridge, rapports indépendants | Intégrer les fonctions de diagnostic utiles dans le manager; archiver le lanceur autonome plus tard |
| `scan_engine` | Ancien répertoire lié à **Kristalizer** | **EXCLU du refactor** : ne pas déplacer/copier/éditer |
| `scan_test` | Échantillons CSV/JSON pour tests de scan | Conserver comme fixtures ou en archive, après identification de leur utilité |
| `Skope` | Explorateur/serviciel Wikidata, index compact, recettes scope, extraction complète des QID, API | **EXTERNE, INTOUCHABLE**. Contrats de lecture et prévisualisation uniquement |

## Outils autonomes associés, pas tous des dépôts

- `ENCYK_CENTRE_PILOTAGE_V313` : GUI de pilotage lecture seule, et sa v31.4 de triage ; ne pas créer un second dashboard avec la même fonction.
- `EncykAudit` et `AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw` : audit des candidats UNESCO, export CSV, historique; utilité réelle, mais l'achèvement encyclopédique n'y est pas calculé.
- `OUTIL_AUDIT_GOULOTS_ENCYKLOPEDIA_V3110` : diagnostic index/discovery/station, pour comprendre les états sans écrire.
- `OUTIL_SAUVEGARDE_RESULTATS_ENCYKLOPEDIA_V3_CORRIGE` : sauvegardes SQLite des **cinq bases de résultat**; à conserver comme outil séparé ou adapté plus tard.
- `ENCYKLOPEDIA_EXPORT_CHATGPT` : exporteur de contexte ZIP/SmartDump pour une IA, utile comme fonction « Partager un diagnostic ».
- `DIAGNOSTIC_ENCYK_V3110_LECTURE_SEULE` : état observé des moteurs v31.10 et fichiers sur Windows, pas une source de vérité sur la future V32.
- `ENCYKLOPEDIA_CONTEXTE_MAX` : paquet de contexte/manifest historique, pas le code applicatif.
- Les ZIP `OVERLAY_*`, `PACK_V27_*`, `RETOUR_*` sont des **artefacts de production** ou historiques; ils ne sont pas des dépôts fonctionnels.

## Relations de possession observées et recommandées

- Source UNESCO : une version de thésaurus; la Factory en dérive des snapshots de branche; le manager les **consomme**.
- Source Wikidata : dump/compact gérés par infrastructure existante; Skope en expose le graphe et les extractions; EncyK **n'est pas** propriétaire du dump ni du canon Kristalizer.
- Source Wikipédia : tables SQL et XML locaux/offsets gérés par `mediatheque-references`; EncyK lit et construit un catalogue/une file.
- Station historique : `poste_chatgpt_v30.py` est propriétaire des jobs/retours historiques; V32 peut créer sa **propre file** sans reprendre les données du pilote.
- Moteur v27 historique : propriétaire du cumul privé v27; V32 doit posséder son propre modèle de sujet/Kristal, avec migration optionnelle.
- Médiathèque générique : propriétaire de références physiques/sources, **pas de la décision qu'un sujet appartient au thésaurus**.

## Frontière avec les autres projets

Le futur méga-repo est le manager **d'EncyK**, pas une absorption de tous les services partagés du poste. « Archiver les anciens dépôts » ne signifie pas casser leurs autres utilisateurs ou recopier leur code dans le nouveau dépôt. Pour chaque dépôt, documenter son utilisation hors EncyK avant archivage; Skope et Kristalizer sont des exclusions explicites.
