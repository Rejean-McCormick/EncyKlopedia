# 04 — Dialogue template → forme de phrase → SemantiK

**Statut : plan de dialogue par feuille et import de résultats implémentés dans vNext.** L'exécution directe d'un RuntimeSet GF/PGF depuis une composition récursive n'est pas encore intégrée.

## Point de départ réel

Le fichier `spek/slot_dialogue.py` construit actuellement un plan `spek.slot-dialogue/1.0` pour les unités d'un `article.json` plat ; il associe un rôle communicatif, des types de blocs autorisés et une longueur maximale. `compose_request()` peut restreindre `constraints.allowed_block_kinds`, `max_length`, `opening_policy` et `closing_policy`, tout en conservant le graphe et les obligations d'une `CommunicationRequest/1.0` fournie.

Le document normatif SemantiK `04_COMMUNICATION_SEMANTICS_LOCK.md` stipule : **SemantiK reçoit ce qui doit être communiqué ; il ne choisit pas quelles obligations conserver.** Une obligation peut générer plusieurs unités ; plusieurs obligations peuvent être regroupées ; aucune ne doit être omise.

## Cible : plan de formulation à chaque feuille résolue

Pour chaque `TextSlot` de l'arbre, Spek prépare un enregistrement **interne** :

```json
{
  "instance_path": "wiki.main/argument@1/evidence@2/statement",
  "template_ref": "rhetorical.evidence@1.0.0",
  "slot": "statement",
  "realization_key": "arg1.evidence2",
  "communication_request_ref": "requests/arg1-evidence2.json",
  "form": {
    "discourse_role": "evidence",
    "allowed_block_kinds": ["utterance"],
    "max_length": 800
  },
  "presentation": {"visual_role": "paragraph", "join_with_next": "block"}
}
```

**Ce format est représenté dans le plan privé** `spek.recursive-dialogue/1.0`, généré par `compose-dialogue`. La référence à la requête doit provenir du plan éditorial ; Spek ne la fabrique pas à partir d'une assertion vue dans `locals`.

## Contrainte : distinguer « intention » et « force »

- `discourse_role` (Spek) = utilité de la feuille dans la composition (`evidence`, `premise`, `qualification`, `question`, etc.).
- `obligation.force` (SemantiK) = acte communicatif réel (`ASK`, `ASSERT`, `PRESENT`, etc.) déjà présent dans les obligations.
- `block_kind` (SemantiK) = forme de bloc (`question`, `utterance`, `heading`, `list`, `notice` lorsque supportés).
- `presentation.visual_role` (Spek) = forme de rendu : paragraphe, emphase, liste, titre visuel, note.

**Ne jamais transformer une assertion en question par simple préférence d'un template.** Une feuille interrogative nécessite une obligation `ASK` compatible. Les autres forces sont conservées, même si l'étiquette rhétorique est « conclusion ».

## Le dialogue par feuille

1. Vérifier que chaque feuille est liée à **un ensemble explicite d'obligations** et à une requête valide ; interdire les clés manquantes/contradictoires.
2. Calculer la contrainte du slot puis faire **l'intersection** avec les contraintes déjà présentes dans la requête. Si vide, refus.
3. Interdire les ouvertures/clôtures incompatibles avec une petite phrase ; ne pas supprimer une obligation qui exige une introduction.
4. Appeler l'adaptateur SemantiK local, avec RuntimeSet effectivement disponible, deadline maîtrisé et référentiels versionnés.
5. Valider la réponse : identifiant, langue, RuntimeSet, structure des blocs, couverture exacte des obligations, provenance et longueur (dans les limites que SemantiK définit réellement).
6. Affecter le résultat à la feuille via `realization_key` **sans réécrire ni réordonner sa sémantique**.
7. Refuser le document publiable si une feuille requise manque, même si un brouillon privé peut afficher son état en attente.

## Jusqu'où va l'orchestration ?

La structure argumentative spécialisée n'est pas ajoutée comme une nouvelle force linguistique non documentée. Elle est définie par le **graphe de templates** : thèse + preuves × N + inférence + objection + conclusion. SemantiK produit chaque unité selon ses obligations et ses types de blocs disponibles. Spek les place et règle la mise en page.

**Attention à l'« assemblage fluide » :** enchaîner des fragments sans syntaxe ne garantit pas une phrase grammaticale. Deux modes explicites sont permis :

- **`block` (par défaut)** : chaque réalisation est une unité autonome ; le renderer gère les espaces/paragraphes, pas la syntaxe.
- **`inline-safe` (option future)** : ne joindre sur une ligne que des réalisations déclarées grammaticalement autonomes et explicitement autorisées ; pas de suppression automatique de point ou de mot. Une phrase complète doit être demandée directement à SemantiK si la liaison exige une flexion ou un connecteur grammatical.

Aucune nouvelle « grammaire de style rhétorique » dans SemantiK n'est nécessaire pour les premières recettes. En cas d'exigence future vraiment grammaticale (accord entre fragments, connecteurs dépendants), formaliser **un champ de contrat SemantiK versionné**, sans paramètre de convenance inventé dans JSON.

## Erreurs attendues

| Erreur | Résultat |
| --- | --- |
| Requête absente | Feuille bloquée ; aperçu privé : « texte en attente » |
| Type de bloc impossible | Refus ; pas de conversion vers une prose libre |
| Obligation non couverte | Refus intégral de l'unité |
| RuntimeSet absent/invalide | Refus ; aucune sortie de remplacement |
| Langue manquante | Refus de cette variante linguistique, sans fallback trompeur |
| Provenance invalide | Refus ; journal privé, pas de fuite vers HTML lecteur |
| Deux slots utilisent une même clé avec formes incompatibles | Refus ou séparation explicite des clés par le producteur amont |

## Transparence

Le journal interne peut contenir les identifiants nécessaires à l'audit, soumis aux contrôles d'accès ; l'interface lecteur et les pages Wiki ne contiennent ni `CommunicationRequest`, ni URI internes, ni empreintes ni paramètres de RuntimeSet.
