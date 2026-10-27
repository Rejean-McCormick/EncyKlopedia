# Alignement Kristal v6

## 1. Frontière d'autorité

```text
kristal_state v6
  = vérité canonique

Konstellation normalized pack
  = index/projection locale de lecture

Structural Profile + NavigationPlan
  = affordances dérivées

Renderer
  = représentation
```

## 2. Signaux v6

Konstellation exploite sans les réduire à une notion générique de « confiance » :

- `coordinates` ;
- `valuations[]` et `value_semantics` ;
- `record_role` ;
- `actionability` ;
- `conflicts_with` ;
- `supersedes` ;
- `lineage` ;
- `evidence_refs` ;
- `provenance_refs`.

## 3. Mappings d'affordances

| Signal | Affordances possibles | Précaution |
|---|---|---|
| coordinates | temporal, spatial, multiScale, classification | ne pas interpréter un axe inconnu sans mapping |
| valuations | quantitative, multidimensional, stateful, temporal | ne pas aplatir en certitude |
| record_role | stateful, eventStream, actionability | rôle != permission |
| actionability | actionability | automatic != autorité |
| conflicts_with | conflict/argumentation | montrer, ne pas arbitrer |
| supersedes | succession/versioned | préserver les versions |
| lineage | lineage/dependency/evolution | dérivation != causalité |
| evidence_refs | evidential | distinct de provenance |
| provenance_refs | provenance | respecter Reader Policy |

## 4. Import direct

Le lecteur v6 doit :

1. valider le schéma ;
2. vérifier `state_id` / `content_hash` lorsque présents ;
3. construire une projection queryable des structures représentables ;
4. conserver les métadonnées v6 nécessaires ;
5. lister les pertes dans `importRecord.losses` ;
6. produire un résumé structurel dérivé.

## 5. Actionability

```text
actionability.mode = automatic
!= permission d'exécuter
```

La recette `action-context` est une **vue de compréhension**. Toute exécution future devra passer par un contrat distinct d'autorisation/exécution, explicitement séparé de Konstellation navigation.

## 6. Extensions Konstellation

Des hints non factuels peuvent être publiés dans une extension dédiée, par exemple :

```json
{
  "extensions": {
    "konstellation": {
      "navigation": {
        "schemaVersion": "0.1",
        "affordances": {"temporal": 1, "lineage": 0.9},
        "preferredRecipes": ["timeline", "evolution"]
      }
    }
  }
}
```

Ces hints ne modifient ni l'identité ni la connaissance canonique.
