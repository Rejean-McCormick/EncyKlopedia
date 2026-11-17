# Wikidata local et contrat d'intégration de Skope (hors périmètre de modification)

## Ce qui existe [OBSERVÉ CODE]

Le projet **Skope** est explicitement un explorateur de l'index compact Wikidata global d'EncyK, **en lecture seule**. Il n'a pas besoin d'une seconde ingestion. `Skope/skope/db.py` propose `connect(path)`, `meta(conn)`, `node(conn,qid,lang)`, `find(conn,text,limit)`, `neighbors(conn,qid,direction,pids)` et `induced_edges(conn,selected)`.

Schéma nécessaire dans l'index : tables `entity`, `name`, `entity_edge`, `meta`. `Skope/skope/db.py` vérifie une métadonnée `complete` et que l'index n'est pas annoncé comme *lossless*. Les noms sont cherchés via `idx_name_norm`, les QID via l'identité entière interne de l'index.

L'implémentation d'identifiant utilise `QID → int(QID[1:])`, tandis que les P/L ont des offsets numériques internes. `entity_edge` expose `subject_id`, `property_id`, `target_id`, `best_rank`, `statement_count`; **les `statement_id`, références et qualifiers ne sont pas disponibles dans ce compact**. Le graphe est donc parfait pour *découvrir*, mais pas pour *citer*.

`Skope/skope/extraction.py` sait récupérer les enregistrements Wikidata originaux complets via un mécanisme de localisation rapide; les résultats préservent labels, aliases, claims, qualifiers, references et sitelinks. Cette extraction ciblée intervient **après la sélection**. `Skope/skope/cli.py` expose `meta`, `preview`, `export`, `serve` et des opérations de portfolio.

## Politique d'accès V32 [CIBLE]

**Ne pas toucher au dépôt Skope.** EncyK offre un `WikidataGraphPort` et un `WikidataFullEntityPort` qui appellent une interface stable de Skope ou utilisent en lecture seule le schéma connu. Si une fonctionnalité d'API manque, créer l'adaptateur **dans EncyK**, sans changer Skope.

La connexion à l'index `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite` sert aux opérations bon marché QID→voisins. Ne pas scanner ni trier les 121 millions d'entités pour des QID connus. Pour la sélection du graphe : requêtes `WHERE target_id=? AND property_id=?` (relations entrantes) ou `WHERE subject_id=? AND property_id=?` (sortantes), avec budgets, pagination et curseurs.

### Exemples conceptuels

```
Concept UNESCO « universités » → QID candidate de classe
     P31 entrant → institutions particulières
     P279 entrant → classes universitaires plus spécifiques
     QID de chaque institution → wiki_qid → page_id Wikipédia
```

Pour « droit à l'éducation », la même règle P31 entrant peut ne pas produire d'entités utiles; la politique doit être **par type de concept**, avec une autre combinaison de propriétés et un fallback Wikipédia. **Ne pas confondre voisin du graphe et instance d'une classe.**

## Deux niveaux de matériau Wikidata

| Niveau | Contenu | Utilisation |
|---|---|---|
| Compact `entity/name/entity_edge` | Labels, alias indexés, voisins et relations agrégées | Découverte, priorisation, explication de route |
| Extraction lossless originale | JSON QID, claims/qualifiers/references, sitelinks | Enrichissement structuré, provenance précise, contradictions |

Les `derived/wikidata-full-facts-index.json` de `UNESCO_Kristals` sont des **prévisualisations de faits** pour 4 288 QID uniques du pilote de 4 289. Ils ne remplacent pas les déclarations originales de Wikidata et n'ont pas le statut de faits Kristal approuvés.

## Limites et performances

- Une relation `entity_edge` peut être un indice faible et très connecté; éviter de parcourir des propriétés « génériques » sans mesurer le rendement.
- Ne jamais déclencher une extraction lossless mondiale avant de savoir quels sujets méritent un Kristal.
- Mesurer la couverture réelle QID→enwiki sur D:; la présence d'un QID UNESCO dans le mapping ne garantit ni son existence dans l'index du jour ni une page anglaise.
- Lorsqu'un index externe est indisponible, continuer depuis les candidats et fichiers déjà matérialisés, plutôt que bloquer tous les autres jobs.
