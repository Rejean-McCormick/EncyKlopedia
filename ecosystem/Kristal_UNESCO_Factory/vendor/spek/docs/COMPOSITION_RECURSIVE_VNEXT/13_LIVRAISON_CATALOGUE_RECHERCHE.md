# Livraison — recherche et templates rhétoriques

Cette livraison étend l'architecture vNext avec **52 définitions supplémentaires** (au total **62 modèles rhétoriques**) fondées sur l'analyse des sources reconnues. Les modèles sont **des adaptations Spek**, pas des copies ni des implémentations certifiées.

## Code modifié

- `spek/composition/engine.py`: contrat de relation éditoriale explicite (`editorial_relation`), stricte vérification des références non dupliquées, règles optionnelles de découpage de paragraphes, sans transformation linguistique.
- `spek/cli.py`: nouvelle commande de catalogue `rhetoric-list`.
- `template_library/rhetorical/templates/`: 52 nouveaux contrats typés, versionnés.
- `template_library/rhetorical/research-inventory.json`: registres et sources consultées.
- `tests/test_rhetorical_research_catalogue.py`: refus des marques inventées, tests de rendu et d'instanciation de tous les modèles nouveaux.

## Risques et limites

- Le marqueur `editorial_relation` **ne prouve pas** qu'une relation existe entre les assertions : Spek vérifie la cohérence structurelle des déclarations uniquement.
- Aucun connecteur, synonyme, lien causal, titre de section ou preuve n'est inféré par Spek.
- Les phrases d'exemple sont manuelles et fictives ; la réalisation GF/PGF et la qualification sémantique réelle restent à faire.
- La catégorie `rhetorical` garde les **dix anciennes définitions** pour compatibilité. Leurs instances existantes ne requièrent pas rétroactivement les nouveaux marqueurs.
- Le Markdown et HTML restent des aperçus privés. Le pipeline de publication Wiki avec approbation C1/C2/C3 n'est pas remplacé.
- La transposition de RST/PDTB vers des modèles productifs est notre interprétation éditoriale ; les sources sont des modèles d'analyse, non des certifications des sorties.

## Exemples et vérifications

Voir `12_INVENTAIRE_SCIENTIFIQUE_RHETORIQUE.md` pour les commandes PowerShell et les détails des modèles.

## Extension modèle discursif (3 novembre)

Les 62 contrats ont maintenant `discourse_model` en plus de `rhetorical_contract`. Ce nouveau niveau distingue les mouvements et dépendances des seules cardinalités de slots. Voir [14](14_GRAMMAIRE_DU_DISCOURS.md).
