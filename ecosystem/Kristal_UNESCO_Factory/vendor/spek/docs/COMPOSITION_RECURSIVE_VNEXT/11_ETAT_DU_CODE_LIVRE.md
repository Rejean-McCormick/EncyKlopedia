# 11 — État réel du code Spek vNext

**Statut : implémentation locale partielle, intégrée au dépôt (2 novembre 2026).**

Ce document distingue le moteur **réellement exécutable** du chantier nécessaire à une publication complète.

## Implémenté

- `spek/composition/engine.py` : chargeur local strict, validation de définitions/instances versionnées, expansion récursive déterministe, bornes de profondeur/nœuds/répétition, cardinalités et refus des clés de réalisation dupliquées.
- Une catégorie `template_library/rhetorical/` **implémentée** contenant 62 définitions versionnées (10 historiques + 52 modèles issus de l’inventaire scientifique) ; aucune sélection implicite de faits.
- `template_library/wiki/templates/article.json` : exemple de template de catégorie *Wiki* qui inclut des templates *rhetorical* via le **même moteur**.
- Plan privé de dialogue par feuille, fondé sur `spek/slot_dialogue.py`, avec contraintes de force et de types de blocs SemantiK ; aucune création de graphe sémantique.
- `spek/composition/semantik_adapter.py` : import et vérification par paire `CommunicationRequest` / `CommunicationResult`, réutilisant les règles SemantiK de `spek/semantik_transfer.py` (couverture, langue, sources et identité de résultat).
- Assembleurs HTML et Markdown **privés**, sans identifiants techniques ou empreintes dans la surface lecteur ; phrases inchangées, pas de phrase de secours. Le mode `flow` réduit les répétitions visuelles de titres, le mode `two_column` est réactif, `stack` et `compact_list` sont disponibles.
- Commandes CLI `compose-check`, `compose-dialogue`, `compose-import-semantik`, `compose-preview`.
- Accès graphique facultatif « Prévisualiser une composition récursive… » dans les options SemantiK de l'onglet Aperçu Wiki (l'opérateur sélectionne explicitement les fichiers).
- Contrat historique `kristal.layout-article-source/0.1`, les 27 layouts précédents, le registre des 127 propositions et les composants existants **conservés**.

## Contrat normatif de cette version

- Définitions : `spek.template-graph/1.0`, sous `template_library/<category>/templates/<template>.json` ; références exactes comme `rhetorical.evidence@1.0.0`.
- Instances : `spek.composition-instance/1.0`, avec `authority: editorial_bindings_explicit_not_approved`, `instance_id`, `template_ref`, `bindings` et éventuellement `presentation`.
- Les bindings textuels portent `node_type: text_slot`, `realization_key` et `communication_request_ref` (référence à un fichier, pas une autorisation de faits).
- Les enfants portent `node_type: template_ref` ; les répétitions portent `node_type: repeat`, une référence exacte et `instances` explicitement énumérées.
- Seul `join_mode: block` est accepté. `inline-safe` est refusé : Spek ne fusionne pas grammaticalement des fragments incomplets.
- Limites codées : profondeur de résolution **8**, nœuds résolus **2 000**, répétitions **100**, fichiers de définition **2 Mo**. Les valeurs ne sont pas élevées par les entrées.

## Exemples exécutables

Les exemples sont dans `docs/COMPOSITION_RECURSIVE_VNEXT/exemples/`.

```powershell
cd C:\mycode\Spek_Semantic-publishing\Spek

py -3 -m spek compose-check --instance docs\COMPOSITION_RECURSIVE_VNEXT\exemples\wiki-deux-arguments-six-preuves.instance.json

py -3 -m spek compose-dialogue --instance docs\COMPOSITION_RECURSIVE_VNEXT\exemples\wiki-deux-arguments-six-preuves.instance.json --language fr --out C:\Temp\spek-dialogue-prive.json

py -3 -m spek compose-preview --instance docs\COMPOSITION_RECURSIVE_VNEXT\exemples\wiki-deux-arguments-six-preuves.instance.json --realizations docs\COMPOSITION_RECURSIVE_VNEXT\exemples\wiki-fractal-realizations-FICTIVES.json --language fr --out C:\Temp\spek-aperçu-vnext
```

**Important :** les phrases de `wiki-fractal-realizations-FICTIVES.json` sont des *fixtures rédigées manuellement* uniquement pour illustrer le rendu. Ce ne sont pas des phrases produites par SemantiK, encore moins des assertions de Kristals réels.

Pour vérifier de véritables résultats SemantiK déjà produits :

```powershell
py -3 -m spek compose-import-semantik --instance chemin\composition.instance.json --requests-dir chemin\requests --results-dir chemin\results --language fr --out C:\Temp\realizations-vnext-prive.json
```

Les fichiers `requests/<nom>.json` doivent correspondre aux références **explicitement fournies** dans l'instance. La commande refuse les résultats non conformes et ne publie rien.

## Toujours à faire avant l'objectif Wiki complet

1. Réaliser l'analyse canonique approfondie des **122 Kristals** restants et soumettre les choix éditoriaux aux contrôles externes (le registre contient 127 propositions, non 127 assignations approuvées).
2. Produire et approuver les `CommunicationRequest` propres aux feuilles et aux assertions sélectionnées. Spek ne les déduit pas.
3. Installer un **RuntimeSet GF/PGF complet et qualifié**, puis connecter sa réalisation directe au moteur récursif. L'import de résultats existants est opérationnel ; **l'appel runtime vNext direct n'est pas inclus**.
4. Qualifier les blocs et sorties documentaires de bout en bout, puis étendre le rendu récursif aux formats PDF/LaTeX et au compilateur collectif Wiki lorsque leur fidélité sera démontrée.
5. Relier les étapes d'approbation au Manager (C1/C2/C3), et conserver GitHub Wiki comme opération distincte. Le rendu privé n'est jamais un consentement à publier.

**Aucune assertion n'est créée, aucune autorisation n'est attribuée et aucun push GitHub n'est effectué par ce moteur.**

## Inventaire scientifique ajouté

Les 52 nouvelles définitions expriment des relations rhétoriques déclarées. Le moteur valide le marqueur `editorial_relation` (relation et références explicites), **pas la vérité sémantique** de ces références. Voir [12 — Inventaire scientifique](12_INVENTAIRE_SCIENTIFIQUE_RHETORIQUE.md).

## Mise à jour du 3 novembre 2026 — Modèles discursifs par template

- Les **62 contrats rhétoriques** disposent désormais de `discourse_model: spek.discourse-model/1.0` (mouvements, dépendances acycliques, point focal, paragraphes, contraintes de transitions).
- Les modèles `toulmin-compact`, `rst-concession`, `rst-cause` et `pdtb-temporal-precedence` acceptent un slot de liaison `bridge` facultatif **réalisé explicitement par SemantiK**.
- Le plan de dialogue privé indique fonction, nuclearité et groupe de paragraphe, sans ajouter de fait ni de connecteur.
- Commandes : `discourse-audit` et `compose-source-check` ; accès graphique à l’audit des mouvements rhétoriques.
- **Aucune qualification sémantique des liens** : le graphe structurel validé n'est pas une démonstration argumentative.
- Vérification d’existence de référence effectuée sur le graphe v11 réel d’Agriculture ; **aucune réalisation GF/PGF réelle** obtenue.

Voir [14](14_GRAMMAIRE_DU_DISCOURS.md) et [15](15_SOURCES_REELLES_ET_LIMITES_SEMANTIK.md).
