# EncyKlopedia — audit automatique de la première branche UNESCO (v31.2)

**Fichier** : `AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw` (Python 3.10+, uniquement bibliothèque standard).
**Branche** : `unesco.mt1.10` par défaut ; modifiable dans l'interface.
**Prérequis** : les bases SQLite v25, v28 et v30 existantes, accessibles sur Windows.

## Mise en route

1. Déposer le `.pyw` dans `D:\` ou un autre dossier local.
2. Double-cliquer sur le fichier : il démarre une analyse immédiatement, sans ouvrir PowerShell.
3. Consulter **41 concepts & alertes**, **Candidats à vérifier**, **Automatisation & historique**.
4. Au besoin, activer **Suivi périodique** (15, 30, 60 ou 180 minutes) ; il fonctionne **seulement pendant que la fenêtre est ouverte**.
5. Tous les résultats sont enregistrés par défaut dans `%USERPROFILE%\Documents\EncyKlopedia_Audits`. Le dossier est modifiable dans l'interface.

Une exécution produit quatre fichiers :

- `AUDIT_...json` : indicateurs, écarts entre les trois bases, alertes, évolution.
- `AUDIT_..._CONCEPTS.csv` : un résultat par concept (41 normalement), dont concepts sans approbation.
- `AUDIT_..._A_REVOIR.csv` : HOLD, non suivis, autres états non tranchés, divergences d'empreintes.
- `AUDIT_..._ECHANTILLON_OMISSIONS.csv` : jusqu'à 30 cas par strate (REJECT, HOLD, non suivis, autres états). Les deux colonnes de contrôle humain sont laissées vides.

Deux petits fichiers sont entretenus **dans le dossier de rapports seulement** : `ETAT_PRECEDENT_...json.gz` (comparaison entre analyses) et `HISTORIQUE_...jsonl` (timeline).

## Audit automatique même quand la fenêtre est fermée

Deux possibilités, **optionnelles** :

### Via le Planificateur de tâches Windows

Placer `ACTIVER_AUDIT_QUOTIDIEN_V312.ps1` dans le même dossier que le `.pyw`, puis exécuter explicitement dans PowerShell :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\ACTIVER_AUDIT_QUOTIDIEN_V312.ps1 -Heure 07:00
```

Le script enregistre une tâche quotidienne au compte Windows courant, utilisant `pythonw.exe --once`. Ce n'est **pas** installé automatiquement par la simple ouverture du `.pyw`. Le PC doit être disponible au moment de l'exécution ; la tâche planifiée ne garantit pas un réveil de la machine. Les erreurs d'audit sont écrites dans `DERNIERE_ERREUR_AUDIT.txt` dans le dossier de rapports.

Pour désinstaller uniquement la tâche planifiée :

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\ACTIVER_AUDIT_QUOTIDIEN_V312.ps1 -Desinstaller
```

### Sans tâche planifiée

```powershell
python D:\AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw --once --output D:\AUDITS_ENCYKLOPEDIA
```

Cette commande crée les rapports, puis quitte. Vous pouvez l'appeler avec le Planificateur de tâches ou un script personnel.

## Considérations méthodologiques et limites

- **Lecture seule garantie au niveau des connexions SQLite** (`mode=ro`, `PRAGMA query_only=ON`). Pas de découverte, pas de modification des candidats, pas de décision automatique, pas de canonisation, pas de publication.
- Les paires sont rapprochées par **(concept_id, page_id)**, en filtrant la branche. `candidate_id`, `evidence_sha256` et `task_id` sont conservés tels quels pour les lignes disponibles.
- « Découvert mais absent de la station et du catalogue » signifie uniquement **absent des index interrogés**. Cela ne prouve pas une perte : réserve, lots anciens ou synchronisation différée peuvent l'expliquer.
- Une valeur **0 nouveau** entre deux rapports ne prouve pas que la découverte est saturée. Le logiciel signale aussi la variation de graines `DONE` pour distinguer un vrai nouveau cycle d'un simple sondage répété.
- L'échantillonnage identifie des dossiers de **vérification humaine**, il **n'est pas** une estimation numérique du rappel et ne remplace pas une validation de citations.
- Les trois bases sont lues successivement ; les résultats ne constituent pas un snapshot atomique en cas d'activité concurrente. Pour une preuve forte, utiliser des snapshots SQLite cohérents.
- Le pourcentage d'achèvement **encyclopédique réel reste indéterminé** (`null`) tant qu'une campagne de saturation, un audit d'omissions et une réconciliation des générations n'ont pas apporté des preuves suffisantes.
- Les rapports contiennent des identifiants, titres et métadonnées de recherche. Ils demeurent **locaux**, sans transfert externe.

## Vérification rapide

```powershell
python D:\TEST_AUDIT_AUTOMATIQUE_V312.py -v
```

Placez ce test dans le même dossier que le `.pyw`. Les trois tests créent des bases SQLite **synthétiques** et vérifient l'export, les rapprochements, les comparaisons et la non-modification des bases.
