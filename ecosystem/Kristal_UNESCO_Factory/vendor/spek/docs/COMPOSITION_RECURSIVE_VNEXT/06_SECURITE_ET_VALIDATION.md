# 06 — Validation, sûreté, déterminisme et provenance

**Statut : exigences de conception et d'essais pour le moteur futur.**

## Deux vues, deux publics

- **Atelier privé** : peut montrer un plan IA provisoire, la disponibilité du Kristal et le statut de préparation de SemantiK. Les données techniques sensibles ne sont disponibles que dans un canal interne autorisé, pas dans le HTML de lecture ordinaire.
- **Pages Wiki candidates** : phrases réalisées, clauses de portée, limites, liens explicitement approuvés. Aucune source brute, URL privée ou empreinte interne.

Un « brouillon privé » ne constitue jamais une permission de divulgation. Les contenus choisis et leurs sources doivent être revus avant toute exportation publique.

## Fail-closed par étape

| Étape | Condition nécessaire | En cas d'échec |
| --- | --- | --- |
| Charger une définition | Format supporté, version exacte, ressource locale autorisée | Refus |
| Résoudre le graphe | Pas de cycle, cardinalités et bornes respectées | Refus |
| Lier les faits | Identité/state ref et assertions autorisées explicitement épinglées | Refus |
| Prescrire les formes | Intentions compatibles avec les types et obligations fournis | Refus |
| SemantiK | RuntimeSet exploitable, bloc valide, couverture, provenance, langue | Refus |
| Assemblage | Pas de feuille manquante, aucun doublon inattendu, règles de jointure valides | Refus de candidate publique |
| Publication | Approbation et règles Manager / C1-C2-C3 + contrôle de divulgation du lot exact | Refus |

## Audit interne sans fuite publique

Pour chaque feuille résolue conserver **en espace privé** :

`composition_instance_id`, `template_id@version`, `instance_path`, `slot`, `realization_key`, `request_ref`, `result_ref`, `state_ref`, couverture des obligations, statut de vérification et digests nécessaires.

Ces métadonnées ne sont **pas** recopiées dans le document lecteur, les attributs HTML, les notes Markdown ou les PDF. Les états sensibles ne sont pas ajoutés aux journaux utilisateur. La séparation doit exister dans le code (modèle privé vs projection de rendu), pas seulement dans le CSS.

## Immutabilité et reproductibilité

- Définitions versionnées et verrouillées durant une compilation ; si fichier/empreinte change entre validation et lecture, refuser.
- Création des sorties dans un dossier de staging privé, promotion atomique après validation ; ne pas écraser des sorties approuvées en place.
- Identité du build : versions des templates + modèle d'instance + sorties linguistiques qualifiées + politique de rendu ; les empreintes restent **privées**.
- **Idempotence** : une même préparation déjà réussie ne doit pas republier ni dupliquer l'effet de bord. Elle peut retourner le même artefact vérifié ; publication seulement via autorité externe.
- Aucun ancien résultat de SemantiK ne doit être réutilisé avec un nouvel état canonique simplement parce que le texte paraît identique.

## Limites de ressources

- Profondeur bornée, nombre total de nœuds/feuilles plafonné, taille du rendu plafonnée, détection des cycles par pile DFS et des références dupliquées.
- Une exécution SemantiK doit avoir un timeout et un budget global ; pas de tentatives infinies. Réessayer uniquement les défaillances transitoires identifiées, **jamais** contourner un refus de contrat ou d'autorisation.
- Parcours locaux uniquement depuis des racines admises ; aucune inclusion de `../`, symlink hors racine ou chargement arbitraire de réseau par un template.
- Refus de code exécutable dans les templates et échappement HTML/LaTeX/Markdown conforme au contexte.

## Dégradation gracieuse, mais limitée

- Recherche du catalogue indisponible : les fonctions de lecture locale déjà chargées peuvent rester disponibles.
- **Réalisation linguistique requise indisponible :** on peut montrer le **plan privé**, mais jamais un document final faussement complet ; pas d'affichage de triplets bruts en remplacement.
- Revue/autorisation absente : uniquement un brouillon non publiable.

## Risques spécifiques aux compositions imbriquées

1. **Perte de nuance** : si un sous-template cache une objection, le rendu est invalide.
2. **Double comptage** : une même obligation apparaissant dans deux répétitions doit être explicitement voulu et traçable.
3. **Effet de saturation** : dix sous-templates affichés comme dix cartes peuvent dégrader la lecture ; surface « flow » obligatoire pour les motifs rhétoriques appropriés.
4. **Conflit de langues** : des fragments `fr` et `en` ne doivent pas être combinés par erreur.
5. **Injections** : les étiquettes de template non fiables ne deviennent pas du HTML ni du code CSS brut.
6. **Publication partielle trompeuse** : si une feuille obligatoire manque, ne pas afficher le document comme approuvé.

## Tests de non-régression essentiels

Documentés en détail dans [10 — Critères d'acceptation](10_TESTS_ACCEPTATION.md). Le contrat exige en particulier des tests négatifs sur cycles, bornes, obligations, confidentialité, alternance de langues, et correspondance d'état canonique.
