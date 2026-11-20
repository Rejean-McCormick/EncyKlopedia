# 14 — Exemples de diagnostic et recettes concrètes pour les agents

## A. Fichier de sélection : distinguer un homonyme d'un concept

**Situation historique réelle** : recherche par préfixe sur *Rain*, *Snow*, *Frost*, *Winds*. Des albums, villes et personnes peuvent ressembler lexicalement à une notion météorologique.

**Règle** : prendre chaque `candidate_id` et son `concept_id`, puis décider selon l'article et l'extrait. Une chanson intitulée *Rain* n'est pas automatiquement une étude de précipitation; une histoire de cyclone tropical peut être pertinente pour plusieurs concepts si la relation est substantielle. Si aucun extrait et homonymie ambiguë, `HOLD`, pas SELECT artificiel.

## B. Article très long : ne pas feindre l'exhaustivité

Un article sur les atmosphères extraterrestres peut couvrir Mercure, Vénus, Mars, les géantes gazeuses, Titan, les exoplanètes et leurs spectres. Extraire les thèmes et mécanismes réellement étudiés, puis déclarer `incomplete` si les sections restantes ne sont pas traitées. Un lot de faits utiles vaut mieux qu'une déclaration `processed` insoutenable.

## C. Contrôle des citations

La présence de la chaîne « 1,5 % de méthane » ailleurs dans le texte ne justifie pas un fait sur Neptune si la phrase extraite concerne Titan. Vérifier **la portée probante, le sujet, la date, l'unité, la qualification** et le texte original. Les appels de notes et modèles Wikipédia peuvent masquer la portion pertinente; trouver la bonne sous-chaîne, pas n'importe quelle chaîne présente.

## D. Refus techniques

Si 379 lignes sont refusées dans un retour, l'agent ne doit pas déduire que les 379 sont « fausses ». Lire leurs erreurs par ordinal, reconstituer le pack source, et distinguer les problèmes de format de preuve. Les propositions déjà validées restent privées; ne pas effacer le bon cumul par une reprise de mission sans contrôle.

## E. Dossier de travail pour une autre IA

1. Demander le ZIP original de mission si l'utilisateur veut traiter un SEL/ENR.
2. Lire le contrat `INSTRUCTIONS_CHATGPT.md` et la liste complète JSONL.
3. Produire un retour **uniquement** pour ce job, avec les vrais IDs et citations.
4. Valider le ZIP contre le manifeste et le validateur de la version installée.
5. Si la source est très volumineuse, traiter le maximum raisonnable et documenter honnêtement `incomplete`.

## F. Inspection technique sans index mondial

Pour vérifier une branche : lire les tables `branches`, `branch_concepts`, `candidates`, `jobs`, `lanes`, `source_results`, `proposals`, `import_errors`. Le registre peut être ouvert `mode=ro` et `query_only=ON` pour éviter une migration. Les sources Skope/Wikipédia doivent être lues via des requêtes indexées et des APIs documentées. Ne pas relancer un build du dump mondial pour un simple désaccord de libellé.

## G. Quand arrêter la découverte ?

Arrêter **la fenêtre** si son budget, plafond, limite de tours, pause ou règle anti-stagnation est atteint. Ensuite, inspecter le rendement et décider d'une nouvelle fenêtre, de compléments PARTIAL ou d'une autre branche. **Ne jamais transformer une fin technique de fenêtre en déclaration d'achèvement encyclopédique.**

## H. Résultat attendu d'un enrichissement documentaire (comme cet overlay)

Fichiers Markdown cohérents, liens vérifiés, point d'entrée AGENTS/README mis à jour, manifeste des fichiers changés, installateur avec sauvegardes, tests et état de validation. Aucune création de candidat, aucune écriture dans l'état V32/V8 et aucune publication canonique.
