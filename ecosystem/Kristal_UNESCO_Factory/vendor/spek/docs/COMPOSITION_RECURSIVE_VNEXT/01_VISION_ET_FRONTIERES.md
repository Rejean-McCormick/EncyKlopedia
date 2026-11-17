# 01 — Vision, invariants et responsabilités

**Statut : spécification cible, non implémentée en totalité.**

## Objectif lecteur

Le Wiki donne une lecture suivie et standardisée des structures d'un Kristal : les éléments importants sont visibles, mais le texte ne ressemble pas à une succession artificielle de cartes, de sous-titres et de traces techniques. La régularité des motifs est **intentionnelle** ; il n'y a pas de variation stylistique aléatoire pour masquer leur répétition.

## Invariants non négociables

1. **Une seule composition.** Les templates rhétoriques, documentaires et visuels appartiennent au même moteur et suivent les mêmes règles de type, version, portée, cardinalité et résolution.
2. **Aucun choix factuel dans Spek.** Spek n'inspecte pas les Kristals pour inventer une composition ; la sélection éditoriale et ses liens à la source arrivent explicitement.
3. **Pas de prose créée par Spek.** Les clauses factuelles et leurs réalisations sont produites par SemantiK à partir d'obligations amont. Spek n'ajoute ni synonymes « créatifs », ni inférences, ni nouvelles conclusions.
4. **Répétition ≠ sélection.** `repeat: 3` signifie exactement trois instances fournies/assignées. Elle n'autorise pas Spek à chercher « trois meilleures preuves ».
5. **Hiérarchie logique ≠ style visuel.** Une thèse peut être la première phrase en gras d'un paragraphe, plutôt qu'un `<h2>`. La navigation sémantique et l'accessibilité conservent une hiérarchie réelle.
6. **Chaque feuille est retraçable.** La relation `instance de template → slot → realization_key → CommunicationRequest/Result → obligations et sources` doit être complète et vérifiée.
7. **Aucun fallback trompeur.** Échec SemantiK : pas de phrases fabriquées ni de triplets bruts en guise de texte publié. Le brouillon peut montrer « Texte en attente de réalisation » ; le build publiable refuse.
8. **Compilation déterministe.** À entrées, versions et politiques identiques, même arbre résolu, même séquence de feuilles et même texte (hors champs de build explicitement exclus des comparaisons).
9. **Domaine privé séparé du public.** Empreintes, URN internes, chemins locaux, identifiants de preuve et données brutes ne doivent pas fuiter dans les sorties lecteur, même dans des attributs HTML invisibles.
10. **Aucune publication implicite.** Une compilation réussie, même avec SemantiK, ne contourne jamais Manager / C1-C2-C3 ni la revue de divulgation.

## Qui décide quoi ?

| Étape | Autorité | Données d'entrée | Produit |
| --- | --- | --- | --- |
| Analyse et proposition de composition | IA, hors moteur Spek | Vraies structures des Kristals et contexte Arketype | Registre IA, justifications, sections et templates proposés |
| Sélection des assertions et revue | Gestion éditoriale / Kristal-Manager | État canonique épinglé, permissions, exigences | Faits et obligations explicitement retenus, statut d'approbation |
| Résolution de composition | **Spek** | Définition versionnée + instance explicitement liée + références sélectionnées | Arbre typé déroulé, unités nécessaires et ordre |
| Prescriptions de phrase | **Spek** | Types des feuilles + layout + politique rhétorique + requêtes déjà préparées | Contraintes de communication compatibles avec SemantiK |
| Réalisation linguistique | **SemantiK Architect** | Requêtes et obligations originales, contraintes admissibles, RuntimeSet qualifié | Blocs et phrases traçables, échecs structurés |
| Assemblage/présentation | **Spek** | Arbre résolu et réalisations conformes | HTML/PDF/TeX/Markdown Wiki privé ou candidat contrôlé |
| Autorisation et transport | Manager + mécanisme externe | Artefacts épinglés, revue C1/C2/C3, approbations | Publication explicite ou refus |

## Deux variations, une seule source

- **Variation de structure :** choix d'une recette (`argument-evidence`, `comparison-narrative`), nombre prescrit de preuves, ordre de sections, emphase visuelle.
- **Variation linguistique :** uniquement les formes grammaticales nécessaires pour réaliser le **même** contenu autorisé en français, anglais, italien, etc., dans les contraintes de SemantiK ; pas de variantes gratuites.

Les templates sont standardisés. Le texte peut rester légèrement répétitif ; c'est préférable à l'invention ou à l'imprévisibilité.

## Première livraison ciblée

Priorité à la composition d'un **article Wiki pilote** : une introduction, un argument comprenant trois preuves explicitement associées, une comparaison et une qualification finale, sans répétitions de titres visuels. Les mêmes primitives doivent ensuite servir à d'autres catégories (`report`, `scientific`, `educational`, `book`) sans duplication du moteur.
