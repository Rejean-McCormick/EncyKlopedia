# Mise à jour documentaire V32.2 : cumul privé → promotion différée

**Contenu : documentation uniquement. Aucune migration, aucun changement d’index, aucune écriture Kristal, aucun PowerShell d’archivage.**

Le ZIP reflète les chemins **relatifs à la racine du dépôt V32.2**. Pour la version fournie `EncyKlopedia_V32_2_REPO_CORRIGE_20261116(1).zip`, il suffit d’inspecter les différences puis de copier les fichiers correspondants dans la racine du méga-repo actuel. Ne pas appliquer aveuglément si la documentation locale a changé depuis la V32.2 transmise.

Le fichier principal à lire est `docs/v32/docs/09_FEDERATION_KRISTAL/09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md`. Les 8 autres fichiers modifiés ajoutent des liens et précisent la séparation entre la boucle de production et l’admission par lots.

**Ce qui existe actuellement :** découverte, deux passes, registre privé SQLite, import des retours, historique, fédération en lecture limitée.

**Ce qui reste à implémenter :** consolidation orientée lots, affectation des îlots/profils, export d’admission, écriture par Authoring Kit qualifié, réception, fédération publiée. `admit_proposals()` est volontairement bloqué.

**Périmètre protégé :** Skope, Kristalizer, Médiathèque C:, index D:, `UNESCO_Kristals` vivant et sa série de 440 fichiers `build/v9` supplémentaires. Le changement documentaire ne les modifie pas.
