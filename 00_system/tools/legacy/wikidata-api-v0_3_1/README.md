# Wikidata Relation Explorer — v0.3

## But

Construire progressivement une carte relationnelle Wikidata autour du registre historique, en séparant nettement deux phases :

1. **Niveau 1 / signature** : pour chaque personne résolue vers un QID, conserver uniquement les marqueurs de relation (`P…`) présents au premier niveau. Aucune valeur de claim n'est exportée.
2. **Expansion sélectionnée** : après inspection du catalogue, choisir explicitement les relations à suivre et une profondeur. Les valeurs des seules relations cochées sont alors récupérées pour construire le graphe.

Le launcher Windows `run_relation_signature_pull.pyw` pilote les deux phases.

---

## Correction du crash gzip

La version précédente annonçait `Accept-Encoding: gzip`, mais décodait ensuite directement les octets de la réponse en UTF-8. Certaines réponses Wikimedia arrivent réellement compressées; leur signature commence par `1f 8b`, d'où l'erreur :

```text
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8b ...
```

v0.3 vérifie `Content-Encoding: gzip` **et** la signature binaire gzip avant de décompresser.

---

## Interface `.pyw`

Sous Windows, double-cliquer :

```text
run_relation_signature_pull.pyw
```

### Onglet 1 — Pull niveau 1

- registre JSON;
- `qid-map.json` optionnel pour reprendre une résolution déjà faite;
- dossier `output`;
- pause API;
- limite de personnes;
- taille de l'échantillon d'estimation;
- bouton **Estimer taille N1**;
- bouton **Lancer le pull N1**.

### Estimation avant le pull

**Estimer taille N1** fait un petit échantillon live de Wikidata sans écrire les résultats du pull. Il projette notamment :

- nombre de personnes probablement résolues;
- nombre moyen de relations par objet;
- nombre de propriétés distinctes observées;
- nombre approximatif d'appels API;
- taille approximative du JSONL;
- taille approximative de la matrice CSV;
- taille totale projetée sur disque.

C'est une projection, pas un quota garanti. La densité relationnelle d'une figure antique ou mythologique peut être très différente de celle d'un auteur moderne.

CLI :

```bash
python scripts/pull_wikidata_relation_signatures.py \
  --registry config/intellectuals.seed.snapshot.json \
  --out output \
  --estimate-only \
  --sample-size 12
```

---

## Phase 1 — signature relationnelle

Pull complet :

```bash
python scripts/pull_wikidata_relation_signatures.py \
  --registry config/intellectuals.seed.snapshot.json \
  --out output
```

Avec QID map stabilisé :

```bash
python scripts/pull_wikidata_relation_signatures.py \
  --registry config/intellectuals.seed.snapshot.json \
  --qid-map output/qid-map.json \
  --out output
```

### Sorties N1

- `people.relation-signatures.jsonl`
- `people.relation-presence-matrix.csv`
- `relations.catalog.csv`
- `focus-relations.coverage.csv`
- `qid-map.json`
- `unresolved.jsonl`
- `run-manifest.json`

Le fichier `relations.catalog.csv` contient notamment :

```text
property_id
label_en
label_fr
datatype
relation_class
people_with_relation
coverage_pct
total_statements
```

L'interface charge ce fichier après le pull et affiche chaque marqueur avec une case à cocher.

---

## Tri et sélection des marqueurs

Dans l'onglet **Explorer / étendre** :

- **Trier par popularité** trie selon `people_with_relation`;
- cliquer la case `☐ / ☑` ou double-cliquer une ligne pour sélectionner la relation;
- filtre texte par PID/libellé/classe;
- option pour n'afficher que `semantic_relation`;
- **Sélectionner sémantiques** pour cocher toutes les propriétés item-valued;
- **Tout décocher**.

Les identifiants externes restent visibles dans le catalogue mais ne sont pas confondus avec les relations sémantiques.

---

## Profondeur : objets et marqueurs alternent

La profondeur est volontairement définie comme des niveaux de graphe alternés :

```text
niveau 1 = objets racines (les personnes)
niveau 2 = marqueurs de relation sur ces objets
niveau 3 = objets/valeurs atteints par les relations cochées
niveau 4 = marqueurs de relation présents sur les objets du niveau 3
niveau 5 = objets/valeurs atteints depuis le niveau 3
niveau 6 = leurs marqueurs
...
```

Donc **un objet + un marqueur = 2 niveaux**.

À chaque niveau de marqueurs :

- toutes les propriétés présentes sur les objets visités sont enregistrées dans la signature;
- seules les propriétés cochées dans l'interface sont suivies vers le prochain niveau objet.

---

## Estimation avant expansion

Après avoir coché des relations et choisi le nombre de niveaux, **Estimer sélection** :

- utilise exactement les `statement_count` du pull N1 pour le premier saut;
- interroge un petit échantillon afin d'estimer le taux de cibles uniques et le branchement des niveaux suivants;
- affiche une estimation du nombre d'arêtes, d'objets et de la taille de sortie.

Aucun graphe d'expansion complet n'est écrit pendant cette estimation.

---

## Expansion sélectionnée

Bouton **Étendre sélection** ou CLI :

```bash
python scripts/expand_wikidata_relations.py \
  --qid-map output/qid-map.json \
  --signatures output/people.relation-signatures.jsonl \
  --property P800 \
  --property P135 \
  --levels 5 \
  --out output/expansion
```

Ou avec `output/selected-relations.json` créé par le GUI :

```bash
python scripts/expand_wikidata_relations.py \
  --qid-map output/qid-map.json \
  --signatures output/people.relation-signatures.jsonl \
  --properties-file output/selected-relations.json \
  --levels 5 \
  --out output/expansion
```

### Sorties phase 2

- `output/expansion/graph.nodes.jsonl` — objets/QID visités et labels;
- `output/expansion/graph.edges.jsonl` — arêtes des relations explicitement sélectionnées;
- `output/expansion/node.relation-signatures.jsonl` — marqueurs présents sur tous les objets visités à chaque niveau relation;
- `output/expansion/expansion-manifest.json` — profondeur, relations suivies, taille du graphe.

**Important :** la phase 2 conserve les valeurs des relations explicitement cochées. C'est intentionnel : c'est ce qui permet de découvrir les ouvrages (`P800`), mouvements (`P135`), domaines, lieux, influences, etc. La phase 1 demeure strictement sans valeur.

---

## Exemples de parcours

### Ouvrages

Sélectionner `P800` (`notable work`) avec profondeur 3 :

```text
personne → P800 → ouvrage
```

### Cartographier les propriétés des ouvrages

Même sélection avec profondeur 4 :

```text
personne → P800 → ouvrage → [tous les marqueurs présents sur l'ouvrage]
```

### Expansion récursive d'un même type de relation

Avec profondeur 5, les relations cochées qui existent aussi sur les objets du niveau 3 sont suivies à nouveau.

---

## Tests

```bash
python -m pytest -q
```

Les tests vérifient notamment :

- qu'aucune valeur n'est exportée dans la signature N1;
- qu'une réponse HTTP gzip est correctement décompressée.

## v0.3.1 — rate limiting Wikimedia

Wikimedia applique désormais des limites explicites aux clients API. Cette version :

- respecte `Retry-After` sur HTTP 429 et 503 ;
- applique un backoff exponentiel au lieu de quitter immédiatement ;
- envoie `maxlag=5` sur les appels Action API ;
- décompresse toujours les réponses gzip ;
- utilise une pause par défaut de `0.75 s` (modifiable dans le GUI) ;
- permet de fournir un email ou une URL dans **Contact Wikimedia** afin d'avoir un User-Agent identifiable ;
- ne fait la recherche dans une seconde langue que lorsque la première passe n'a pas résolu le nom ;
- checkpoint `output/qid-map.json` après chaque résolution réussie ;
- réutilise ce QID map lors d'une estimation ou d'une reprise ;
- corrige un bug où `seed_by_key` pouvait être référencé avant son initialisation.

### Estimation avant pull

Le bouton **Estimer taille N1** est un échantillonnage live, pas un scan complet. Par défaut il utilise 6 noms. Les QID trouvés pendant cet échantillon sont maintenant conservés dans `output/qid-map.json`, donc ce travail n'est pas perdu lorsque le pull complet démarre.

Si Wikidata répond `429 Too Many Requests`, l'application affiche par exemple :

```text
[HTTP 429] Wikidata demande de ralentir; pause 20.0s (1/8)
```

Ne relancez pas plusieurs instances en parallèle : laissez le processus reprendre automatiquement.

### Ligne de commande recommandée

```bash
python scripts/pull_wikidata_relation_signatures.py \
  --registry config/intellectuals.seed.snapshot.json \
  --out output \
  --sleep 0.75 \
  --contact "votre-email-ou-URL" \
  --estimate-only \
  --sample-size 6
```

Après l'estimation, le même `output/qid-map.json` peut être utilisé pour le pull complet.
