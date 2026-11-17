# Chaîne structurante : UNESCO → Wikidata → Wikipédia

## Principe : réutiliser une jointure d'identités existante

```
UNESCO URI / concept_id ── identifiant P3916 ──> QID Wikidata
           │                                       │
  SKOS broader/narrower/related            propriété/voisin QID
           │                                       │
           └────── route de candidature ───────────┤
                                                   │
                 wiki_qid (page_props.wikibase_item)
                                                   │
                      wiki_pages.page_id (ns=0, enwiki)
                                                   │
             XML page → révision → texte/intégration
```

La vraie correspondance **QID ↔ article EN** est déjà indexée localement. `mediatheque-references/tools/wiki/dump_import/import_dumps.py` lit les propriétés `wikibase_item` de `page_props` dans `wiki_qid(page_id,qid)`; `catalogue_global_v25.source_by_qid` effectue `wiki_qid q JOIN wiki_pages p ON p.page_id=q.page_id WHERE q.qid=? AND p.ns=0`. Le titre ne sert ni de clé d'identité ni de synonyme pour le concept.

Le QID **ancre** un sujet; les graphes Wikidata `P31`, `P279` ou autres relations indexées servent à proposer **d'autres** sujets. Pour chaque relation, il faut conserver sa propriété, son sens, son point de départ et son niveau d'éloignement : la transitivité de *sous-classe* et *instance de* ne s'applique pas indifféremment à toutes les notions UNESCO.

## Chaîne de données disponible

| Liaison | Source observée | Nature | Force |
|---|---|---|---|
| UNESCO concept → QID | `derived/wikidata-p3916-candidates.json` de chaque branche | Candidat P3916, unique/ambigu/absent | Forte pour découverte, **non certifiée** |
| Concept → concept | `canon/domain/unesco-source.json` (relations `broader/narrower/related`) | Relations de thésaurus SKOS importées | Structure conceptuelle, pas pertinence de page |
| QID → voisins Wikidata | `Skope/skope/db.py`, `entity_edge` | Relation agrégée, rang/compte | Découverte structurée, pas référence originale |
| QID → enwiki page | `wiki_qid` + `wiki_pages` | Jonction indexée explicite | Identité Wikimedia du sujet/page dans le snapshot |
| enwiki page → révision/texte | Index SQL + index XML v21 + XML local | Source documentaire du pack | Matériau pour enrichissement et citations |

## Critères de jointure V32 [CIBLE]

- Préférer correspondance **exacte d'identifiant** aux recherches lexicales. Un QID valide doit être joint au `page_id` local et une page `ns=0` non redirigée lorsque le cas d'usage demande du contenu.
- Un QID sans `enwiki` reste un **sujet Wikidata** potentiellement utile; pas de faux article inventé. Il peut être documenté par Wikidata seulement ou mis en liste « autre langue / sans texte EN ».
- Plusieurs concepts UNESCO peuvent pointer vers le même QID; un QID peut être voisin de nombreux concepts. **Déduplication au niveau du sujet, décision au niveau du couple sujet–concept.**
- Une page Wikipédia peut manquer dans le snapshot ou changer de QID après mise à jour; indiquer la génération source et permettre le recalcul de la jointure.
- Mappings ambigus P3916 : garder les QID alternatifs séparés avec `review_needed`, ne choisir aucun gagnant silencieux.

## Exemple abstrait de requête indexée (non exécutée sur D:)

```sql
SELECT q.qid, p.page_id, p.title, p.latest_revision, p.redirect
FROM wiki_qid AS q
JOIN wiki_pages AS p ON p.page_id = q.page_id
WHERE q.qid = ? AND p.ns = 0
LIMIT 20;
```

La requête doit utiliser l'index `idx_wiki_qid_qid` sur le vrai corpus. Elle ne parcourt pas l'ensemble de `wiki_pages`. Les adresses et index réels sont dans [Chemins et SQLite](04_CHEMINS_ET_SQLITE.md).

## Ce que cette chaîne **ne** donne pas automatiquement

- Une preuve qu'une page voisine traite substantiellement un concept UNESCO.
- Une classification complète de l'encyclopédie Wikipédia mondiale.
- Le JSON original lossless de Wikidata (l'index compact agrège les arêtes).
- Une connaissance Kristal acceptée; l'IA doit d'abord sélectionner la pertinence, puis structurer le contenu de l'article.
