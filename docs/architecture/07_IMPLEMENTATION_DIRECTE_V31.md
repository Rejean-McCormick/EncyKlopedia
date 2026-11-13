# Architecture EncyKlopedia V31 — État du développement direct

**Version :** 13 novembre 2026, révision implémentation 1.

## 1. Réalisation intégrée au moteur v30

- `poste_chatgpt_v30.py` produit désormais des packs v28 de **300 candidats cibles** (nombre variable selon la densité des preuves), en sélectionnant 75 % de bonnes priorités et 25 % d'échantillonnage stratifié parmi les candidats restants. Il conserve les états des tâches figées et le CSV source natif du moteur v28 ; aucune transformation des preuves n'est permise.
- `priorisation_native_v31.py` score chaque couple article–concept d'après le titre, le nombre de liens et de sources ; il réutilise le cache multibranche lorsqu'il est disponible. La faible priorité **ne constitue jamais** un rejet.
- `qualification_globale_v31.py` inventorie toutes les pages Wikipédia ns=0 sans exclusion, traite les redirections comme des pages distinctes, conserve des profils même sans branche et propose plusieurs branches si les manifestes V25 existent. Il utilise les tables déjà présentes `wiki_pages`, `wiki_categorylinks`, `wiki_pagelinks`, `wiki_linktargets` et `wiki_qid`. Les cibles des liens ne sont pas traitées comme des `page_id` : résolution via `wiki_linktargets`.
- `preuves_xml_v31.py` balaie le dump décompressé une fois pour les pages déjà candidates et crée un cache d'extraits avec révision et empreinte. `contexte_revue_unesco_v28.py` exploite ce cache lorsque les offsets v21 ne correspondent pas au XML, mais confirme encore la signature, la révision et les hachages avant de présenter les passages.
- `statistiques_globales_v31.py` produit des statistiques globales HTML/JSON, y compris l'inventaire, les branches candidates, le catalogue et Kristal privé ; les résultats v30 sont préservés comme historique distinct.

## 2. Autonomie et étapes nécessaires à l'exploitation

**Installation :** `INSTALLER_MAJ_FINALE_V31.ps1` intègre le code immédiatement (sans mode observation, ni rollback applicatif ajouté). Les scripts existants sont seulement remplacés si les empreintes source coïncident avec la copie auditée. Redémarrer la station v30 afin que son processus charge la nouvelle version.

**Traitement global :** lancer `LANCER_QUALIFICATION_GLOBALE_V31.ps1 -Tout` pour classifier les articles présents dans l'index sans exporter leurs contenus vers ChatGPT. Le traitement est incrémental et reprenable ; une nouvelle branche peut être ajoutée ultérieurement, les profils seront recalculés à partir des indices conservés sans reparcourir l’index source. La valeur de `-Branches` doit désigner les manifestes officiels des branches à classer.

**Preuves XML :** `PREPARER_PREUVES_XML_V31.ps1` construit le cache des candidats v28 ; les bundles enrichis nouveaux sont générés depuis ce cache sans altération des ZIP historiques.

**Statistiques :** `GENERER_STATS_GLOBALES_V31.ps1` relève les compteurs et construit le tableau de bord.

## 3. Frontières constatées

La découverte et la station v28 issues des sources ciblées restent centrées sur le manifeste de la branche mt1.10 : **la classification universelle V31 est multibranche mais le cycle de revue native n'est pas encore généralisé à toutes les découvertes de branches**. Les autres branches sont proposées sous forme de profils/associations, sans les déclarer approuvées ni importer de nouvelles affectations. Pour les nouvelles branches, il faut disposer des manifestes et des travaux de découverte correspondants.

Le diagnostic local ne prouve pas la présence d'un index global des phrases/paragraphes ; la récupération ciblée d'extraits ne prétend pas en créer un. Le contenu XML peut être long à parcourir. Les statistiques ne doivent jamais confondre la proportion des pages inventoriées et la fin d'une branche.

## 4. Validation effectuée

Les tests V31 utilisent des bases SQLite et un XML synthétiques pour contrôler : reprise idempotente, absence de suppression des pages sans branche, redirections, QID, liens résolus, stabilité du fichier source, 300 candidats natifs par lot, non-duplication, extraits/révisions/hachages et statistiques non inventées. L'exécution sur les données Windows n'a pas été simulée.
