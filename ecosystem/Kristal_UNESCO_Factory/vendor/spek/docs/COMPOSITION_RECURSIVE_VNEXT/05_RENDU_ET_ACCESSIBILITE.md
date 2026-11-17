# 05 — Rendu rhétorique, typographie et accessibilité

**Statut : le renderer récursif HTML et Markdown privé prend en charge** `flow`, `stack`, `two_column`, `compact_list`, les rôles `lead_sentence`, `paragraph`, `section_heading` et `qualification`. PDF et LaTeX récursifs restent à implémenter. `inline-safe` est explicitement refusé.

## Problème corrigé

L'empilement de templates n'implique pas l'empilement de cartes, de `<h2>`, de bordures et de badges. Un graphe documentaire peut contenir dix templates internes tout en se lisant comme trois paragraphes. **La structure interne reste riche ; la surface doit être sobre.**

## Trois hiérarchies séparées

1. **Composition** : parent/enfant et ordre des slots ; sans incidence directe sur les balises HTML.
2. **Rhétorique** : thèse, preuve, opposition, synthèse, précaution ; rôle communicatif, pas nécessairement un titre.
3. **Document sémantique** : niveaux réels des sections pour lecteurs d'écran, sommaire et navigation (`h1`…`h6`).

Le renderer respecte les trois. Un `heading` logique de template peut devenir une phrase principale visible en gras **seulement si** sa politique de présentation le prescrit et si le vrai document conserve une structure de titres accessible.

## Propriétés de rendu proposées

```json
{
  "visual_role": "lead_sentence",
  "surface": "paragraph",
  "emphasis": "strong",
  "show_template_label": false,
  "show_slot_label": false,
  "join_mode": "block",
  "layout_variant": "flow"
}
```

Exemple non normatif. Valeurs proposées : `visual_role ∈ {section_heading, lead_sentence, paragraph, supporting_sentence, qualification, caption, hidden_navigation_label}`. `layout_variant ∈ {flow, two_column, stack, compact_list, timeline}` selon la famille et le format. Les valeurs doivent être versionnées et validées ; pas de CSS libre dans des contrats importés.

## Emphase : titre transformé en élément principal

Un template `argument-evidence` contenant un champ logique « thèse » peut donner :

> **Les fonctions observées varient selon plusieurs mécanismes.** Une première preuve décrit l'état mesuré. Une seconde rapporte une variation indépendante. Une troisième explicite une limite. La conclusion demeure bornée par les observations retenues.

Les phrases de cet exemple sont **fictives** et ne constituent pas une réalisation SemantiK. Le renderer ne les a pas écrites : il n'a fait qu'appliquer une structure visuelle aux unités déjà présentes.

## Politique d'affichage par défaut

| Élément interne | Surface lecteur par défaut | Détail interne visible ? |
| --- | --- | --- |
| Document Wiki | Titre principal et sommaire accessibles | Non |
| Groupe rhétorique `argument` | Bloc narratif sans carte superflue | Non |
| Thèse | Première phrase saillante | Non |
| Trois preuves | Trois énoncés/liste compacte, ordre prescrit | Non |
| Objection | Phrase/encadré explicite, non escamotable | Non |
| Incertitude | Qualification visible | Non |
| Référence source autorisée pour divulgation | Lien éditorial compréhensible | Identifiants techniques non exposés |
| `source_digest`, `runtime_set`, `request_id`, `local_path` | Aucun | Jamais, même dans le DOM caché |

## Sorties

- **HTML** : titres structurants, paragraphes, listes, `<figure>` et notes selon le rôle de surface ; CSS à variables dont `--brand-primary: #1E6864`. Les composants répétés ne génèrent pas nécessairement une boîte chacun.
- **Markdown GitHub Wiki** : titres de vrai niveau seulement, texte en gras pour emphase, listes lisibles ; supprimer métadonnées et empreintes du contenu public. Vérifier l'absence de HTML brut secret.
- **LaTeX/PDF** : éléments correspondants (paragraphes, emphase, environnements de listes), sans tronquer des qualifications et sans supposer que la mise en colonnes est toujours réalisable en petit format.
- **Écran étroit et impression** : passage `two_column` → `stack` sans modifier contenu, ordre ni portée.

## Invariants d'accessibilité

- Un `h1` pour le titre du document, niveaux de sections cohérents et ancres stables ; pas d'utilisation de `<strong>` comme seul moyen d'exposer un vrai chapitre.
- Liens de sommaire navigables au clavier, focus visible, contraste suffisant avec `#1E6864`.
- Les comparaisons ont un ordre de lecture linéaire, même en colonnes ; les preuves numérotées exposent leur ordre logique au lecteur d'écran.
- Aucune preuve ou limite rendue uniquement par la couleur ou par une icône.
- Les textes alternatifs factuels, s'il y en a, sont soumis à la même contrainte de réalisation/approbation ; Spek ne doit pas inventer de faits dans `alt`.
- Une bascule « vue technique » appartient à l'atelier **privé**, jamais à l'HTML destiné à publication.

## Exposition des détails d'implémentation

Dans les pages lecteur, bannir les formes `referent:`, `urn:...`, `string:`, `layout-id@version`, les chemins locaux, les hash et les clés d'obligation. Les tests doivent scanner les sorties **entières**, y compris attributs, commentaires, JavaScript inline et données sérialisées, sans supposer qu'un élément `display:none` protège quoi que ce soit.
