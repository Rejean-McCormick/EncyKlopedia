# Anti-patterns interdits

## 1. UI par domaine

**Mauvais :** `if (kristalType === "math") showProofUI()`.

**Bon :** détecter `proof + dependency` puis proposer `proofs` avec `dag-proof`.

## 2. Renderer fourni par le Kristal

**Mauvais :** charger une URL JavaScript ou un composant Svelte depuis les données.

**Bon :** `navigationHints` déclaratifs + Renderer Registry contrôlé.

## 3. Affordance traitée comme vérité

**Mauvais :** « ce Kristal est causal à 82 % » comme assertion scientifique.

**Bon :** « Konstellation a détecté suffisamment de relations causales pour proposer une vue causal-feedback ».

## 4. Actionability = permission

**Mauvais :** bouton Exécuter parce que `mode=automatic`.

**Bon :** vue informative des conditions d'action ; exécution séparée par contrat autorisé.

## 5. Query mutation cachée

**Mauvais :** cliquer sur une vue modifie implicitement les filtres.

**Bon :** changement de vue sans mutation ; filtre/pivot seulement par action explicite.

## 6. Policy appliquée trop tard

**Mauvais :** calculer le graphe complet puis masquer les nœuds interdits.

**Bon :** filtrer selon Reader Policy avant projection, scores, counts et explanations.

## 7. Hard cap silencieux

**Mauvais :** afficher 220 edges sans dire que la vue est tronquée.

**Bon :** `truncated: true`, total estimé/connu et possibilité d'expansion/pagination.

## 8. Fausse chronologie

**Mauvais :** interpréter tout entier comme une année.

**Bon :** se baser sur value kinds, axes, valuations ou mappings explicites.

## 9. Dérivation = causalité

**Mauvais :** transformer `derived_from` en « cause ».

**Bon :** utiliser lineage/dependency sauf indication causale explicite.

## 10. Evidence = provenance

**Mauvais :** fusionner les deux en un champ source unique.

**Bon :** préserver leurs rôles distincts.

## 11. Planner opaque

**Mauvais :** recommander une vue sans explication ni signaux.

**Bon :** associer chaque score à des evidence compréhensibles.

## 12. Import silencieusement lossy

**Mauvais :** jeter une valuation complexe non supportée.

**Bon :** la préserver en metadata ou la déclarer dans `importRecord.losses`.

## 13. Graph everything

**Mauvais :** utiliser Constellation comme réponse universelle.

**Bon :** choisir arbre, timeline, DAG, flow, matrix ou fallback selon structure.

## 14. Catégorie métier comme architecture

**Mauvais :** `history => timeline` sans inspection.

**Bon :** catégorie comme prior faible, structure effective comme décision.
