# Construire les lots : volumétrie réelle, dix postes et débit de connaissances

## Le principe

La **taille d'une mission ne s'évalue pas par son nombre d'items seulement**. Quatre mille candidats avec libellés et un court résumé n'ont pas le même coût qu'un pack de cent longs wikitexts. Le système actuel utilise 120 articles / 400k mots / 60 MiB pour Kristal v31.8 et 4 000 propositions UNESCO; V32 en fait des **valeurs historiques de référence**, pas des contraintes figées.

## Dimensionnement passe 1

Pour les candidats directs P3916 avec un synopsis et une portée UNESCO, le coût d'analyse est léger et un lot peut être grand. Pour les candidats issus de chemins P279 longs ou de plusieurs sous-sections, le contexte est plus lourd et on réduit le nombre de lignes. Ne pas sacrifier la qualité en envoyant 4 000 cas ambigus avec seulement leurs titres.

**Objectif :** les packs contiennent un nombre de lignes que ChatGPT peut traiter complètement, avec contexte suffisamment discriminant et sortie compactée. On préfère 3 000 décisions justifiables à 4 000 décisions de mots-clés hors sujet.

## Dimensionnement passe 2

La source d'enrichissement doit inclure **le texte complet** d'une révision sélectionnée. Un article très long peut obtenir son propre job. Les petits articles peuvent être regroupés. La taille du ZIP compressé ne remplace pas l'estimation du volume décompressé et du volume réel de lecture.

Le modèle de packing peut utiliser : `estimated_input_tokens`, `target_output_tokens`, `article_count`, `total_uncompressed_bytes`, `section_count`, `wikidata_claim_count` et `expected_output_density`. Les limites sont ajustables selon le modèle/mode de la conversation et les résultats observés; aucun seuil magique n'est supposé.

## Répartition des tâches

Un scheduler commun puise dans : `ready_selection`, `ready_enrichment`, `needs_repair`, `deferred_selection` et `on_hold`. Il choisit le prochain paquet utile selon priorité, disponibilité des sources et diversité. Les dix slots ChatGPT sont un **maximum d'interface**, pas une exigence de dix jobs en permanence.

Un article sélectionné par plusieurs concepts doit générer **un enrichissement de sujet**, pas N packs de copies. Le gestionnaire peut privilégier des lots déjà préchargés pour garder une navigation rapide sans relancer les opérations lourdes.

## Validation minimale des retours

- Nombre de `candidate_id` sélection passés / reçus; repérer l'incomplétude et permettre de reprendre uniquement les manquants.
- `subject_key`/`kristal_id` et révision Wikipédia conforme au pack; source citation existante dans le wikitext et suffisamment précise.
- Les items invalides restent **corrigeables individuellement**; éviter le rejet de tout un pack pour un simple champ textuel non critique.
- L'import SQL est idempotent pour qu'une action « Déposer ZIP » répétée n'ajoute pas deux fois les mêmes claims.

## Mesures et réglage par retours réels

À chaque pack, conserver `items_requested`, `items_imported`, `facts_added`, `facts_merged`, `source_bytes`, `response_bytes`, `rejection_reason_count`, `elapsed_human_cycle` (si fiable), `post_import_next_action`. Comparer les modes de packing par *nombre de faits utiles et sourcés par session*, pas par une durée fixe.
