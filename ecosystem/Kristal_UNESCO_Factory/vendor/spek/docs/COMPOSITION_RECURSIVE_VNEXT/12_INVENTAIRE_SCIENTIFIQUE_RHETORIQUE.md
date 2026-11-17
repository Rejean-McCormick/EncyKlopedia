# Inventaire scientifique des formes rhétoriques — Spek vNext

**Statut : étude documentaire et adaptations Spek, non certification.**

La démonstration précédente de 16 phrases prouve l'assemblage, **pas** la qualité rhétorique. Ce catalogue ancre les modèles dans des sources identifiables, et sépare cinq niveaux :

1. **Relation de cohérence** : les segments sont-ils une concession, une élaboration, une explication, etc. ? (RST)
2. **Relation discursive annotée** : les propositions ont-elles un rapport temporel, conditionnel, contrastif ou expansif ? (PDTB 3.0)
3. **Schéma d'argumentation** : quelles prémisses, garanties et objections soutiennent la conclusion ? (Toulmin, Walton)
4. **Genre / mouvement documentaire** : dans quelle progression s'inscrit l'article ? (Swales CARS, OASIS DITA)
5. **Acte et réalisation linguistique** : quelle intention et quelle forme SemantiK doit-il réaliser ? (ISO 24617-2 comme repère conceptuel, contrat SemantiK réel comme interface normative)

Ce ne sont **pas cinq moteurs** : tous ces niveaux sont représentés par la même grammaire `spek.template-graph/1.0`, avec slots, cardinalités, sous-templates et répétitions.

## Sources spécialisées consultées

- **RST** — Théorie des structures rhétoriques — Mann & Thompson, définitions officielles (SFU) (theorie) : https://www.sfu.ca/rst/07french/definitions.html
- **PDTB** — Penn Discourse Treebank 3.0, manuel des relations (taxonomie linguistique) : https://catalog.ldc.upenn.edu/docs/LDC2019T05/PDTB3-Annotation-Manual.pdf
- **TOULMIN** — Purdue OWL, modèle de Toulmin (modele argumentatif) : https://owl.purdue.edu/owl/general_writing/academic_writing/historical_perspectives_on_argumentation/toulmin_argument.html
- **WALTON** — Walton et Macagno, classification des schémas argumentatifs (recherche argumentative) : https://journals.sagepub.com/doi/full/10.1080/19462166.2015.1123772
- **CARS** — University of Massachusetts Amherst, modèle CARS de Swales (modele de genre) : https://www.umass.edu/writing-center/resources/creating-research-space
- **DITA** — OASIS DITA 1.3, types de contenu technique (standard technique) : https://docs.oasis-open.org/dita/dita/v1.3/csd01/part2-tech-content/archSpec/technicalContent/dita_technicalContent_InformationTypes.html
- **ISO** — ISO 24617-2:2020, actes de dialogue (norme) : https://www.iso.org/standard/76443.html
- **W3C** — W3C WAI, hiérarchie des titres (recommandation d’accessibilité) : https://www.w3.org/WAI/tutorials/page-structure/headings/

Le modèle RST classique et les usages du PDTB ont été conçus pour l'**analyse de discours**, pas comme des recettes permettant d'inférer automatiquement des relations vraies entre deux assertions. Nos templates sont des **adaptations éditoriales de Spek**. L'ISO est un standard, mais nous n'implémentons pas DiAML ni ne revendiquons de conformité ISO. De même les gabarits `dita-*` ne sont **pas des documents DITA XML**.

## Inventaire livrable

| Famille | Modèles implémentés | Ce que le modèle formalise |
|---|---:|---|
| coherence | 20 | Noyau, satellite, concession, preuve, cause, condition, séquence, etc. |
| discourse | 10 | Contraste, analogie discursive, exception, expansion et relations temporelles. |
| argument | 11 | Thèse, données, garantie, soutiens et schémas Walton avec questions critiques. |
| genre | 8 | Introduction de recherche, concepts, tâches, références et dépannage. |
| epistemique | 3 | Observation, hypothèse, mesure, incertitude, perspectives. |
| original_vnext | 10 | Les 10 motifs déjà présents dans Spek vNext. |

### Catalogue des modèles exécutables

Les modèles sont disponibles dans `template_library/rhetorical/templates/`. Le registre machine est `template_library/rhetorical/research-inventory.json`.

| ID Spek | Base conceptuelle | Slots requis | Précaution |
|---|---|---|---|
| `rhetorical.toulmin-claim-counterclaim` | toulmin.rebuttal | claim, counterclaim, response, limits | Ne pas présenter une objection comme réfutée sans réponse autorisée. |
| `rhetorical.toulmin-compact` | toulmin.claim-grounds-warrant | claim, grounds, warrant | Le warrant est un lien argumentatif fourni, pas déduit. |
| `rhetorical.toulmin-warrant-check` | toulmin.warrant-backing | grounds, warrant, backing | La garantie et son soutien sont des éléments distincts. |
| `rhetorical.walton-analogy` | walton.analogy | source_case, target_case, relevant_similarity, inference, limits | Une analogie ne constitue pas une preuve de causalité. |
| `rhetorical.walton-cause-effect` | walton.cause-effect | cause_claim, evidence, effect, confounders | Ne pas afficher un lien de causalité non établi. |
| `rhetorical.walton-consequences` | walton.consequences | choice, benefits, costs | Ne pas convertir des effets hypothétiques en résultats avérés. |
| `rhetorical.walton-example` | walton.example | examples, generalization, limits | Ne pas généraliser sans échantillonnage approprié. |
| `rhetorical.walton-expert-opinion` | walton.expert-opinion | domain, expert_statement, inference, qualification | La compétence, fiabilité et indépendance sont à évaluer hors du rendu. |
| `rhetorical.walton-position-to-know` | walton.position-to-know | source_position, testimony, inference, reliability | Témoignage attribué, fiabilité non présumée. |
| `rhetorical.walton-practical-reasoning` | walton.practical | goal, actions, expected_effect, risks | L’action proposée est une recommandation conditionnelle, pas une prescription automatique. |
| `rhetorical.walton-sign` | walton.sign | indicator, rule, inference, alternative | Un indice n’établit pas nécessairement la conclusion. |
| `rhetorical.rst-antithesis` | rst.antithesis | rejected, retained | Ne pas présupposer une incompatibilité inexistante. |
| `rhetorical.rst-background` | rst.background | background, nucleus | Le contexte doit être nécessaire à la compréhension. |
| `rhetorical.rst-cause` | rst.cause | cause, effect | Lien causal explicitement établi, jamais déduit de l’ordre. |
| `rhetorical.rst-circumstance` | rst.circumstance | circumstance, situation | Ne pas inventer de cadre temporel ou spatial. |
| `rhetorical.rst-concession` | rst.concession | conceded, main | Ne pas effacer la validité de la concession. |
| `rhetorical.rst-condition` | rst.condition | condition, consequent | Ne pas transformer une association en implication établie. |
| `rhetorical.rst-contrast` | rst.contrast | a, b, criterion | Critère commun fourni explicitement. |
| `rhetorical.rst-elaboration` | rst.elaboration | nucleus, details | Les détails doivent concerner le noyau. |
| `rhetorical.rst-evaluation` | rst.evaluation | situation, evaluation | L’évaluation doit rester attribuée, pas naturalisée en fait. |
| `rhetorical.rst-evidence` | rst.evidence | nucleus, evidence | L’existence d’éléments de preuve ne certifie pas leur suffisance. |
| `rhetorical.rst-interpretation` | rst.interpretation | observation, interpretation | Ne pas confondre une observation et son interprétation. |
| `rhetorical.rst-justify` | rst.justify | statement, justification | Justification distincte des simples preuves de fait. |
| `rhetorical.rst-means` | rst.means | goal, means | Les moyens ne garantissent pas la réalisation du but. |
| `rhetorical.rst-preparation` | rst.preparation | preparation, nucleus | Amorce portant sur le contenu, pas de remplissage décoratif. |
| `rhetorical.rst-purpose` | rst.purpose | action, purpose | Le but est attribué à la source. |
| `rhetorical.rst-result` | rst.result | situation, result | Différencier conséquence causale et simple succession. |
| `rhetorical.rst-sequence` | rst.sequence | events | N’impose aucune date si elle n’est pas fournie. |
| `rhetorical.rst-solutionhood` | rst.solutionhood | problem, solution | Une solution proposée n’est pas nécessairement validée. |
| `rhetorical.rst-summary` | rst.summary | elements, summary | Résumé fourni par SemantiK sous obligations explicites, pas synthétisé automatiquement. |
| `rhetorical.rst-unless` | rst.unless | statement, unless | L’exception doit être attestée. |
| `rhetorical.pdtb-conjunction` | pdtb.expansion.conjunction | items | La juxtaposition n’implique pas le même statut épistémique. |
| `rhetorical.pdtb-disjunction` | pdtb.expansion.disjunction | options | Les alternatives ne sont pas forcément exclusives. |
| `rhetorical.pdtb-exception` | pdtb.expansion.exception | general, exception | Portée exacte de l’exception obligatoire. |
| `rhetorical.pdtb-instantiation` | pdtb.expansion.instantiation | general, instances | Les exemples illustrent, ils ne prouvent pas une règle générale. |
| `rhetorical.pdtb-level-of-detail` | pdtb.expansion.level-of-detail | overview, detail | Chaque précision doit référer à l’aperçu. |
| `rhetorical.pdtb-negative-condition` | pdtb.contingency.negative-condition | absent_condition, consequence | La négation de la condition doit être explicite. |
| `rhetorical.pdtb-purpose` | pdtb.contingency.purpose | action, goal | But explicite, non inféré du résultat. |
| `rhetorical.pdtb-similarity` | pdtb.comparison.similarity | first, second, shared | Ne doit pas éliminer les différences. |
| `rhetorical.pdtb-temporal-precedence` | pdtb.temporal.asynchronous | earlier, later | N’implique pas la causalité. |
| `rhetorical.pdtb-temporal-synchronous` | pdtb.temporal.synchronous | first, second | Simultanéité attestée, ne suppose aucune influence. |
| `rhetorical.epistemic-measurement-context` | spek.measurement | measure, condition, uncertainty | Ne pas présenter une mesure sans contexte ou incertitude. |
| `rhetorical.epistemic-multiple-perspectives` | spek.multiple-perspectives | perspectives, limits | Aucun point de vue n’est implicitement privilégié. |
| `rhetorical.epistemic-observation-hypothesis` | spek.observation-hypothesis | observation, hypothesis, limits | L’hypothèse n’est pas un résultat. |
| `rhetorical.cars-introduction` | swales.cars | territory, gap, purpose | Lacune et contribution doivent être explicitement sélectionnées, pas inventées. |
| `rhetorical.cars-research-question` | swales.cars.question | context, gap, question, objective | La question est expressément autorisée; ne pas en inférer une. |
| `rhetorical.dita-concept` | dita.concept | term, definition | Adaptation éditoriale, pas document DITA XML conforme. |
| `rhetorical.dita-glossary` | dita.glossary | term, definition | Une entrée par acception, non une liste de synonymes. |
| `rhetorical.dita-reference` | dita.reference | identifier, description | Pas de garantie de compatibilité DITA XML. |
| `rhetorical.dita-task` | dita.task | objective, steps | Ordre des étapes explicitement fourni, pas inféré. |
| `rhetorical.dita-troubleshooting` | dita.troubleshooting | symptom, verification, resolution | Une cause possible ne doit pas être présentée comme cause démontrée. |
| `rhetorical.scientific-method-result` | dita.research-sequence | method, observations, interpretation, limits | Modèle Spek dérivé de pratiques documentaires, pas un type DITA normatif. |
| `rhetorical.argument-evidence` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.assertion` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.comparison-narrative` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.conclusion` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.definition` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.evidence` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.observation-interpretation` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.qualification` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.synthesis` | spek.original | voir définition | Motif vNext préexistant |
| `rhetorical.transition` | spek.original | voir définition | Motif vNext préexistant |

## Point capital : un nom de relation n'est pas une preuve

Une instance de nouveau template exige désormais `editorial_relation` :

```json
{
  "relation_tag": "rst.condition",
  "status": "declared_unverified",
  "source_assertion_refs": ["reference-source-1", "reference-source-2"]
}
```

- Spek vérifie la **présence et la forme** de cette déclaration et son exact accord avec le template.
- Spek **ne lit pas les assertions pour vérifier leur vérité ni l'existence effective du lien**, ce qui demeure externe (IA éditoriale, Manager et vérifications de provenance).
- Aucun template n'est appliqué automatiquement sur la base d'une ressemblance lexicale.
- L'absence de déclaration bloque la résolution du nouveau modèle.
- Ce marqueur n'autorise ni la réalisation GF/PGF ni la publication. Les marqueurs ne sont pas exposés dans le HTML.

Pour les arguments par expertise, analogie, conséquences, etc., le catalogue contient également des **questions critiques** inspirées de Walton, utiles à la revue humaine. Ces questions sont descriptives : Spek ne peut pas en deviner les réponses.

## Contraintes de mise en page et d'accessibilité

- `flow` assemble des phrases **déjà complètes** dans un flux, en conservant intégralement leur ponctuation et leur texte.
- `stack` sépare les mouvements ou étapes lorsque l'enchaînement visuel l'exige.
- `compact_list` et `two_column` conviennent aux listes et alternatives quand les données et la lecture le justifient.
- **Pas de connecteurs artificiels** « cependant », « par conséquent » insérés automatiquement : il faut les demander dans une réalisation SemantiK couverte par une obligation explicite.
- **Pas de multiplication des titres**, mais conserver les vrais titres hiérarchiques d'un document long pour l'accessibilité (W3C WAI).
- Une relation causale, temporelle ou de preuve n'est jamais déduite de l'ordre de deux paragraphes.
- La qualification épistémique et l'objection ne disparaissent pas sous prétexte de fluidité.

## Exemple beaucoup plus significatif

`exemples/toulmin-etude-fictive.instance.json` emploie un modèle Toulmin compact avec trois sous-templates `evidence`, une garantie, un soutien, une limite et une objection. `exemples/toulmin-etude-fictive-realizations.json` contient des phrases **entièrement fictives rédigées manuellement**, non produites par SemantiK. Il ne prouve donc que l'organisation et le rendu, pas la validité d'un argument réel.

```powershell
cd C:\mycode\Spek_Semantic-publishing\Spek
py -3 -m spek compose-check --instance docs\COMPOSITION_RECURSIVE_VNEXT\exemples\toulmin-etude-fictive.instance.json
$out = Join-Path $env:TEMP "spek-toulmin-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
py -3 -m spek compose-preview --instance docs\COMPOSITION_RECURSIVE_VNEXT\exemples\toulmin-etude-fictive.instance.json --realizations docs\COMPOSITION_RECURSIVE_VNEXT\exemples\toulmin-etude-fictive-realizations.json --language fr --title "Argument fictif — étude de démonstration" --out $out
Start-Process (Join-Path $out 'index.html')
```

## Ce qui manque toujours

Les 62 modèles sont des **contrats structurels exécutables** : ils ordonnent les formes de phrases et valident leurs types. Ce ne sont pas 62 schémas **sémantiquement qualifiés** contre des faits canoniques ; les déclarations éditoriales doivent être reliées à de vraies assertions et vérifiées en amont. La réalisation GF/PGF directe, la sélection éditoriale des faits et la publication C1/C2/C3 restent externes.

## Navigation dans Spek

```powershell
py -3 -m spek rhetoric-list
py -3 -m spek rhetoric-list --family argument
py -3 -m spek rhetoric-list --format json
```

Le [catalogue visuel](CATALOGUE_RHETORIQUE.html) complète cette vue. Les catégories vNext restent des templates imbriquables, et non une couche de rédaction libre.
