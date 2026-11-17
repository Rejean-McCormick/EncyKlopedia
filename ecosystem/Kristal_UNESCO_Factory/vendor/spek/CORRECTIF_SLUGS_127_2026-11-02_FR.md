# Spek — correction des slugs normalisés (2 novembre 2026)

Les **slugs canoniques** sont désormais `agriculture`, `ai`, `accounting`, etc. La chaîne `Kristal-` est un ancien préfixe du rapport Manager (pour 99 entrées sur 127), pas une partie du slug courant.

## Corrections

- Les 127 entrées de `template_library/wiki/kristal-ai-proposals.json` utilisent les slugs sans préfixe. L’ancien identifiant est conservé uniquement dans `source_report_identity` pour la traçabilité.
- Les cinq revues de `kristal-structure-reviews.json` utilisent les mêmes slugs.
- Le lecteur Spek recherche l’identité canonique exacte et accepte un ancien préfixe seulement lors de la lecture d’anciens fichiers. Il ne choisit jamais un template automatiquement.
- L’atelier réactualise son panneau central après « Ouvrir un Kristal… » même si « Mon travail » était déjà sélectionné. Il affiche le nom, le slug, la proposition et la revue éventuelle.
- Le registre `kristal-assignments.json` reste **vide** : aucune assignation approuvée et aucune permission de publication n’ont été ajoutées.

## Attention

Le rapport du 2 novembre contient l’identifiant atypique `Kristal-ScolQc`. Le registre utilise la clé normalisée `scolqc` comme convention technique, mais **cette identité locale doit être confirmée sur son workspace actuel** ; nous n’avons pas vérifié ce dossier après sa normalisation. Aucune provenance/empreinte historique n’a été modifiée.

## Installation

Fermer Spek. Extraire le ZIP correctif dans le **dossier parent** qui contient `Spek/`, puis remplacer les fichiers existants. Relancer `Spek/Spek_Template_Manager.pyw` ou `Spek/START_SPEK.bat`.

La modification n’affecte pas `locals`, `GitSink.bat`, l’historique Git ni les autorisations de publication.
