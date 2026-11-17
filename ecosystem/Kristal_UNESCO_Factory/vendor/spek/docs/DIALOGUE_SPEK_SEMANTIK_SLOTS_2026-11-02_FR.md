# Spek ↔ SemantiK Architect — Dialogue de formulation par champ

## Ce que fait désormais Spek

**Spek choisit la forme communicative de chaque champ du template**, avant de demander à SemantiK Architect de réaliser sa phrase. C'est le sens de « Spek fait la conversation » : Spek pose une commande structurée et bornée ; SemantiK répond avec des blocs réalisés et leur traçabilité ; Spek vérifie le résultat puis remplit les slots du layout.

La décision est prise à partir des **27 contrats de layout réellement installés**, de l'emplacement (`slot`) et du type explicite de l'unité déjà retenue par le plan éditorial. Les exemples de demandes sont :

| Champ Spek | Intention Spek | Contrainte SemantiK |
| --- | --- | --- |
| `concept-card.definition` | Définition | Énoncé (`utterance`), avec les obligations déjà fournies |
| `comparison.topic` | Question | Obligation `ASK`, bloc `question` |
| `result-card.uncertainty` | Précaution / qualification | `notice` ou `utterance` |
| `chronology.events` | Faits événementiels | `utterance` ou `list` si le contenu sélectionné est une collection |
| `taxonomy-tree.specializations` | Présentation de relations | `utterance`, sans inférer une hiérarchie non attestée |
| `article.title_key` | Titre court | `heading` lorsque pris en charge, `utterance` sinon |

Pour chaque champ, Spek produit un **plan de formulation** (`spek.slot-dialogue/1.0`) avec l'intention, les types de blocs, la taille maximale et le contexte du template. Ce plan est **interne et privé**. Il ne contient ni assertions sélectionnées ni texte inventé.

## La conversation technique réelle

1. Le Manager / le plan éditorial explicitement approuvé fournit `article.json`, les clés de réalisation, les unités et les faits autorisés.
2. Les **CommunicationRequest** SemantiK, avec leurs graphes, obligations, sources et profil de capacité, sont fournies via `mapping.json` (ou un producteur amont explicite). **Spek ne fabrique pas ces éléments.**
3. Avant chaque appel SemantiK, Spek associe la clé à son slot et restreint **dans une copie temporaire** les contraintes de présentation : `allowed_block_kinds`, `max_length`, `opening_policy`, `closing_policy`, éventuellement `list_policy`. Une question requiert explicitement `ASK`; Spek refuse de convertir une assertion en question.
4. SemantiK Architect traite la requête avec son **vrai RuntimeSet**, puis retourne un `CommunicationResult` structuré.
5. Spek vérifie **en plus** le type de bloc produit : s'il ne correspond pas à la forme demandée, le résultat est refusé. Les contrôles existants vérifient aussi couverture complète des obligations, provenance, RuntimeSet, identifiant déterministe, langue et compatibilité du layout.
6. Spek remplit le template, produit un **aperçu privé**, sans validation de publication.

Les fichiers originaux `article.json`, `mapping.json` et `requests/*.json` ne sont jamais réécrits. Si une contrainte linguistique ou une obligation est incompatible avec le slot, l'exécution s'arrête : **aucune phrase de substitution**.

### Limite exacte de l'API SemantiK actuelle

Le schéma `CommunicationRequest/1.0` n'offre pas un champ normatif arbitraire « style de phrase : comparaison causale, synthèse argumentative, etc. ». Il expose **la force communicative, le contexte et les types de blocs** ; le planificateur de SemantiK choisit ensuite les opérations grammaticales à partir des **faits et rôles déjà présents**. Spek peut donc **demander et contrôler les formes supportées par ce contrat**, mais ne peut pas forcer une structure rhétorique spécialisée que SemantiK n'expose pas encore. Il faudrait étendre formellement le contrat commun pour aller plus loin (sans contourner les capacités GF/PGF).

L'application d'un RuntimeSet GF/PGF qualifié reste nécessaire pour obtenir des phrases réelles. Cette mise à jour **n'ajoute pas `grammar.pgf`** à SemantiK Architect.

## Utilisation

Dans l'atelier, onglet **3 · Aperçu Wiki** :

- **Voir les formes demandées par Spek…** : sélectionne un `article.json` et consulte une table par champ (sans réaliser de phrases).
- **Réaliser avec SemantiK…** : choisis l'article, le mapping explicite, le dépôt Architect et le RuntimeSet. Spek prépare les demandes de formes et vérifie les réponses avant le rendu.
- **Prévisualiser le Wiki** : compile le HTML lorsque les réalisations contrôlées sont disponibles.

Commande de prévisualisation des formes, **sans appeler SemantiK** :

```powershell
py -3 -m spek.slot_dialogue --article C:\chemin\article.json --layouts .\layouts --language fr --output C:\chemin\formes-de-phrases.json
```

Le fichier de sortie doit être **nouveau**. Il reste privé et ne peut pas être utilisé comme approbation de publication.

## Séparation des responsabilités

- **IA** : analyse des Kristals réels, composition documentaire, décision éditoriale proposée.
- **Manager** : état canonique, sélection autorisée des faits et contrôles éditoriaux C1/C2/C3.
- **Spek** : composition explicite de templates, **choix des formes de phrases par slot**, demande à SemantiK, validation de compatibilité et mise en page.
- **SemantiK Architect** : réalisation grammaticale des obligations sélectionnées via ses ressources linguistiques réelles.
- **Orchestrator** : qualification / activation des RuntimeSets ; pas de choix de fait ni de rédaction du Wiki.

Aucun push GitHub n'est déclenché par cette couche.
