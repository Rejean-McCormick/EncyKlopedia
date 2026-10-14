# Skope 0.13.13 — Carte à trois niveaux de connectivité

## Installation
Fermer Skope, décompresser ce ZIP à la racine du dépôt EncyKlopedia existant,
en remplaçant les fichiers du code. Relancer Lancer_Skope.pyw puis Ctrl+F5.
Les chemins du ZIP sont relatifs à la racine du dépôt.

## Utilisation
Calculer le périmètre, puis ouvrir Carte. La carte traite tous les nœuds et
les liens entre nœuds présents dans le rapport (au lieu des 70 premiers nœuds).

- Bleu : réseau dense, peint d’abord en fond (10 voisins ou plus par défaut).
- Vert : réseau intermédiaire (3 à 9 voisins).
- Ambre : réseau peu connecté (0 à 2 voisins), au premier plan.
- Chaque couche a sa case de visibilité, son compteur et un curseur de teinte.
- Curseurs : deux seuils de connectivité, nombre minimum de voisins à afficher,
  opacité du réseau dense, quantité de mots-clés et agrandissement du voisinage.
- Survol d’une entité : loupe nommée. Clic : fixer/libérer. Échap : libérer.
- Le champ Inspecter offre aussi un accès par nom ou QID, sans souris.
- Réinitialiser la vue rétablit les réglages d’affichage.

Les mots-clés sont les libellés des entités les plus connectées, avec priorité
à la racine et évitement des collisions. Ce ne sont pas des thèmes générés par IA.
La loupe redispose le voisinage pour la lecture : jusqu’à 12 voisins visibles,
classés par connectivité, avec noms, QID, nombre de voisins et relations locales.
Le compteur explicite la limite de 12. Sur mobile, elle apparaît au-dessus de la carte.
Les voisins ne sont pas nécessairement des descendants taxonomiques.

## Sens de « densité »
Il s’agit ici du degré local : voisins distincts de chaque entité dans le
rapport, indépendamment du sens et du nombre de propriétés entre deux voisins.
Une boucle d’une entité vers elle-même ne compte pas comme voisin.
Un trait prend la classe de son extrémité la plus connectée. Les traits denses
sont dessinés avant les autres, avec une opacité réglable.
Ce n’est ni une densité géographique ni la densité mathématique d’une communauté.
La disposition radiale est fondée sur une forêt de parcours du graphe ; tous les
liens du rapport dont les deux extrémités sont présentes restent représentés.
Les nœuds déconnectés sont inclus.

Les compteurs de couches portent sur tout le rapport ; le compteur au-dessus
de la carte indique les entités et traits actuellement visibles / disponibles.
Un filtrage masque également les traits dont une extrémité est masquée.
Les filtres restent visuels et ne changent ni la recette, ni le ZIP d’export.
Ils ne sont pas enregistrés entre deux démarrages. Une exploration tronquée
reste partielle ; cette version ne change pas le plafond de collecte.

## Validation réalisée
- Syntaxe JavaScript : app.js et density.js.
- Serveur HTTP local : index, density.js, app.js et style.css servis en HTTP 200.
- Deux tests existants de géographie dans l’interface : réussis.
- Test DOM et Canvas natif sur 10 000 entités et 10 019 relations simulées : réussi.
  Vérifications : comptages complets, voisins uniques, classement et filtres,
  seuils ordonnés, teintes, survol, fixation, Échap, remise à zéro, graphe vide,
  entité isolée, extrémité absente, boucles et immutabilité du rapport.
- Rendu Canvas inspecté visuellement. Aucun test effectué avec l’index réel.
- Validation navigateur complète non réalisée : Chromium n’a pas démarré dans
  cet environnement. Le test DOM ne remplace pas cette validation.
- Suite Python existante : 31 tests exécutés, 5 réussis et 26 erreurs dues à
  l’absence de fixtures/demo.wikidata.jsonl dans le snapshot reçu.
  Ce fichier n’a pas été inventé pour contourner ces erreurs.

Le test reproductible tests/test_density_dom.cjs requiert Node, jsdom et
@napi-rs/canvas résolubles par Node. Il ne dépend ni de Wikidata ni du réseau.
