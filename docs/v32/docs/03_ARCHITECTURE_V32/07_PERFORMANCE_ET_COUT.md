# Performance : obtenir beaucoup de connaissances sans reconstruire les corpus

**V32.1 :** toutes les sorties d’enrichissement décrites ici sont des **propositions EncyK**, consultables en mode exploratoire. Une admission dans un état Kristal est séparée et ne sera activée qu’après qualification de l’auteur; voir [modèle fédéré](../09_FEDERATION_KRISTAL/00_DECISIONS_V321.md).


## Coûts dominants

- **Gros index** : Wikidata compact et Wikipédia SQL dépassent chacun largement 100 Go sur le poste; un scan intégral répété par branche est à proscrire.
- **Lecture XML** : extraire une page entière depuis l'index d'offsets v21 coûte relativement peu; parcourir 110 Go d'XML pour chaque page est absurde.
- **Conversations ChatGPT** : le temps humain de transmission/import et la capacité de traitement par pack sont le facteur de débit; la mise en file de dix missions utiles compte plus que le nombre d'onglets.
- **Mauvais candidats** : faire enrichir une page qui n'a rien à voir avec le concept gaspille un pack; la passe 1 doit maximiser le rendement sans fausse exigence de rappel parfait.
- **Duplication des sujets** : extraire plusieurs fois le même article sous des branches différentes coûte inutilement. Cacher par page/révision et cumuler par sujet/Kristal.

## Chemins rapides

| Opération | Chemin recommandé | Chemin à éviter |
|---|---|---|
| Ancrage | Lire les JSON P3916 2026 une fois, joindre 4 289 QID via index | Relancer WDQS ou la Fabrique mondiale à chaque branche |
| Sitelink EN | `wiki_qid.qid` indexé → `wiki_pages` | Recherche du titre en boucle pour chaque synonyme |
| Voisins Wikidata | `entity_edge` indexé par sujet/cible et propriété | Trier toutes les arêtes du graphe |
| Texte source | `page_id` → offset XML v21 | Scan séquentiel XML par tâche |
| Retour IA | ZIP déjà prêt, validation ciblée, import en transaction | Recomposer/réexaminer tous les jobs passés |
| Statistiques | `COUNT` sur tables de travail, cache de rapport | Recalculer un audit 200k paires en mémoire après chaque clic |

## Packs de travail : pas de quota universel

Les **4 000 candidats UNESCO** et **120 articles Kristal** sont des paramètres de l'ancien flux, non des optimums universels pour V32. Une revue de sélection a des lignes relativement petites, mais les paires riches en notes et extraits coûtent plus de contexte. Un enrichissement a besoin de beaucoup de texte. **Pack selon poids réel en tokens/octets et complexité**, avec valeurs ajustables par mode.

Proposer au moins trois stratégies configurables : `throughput` (beaucoup de sujets distincts), `balanced` (défaut), `deep` (articles exceptionnellement riches). Les prompts demandent de travailler jusqu'à couvrir **toutes les unités assignées**, pas un premier aperçu rapide. Un pack lourd doit être subdivisé en missions **complètes**, pas renvoyé après un échantillon non déclaré.

## Mesures qui servent à décider

1. QID UNESCO couverts par `enwiki` / par branche.
2. Routes de graphe parcourues et candidates nouvelles par propriété.
3. Taux de **SELECT** par strate de route, `REJECT` et `HOLD`.
4. Nombre de sujets Kristal uniques et réutilisations interbranches.
5. Faits nouveaux par article retenu, citations valides, articles laissés sans faits.
6. Temps de cycle préparation → retour → import; temps humain séparé du calcul local.
7. Nombre d'extractions Wikidata lossless et Wikipédia réellement évitées par le dédoublonnage.

**Ne pas retenir comme KPI directeur :** taux de saturation à 100 %, occupation obligatoire 10/10, nombre brut de candidats, nombre de fichiers MD/JSON produits ou longueur artificielle des prompts.
