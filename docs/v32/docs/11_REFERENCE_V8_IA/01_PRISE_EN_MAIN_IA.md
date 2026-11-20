# 01 — Prise en main pour une IA nouvelle

## Mission en 90 secondes

EncyKlopedia veut produire, à partir des 88 branches UNESCO et de grands corpus locaux Wikipédia/Wikidata, des **propositions encyclopédiques privées en français** par vagues ChatGPT. Les pages sont découvertes, les relations article/concept sélectionnées, les sources originales proposées à l'IA pour extraction, puis les faits et citations entrent dans un registre SQLite privé. Une admission dans un Kristal est **une opération d'autorité distincte, ultérieure et autorisée**.

L'utilisateur préfère **l'ampleur, la profondeur documentaire, le faible coût de manipulation et la réutilisation des données**, sans supposer une complétude à 100 % ni publier prématurément.

## Mini glossaire des entités

| Terme | Signification | Confusion interdite |
|---|---|---|
| Branche `unesco.mt2.45` | Domaine/microthésaurus UNESCO | ≠ base canonique autonome |
| Concept UNESCO | Entrée thématique, relations plus large/associée | ≠ article Wikipédia |
| QID `Q...` | Identifiant externe Wikidata | ≠ îlot Kristal, ≠ assertion prouvée |
| `enwiki:page_id` | Page Wikipédia anglaise | ≠ QID, ≠ branche |
| `revision_id` + SHA | Texte précis cité dans un pack | ≠ page Wikipédia actuelle |
| `candidate_id` | Relation branche/concept/page à trier | ≠ article unique |
| `SEL_...` | Mission de décision documentaire | ≠ mission d'extraction |
| `ENR_...` | Mission d'extraction sourcée | ≠ publication |
| `proposal_id` | Proposition privée distincte selon identité V32 | ≠ fait scientifiquement confirmé |
| Îlot Kristal | Autorité de connaissance admise | ≠ un espace de branche par défaut |

## Lecture contextuelle : 4 itinéraires rapides

**Produire un retour ChatGPT :** ouvrir le ZIP, lire `INSTRUCTIONS_CHATGPT.md`, `selection_pack.json` ou `enrichment_pack.json`, la liste JSONL, et le Wikitext original. Ne jamais extrapoler depuis l'index V7. Voir chapitre 07.

**Développer le logiciel :** lire les modules réels, la version installée, les contrats de DB, les tests et les limites V8. Préférer adaptateurs et extension additive au remplacement de Skope/Kristalizer. Voir 04, 06, 08, 10.

**Auditer la production :** distinguer paires, pages uniques, propositions nouvelles, erreurs et PARTIAL; ne pas annoncer « branche terminée » après 10 postes vides. Voir 09 et 14.

**Documenter :** mettre à jour un point d'entrée, pas créer un énième README concurrent; conserver une table de preuve et un lien vers le code effectif. Voir 13.

## État du projet au moment de l'overlay

**[CODE VÉRIFIÉ]** Le snapshot de dépôt contient V32.2, `encyk_v32/pipeline.py`, `sql.py`, `sources.py`, et une documentation V7 récente. **[V8 À REQUALIFIER]** Une distribution V8 autonome a été décrite et validée en simulation dans la conversation précédente, mais son ZIP n'est pas inclus dans le snapshot documentaire actuellement reçu. **[JOURNAL]** Les essais historiques Météorologie ont produit des lots et milliers de propositions, mais l'utilisateur a autorisé à recommencer sans leur migration.

**Conséquence :** on documente V8 comme le **workflow retenu** et V32.2 comme le **contrat du code vérifié ici**, en signalant tout point V8 à comparer avec son ZIP dès qu'il est fourni.
