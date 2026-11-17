# 03 — Catégorie de templates rhétoriques

**Statut : 62 définitions exécutables au total (10 historiques + 52 modèles documentés) dans Spek vNext.** Les templates sont stockés dans `template_library/rhetorical/templates/` avec `spek.template-graph/1.0`. Le catalogue ci-dessous reste une description éditoriale de leurs intentions ; voir les JSON pour les slots normatifs.

## Placement dans la même bibliothèque

```text
template_library/
  wiki/
  scientific/
  educational/
  report/
  book/
  rhetorical/
    category.json                 # catégorie de même rang, une fois implémentée
    templates/
      assertion.json
      definition.json
      argument-evidence.json
      comparison-narrative.json
      observation-interpretation.json
      qualification.json
      transition.json
      synthesis.json
      conclusion.json
```

Cette proposition **n'introduit pas un deuxième compilateur**. Les templates `rhetorical` sont des définitions appelables comme sous-templates par les autres catégories, avec les **mêmes slots, règles de cardinalité, types et versions**.

## Catalogue de départ

| Template proposé | Organisation déterministe | Composition enfant typique | Rendu possible |
| --- | --- | --- | --- |
| `rhetorical.assertion` | Proposition principale + éventuelle portée | `text:claim`, `text:scope` | Phrase principale avec complément discret |
| `rhetorical.definition` | Notion + définition + limite | `text:term`, `text:definition`, `qualification` | Paragraphe définitoire, sans titre superflu |
| `rhetorical.argument-evidence` | Thèse → preuves × N → inférence → objection → conclusion | `assertion`, `evidence × N`, `qualification`, `conclusion` | Flux argumentatif, paragraphes ou liste compacte |
| `rhetorical.comparison-narrative` | Question → critère partagé → A → B → synthèse → limites | `question`, `criteria`, `approach-a`, `approach-b`, `conclusion` | Deux colonnes ou paragraphe comparatif |
| `rhetorical.observation-interpretation` | Observation → interprétation → vérification → limites | `observation`, `interpretation`, `qualification` | Progression sans nouvelles inférences |
| `rhetorical.evidence` | Énoncé de preuve + provenance contrôlée + portée | `evidence`, `scope` | Phrase de preuve et indice de source autorisé |
| `rhetorical.qualification` | Limite, incertitude ou exception | `qualification` | Encadré discret ou phrase finale de réserve |
| `rhetorical.transition` | Transition non factuelle vers un thème déjà prescrit | `text:bridge` | Connecteur discret entre paragraphes ; rien d'ajouté au fond |
| `rhetorical.synthesis` | Résultats déjà sélectionnés + synthèse fournie | `conclusion`, `qualification` | Paragraphe de clôture court |
| `rhetorical.conclusion` | Résultat final et condition | `conclusion`, `scope` | Fin d'argument, pas un nouveau chapitre |

Les dix noms sont maintenant **implémentés** dans le moteur récursif, selon les slots/version du catalogue réel. Les contraintes typées de certaines familles spécialisées devront être écrites explicitement au moment de l'implémentation.

## Principes de mise en page rhétorique

1. **Le titre logique peut devenir le premier énoncé saillant.** `statement` comme `<strong>` ou premier paragraphe, plutôt qu'un nouveau titre de section.
2. **Un groupe rhétorique n'oblige pas un `<section>` visible.** Un template enfant peut s'intégrer à son parent sans répéter bordure, icône, en-tête ou étiquette technique.
3. **Les preuves répétées ne deviennent pas automatiquement des cartes.** Elles peuvent être des phrases successives ou une liste si la politique l'autorise.
4. **La comparaison n'impose pas deux colonnes.** Le contexte de lecture et la taille de l'écran déterminent la disposition visuelle, mais pas le contenu ni l'ordre logique des éléments.
5. **Les limites ne disparaissent pas au prétexte de rendre le texte fluide.** Elles restent visibles et conformes au statut épistémique.
6. **Une rubrique purement visuelle est non factuelle.** Toute phrase indiquant un fait doit provenir d'une réalisation.

## Contrôle de répétition

Un parent peut inclure : `argument-evidence × 2`, chaque argument contient `evidence × 3`, puis un `synthesis`. Cela produit deux arguments et six blocs de preuve **si et seulement si** six éléments sont explicitement fournis et compatibles. Le moteur ne fait ni multiplication sémantique ni recherche automatique.

## Pas de paraphrases artistiques

Deux occurrences d'un même motif ont la même **fonction rhétorique** mais reçoivent les réalisations propres à leurs obligations. Une alternative de wording, une variation stylistique ou une suppression de clause sous prétexte de fluidité n'appartient pas à Spek. Les choix linguistiques internes permis à SemantiK demeurent bornés par son contrat déterministe.


## Extension documentée

Voir [12 — Inventaire scientifique](12_INVENTAIRE_SCIENTIFIQUE_RHETORIQUE.md) et `template_library/rhetorical/research-inventory.json` pour les 52 modèles ajoutés, leurs sources, conditions et limites.
