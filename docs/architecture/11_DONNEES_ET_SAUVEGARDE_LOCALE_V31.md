# EncyKlopedia — Données durables, chemins et sauvegarde des résultats

**Référence :** ENC-DATA-2026-11-15/1 — d'après les chemins et schémas confirmés dans l'audit du poste Windows.  
**Attention :** ce document est un inventaire, **pas** une procédure de restauration automatique.

## 1. Où résident le code et les résultats ?

- Dépôt **code** : `C:\mycode\EncyKlopedia\EncyKlopedia` ; launcher `LANCER_ENCYKLOPEDIA.cmd`.
- Racine **données** : `D:\EncyKlopedia`.
- Index Wikipédia : `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite` (environ 125,6 milliards d'octets dans l'audit). C'est une **source volumineuse existante, non à sauvegarder** dans les sauvegardes légères de résultats. Les XML décompressés (~110 Go) sont également exclus.

## 2. Bases de résultats essentielles (jeu cohérent)

| Domaine | Chemin relatif à `D:\EncyKlopedia` | Contenu à protéger |
|---|---|---|
| Station | `30_working\poste_chatgpt_v30\station_v30.sqlite` | Tâches/historique, décisions et preuve du suivi, `review_index`, `hold_reexaminations`, mises à jour |
| Kristal privé | `30_working\production_kristals_v27\KRISTAL_CUMULATIF_PRIVE_V27.sqlite` | Faits privés, citations et visites |
| Catalogue UNESCO | `80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite` | Articles et affectations validées provisoirement |
| Découverte UNESCO | `30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite` | Couples, preuves, graines et curseurs (v31.10/v31.11 si installés) |
| File Kristal | `30_working\production_kristals_v27\FILE_PACKS_V27.sqlite` | Visites et empaquetages précédents pour ne pas répéter le travail |

Deux bases **facultatives** observées absentes à la sauvegarde du 15 novembre : `30_working\qualification_multibranche_v31\qualification_multibranche_v31.sqlite` et `30_working\preuves_xml_cibles_v31\PREUVES_XML_CIBLES_V31.sqlite`. Leur absence **ne signifie pas** que la production v27/v28 est vide ni que le résultat a été perdu.

## 3. Qu'est-ce qu'on ne sauvegarde pas dans la sauvegarde légère ?

Les packs ZIP d'entrée, les ZIP de retour ChatGPT, les JSON/CSV intermédiaires, le code, les caches dérivés volumineux, les XML décompressés et la grosse base source Wikipédia. **Ce choix protège les résultats**, pas la possibilité de reconstruire chaque artefact documentaire original hors du contenu persistant des bases. La politique de rétention et de conservation séparée des ZIP sources doit être définie distinctement si une preuve hors base doit rester accessible longtemps.

## 4. Procédure recommandée et limites

1. Arrêter complètement station, producteurs et importateurs. Un simple état d'interface « 0/10 » n'implique pas forcément la fermeture du processus.
2. Exécuter **l'outil de sauvegarde des résultats v3** (mode 1), dans un dossier séparé ; garder destination hors de `D:\EncyKlopedia` et, idéalement, recopier sur un autre disque.
3. L'outil utilise l'API de sauvegarde SQLite et vérifie **5 bases**, le SHA-256 et `PRAGMA quick_check`; il produit un manifeste et un dossier `ENCYK_RESULTATS_...` seulement si tous les contrôles passent.
4. Ne jamais considérer un dossier `_INCOMPLETE_...` comme une sauvegarde validée. Ne jamais copier manuellement une seule base pendant qu'un WAL/SHM reste actif.
5. Pour la restauration : travailler d'abord sur **un clone isolé**, utiliser exactement les chemins du manifeste de sauvegarde, contrôler cohérence inter-bases et état des importations ; ne pas remplacer à chaud les SQLite de production. **La procédure de restauration v3 n'a pas été validée de bout en bout sur la station Windows** dans les sources disponibles.

La dernière sauvegarde **confirmée par l'utilisateur** dans cette conversation a validé 5 bases et 340 918 272 octets, mais elle **précède** les nouvelles connaissances produites ensuite. La date exacte et la validité du dernier backup doivent être vérifiées localement.

## 5. Autorité, duplication et persistance

- `station_v30.sqlite` : états des tâches et `review_index`. Ne pas réinitialiser pour « débloquer dix postes ».
- `DECOUVERTE_ARTICLES_RELIES_V28.sqlite` : candidats avec preuve de découverte. `candidate_pairs` représente un **stock historique**, pas le nombre de lignes encore prêtes à réviser.
- `catalogue_global...v25.sqlite` : affectations après import ; ne pas les inférer à partir de la seule existence d'une paire découverte.
- `FILE_PACKS_V27.sqlite` : `PACKED` signifie empaqueté, pas nécessairement importé. Lire également les visites/claims du magasin privé.
- Les bases sont lues séparément dans les diagnostics : les totaux peuvent diverger temporairement pendant un import. Seuls une suspension des écritures ou un protocole coordonné donnent une photographie cohérente.

Voir aussi [guide opérationnel](10_GUIDE_OPERATIONNEL_LOCAL_V31.md) et [diagnostic](12_DIAGNOSTIC_COUVERTURE_ET_GOULOTS_V31.md).
