# EncyKlopedia — Centre de pilotage unifié v31.3 (préversion sûre)

**Périmètre :** station ChatGPT v30, audit UNESCO v31.2, catalogue v25, découverte v28 et production privée Kristal v27. **Aucune modification des moteurs existants**. Cette version est un outil de supervision séparé et **ne s'installe pas comme overlay**.

## Démarrage sur Windows 11 / Python 3.12

1. Décompresser le ZIP entier dans un dossier, par exemple `D:\CENTRE_PILOTAGE_ENCYK_V313`.
2. Double-cliquer sur `CENTRE_PILOTAGE_ENCYK_V313.pyw`. Les fichiers `encyk_global_v313.py` et `AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw` doivent rester **dans le même dossier**.
3. L'application ouvre une fenêtre sans console et lit les cinq bases aux chemins du diagnostic du 14 novembre 2026. Modifier un chemin au besoin dans « Sources et sécurité ».
4. Le premier diagnostic démarre automatiquement. Le bouton **Actualiser les 5 bases** relit les données.
5. Le suivi périodique est **désactivé par défaut**. Les options 15, 30 et 60 minutes s'appliquent uniquement tant que la fenêtre reste ouverte.

Pour lancer sans interface et générer les rapports (PowerShell 7) :

```powershell
python D:\CENTRE_PILOTAGE_ENCYK_V313\CENTRE_PILOTAGE_ENCYK_V313.pyw --once
```

Pour effectuer les tests (sans accès aux bases de production) :

```powershell
cd D:\CENTRE_PILOTAGE_ENCYK_V313
python -m unittest TEST_CENTRE_PILOTAGE_V313.py -v
```

## Données lues

- **Station** `station_v30.sqlite` : nombre de tâches globales et par type, états DONE/READY et autres, branche en revue, postes assignés ; aucun changement de statut.
- **Catalogue** `catalogue_global_unesco_wikipedia_v25.sqlite` : inventaire, concepts configurés, affectations, décisions UNESCO importées.
- **Découverte** `DECOUVERTE_ARTICLES_RELIES_V28.sqlite` : candidats et graines déjà connus ; aucune nouvelle découverte.
- **Kristal** `KRISTAL_CUMULATIF_PRIVE_V27.sqlite` : **uniquement** nombres de claims, citations, articles visités et deltas, ainsi que les catégories d'état. Aucun texte, citation ou payload privé n'est sélectionné.
- **File Kristal** `FILE_PACKS_V27.sqlite` : nombre de packs préparés, états de file et nombre d'époques source.

L'audit de couverture UNESCO est **réutilisé sans modification** à partir du fichier original `AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw`. Les paires (concept_id, page_id), identifiants et empreintes restent dans les exports d'audit déjà prévus.

## Exports

Le bouton **Exporter les rapports** écrit cinq fichiers dans le dossier choisi, par défaut `%USERPROFILE%\Documents\EncyKlopedia_Audits` :

- `SUPERVISION_GLOBALE_V313_*.json` : indicateurs du centre et audit complet.
- `AUDIT_...json` : audit de branche v31.2 avec historique.
- `AUDIT_..._CONCEPTS.csv` : couverture par concept.
- `AUDIT_..._A_REVOIR.csv` : candidats HOLD, non suivis et anomalies documentaires.
- `AUDIT_..._ECHANTILLON_OMISSIONS.csv` : échantillon en attente de contrôle humain.

Le simple rafraîchissement de l'affichage **ne crée aucun fichier**. Les exports sont lancés seulement par l'utilisateur ou par `--once`. Garder ces rapports locaux : le JSON de branche et les CSV peuvent contenir des identifiants, titres ou métadonnées documentaires.

## Garanties et limites

- Lecture SQLite via `mode=ro` + `PRAGMA query_only=ON`. Les tests synthétiques vérifient aussi qu'une mise à jour SQL est refusée.
- Aucune création, suppression ou réinitialisation de tâches, aucun import, aucune publication, aucune admission canonique, aucune levée du gel UNESCO.
- Les anciens lots UNESCO (notamment ceux de 110) ne sont pas modifiés.
- Les HOLD, DEFERRED et candidats simplement absents d'un index ne sont **jamais exclus** de l'inventaire.
- Un nombre de graines en attente à zéro **ne prouve pas** la saturation exploratoire ; le `achevement_reel_pct` reste `null`.
- Chaque base SQLite est lue séparément : en cas de changement pendant le diagnostic, les compteurs ne sont pas un instantané atomique.
- Aucune décision sémantique automatique ni validation indépendante des citations.
- **La version a été testée sur Linux avec des bases synthétiques ; le lancement graphique sous Windows 11 et sur la base de production reste à vérifier localement.**

## Interprétation du diagnostic reçu le 14 novembre 2026

L'instantané fourni indique 281 tâches station (277 DONE, 4 READY), 36 786 candidats suivis dans la première branche (30 589 DECIDED, 6 197 HOLD), 39 301 paires découvertes, 2 705 articles de catalogue et 25 812 claims Kristal privés. Ces nombres sont des **observations ponctuelles**, non des constantes codées dans l'outil. Ils peuvent avoir évolué depuis le diagnostic.

## Étape suivante recommandée

Une fois la supervision validée localement, étudier séparément la révision des 6 197 HOLD, le statut des 667 paires non rapprochées et les campagnes de saturation autorisées. **Ce programme n'entreprend aucune de ces actions lui-même.**
