# 08 — Plan d'implémentation et migration

**Plan actualisé : premières étapes codées, chaîne complète encore inachevée.** Voir [11 — État réel du code livré](11_ETAT_DU_CODE_LIVRE.md) pour distinguer le moteur récursif et la qualification éditoriale externe.

## Politique de migration

- **Ne pas remplacer** `spek/core.py`, les 27 layouts et leurs parcours de build en une seule opération.
- **Préserver** les registres IA actuels et les 127 propositions ; aucune conversion en assignation approuvée.
- Ajouter une **version distincte de contrat** pour les définitions/instances récursives ; validation fail-closed, pas d'interprétation heuristique d'anciens JSON.
- Un même code peut rendre les vieux formats et le nouveau pendant la transition. Pas de migration silencieuse de données canoniques.

## Phases ordonnées

**Progrès au 2026-11-02 :** phase 1 (AST et catalogue), phase 2 (plan par feuille/import vérifié) et partie HTML/Markdown de la phase 3 implémentées. Phase 4 : accès GUI facultatif, sans conversion silencieuse du compilateur historique. Phase 5 : non réalisée.

### Phase 0 — Valider cette spécification

- Accepter les invariants, le découpage et les frontières d'autorité.
- Trancher les points ouverts de l'ADR : `join_mode`, bornes de récursion, choix des blocs autorisés et politique de répétition.
- Livrable : ADR acceptée ; aucun code.

### Phase 1 — Contrats, validateurs et AST

- Ajouter définitions versionnées `rhetorical/` à la bibliothèque, plus chargeur local strict.
- Parser `Definition` et `Instance` dans des objets typés ; validation cycles, cardinalités, références, ids, versions.
- Construire `ResolvedComposition` déterministe, **sans appel à SemantiK ni rendu**.
- Livrable : tests unitaires avec exemples `argument ×3`, comparaison imbriquée et cas invalides.

### Phase 2 — Générateur de dialogue par feuille

- Étendre la couche `slot_dialogue.py` à un arbre de feuilles ; conserver les contraintes existantes de `CommunicationRequest/1.0`.
- Fournir `RealizationPort` et adaptateur SemantiK ; aucun changement opportuniste à SemantiK sans besoin de contrat démontré.
- Livrable : plan reproductible `instance_path → request_ref → constraints` et tests d'incompatibilité.

### Phase 3 — Présentation rhétorique

- Développer un renderer sur AST résolu avec `visual_role` et `join_mode` stricts.
- HTML + Markdown Wiki en premier, PDF/TeX ensuite sans dégradation sémantique.
- Ajouter navigation réelle, accessibilité et protection stricte des données internes.
- Livrable : argument à trois preuves **sans titres répétés**, comparaison en colonnes et en flux.

### Phase 4 — Compatibilité et intégration UI

- Conserver l'import et le rendu des `article.json` plats pour les anciens projets.
- Dans l'atelier : vue **Plan / Structure / Texte SemantiK / Publication** ; les détails du graphe restent avancés.
- Ajouter journal privé de couverture et diff de composition sans exposer identifiants internes dans l'aperçu lecteur.
- Livrable : scénario complet sur un Kristal pilote explicitement choisi et épinglé.

### Phase 5 — Qualification de la chaîne éditoriale

- Requête SemantiK qualifiée, conformité des blocs, sélection/approbations externes.
- Produire `Home.md`, `_Sidebar.md`, pages `Kristal-<slug>.md` et manifest interne pour la collection visée.
- Vérifier C1/C2/C3 via Manager ; Spek ne pousse pas GitHub par défaut.
- Livrable : candidat Wiki vérifié sur un Kristal, puis extension contrôlée aux 127.

## Structure de code actuelle et extensions proposées

```text
Spek/
  template_library/rhetorical/...
  spek/composition/              # AST, résolution, validation
  spek/semantik_adapter/         # ACL SA, ports et conformité
  spek/presentation/             # arbre de rendu, styles par sortie
  spek/legacy_adapter.py         # contrat plat -> chemin historique ou proxy compatible
  tests/test_composition_*.py
  docs/COMPOSITION_RECURSIVE_VNEXT/ (ce dossier)
```

Les modules existants `spek/slot_dialogue.py`, `spek/render.py`, `spek/wiki.py`, `spek/studio_gui.py` devront être adaptés, pas supprimés sans migration.

## Définition de « terminé »

Un parcours démontré avec **faits effectivement sélectionnés**, arbre de templates réellement résolu, petites phrases SemantiK réelles et conformes, lecteur Wiki fluide, preuves internes traçables, contrôles de divulgation et autorisations externes. Une maquette HTML ou une liste de templates ne suffit pas.

## Non-objectifs de cette évolution

- Choisir les 127 plans depuis l'analyse runtime des Kristals.
- Développer un nouveau modèle neuronal générant des paragraphes.
- Remplacer GF/PGF ou le Runtime Orchestrator.
- Construire une infrastructure microservices ou un moteur de workflow de publication concurrent du Manager.
