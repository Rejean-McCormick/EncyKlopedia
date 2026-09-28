# Plan de benchmark

## Pourquoi benchmarker

Les claims « plus rigoureux », « plus exact », « moins cher » ou « meilleur en traduction » doivent être mesurés si on veut les utiliser publiquement comme comparaisons.

## Benchmark 1 — Fidélité aux sources

Échantillon : 50 questions difficiles.

Comparer :

- chatbot générique sans corpus ;
- chatbot avec retrieval sur pages brutes ;
- chatbot au-dessus du corpus structuré.

Mesures :

- assertions supportées ;
- erreurs factuelles ;
- confusion de statut doctrinal ;
- citations correctes ;
- refus appropriés.

## Benchmark 2 — Reproductibilité

Mesurer :

- stabilité des résultats déterministes ;
- capacité à reconstruire l'état ;
- différences entre modèles de chatbot.

## Benchmark 3 — Coût

Mesurer séparément :

- stockage du corpus ;
- indexation ;
- coût par requête ;
- coût d'un modèle local ;
- coût d'un fournisseur commercial.

## Benchmark 4 — Multilingue

Construire un petit gold set latin/français/anglais/espagnol sur des termes sensibles.

Évaluer :

- fidélité conceptuelle ;
- conservation des distinctions doctrinales ;
- stabilité terminologique ;
- traçabilité traduction → assertion source.

## Politique de claims

Avant benchmark : parler d'**avantages architecturaux**.

Après benchmark : publier les comparaisons mesurées, avec protocole et limites.
