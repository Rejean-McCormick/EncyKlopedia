# 02 — Modèle unifié de composition

**Statut : contrat vNext partiellement implémenté.** `spek.template-graph/1.0` et `spek.composition-instance/1.0` sont exécutables par `spek.composition.engine` ; le compilateur historique `spek.core.compile_inputs` continue de recevoir son ancien format. Voir [11 — État réel du code](11_ETAT_DU_CODE_LIVRE.md).

## Trois objets à ne pas confondre

1. **Définition versionnée** (`TemplateDefinition`) : une recette réutilisable (slots, types, bornes, ordre, règles de rendu), sans références à un Kristal précis.
2. **Instance éditoriale** (`CompositionInstance`) : l'arbre de templates sélectionné par l'IA et validé en amont, avec les références exactes aux unités autorisées. *Elle n'est pas générée en examinant les faits à l'exécution.*
3. **Arbre résolu** (`ResolvedComposition`) : produit déterministe de Spek, où chaque répétition est développée en instances stables et chaque feuille porte sa clé de réalisation ; ce n'est pas un document publiable.

## Grammaire abstraite cible

```text
TemplateNode := Sequence | Group | Repeat | ComponentRef | TextSlot
Sequence    := ordered_children[TemplateNode+]  (ordre obligatoire)
Group       := layout_role + children[TemplateNode*]
Repeat      := template_ref + instances[ExplicitBinding+] + bounds
ComponentRef:= template_id@version + bindings
TextSlot    := slot_name + allowed_kinds + constraints + realization_key
```

- **Pas de référence à une catégorie privilégiée** : la catégorie `rhetorical` utilise `ComponentRef` comme `wiki` ou `scientific`.
- **Pas de récursion libre** : les références doivent former un DAG après résolution, et l'instanciation doit avoir une profondeur bornée. Les définitions peuvent partager une sous-recette, pas se référencer en boucle.
- **Séquence non implicite** : aucun tri dynamique par importance, par score ou par volume d'assertions.
- **Pas de fallback par « layout préféré ».** Si un `template_id@version` manque, refus.
- **Répétition explicitement alimentée :** `repeat.count` n'invente pas des valeurs ou des preuves. Une collection à trois éléments doit contenir trois bindings explicites.

## Contrats pour les slots

Chaque slot doit déclarer a minima : `name`, `kind` (`text` / `child`), `allowed_kinds` ou `allowed_template_ids`, `min`, `max`, et sa politique de visibilité. Pour une feuille textuelle : `realization_key` et `presentation_role`. Une chaîne littérale ne peut servir qu'à une étiquette de mise en page **non factuelle et versionnée** (par exemple « En bref ») ; les propositions factuelles exigent SemantiK.

## Identités stables

- ID de définition : `rhetorical.argument-evidence` (référence exacte : `rhetorical.argument-evidence@1.0.0`).
- Version de définition : `1.0.0`.
- Chemin d'instance : `wiki.main/argument@1/evidence@2`.
- Identité d'une réalisation : une clé explicite, par exemple `argument.premise.2`.
- Version/digest d'une instance : lié aux versions des définitions, aux bindings et aux choix de mise en page. Les empreintes restent dans les artefacts **internes**.

Un même template réutilisé trois fois donne **trois chemins d'instance**. Le fait de réutiliser la définition ne crée pas de réutilisation implicite du même fait ni de la même phrase.

## Politique de répétition

| Cas | Autorisé ? | Règle |
| --- | --- | --- |
| `preuve × 3`, trois preuves explicitement liées | Oui | 3 enfants distincts, stable order, cardinalité exacte |
| `preuve × 3` avec deux preuves seulement | Non | Refus, sans remplissage synthétique |
| `preuve × N` sur collection approuvée de N éléments | Oui | `N` découle seulement de la longueur de la collection explicitement fournie ; bornes vérifiées |
| Répéter la même phrase trois fois | Pas par défaut | Uniquement si le contrat et les clés indiquent explicitement cette répétition ; alerte de redondance |
| Auto-chercher les trois exemples les plus pertinents | Non | Ce serait une sélection factuelle interdite à Spek |

## Expansion et validation, ordre impératif

1. Vérifier identités, versions exactes, signatures/empreintes attendues des ressources internes et chemins autorisés.
2. Valider le graphe de définitions (absence de cycles, profondeur et fan-out plafonnés).
3. Résoudre les références de templates, développer les répétitions avec les seules instances fournies.
4. Valider cardinalités et compatibilité de chaque slot enfant/texte, y compris la compatibilité avec les types existants de `layouts/*.json`.
5. Établir pour chaque feuille `realization_key`, `request_ref` et autorisations amont ; refuser les clés conflictuelles.
6. Construire le plan de dialogue et vérifier la compatibilité des forces et contraintes SemantiK avant tout appel.
7. Réaliser, valider chaque résultat, puis assembler le rendu sans réécriture.

## Bornes de sécurité proposées (à calibrer par tests)

- Profondeur par défaut : **8** ; nombre de nœuds résolus : **2 000** ; répétitions par nœud : **100** ; taille textuelle par feuille : selon le contrat slot et SemantiK.
- Ces chiffres sont **appliqués au moteur récursif** ; le compilateur historique conserve ses règles propres. Ils doivent être configurables dans la politique versionnée, tout en empêchant les entrées de les relever sans autorité.
- Refus d'un chemin/ID non sûr, d'une ressource arbitraire distante et de tout template contenant du code exécutable.

## Compatibilité des modèles actuels

`kristal.layout-article-source/0.1` demeure pris en charge par le moteur historique. Une migration future produira une **projection dérivée** de l'arbre résolu vers les sections compatibles du compilateur actuel, mais elle devra refuser explicitement les compositions dont les règles de jointure/rendu ne peuvent pas être représentées sans perte. Aucune conversion silencieuse « paragraphes imbriqués → cartes plates ».
