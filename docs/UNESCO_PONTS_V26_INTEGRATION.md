# Catalogue UNESCO × Wikipédia — intégration des 28 ponts revus v26

## Principe

Le moteur v25 a déjà construit un **catalogue global partagé**. Le manifeste de sa branche `unesco.mt1.10` est volontairement immuable après initialisation. **Il ne faut pas remplacer le fichier `v25_data/ponts_mt110.csv` par les 28 ponts**, car cela ferait changer la signature du manifeste et bloquerait la reprise.

L'overlay ajoute une opération explicite, traçable et incrémentale, distincte du semis initial de la branche. Il conserve :

- les `articles` (une identité par page Wikipédia, tous rattachements confondus) ;
- les `assignments` et les tâches déjà complétées ;
- les 41 concepts du pilote et les paramètres de branche v25 ;
- les snapshots antérieurs et les Kristals (aucune canonisation ni publication).

Le CSV embarqué est le fichier transmis après la revue v26 : **423 décisions**, avec **28 `INCLUDE`**, **189 `HOLD`** et **206 `EXCLUDE`**. Seuls les ponts `INCLUDE` engendrent des tâches de découverte. Les 395 autres décisions ne déclenchent aucune association d'article.

Les 28 ponts sont limités à `depth_limit=0` (membres directs des catégories), et tous les résultats restent **des candidats** ; l'appartenance à une catégorie Wikipédia n'équivaut pas à une affirmation encyclopédique vérifiée.

## Déploiement (aucun installateur)

Extraire ce ZIP à la racine :

`C:\mycode\EncyKlopedia\EncyKlopedia`

Les chemins internes sont relatifs à cette racine. Accepter le remplacement du **seul fichier existant modifié** : `tools/unesco_pilot/catalogue_global_v25.py`. Les autres fichiers sont nouveaux.

Ouvrir PowerShell dans cette racine. Faire d'abord un précontrôle (lecture seule) :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\INTEGRER_PONTS_REVUS_UNESCO_V26.ps1" -PreflightOnly
```

Pour importer les ponts et traiter les familles (un seul lancement, reprise automatique des lots) :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\INTEGRER_PONTS_REVUS_UNESCO_V26.ps1"
```

Le message final attendu est `V26_PONTS_INTEGRATION_OK`. Si le nombre de catégories ou de membres dépasse un plafond, le rapport signalera `tasks_pending` / `tasks_capped`. Il ne faut pas effacer le catalogue : la commande est **reprenable et idempotente**.

Vérification seule :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\INTEGRER_PONTS_REVUS_UNESCO_V26.ps1" -VerifyOnly
```

## Sorties

Catalogue SQLite conservé :

`D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite`

Le moteur crée une nouvelle séquence de snapshot (sans toucher aux anciennes) sous :

`D:\EncyKlopedia\30_working\catalogue_global_unesco_wikipedia_v25\snapshots\`

La commande renvoie les chemins exacts `reader` et `export`. `LATEST.json` pointe vers la dernière séquence ; transmettre ensuite `EXPORT_V25_POUR_CHATGPT.zip` de cette séquence pour examiner la nouvelle couverture.

## Sécurités et limites

- Wikipédia SQL : lecture seule (SQLite `mode=ro`, `PRAGMA query_only`). Aucun parcours du XML.
- Le script refuse un catalogue absent, une signature SQL incompatible, une configuration de branche modifiée, un pont différent déjà importé ou une catégorie sans identifiant `linktarget`.
- L'import crée deux registres additifs **dans le catalogue dérivé**, `reviewed_bridge_imports_v26` et `reviewed_bridges_v26`, ainsi qu'une trace dans `audit_events`.
- Une deuxième exécution du même CSV ne recrée ni article ni pont ; elle peut poursuivre les tâches inachevées.
- Les éventuels ponts déjà découverts par la v25 sont reconnus. Leur niveau de preuve originel n'est pas réécrit silencieusement.
- Le nombre de nouveaux articles dépend de ta base locale, et **n'est pas connu avant l'exécution réelle sur D:**.
- Cette version ne sélectionne pas les articles finaux pour publication ; elle ajoute des candidats à la cartographie encyclopédique.
