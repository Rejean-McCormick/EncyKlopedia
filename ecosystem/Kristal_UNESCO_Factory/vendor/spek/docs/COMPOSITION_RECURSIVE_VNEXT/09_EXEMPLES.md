# 09 — Exemples de compositions (fictifs)

**Les instances JSON v1.0 décrites ici sont désormais exécutables par `compose-check`, `compose-dialogue` et `compose-preview`, avec des réalisations fournies explicitement.** Aucune assertion de Kristal n'est incluse. Voir [11 — État du code](11_ETAT_DU_CODE_LIVRE.md).

## Exemple A — Un argument et trois preuves

```text
rhetorical.argument-evidence@1.0.0
  ├─ rhetorical.assertion (thèse)             → realization_key: arg1.thesis
  ├─ rhetorical.evidence × 3                  → arg1.proof.1, arg1.proof.2, arg1.proof.3
  ├─ inference (feuille)                      → arg1.inference
  ├─ rhetorical.qualification (objection)     → arg1.objection
  └─ rhetorical.conclusion                    → arg1.conclusion
```

La **définition** « preuve » est unique ; les **trois instances** ont trois clés et bindings distincts. La sortie peut se lire comme deux paragraphes au lieu de six cartes. Le renderer ne réécrit pas la phrase et n'ajoute pas de fait.

[Exemple JSON](exemples/argument-trois-preuves.instance.json)

## Exemple B — Argument fractal

```text
wiki.article@1.0.0
  ├─ rhetorical.definition@1.0.0
  ├─ rhetorical.argument-evidence@1.0.0 [instance argument-1]
  │    ├─ assertion
  │    ├─ evidence × 3
  │    ├─ objection
  │    └─ conclusion
  ├─ rhetorical.argument-evidence@1.0.0 [instance argument-2]
  │    ├─ assertion
  │    ├─ evidence × 3
  │    ├─ objection
  │    └─ conclusion
  └─ rhetorical.synthesis@1.0.0
```

Le même template est réutilisé deux fois, chacune avec ses trois preuves. Résultat : **six preuves explicitement fournies**, aucune détection automatique. La composition finale pourrait utiliser trois sections de Wiki : mise en contexte, arguments, synthèse.

## Exemple C — Comparaison qui se lit comme une progression

```text
rhetorical.comparison-narrative@1.0.0
  ├─ question                      → obligation ASK
  ├─ criterion                     → critère sélectionné
  ├─ approach-a                    → description A
  ├─ approach-b                    → description B
  ├─ synthesis                     → synthèse source déjà autorisée
  └─ qualification                 → limites explicites
```

**Visuel desktop** : A et B peuvent être deux colonnes. **Visuel mobile/Wiki** : la question est l'élément d'ouverture, puis A et B suivent en séquence. Le critère n'est pas perdu, ni la qualification. Le texte « A est meilleur que B » ne peut jamais être créé par la mise en page s'il n'est pas attesté par les obligations amont.

[Exemple JSON](exemples/comparaison-narrative.instance.json)

## Exemple D — De la carte au flux de prose

**Ancien rendu technique (à éviter sur la page lecteur)** :

```text
[THÈSE] Phrase A
[PREUVE 1] Phrase B
[PREUVE 2] Phrase C
[PREUVE 3] Phrase D
[CONCLUSION] Phrase E
```

**Nouveau rendu rhétorique, si les unités sont autonomes** :

> **Phrase A.** Phrase B. Phrase C. Phrase D.
>
> Phrase E.

`Phrase A` à `Phrase E` symbolisent des **réalisations déjà obtenues** de SemantiK, non des textes que Spek compose ou transforme. La politique `block` gère la séparation des blocs ; elle ne doit pas coller aveuglément des fragments de syntaxe ou ajuster la ponctuation.

## Exemple E — Publication Wiki

Un plan `wiki.article` peut contenir trois groupes internes rhétoriques. Le Markdown publié ne devrait pas contenir trois copies de « Argument », « Preuve », « Conclusion » par défaut. La **table des matières** reflète seulement les véritables divisions documentaires. En privé, le manifeste/audit conserve toutes les instances résolues, sources et requêtes sans les exposer.
