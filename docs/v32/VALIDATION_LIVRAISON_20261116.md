# Validation de la livraison unifiée V32.1

Contrôles réalisés dans un environnement Linux de test, **non sur le D: Windows de production**.

| Vérification | Résultat |
|---|---|
| Import des 88 espaces UNESCO fournis | 88 branches, 4 500 concepts, 4 289 QID candidats uniques |
| Candidats ambigus / sans P3916 | 134 / 77, sans alignement inventé |
| Tests nouveaux V32 (bases SQLite synthétiques) | 6 réussis |
| Tests ciblés moteurs historiques v31.8/v31.9/v31.12 | 15 réussis |
| Démarrage Tkinter en affichage virtuel | Réussi |
| Intégrité des index sources réels Windows | Non testée, fichiers non fournis |
| Admission dans un état Kristal v11 | Non autorisée; adaptateur Kit reste à qualifier |
| Suite historique complète (297 tests) | 8 échecs et 7 erreurs, 12 ignorés — versions obsolètes (880 vs 4 000), archives source et binaires externes manquants, et attentes anciennes de station |

Ce rapport n'atteste **ni une couverture encyclopédique totale, ni l'exactitude sémantique des futurs retours ChatGPT**. Le manager n'aspire aucun dump en l'absence de requête explicite et n'exécute aucune admission canonique.

## Récupération du code existant

Les versions des fichiers principaux sont assemblées à partir du snapshot de code fourni et, par ordre chronologique, des overlays v31.8, v31.9, v31.10, v31.11 et v31.12. Les anciens programmes et leurs dépendances sont conservés dans leurs chemins d'origine ou dans `ecosystem/` et `archive/`. Skope et Kristalizer n'ont été ni copiés ni modifiés.

Les archives de certains anciens tests attendaient des fichiers ZIP non présents dans les sources fournies. Aucun fichier factice n'a été fabriqué pour les faire passer.

## Arrêts sûrs

- Base V32 déjà occupée par un autre programme → refus avant création de tables.
- QID non trouvé dans l'index → aucune fausse page associée.
- Contrôle d'index Wikidata déclaré incomplet → refus d'utiliser le graphe.
- Import de retour non rattaché à un `job_id` → refus; pas de décision automatique.
- Citation prétendue non trouvée dans la révision incluse → refus transactionnel.
- Demande d'admission canonique dans un îlot Kristal → refus explicite.

Les choix de rapidité restent : aucun parcours intégral des corpus à chaque lancement, pas de triple vérification rituelle, budgets par vague et deux passes riches.
