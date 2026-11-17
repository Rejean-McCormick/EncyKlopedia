# Cinq objets distincts : sujet, assertion, îlot, état, branche

**Statut : [CIBLE].** Ce document décrit la sémantique V32.1, et non un format natif déjà garanti par le Framework.

| Objet | Identifiant | Qui en détient l'autorité ? | Cardinalité |
|---|---|---|---|
| **Sujet** | `wd:Q...`, identifiant local `namespace:id`, alias justifiés | Catalogue/résolveur d'identité; QID externe reste sous Wikidata | Un sujet peut relever de nombreux concepts et îlots |
| **Assertion contextualisée** | ID stable dans l'espace d'auteur, avec qualifications/conditions | Îlot auteur correspondant | Un îlot possède de nombreuses assertions |
| **Îlot Kristal** | Référence stable + namespace + propriétaire | Autorité propre à l'îlot | Plusieurs sujets possibles par îlot |
| **État** | Référence exacte d'une version/engagement de l'îlot | Écrivain de l'îlot | Un îlot a plusieurs états; snapshot parent pointe des états précis |
| **Branche UNESCO** | Identifiant de taxonomie versionnée | Import du thésaurus/version UNESCO | Une branche contient des concepts; une ressource peut avoir plusieurs liens de branche |

## Règle de granularité

**Ne pas créer automatiquement de Kristal à chaque QID.** Un QID direct P3916 ou issu du graphe devient d'abord un sujet/candidat. Un îlot autonome est justifié par un domaine d'auteur, un modèle, des permissions, un volume ou un cycle de vie propre. Des îlots monothématiques existants restent parfaitement valides.

- Une branche UNESCO est un **axe de navigation**, pas un conteneur d'autorité exclusif.
- Un sujet peut figurer dans deux îlots qui expliquent des aspects **différents**. Les faits ne doivent pas être écrasés par déduplication globale.
- Une assertion factuelle ne se réduit pas systématiquement à `(sujet, prédicat, objet)` : temporalité, méthode de mesure, qualification, incertitude et contexte appartiennent au modèle métier.
- Les chemins de fichiers physiques ne sont pas des identités. Des copies historiques du même workspace ne constituent pas plusieurs îlots.

## Identité versus pertinence

`UNESCO concept` -- P3916 candidat --> `Wikidata QID` -- `wiki_qid` --> `enwiki page_id` est une **chaîne d'identifiants et de pistes de découverte**. Elle ne prouve ni l'équivalence sémantique universelle, ni la pertinence substantielle de tout article relié.

Conserver pour chaque alignement son origine, méthode, statut (`candidate`, `ambiguous`, `accepted`...), preuve et version de thésaurus. Une valeur « exactMatch » dans un crosswalk candidat n'est pas ipso facto une équivalence validée. Les règles de mapping exact propres au Framework, si adoptées, s'appliquent seulement dans leur périmètre qualifié.

## Réseau en quatre couches

1. **Navigation** : branche–concept–sujet–îlot (couverture/UX).
2. **Identité** : crosswalks, QID, sitelinks, alias et statuts.
3. **Connaissance** : relations typées *admises*, conditions et preuves dans leurs îlots propriétaires.
4. **Suggestion** : liens Wikidata/lexicaux/exploratoires, scores et hypothèses; jamais automatiquement des faits.

**Exemple :** un QID d'université peut être rattaché à plusieurs thèmes UNESCO; ses données administratives et ses programmes de formation peuvent relever de deux îlots de domaine. Un seul QID, zéro ou plusieurs îlots autonomes selon les responsabilités — et non une duplication imposée par chaque branche.
