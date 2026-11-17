# Plan de réalisation V32.1 : cinq lots, zéro big bang

**Cadence décidée en V32.2 :** la grande boucle de production est **B : sélectionner/extraiter/cumuler en privé**. La préparation des lots de promotion et leur admission via le **lot C** se déclenchent ultérieurement **par vague ou branche mûre**, sans arrêter B; le lot C doit être démontré tôt sur une copie, pas repoussé jusqu’à la fin des 87 branches. Voir [le workflow cible](09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md).

**Objectif** : un seul manager local `.pyw` et le maximum de réemploi, sans déplacer les index géants ni déplacer Skope/Kristalizer. Laisser intact le patrimoine Kristal, puis monter en charge. Les lots sont des **tranches verticales**, pas des chantiers de réécriture complète à terminer avant tout résultat.

| Lot | Résultat concret | Critère de démonstration | Hors périmètre |
|---|---|---|---|
| **A — Inventaire + lecture** | Catalogue d'îlots dédupliqué, recherche par branche/sujet, ouverture d'états, capabilities | Education et Soil lisibles; Accounting identifié avec limitations; état manquant signalé sans bloquer l'app | Pas de migration de 100+ îlots, pas de canon EncyK |
| **B — Production + propositions** | UNESCO/P3916 + graphe + `wiki_qid`, deux passes ChatGPT, sortie provisoire sourcée, dix lanes existantes adaptées | Rejouer lot sans doublon; sujet multibranche réutilise acquisition; erreur de ligne isolée; volume de propositions mesuré | Pas d'import canonique forcé; pas de qualification complète de tout Wikipédia |
| **C — Admission qualifiée** | Adaptateur à l'opération réellement supportée par Kit, politique, état attendu, reçu, reprise | 1 admission Education, puis Soil; crash avant/après écriture; conflit de version détecté; zéro duplication | Pas d'API d'import générique inventée; pas de migration exhaustive |
| **D — Fédération + Kompiler** | Snapshot parent à enfants épinglés, lecteur exploratoire/admis, contexte sous budget | Après changement enfant, ancien snapshot stable; permissions/omissions visibles; pas d'auto-citation | Pas de nouveau moteur graphe spécialisé |
| **E — Campagne mesurée** | Production extensible sur 3 modèles, 87 branches ensuite, budgets et gain utile | Acquisition/extraction/admissions/coûts mesurés; tests de questions avant/après; limites de performance connues | Pas de promesse 100 %, ni hausse aveugle d'agents ou de dépenses |

## Ordre et dépendances réelles

Le lot **B peut fonctionner pour la consultation exploratoire sans admission du lot C**. Le lot D dépend d'une lecture d'états qualifiée, mais peut commencer avec des états historiques. Le manager racine et sa file durable sont construits **dès A/B**, pas ajoutés à la toute fin. Le lot C ne bloque pas la production provisoire à haut débit; il bloque uniquement les **écritures dans les états admis** tant que le chemin d'auteur n'est pas qualifié.

## Premier essai vertical

- Lire l'inventaire existant et ouvrir deux îlots réels sans les modifier.
- Sur une branche UNESCO **autre que `mt1.10`**, mesurer la jointure P3916→QID→`wiki_qid` sur D:, statut ambigu compris.
- Faire 1 petit lot de sélection et 1 lot d'enrichissement **substantiel**, produire les propositions provisoires et les visualiser.
- Tester une source absente, un retour ZIP répété, une reprise après fermeture, puis une branche supplémentaire avec sujet partagé.
- Sur Education, tenter une seule admission dans un environnement contrôlé si le chemin du Kit est vérifié; sinon la reporter explicitement sans bloquer la production exploratoire.

## Profil de campagne et décision d'accélération

Le nombre de conversations occupées ne mesure pas la réussite. Suivre : articles/révisions acquis et réutilisés, propositions nouvelles et exploitables par branche, taux de sélection, pertinence d'un échantillon, erreurs/réparations, duplication, coûts de reprise, **états effectivement admis** et qualité de lecture. Les seuils sont **fixés à partir du pilote avant** l'extension, pas après pour fabriquer un résultat.

Budget et priorité : `manque × utilité × nouveauté attendue / coût marginal`, comme heuristique de planification transparente, avec une part d'effort réservée aux branches moins documentées. Ne pas sacrifier les qualifications importantes (dates, méthodes, négations) pour augmenter artificiellement le nombre de claims.

## Archivage

Archiver **les anciennes interfaces et scripts redondants** après que leurs fonctions soient utilisées et remplacées; ne pas archiver ni convertir en masse les îlots comme préalable. Sauvegarder les décisions et propositions historiquement utiles. Préserver les états exacts et noms d'espace. Skope/Kristalizer exclus de toute modification.
