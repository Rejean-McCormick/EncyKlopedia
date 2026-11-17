# Arketype, Framework, Kit, Manager, Kompiler : rôles distincts

**Cette page résume des constats contenus dans le rapport transmis**, non une nouvelle validation directe des dépôts externes. Vérifier API, licence, version et comportements dans les sources originales avant implémentation.

| Composant mentionné | Rôle à exploiter | Ce qu'il ne faut pas lui attribuer |
|---|---|---|
| Kristal Framework v11 | États, namespaces, références, fédération de snapshots | Pas une preuve de vérité de chaque assertion |
| Authoring Kit / Integration Pack | Auteur supporté, pins, qualification, reprise | Pas un import générique supposé ; pas d'atomicité inter-systèmes garantie |
| Arketype | Catalogue de modèles/recettes, guide de forme | **Non normatif**, ne certifie pas le domaine |
| Manager des Kristals | Inventaire/résolution des espaces | Ne pas fusionner les namespaces par opportunisme |
| Kompiler | Contexte de lecture projeté depuis des états Kristal | Ne pas perdre conditions/qualificatifs ni faire réentrer la synthèse comme source |
| KristalDiag | Diagnostic dans son périmètre de version | Test v10 ≠ qualification globale v11 |
| Kristal-Wikidata-Workflow | Extraction et preuves Wikidata étudiées | Son répertoire de canon à construire n'est pas une admission accomplie |

## Adoption d'un profil Arketype

Recette suggérée → examiner formes et exemples → traduire les contraintes réellement utiles en **profil d'auteur versionné** → qualifier sur un îlot réel → seulement alors appliquer aux opérations admises. Plusieurs formes peuvent se combiner; un modèle proposé n'est pas une preuve de conformité ou de qualité. Ne pas changer le format natif d'un îlot pour satisfaire une maquette.

## Trois modèles pour la qualification

- **Education** : ne pas fusionner preuve d'apprentissage et maîtrise; traiter correctement les domaines et personnes.
- **Soil** : préserver méthode, conditions de mesure et variations contextuelles.
- **Accounting** : troisième forme contrastée à **lire d'abord**, avant toute admission dans son modèle natif.

Le rapport indique que des échantillons Education et Soil ont passé des contrôles référentiels v11 (723 et 847 assertions), mais que leurs crosswalks contenaient zéro mapping; cela **ne qualifie pas l'alignement Wikidata**. Les mesures et dépôts ayant servi à ces chiffres doivent être remis ou retrouvés avant de les traiter comme des tests reproductibles dans EncyK.

## Point de vigilance Kompiler

Selon le rapport, l'adaptateur actuel génère d'abord la vue v11 puis sélectionne les identifiants; cela peut coûter plus que la sélection finale. Mesurer sur charge représentative. Si nécessaire, ajouter **dans un adaptateur EncyK qualifié** une projection sélective/indexée, avec invalidation, périmètre d'accès et version de profil. Ne pas modifier Kompiler à l'aveugle ni introduire de caches illimités.

## Ne pas toucher aux composants exclus

**Skope et Kristalizer** : aucune modification, aucun fork, aucune copie de source dans le méga-repo. Des adaptateurs externes peuvent utiliser des API/CLI documentées ou des index en lecture autorisée.
