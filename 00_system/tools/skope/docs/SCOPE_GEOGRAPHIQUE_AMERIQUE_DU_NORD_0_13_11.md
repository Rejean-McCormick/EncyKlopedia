# Skope : scope géographique — Amérique du Nord, Canada prioritaire

Un **scope** peut maintenant déclarer `geography` dans la recette :

```json
{
  "focus": "north-america", "priority": "canada", "mode": "annotate",
  "region_qid": "Q49", "priority_qid": "Q16",
  "evidence_properties": ["P9714", "P183", "P2341"]
}
```

Via **Wizard → 5 · Géographie**, l'utilisateur peut choisir les deux QID géographiques (région et priorité) et un mode :
- `annotate` (recommandé) : classer Canada, Amérique du Nord, autres lieux, non documenté ; **aucun taxon exclu** ;
- `documented_only` : conserver uniquement des taxons reliés géographiquement au Canada ou Amérique du Nord, en conservant la racine taxonomique comme contexte ; risque très élevé de faux négatifs documentaires ;
- `off` : pas de traitement géographique.

Les QID sont personnalisables pour d’autres régions ; Skope vérifie leur format, pas la validité de leurs hiérarchies.

Les comptes reposent sur des **liens Wikidata agrégés** du dump indexé : P9714 (taxon range), P183 (endemic to), P2341 (indigenous to). Pour l'identification du pays, Skope inspecte au plus 2 liens P17/P131/P30 en provenance des lieux cités. Cet examen borné n'est pas une reconstruction géographique exhaustive.

**La traversée P171 n'est pas géographiquement filtrée avant exploration** : un plafond atteint implique un périmètre tronqué, même avec un mode géographique. Les données de répartition de Wikidata ne sont pas exhaustives. Absence de liaison !== absence du Canada. La géographie du scope est une priorité documentaire à confronter avec des sources d'occurrences scientifiques (GBIF, flore canadienne), non une preuve.

Le ZIP contient la recette, la couverture et la cible Kristal ; aucune écriture dans le canon du Kristal ni la base SQLite. La collecte complète et l'adaptateur de données géographiques demeurent à développer.
