# Intégrations et frontières externes

## 1. Types d'intégration

Konstellation peut consommer :

- un `kristal_state` v6 direct ;
- un domaine d'une `Kristal-Kollection` ;
- un Runtime Pack Kristal ;
- un pack JSON normalisé ;
- une projection HTTP paginée ;
- des Reader Policies ;
- une intégration SemantiK/SA explicitement configurée.

## 2. Règle de frontière

Les intégrations externes peuvent fournir données, policy et métadonnées. Elles ne peuvent pas injecter :

- composant Svelte ;
- JavaScript exécutable ;
- HTML de confiance ;
- permissions implicites ;
- mutation silencieuse de QuerySpec.

## 3. Kristal v6 direct

Configuration de référence :

```json
{
  "adapter": "kristal-state-v6",
  "state": "kristal-v6-state.json",
  "requireIdentity": true
}
```

L'adaptateur :

1. valide le schéma ;
2. vérifie l'identité lorsque déclarée ;
3. projette seulement les structures représentables sans perte ;
4. préserve les métadonnées v6 utiles ;
5. déclare les pertes ;
6. dérive les affordances.

## 4. Kristal-Kollection

```json
{
  "adapter": "kristal-kollection-v1",
  "directory": "/chemin/vers/Kristal-Kollection",
  "kristal": "Time"
}
```

L'adaptateur sélectionne un dossier `domains/Kristal-*`, découvre son état v6 et conserve les
écarts au contrat strict sous forme de diagnostics. Il ne corrige pas silencieusement un hash
canonique divergent et ne transforme pas une variante de collection en artefact v6 validé.

## 5. navigationHints

Les hints sont des métadonnées de planification non factuelles.

Forme recommandée :

```json
{
  "schemaVersion": "0.1",
  "affordances": {
    "temporal": {"score": 1, "reason": "dates canoniques"},
    "lineage": 0.9
  },
  "relationAffordances": {
    "derived_from": ["lineage", "dependency"]
  },
  "preferredRecipes": ["timeline", "evolution"],
  "recipeLabels": {
    "evolution": "Trajectoire"
  }
}
```

Les aliases `capabilities` et `relationCapabilities` existent pour compatibilité v0.6 mais la terminologie cible est `affordances`.

## 6. SemantiK / SA

Une formulation ou communication externe doit rester explicitement déclenchée. Le serveur recalcule les résultats à partir de QuerySpec ; il ne considère jamais un résultat fourni par le client comme vérité.

## 7. Erreurs d'intégration

Les erreurs doivent être structurées et distinguer au minimum :

- schéma invalide ;
- identité invalide ;
- policy incompatible ;
- capacité externe indisponible ;
- projection non supportée ;
- perte d'import ;
- timeout ;
- source inaccessible.

## 8. Collections GitHub Kristal v10 draft.3 (opt-in)

L’adaptateur `kristal-github-collection-v10` exploite `kristals/index.json`
(`kristal.github-collection-index/1.0`) et `.kristal/sync-manifest.json`
(`kristal.github-sync-manifest/1.0`) sans accès réseau et sans exécuter d’instructions IA.
Son résultat normalisé est **uniquement une navigation d’hébergement dérivée** :
`hosted_state`, `logical_artifact` (membre v9 déclaré) et `hosted_file`.

Les empreintes et les liaisons entre manifests, AI index et State Snapshot sont
vérifiées, pas les signatures, ni la fidélité sémantique de l’engagement logique.
Les fichiers non déclarés ou les liens symboliques sont refusés. Aucune conversion
v9→v6 automatique n’est autorisée. Voir [le guide v10](30-kristal-v10-github.md).
