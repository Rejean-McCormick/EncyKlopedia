# UNESCO Factory — chemins après déplacement vers EncyKlopedia

Overlay uniquement de chemins; `factory_core.py` et les importateurs canoniques restent inchangés.

La racine de cette Factory est désormais :

`C:\mycode\EncyKlopedia\Kristal_UNESCO_Factory`

L'interface GUI détecte la racine à partir de son emplacement physique (ou `KRISTAL_ROOT`). Par défaut, elle recherche la source UNESCO en priorité sous `D:\EncyKlopedia\10_sources\unesco`, puis dans `C:\mycode\EncyKlopedia\Sources`, puis dans l'ancien `C:\mycode\Kristal\Sources` **uniquement si une copie y existe encore**. Le RDF de LinkedDataHub, daté 2025, **n'est jamais choisi automatiquement** pour remplacer la source plus récente du RUN.

Les sorties futures sont proposées sous :

`D:\EncyKlopedia\90_runtime\unesco\factory`

Les anciens RUNs et le Kristal actif ne sont pas déplacés. Ce correctif n'exécute ni la Factory ni Kristalizer et ne génère aucune nouvelle assertion. L'environnement Python privé `\.venv` reste recréable sous le nouveau répertoire si nécessaire.
