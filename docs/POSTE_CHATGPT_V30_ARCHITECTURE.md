# Centre de production EncyKlopedia v30 — Architecture et contrôles

## Pipeline

```
Index direct XML v21 + catalogue UNESCO v25 (lecture seule)
      ↓ génération locale v27 / découverte locale v28
PACK_V27_*.zip            DECOUVERTE_ARTICLES_RELIES_V28.sqlite
      ↓                         ↓
      └── SQLite v30 : tâche / preuve / état / priorité ──┐
                                                        ↓
                                              dix postes simultanés
                                                        ↓
                                          paquet + prompt par conversation
                                                        ↓
                                  retour ZIP JSON v27 / CSV compact v28
                                                        ↓
                                       vérification, précontrôle, cumul
                                                        ↓
                                     station remplace automatiquement la tâche
```

## Contrôle de non-répétition

- `jobs` : travaux uniques et états durables. Les anciens packs ne sont pas recréés si leur `pack_id` figure dans les imports du Kristal cumulatif.
- `review_index` : une ligne par `candidate_id`. Priorité issue du véritable moteur `decouvrir_articles_relies_v28.py`. Exclusions des rattachés/revus du catalogue, des anciennes revues `HOLD` et des candidats déjà en file.
- Les sources v28 restent **figées** tant qu'une tâche de revue subsiste. La nouvelle découverte peut reprendre lorsque les revues sont terminées ou ignorées.
- Les fichiers de base d'une tâche restent immuables; les résultats courts sont fusionnés avec cette base sans altérer les preuves initiales.
- Les `HOLD` v28 n'ont pas de décision définitive en catalogue; ils sont conservés seulement dans la base v30 (réexamen volontaire possible).

## Import

- ZIP entrant : limite 100 Mo par fichier, 130 Mo décompressé; pas de lien symbolique ni chemin ascendant; extension JSON/CSV uniquement (README TXT/MD toléré). Jamais exécuter de code ZIP.
- Kristal : `pack_id`, `pack_sha256`, drapeaux de publication et SHA source vérifiés, puis appel du véritable moteur v27 `-Action Import`.
- UNESCO : une ligne par candidat recommandée dans le CSV trois colonnes `candidate_id,decision,justification`; les champs sources sont recopiés depuis la base immuable locale, jamais depuis le retour. Le moteur v28 fait `-Action Apply -DryRun`, puis `-Action Apply`.
- Réponses v28 partielles : les lignes manquantes deviennent HOLD **seulement après une confirmation humaine explicite**. Une réponse tout-HOLD demande aussi confirmation. Ceci évite que les réponses interrompues soient considérées automatiquement comme des analyses terminées.
- Erreurs : `ERROR` persiste et le poste n'est pas remplacé. L'opérateur peut corriger le ZIP puis réessayer. Après une interruption d'importation, la tâche reste en erreur jusqu'à reprise; les importeurs en aval restent idempotents.

## Mise à jour logicielle

Les archives de code ne sont pas acceptées dans la zone de retour des connaissances. Une mise à jour logicielle est prévalidée avec manifeste `encyklopedia.safe-overlay.v30/1`, chemins relatifs contrôlés, SHA-256 individuels, `requires_sha256` optionnel pour les fichiers déjà présents, sauvegardes complètes et confirmation manuelle. Une restauration est refusée si un fichier installé a changé depuis, afin de ne pas écraser un travail ultérieur. Un hash dans le ZIP ne certifie ni la provenance ni la sécurité du code.

## Tests de non-régression

`python -m unittest discover -s tests -p 'test_poste_chatgpt_v30.py' -v`

Dépendances : Python 3.11+, `pwsh` pour les moteurs locaux; aucune bibliothèque PyPI requise par le poste.
