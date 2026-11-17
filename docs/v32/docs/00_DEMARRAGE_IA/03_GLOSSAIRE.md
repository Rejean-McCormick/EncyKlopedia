# Glossaire anti-confusion

| Terme | Sens pour V32 | A ne pas confondre avec |
|---|---|---|
| Branche UNESCO | Microthésaurus `mtX.Y`, espace de regroupement conceptuel; 88 présents | Sujet encyclopédique unique |
| Concept UNESCO | Identifiant `conceptNNN` et URI UNESCO, labels, notes, relations SKOS | QID ou nom d'article |
| Espace Kristal de branche | Dossier `UNESCO_Kristals/branches/unesco-mt…` existant | Kristal encyclopédique de sujet V32 |
| Sujet | Entité ou thème identifiable par QID ou namespace local, lié aux concepts | Un îlot à créer systématiquement |
| Îlot Kristal | Périmètre de connaissance, d’auteur, de stockage ou de gouvernance | QID ou branche UNESCO obligatoire |
| État Kristal | Version/engagement exact de contenu d’un îlot | Vue EncyK recalculable |
| Proposition EncyK | Assertion candidate sourcée et contextualisée, encore provisoire | Assertion admise dans un îlot |
| Reçu d’admission | Trace liant décision/politique, état attendu et nouvel état réellement observé | Simple accusé de retour ZIP |
| QID | Identifiant d'entité Wikidata `Q…` | Titre Wikipédia, clé de propriété `P…` |
| P3916 | Propriété Wikidata indiquant un identifiant thésaurus UNESCO | Garantie d'alignement sémantique approuvé |
| Sitelink | Association Wikidata QID ↔ page d'un projet Wikimedia | Preuve de pertinence pour une branche |
| `wiki_qid` | Index local `page_id→qid` extrait de `page_props.wikibase_item` | Représentation de toutes les déclarations Wikidata |
| P31 / P279 | Instance de / sous-classe de; sens des arêtes crucial | Synonymes ou recherche plein texte |
| Candidat | Proposition de relation (concept, sujet, page) avec route de découverte | APPROVE / vérité établie |
| Route de découverte | Chemin, propriété, direction et ancre expliquant pourquoi on propose | Citation textuelle qui soutient un fait |
| SELECT | Décision de pertinence V32, concept/page donné | Import APPROVE v28 historique ou publication |
| HOLD | Besoin d'une autre preuve/lecture; ne bloque pas toute la branche | Rejet automatique |
| Assertion contextualisée | Connaissance typée, conditions et preuves, avec autorité dans un îlot après admission | Proposition provisoire EncyK ou vérité absolue |
| Couverture | Proportion d'un **stock connu** traité | Rappel sur toute l'encyclopédie mondiale |
| Index compact Wikidata | Index de découverte, entités et arêtes agrégées | JSON lossless et preuves complètes |
| Index XML v21 | Offsets pour récupérer une révision Wikipédia source | Même chose que base SQL `wiki_pages` |
| Centre de production | Interface v30 de packs historiques | Futur manager V32 complet |
| Médiathèque | Préservation et gestion des sources | Autorité sémantique des Kristals |
| Kristalizer | Outil/écosystème sémantique externe hors modification | Une partie à embarquer dans le méga-repo |
