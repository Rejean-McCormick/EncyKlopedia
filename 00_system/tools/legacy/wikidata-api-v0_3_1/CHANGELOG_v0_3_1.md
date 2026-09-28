# v0.3.1

Correctif de robustesse Wikimedia/API.

- HTTP 429/503 : respect de `Retry-After` et backoff exponentiel.
- `maxlag=5` ajouté à tous les appels Action API.
- pause par défaut portée de 0.10 s à 0.75 s.
- champ GUI « Contact Wikimedia » pour un User-Agent identifiable.
- résolution optimisée : seconde langue seulement en fallback.
- `qid-map.json` checkpointé au fil de la résolution et réutilisé par l'estimation.
- estimation par défaut réduite à 6 entrées.
- correction `seed_by_key` avant le fetch batch final.
- expansion N>1 réutilise la même politique de rate limiting.
- tests : 4 passed.
