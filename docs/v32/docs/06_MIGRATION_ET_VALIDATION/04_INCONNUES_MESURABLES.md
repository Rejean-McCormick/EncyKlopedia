# Registre des inconnues : ce qui doit être mesuré sur D: et dans les sources vivantes

**Complément V32.1 :** les API du Framework, Kit, Pack, Arketype, Manager, Kompiler et la qualification d’îlots réels ne sont connues ici qu’à travers le [rapport utilisateur du 16 novembre](../08_REFERENCES/07_RAPPORT_DECISION_20261116.md). Voir [inconnues et sources](../09_FEDERATION_KRISTAL/08_INCONNUES_ET_SOURCES.md) avant de coder les adaptateurs.


**Ne pas déduire de l'existence d'un QID, d'une API ou d'un fichier qu'une jointure est effectivement peuplée.** Les snapshots montrent le code et les données dérivées, mais les bases 125 Go et les pipelines locaux vivants ne sont pas inclus intégralement.

| Question | Connu depuis snapshots | Inconnu aujourd'hui | Mesure minimale |
|---|---|---|---|
| Couverture UNESCO↔QID | 4 289 QID candidats uniques, 134 ambigus, 77 sans mapping; 88 branches | Valeurs modifiées depuis snapshot, qualité des alignements | Compter par branche et statut, ne pas approuver auto |
| Jointure QID→page `enwiki` | Table `wiki_qid`, v25 `source_by_qid` | Combien des 4 289 aboutissent à une page valide | `SELECT` paramétrés par QID, groupés par branche |
| Skope compact | Code `entity`, `name`, `entity_edge`; P31/P279 utilisables | Fraîcheur, densité et propriété réelle de l'index présent sur D: | `PRAGMA user_version`, compte arêtes/propriétés, exemples de QID |
| Wikidata original | Extractions ciblées possibles | Disponibilité, chemin, complétude des claims, références/qualificatifs | Préflight extraction sur 20 QID |
| Wikipédia XML | Résolveur v27 et offsets v21 | Proportion des pages jointes résolubles sur l'index actuel | Test 50 pages multi-longueurs, pages courtes et longues |
| Source UNESCO 2026 | Snapshots 31-08-2026 dans 88 branches | Fichier RDF complet d'origine et version la plus récente | Retrouver source/URI si disponible, ne pas bloquer V32 |
| Relations pertinentes | Code graphe Wikidata et liens SKOS | Précision utile par branche/propriété/sens | Échantillon par chemin, ratio retenu IA |
| Débit du pack IA | v31.8 120 articles/400k mots/60MiB, cas réel 64 articles→305 claims | Débit typique, coût/rejet par article long | 3 formats de lots comparés sur sessions |
| Révision Wikipédia stable | Les packs figent une révision, v27 stocke citation/revision | Révision des pages depuis import | Préserver version lue, ne pas imposer refresh global |
| Multibranche live | Route v31.1 code présent | Combien de branches réellement prêtes, DEFERRED préservés ? | `PENDING=0,DEFERRED>0` en fixture puis sur stock adapté |
| Duplication entre sujets | QID partagés possibles entre concepts et branches | Volume de déduplication réalisable | Ratio `relations total / subject QIDs distincts` |
| Ressources PC | Index imposants sur D: | I/O RAM CPU, coût de deux lectures parallèles | Instrumentation p50/p95 sur requêtes ciblées |

## Séquence d'enquête rapide

1. **`doctor`** (cible) : tester la présence des cinq chemins clés, les schémas attendus et de petites requêtes; ne pas lancer d'indexation.
2. **Joindre 4 289 QID**, en lots de paramètres avec `wiki_qid`, conserver les QID sans page.
3. **Prototyper les traversées pertinentes** pour trois branches contrastées et enregistrer `(concept_id,qid,page_id,path,property,direction)`.
4. **Faire une petite sélection IA** des nouveaux candidats, calculer le ratio réellement intéressant, puis enrichir une tranche.
5. **Ajuster** budgets par chemins, tailles de packs et balance des lanes, sans attendre d'avoir prouvé la saturation complète de Wikipédia.

## Questions de décision qui ne bloquent pas l'analyse

- Traitement des entités avec plusieurs pages de différentes langues : première étape = `enwiki` direct; multilingue reste extension.
- Attribution d'un sujet sans QID : identité provisoire `enwiki:page_id` et lien réconciliable plus tard.
- Niveaux de lien entre concept et Kristal : candidat, sélectionné, à réexaminer; aucune admission canonique.
- Quand archiver les anciennes UI : dès que le manager couvre les cas d'usage réellement fréquents.

Les chiffres d'une campagne doivent être horodatés et rapportés aux sources consultées. Une mesure instantanée de « zéro nouveau » ne constitue pas un certificat de saturation. En revanche, le produit n'a **pas besoin** d'un tel certificat pour ouvrir les 87 branches restantes.
