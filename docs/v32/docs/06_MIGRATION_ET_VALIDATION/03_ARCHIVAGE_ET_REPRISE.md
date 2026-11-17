# Registre d'archivage — dépôt par dépôt et propriété des données

**[CIBLE]** L'archivage est effectué après adoption des remplacements, jamais pendant la documentation. On conserve le code historique pour retracer les interfaces utiles. Le futur mega-repo absorbe les fonctions **du domaine EncyK**, pas les référentiels ni outils explicitement exclus.

| Ensemble existant | Destination souhaitée | Décision et conditions |
|---|---|---|
| `EncyKlopedia` actuel | **Base du mega-repo**, historique V31 sous `legacy/` | Reprendre station, v25/v27/v28, lecteur séparé; refondre domaine |
| `UNESCO_Kristals` | Sources/versionnées consultables par registry | Conserver 88 snapshots, branche/concepts/P3916; ne pas fusionner « espace » et « sujet » |
| `Kristal_UNESCO_Factory` | Code des adaptateurs et utilitaires importés puis archive | Garder lecture P3916, index de faits, pipelines utiles |
| `UNESCO_Workbench` | Fonctions de préparation/contrôle en avancé | Préserver provenance RDF, outils de comparaison historique |
| `LinkedDataHub-UNESCO` | Source comparative RDF, archive datée | Ne pas remplacer les 2026 snapshots par la démo 2025 |
| `mediatheque-references` | **Source index Wikipédia partagée** + adaptateur | Vérifier si d'autres outils l'utilisent avant archivage; importer/indices demeurent autoritaires |
| `mediatheque` | **Dépendance partagée externe** | Ne pas en recopier le gestionnaire de sources; brancher des fonctions ciblées si besoin |
| `LevelUpDiag_EncyK` | Diagnostics accessibles depuis le manager | Retenir campagnes utiles, garder fixtures |
| `EncykAudit`, V313/V314 pilotage | Intégrer reporting utile, archiver UI autonome | Corriger comptes connus avant reprise sans réinventer un moteur concurrent |
| `ENCYKLOPEDIA_EXPORT_CHATGPT` | Outil de support/exports ciblés dans `tools/` | Option avancée, jamais obligatoire pour lancer une vague |
| Backup V2/V3, audit goulets | Intégrer sauvegarde légère et diagnostics utiles | V3 préférée; ne pas empaqueter copies de 125 Go |
| `scan_engine`, composants Kristalizer | **EXTERNE : ne pas modifier** | API/CLI contractuelle seulement, pas de copie interne |
| `Skope` | **EXTERNE : ne pas modifier** | Lire index/commandes, pas de fork ni déplacement de code |

Cette liste regroupe des snapshots d'applications et de dossiers, pas nécessairement un dépôt Git par ligne. Le CSV `../07_INVENTAIRES/inventaire_depots.csv` indique les 11 ensembles effectivement inventoriés; l'inclusion d'autres outils dans les archives et le nombre réel de dépôts Git sont à confirmer sur le poste.

## Quand déclarer une fonction « absorbée »

1. L'ancienne fonction est repérée avec ses entrées, sorties et données propriétaires.
2. Une fonction métier V32 réutilise le code ou fournit un adaptateur compatible.
3. Le parcours correspondant fonctionne dans le mega-repo : exécution, retour ZIP et reprise s'il s'agit de production.
4. Les résultats persistants sont consultables, ou une archive/export de consultation est disponible.
5. On consigne dans le registre la destination et la raison de l'archivage.

Pas d'obligation de calculer un hash de chaque fichier migré, ni de faire signer un manifeste. La fonctionnalité et l'état importé sont les vrais critères. Le comportement externe ne doit pas être supprimé sans alternative quand la fonction est encore utile.

## Pilotage de versions pendant la migration

Deux identifiants différents : `schema_version` pour un magasin et `software_version` pour code/UI. Ne pas faire dépendre le démarrage d'une chaîne de contrôle de ZIP historique. Utiliser une migration SQL réversible lorsque la structure évolue; si le schéma V32 est nouveau, le créer à côté des anciennes bases et ne pas forcer leur conversion.

## Destructivité

Le V32 n'a aucune raison de détruire les 21k HOLD de `mt1.10`, ses packs ou son catalogue. Les mettre en archive read-only et ne plus les utiliser comme contraintes de conception. La première branche pourra être reconstruite plus tard par le nouvel orchestrateur si cela devient utile, pas par obligation dès la première livraison.
