# Plan de consolidation du méga-repo — V32.1

**[CIBLE]** Le nouveau produit absorbera progressivement les fonctions des anciennes interfaces, pas leurs données propriétaires. Ne pas toucher à **Skope ni Kristalizer**. Garder l'index Wikipédia, Wikidata et UNESCO à leurs emplacements; aucun transfert de 125 Go ni réindexation totale.

## Décision sur l'archivage

**Archiver les anciens outils devenus redondants après remplacement constaté; préserver les îlots et états Kristal existants.** Les 100+ îlots évoqués dans le rapport sont un patrimoine à lire/fédérer, pas à effacer ou convertir en bloc. Le pilote `mt1.10` reste facultatif et peut être archivé. Les namespaces, références et droits ne sont pas centralisés artificiellement.

## Phases d'exécution : A–E

Voir la [spécification détaillée](../09_FEDERATION_KRISTAL/07_LOTS_A_E.md). **A** inventaire + lecture fédérée, **B** acquisition deux passes + propositions, **C** une admission vraie/qualifiée Education puis Soil, **D** snapshots et Kompiler, **E** campagne mesurée puis extension aux 87 branches.

### Valeur du manager dès le début

Construire le `EncyKlopedia.pyw` racine et sa file durable **pendant A/B** : une GUI unique consultable et opérable, pas cinq nouvelles apps ni un gros programme graphique uniquement à la fin. Adapter les fonctions V25/V27/V28/V30/31 utiles plutôt que les copier sans nécessité. Les nouveaux ports d'auteur seront désactivés tant que leur API n'est pas confirmée.

## Registre de migration fonctionnalité par fonctionnalité

Pour chaque ancienne app : fonction utile, propriétaire des données, adaptateur actuel, nouveau module, scénario validé, statut de dépendance, décision d'archivage. Cela remplace tout formulaire pesant de fichiers. Conserver l'historique Git ou une archive consultable et ne pas archiver une dépendance partagée en production.

## Sources et priorité des mesures

- Mesurer la jointure P3916 → QID → `wiki_qid` sur D:, par branche, sans scanner les XML entiers.
- Mesurer les propriétés/index Wikidata rentables et leurs faux positifs avant expansion massive.
- Relire les contrats Framework/Kit/Pack/Manager/Kompiler décrits dans le rapport utilisateur du 16 novembre; ils ne sont pas tous inclus dans le SmartDump étudié.
- Démarrer une petite sélection puis un enrichissement **substantiel** et éprouver les reprises; les propositions sont exploitables immédiatement en mode exploratoire.
- N'activer l'admission d'îlots qu'après démonstration sur un état réel dans un environnement contrôlé.

## Non-objectifs

Aucune vérification globale à 100 % de Wikipédia, aucun audit exhaustif de tous les îlots avant lecture, aucun nouveau canon EncyK, aucune fusion de namespaces, aucun microservice ou graphe spécialisé sans mesure, aucune triple revue par défaut, aucun manifeste obligatoire pour chaque déplacement.
