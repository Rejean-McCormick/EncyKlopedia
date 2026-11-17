# 10 — Critères d'acceptation et plan de tests

**Statut : tests unitaires et négatifs du moteur récursif ajoutés** (`tests/test_recursive_composition.py`), mais plusieurs cas de la chaîne GF/PGF et publication de bout en bout restent à tester. Ce tableau reste l'objectif d'acceptation, pas une attestation de qualification.

## Fonctionnels

| ID | Scénario | Attendu |
| --- | --- | --- |
| F01 | Une définition de template utilisée par trois instances | 3 chemins uniques, même définition versionnée |
| F02 | Composition `argument` avec 3 preuves explicitement liées | 3 feuilles, même ordre, aucun choix implicite |
| F03 | La même composition compilée deux fois | Même AST résolu et même rendu hors métadonnées non déterministes |
| F04 | Une rubrique « thèse » affichée comme phrase principale | Pas de `<h2>` artificiel, structure accessible maintenue |
| F05 | Comparaison desktop vs mobile | Ordre logique, contenu, qualificatifs identiques |
| F06 | Un template `rhetorical` sous `wiki` puis `report` | Le même moteur et les mêmes règles typées |
| F07 | Le compilateur plat historique | Comportement inchangé sur fixtures et tests existants |
| F08 | Deux arguments de 3 preuves chacun | 6 bindings distincts ; pas de doublon accidentel |

## Refus attendus

| ID | Entrée invalide | Attendu |
| --- | --- | --- |
| N01 | A → B → A | Cycle détecté avant réalisation |
| N02 | 3 répétitions prescrites, 2 bindings seulement | Refus |
| N03 | Type d'unité non autorisé dans slot | Refus |
| N04 | Version de template inconnue | Refus, pas de fallback |
| N05 | `ASK` demandé avec obligations `ASSERT` | Refus |
| N06 | SemantiK retourne bloc incompatible | Refus |
| N07 | Obligation absente de `CommunicationResult` | Refus |
| N08 | Texte de qualification manquant | Refus pour export public |
| N09 | Deux instances se disputent une clé avec des contraintes opposées | Refus |
| N10 | Profondeur, fan-out ou taille dépasse les bornes | Refus sans exécution coûteuse |
| N11 | RuntimeSet absent / mauvais état | Aucun texte de remplacement |
| N12 | Binding d'un autre état canonique | Refus |
| N13 | Template tente inclusion réseau, symlink ou `../` | Refus |
| N14 | Document sans approbation de divulgation | Aucun artefact publiable |

## Exposition d'informations

Pour chaque sortie HTML, PDF, LaTeX et Markdown Wiki **candidate lecteur** :

- Vérifier l'absence de `source_digest`, empreintes SHA-256, chemins `C:\`, `file:///`, `urn:`, `referent:`, `string:` et références internes de preuve si elles ne sont pas explicitement divulgables.
- Inspecter intégralement HTML DOM, attributs `data-*`, commentaires, contenu des scripts et liens.
- Vérifier les escapes HTML/LaTeX et les citations/lignes qui peuvent contenir des marqueurs hostiles.
- Vérifier que la page ne prétend pas avoir été publiée ou qualifiée lorsqu'elle est privée.

## Conformité linguistique

- Chaque slot lié à une réalisation obtient une ou plusieurs unités conformes aux capacités réelles de SemantiK.
- L'ensemble des obligations de l'entrée est exactement couvert, sans omission et sans invention.
- Aucun fallback interlangue ; pas de traduction improvisée par Spek.
- La comparaison et la thèse ne changent ni la force épistémique ni l'autorisation de publication.

## Tests de l'interface

- Recherche du Kristal par slug normalisé sans `kristal-` ; aucun changement éditorial inféré.
- Affichage du plan même sans RuntimeSet, mais avec statut **brouillon non publiable**.
- Aperçu Wiki seulement avec réalisations complètes et explicitement liées.
- Outils avancés séparés du parcours lecteur.
- Écrans 1024×768 et mobile HTML : aucune commande de base masquée et navigation clavier fonctionnelle.

## Critères de sortie du chantier

1. Dossier `/docs` approuvé.
2. Contrats JSON versionnés avec tests de compatibilité.
3. Expansion de template finie et déterministe.
4. Réalisations SemantiK réelles sur un cas autorisé, sans prose inventée.
5. HTML et Markdown Wiki lisibles, sans titres répétés ni données internes.
6. Contrôle de l'état source, des réalisations, de la divulgation et des approbations externes.
7. Aucune publication automatique après simple compilation.
