# EncyKlopedia — Inventaire local Wikipédia v26 (overlay dépôt consolidé)

Cet outil travaille directement à partir du dépôt `C:\mycode\EncyKlopedia\EncyKlopedia`.
Il n'utilise **aucun installateur**. La base SQL de Wikipédia est ouverte en **lecture seule** ;
l'inventaire des catégories est une base SQLite dérivée et reprenable sur `D:`.
L'outil ne modifie ni le catalogue v25 ni les Kristals et ne publie rien.

## Pose de l'overlay

Décompresser le ZIP **dans** `C:\mycode\EncyKlopedia\EncyKlopedia`, en remplaçant uniquement
les fichiers homonymes. Les chemins du ZIP sont relatifs à la racine de ce dépôt.
Conserver une copie du snapshot original si un retour arrière est nécessaire.

## Commandes (PowerShell 7, depuis la racine du dépôt)

Première tranche, puis export pour examen IA :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1 -MaxRows 200000
```

Poursuite **sans générer un ZIP à chaque tranche** (répéter jusqu'à `completed: true`) :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1 -ScanOnly -MaxRows 1000000
```

Statut sans nouvelle analyse ; puis export ponctuel de revue :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1 -StatusOnly
pwsh -NoProfile -ExecutionPolicy Bypass -File .\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1 -ExportOnly
```

Export attendu :

`D:\EncyKlopedia\30_working\inventaire_categories_wikipedia_v26\EXPORT_INVENTAIRE_V26_POUR_CHATGPT.zip`

Ne transmettre que ce petit export, **pas** les bases SQLite ni les dumps Wikipédia.

Pour effectuer ensuite une recherche ciblée à partir d'un JSON conforme au schéma `encyklopedia.category-probe-request.v26/1` :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1 -QueriesFile 'D:\dossier\requete_v26.json'
```

Pour valider localement un fichier de décisions reçu après revue IA, sans encore appliquer les ponts au catalogue v25 :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1 -DecisionsFile 'D:\dossier\decisions_v26.json'
```

## Précautions

- L'outil sélectionne un **unique** exécutable Python >= 3.11 compatible SQLite FTS5 et ignore les alias WindowsApps.
- Les modes `-ScanOnly`, `-ExportOnly`, `-StatusOnly`, `-QueriesFile`, `-DecisionsFile` sont exclusifs.
- L'inventaire local est partiel tant que l'état retourné ne mentionne pas `completed: true`.
- Les correspondances lexicales sont des **candidats**, pas des catégories UNESCO validées.
- Si la base source change, le moteur refuse la fusion avec l'inventaire antérieur.
- Aucun programme n'a été exécuté sur `D:` depuis l'environnement de préparation de cet overlay.
