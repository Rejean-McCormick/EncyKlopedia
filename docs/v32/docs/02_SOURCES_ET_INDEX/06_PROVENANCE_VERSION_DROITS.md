# Provenance utile, identité et fiabilité sans cérémonial

## Les quatre identités qui valent la peine d'être conservées

| Objet | Clé stable | Provenance utile |
|---|---|---|
| Concept UNESCO | `concept_id`, avec vocabulaire/source | URI, date de snapshot, langue, notes de portée |
| Entité Wikidata | `QID` | propriété et direction d'un chemin, source compacte ou original complet |
| Page Wikipédia | `wiki`, `page_id` | `revision_id`, titre de la révision, extrait textuel |
| Sujet Kristal V32 | `kristal_id` stable | QID source ou identifiant local, concepts et pages associés |

Le titre/label humain est mutable; le lien de sujet/Kristal dépend d'un identifiant et d'une relation typée. Un article peut être source de plusieurs claims ou sujets sans devoir être stocké plusieurs fois.

## Provenance légère mais vérifiable

Pour **une décision de pertinence** : garder `candidate_id`, relation du concept, page, chemin de découverte (QID/propriété/direction), raison courte de la décision, et si du texte a été lu, la révision.

Pour **un fait extrait** : garder l'énoncé précis, son sujet, la révision, un localisateur (section, passage) et une **citation littérale effectivement présente** dans le texte source. Cette vérification directe est beaucoup plus utile qu'un manifeste SHA de centaines de fichiers auxiliaires.

Pour **un claim Wikidata** : garder QID, propriété, valeur, qualificatifs/références quand présents; si l'on dispose uniquement du graphe compact, déclarer « indice non confirmé » plutôt que fabriquer une source originale.

## Ce que nous abandonnons comme contrainte de développement universelle

- Empreinte obligatoire pour chaque document Markdown, script déplacé, tableau temporaire ou miniature.
- Manifeste de fichiers omniprésent et préconditions cryptographiques bloquant un refactor qui change tout.
- Triple revue systématique de chaque article, réexécution de l'audit mondial à chaque modification.
- Déclaration de saturation à 100 % avant de passer à la branche suivante.

**Garder une vérification au point de valeur** : lors de l'import du retour IA, on compare les IDs/tâche/révision et la source du claim; pour la continuité, on vérifie que le job n'a pas été appliqué déjà. Les anciens validateurs de ZIP/quotes sont des références fonctionnelles; ils pourront être allégés si la nouvelle structure le demande, sans sacrifier l'intégrité minimale du résultat.

## Publication future et droits

Le système cible reste **privé**, sans admission canonique automatique. UNESCO mentionne `CC BY-SA 3.0 IGO`; Wikipédia inclut des obligations d'attribution/partage pour certains usages, et Wikidata contient notamment des données généralement sous CC0 mais pas nécessairement toutes les couches externes. Conserver la référence/source pour permettre à l'agent de finition de préparer une publication conforme plus tard. Ne pas ralentir toutes les vagues de construction avec la certification complète des droits de publication.
