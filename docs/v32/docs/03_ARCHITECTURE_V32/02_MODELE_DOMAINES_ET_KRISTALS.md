# Modèle V32.1 — branche, sujet, îlot, état et assertion

**[CIBLE].** Référence prioritaire : [cinq objets](../09_FEDERATION_KRISTAL/01_MODELE_IDENTITES_ET_GRANULARITE.md).

La branche UNESCO classe les **concepts**; Wikidata identifie des **sujets**; Wikipédia apporte sources et passages; un **îlot Kristal** est un périmètre d'auteur/gouvernance, pas une ligne QID. Un îlot peut couvrir plusieurs sujets. Un sujet peut être expliqué par plusieurs îlots et rattaché à plusieurs branches. Les états exacts de chaque îlot appartiennent à leur auteur.

## Contrats cibles de travail EncyK (non normatifs)

- `Branch`, `Concept`, `ConceptRelation`, `AlignmentAssertion` : structure de navigation et identité candidate.
- `SubjectRef` : `wd:Q...` ou `namespace:local`, mais aucune allocation forcée d'un Kristal.
- `WikipediaSource` : `enwiki:page_id`, révision, locator, métadonnées d'accès.
- `CandidateRoute` et `SelectionDecision` : pertinence par couple avec chemin et contexte.
- `IslandRef`, `IslandCapability`, `IslandStateRef` : inventaire d'îlots lisibles et de leurs états.
- `Proposal`, `ProposalEvidence`, `ProposalCondition` : extrait de passe 2, **provisoire**.
- `AdmissionDecision`, `AdmissionReceipt` : uniquement lorsqu'une opération d'auteur qualifiée existe.
- `FederationSnapshot` et `ContextProjection` : références exactes et vues dérivées.

## Invariants pragmatiques

Conserver identités source, provenance, qualifiers et révision. Dédupliquer l'acquisition interbranches, mais **pas toutes les interprétations** : un article peut soutenir différents modèles de domaine. Pas de fait « globalement vrai » hors conditions simplement parce qu'il partage un QID. Les contradictions restent contextualisées.

## Ce qui n'est plus retenu

La suggestion historique `SubjectKristal(kristal_id unique par subject_key)` et la table EncyK `fact_claim` comme autorité définitive ne constituent plus le modèle V32.1. Elles peuvent servir de **référence de staging historique**, pas d'architecture du canon. Voir [répartition des autorités](../09_FEDERATION_KRISTAL/02_AUTORITES_FEDERATION_ET_LECTURE.md).
