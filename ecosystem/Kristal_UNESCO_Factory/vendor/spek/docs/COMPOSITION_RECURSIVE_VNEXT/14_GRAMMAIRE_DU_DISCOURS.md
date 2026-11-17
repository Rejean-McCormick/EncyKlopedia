# 14 — Grammaire du discours : 62 templates rhétoriques exécutables

**Version :** 3 novembre 2026 — `spek.discourse-model/1.0` (adaptation Spek, non normative).  
**Statut :** implémenté pour les 62 templates existants, vérifiable par CLI, utilisable pour les aperçus privés HTML et Markdown.  
**Non inclus :** vérification des relations sémantiques, création de requêtes factuelles, exécution GF/PGF, autorisation de publication, certification des standards cités.

## Motivation

Un enchaînement de seize phrases ne fait pas automatiquement un texte argumentatif. Le moteur doit connaître les **mouvements** et les **liens** du discours, tout en préservant le principe fondamental : **Spek organise ; SemantiK réalise les phrases ; le responsable éditorial sélectionne les sources et déclare les relations.**

RST, PDTB, Toulmin et Walton sont ici **des références théoriques distinctes**. Le contrat Spek leur emprunte des distinctions de structure ; il ne prétend pas exécuter leurs procédures de validation ou reproduire officiellement leur annotation.

## Nouveaux champs dans les 62 définitions

Chaque fichier `template_library/rhetorical/templates/*.json` possède désormais un `discourse_model` :

| Élément | Contrat | Effet réel |
| --- | --- | --- |
| `format` | `spek.discourse-model/1.0` | Validation stricte du modèle |
| `relation_tag` | Identique au `rhetorical_contract` existant, ou `structural.*` pour les dix anciens | Empêche la substitution silencieuse d'une relation |
| `focus_slot` | Slot principal déclaré | Point vers lequel convergent les dépendances |
| `moves[]` | Un mouvement **par slot**, dans l'ordre | Fonction, nuclearité, groupe de paragraphe, rôle visuel |
| `links[]` | Liens orientés vers le mouvement focal, sans cycle | Relations du discours déclarées, **non prouvées** |
| `paragraph_groups[]` | Partition exacte des slots, ordonnée | Coupures de paragraphes dans `flow`, groupes logiques ailleurs |
| `cohesion` | Aucune transition implicite ; aucune réécriture | Les connecteurs doivent être des unités SemantiK explicites |
| `semantic_review` | Questions critiques et avertissement | Signale ce que Spek ne peut pas vérifier |

Extrait **simplifié** de `rhetorical.toulmin-compact@1.0.0` :

```json
{
  "discourse_model": {
    "format": "spek.discourse-model/1.0",
    "relation_tag": "toulmin.claim-grounds-warrant",
    "focus_slot": "claim",
    "paragraph_groups": [
      ["claim", "grounds", "bridge"],
      ["warrant", "backing"],
      ["qualifier", "rebuttal"]
    ],
    "cohesion": {
      "connectives": "only_explicit_semantik_realizations",
      "rewrite_existing_phrases": false,
      "infer_relations_from_adjacent_slots": false,
      "text_without_realization": "refuse",
      "transition_slot_policy": "optional_explicit_text_slot_only"
    }
  }
}
```

Le fichier complet possède également **sept mouvements** et leurs liens. La preuve `grounds` soutient la thèse ; la garantie `warrant` doit légitimer l'inférence ; le soutien `backing` vise la garantie, et non directement la thèse ; les réserves en limitent la portée. Spek valide ces **liens déclarés** comme un graphe dirigé acyclique. Il ne décide pas que les assertions reliées prouvent véritablement une conclusion.

## Les quatre formes enrichies d'une liaison explicite

Quatre modèles disposent maintenant d'un slot `bridge` **facultatif**, de type `relation` :

- `toulmin-compact`
- `rst-concession`
- `rst-cause`
- `pdtb-temporal-precedence`

Quand ce champ est rempli, il exige une vraie `communication_request_ref` ainsi qu'une `realization_key` distincte. Le dialogue privé indique à SemantiK qu'il doit produire une unité de type relation, sous ses contrats existants. L'import refuse la moindre réalisation manquante ou non conforme.

**Attention :** Spek ne génère jamais de « cependant », « donc », « puisque » ou autres connecteurs à partir du seul nom du template. Une phrase de liaison suppose une requête sémantique autorisée. Le simple marqueur `editorial_relation` ne démontre pas cette autorisation.

## Nuclearité et genres : ne pas confondre les niveaux

- Les adaptations RST distinguent **noyau**, **satellite** et parfois **multinucléarité**.
- Les adaptations PDTB conservent leurs liens discursifs, mais la description de `moves` dans Spek n'est **pas** une annotation officielle PDTB.
- Les modèles Toulmin/Walton relient thèse, données, garantie, soutien, objections et qualifications.
- Les modèles CARS/DITA portent sur des **mouvements de genre**, pas des relations de causalité démontrées.
- Les dix templates originaux conservent un statut de **structure de présentation** et leurs anciennes instances sont compatibles.

## Déroulement et règles de refus

1. `Library` valide le contrat, les rôles, les groupes, l'ordre et les liens de chacun des 62 modèles.
2. `resolve()` vérifie les bindings et les déclarations de relation existantes, sans sélectionner les faits.
3. `dialogue_plan()` ajoute au plan **privé** la fonction de chaque petite phrase (`discourse.function`, `nuclearity`, `paragraph_group`). Les contraintes SemantiK existantes sont conservées et intersectées, sans modifier le graphe ni les obligations.
4. `compose-import-semantik` vérifie chaque couple requête/résultat complet et sa couverture.
5. `compose-preview` rend **mot pour mot** les textes reçus et les groupes de paragraphes prescrits. Aucune reformulation, invention ou phrase de remplacement.
6. L'audit `discourse-audit` compte les structures et les liens **non vérifiés** sans divulguer les références source ni les hashes.

Refus : champ orphelin, répétition abusive, absence de réalisation, lien cyclique, mouvement inconnu, paragraphe ne couvrant pas tous les slots, étiquettes techniques dans le rendu, source non trouvée si le contrôle explicite est demandé.

## Commandes PowerShell

Depuis le répertoire `Spek` :

```powershell
$ex = 'docs\COMPOSITION_RECURSIVE_VNEXT\exemples'

py -3 -m spek rhetoric-list --family argument
py -3 -m spek discourse-audit --instance "$ex\toulmin-avec-liaison-FICTIVE.instance.json"

$out = Join-Path $env:TEMP "spek-rhetorique-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
py -3 -m spek compose-preview `
  --instance "$ex\toulmin-avec-liaison-FICTIVE.instance.json" `
  --realizations "$ex\toulmin-avec-liaison-FICTIVE-realizations.json" `
  --language fr --out "$out"
Start-Process "$out\index.html"
```

L'exemple utilise **neuf phrases fictives fournies manuellement**, dont une phrase de liaison. Il n'est **pas** une preuve de génération GF/PGF. On peut aussi lancer l'audit via **Aperçu Wiki → Options de préparation SemantiK → Auditer les mouvements rhétoriques…**.

## Compatibilité et versionnement

Les anciennes instances restent résolubles : `bridge` est facultatif. Nous avons enrichi les métadonnées et, pour certains templates, le découpage des paragraphes, sans modifier les identifiants `@1.0.0`. **Pour une reproductibilité stricte des aperçus, il faut donc épingler aussi le commit ou l'empreinte du dépôt Spek.** Une future migration de catalogue devra permettre plusieurs versions de définitions côte à côte sans réinterpréter une composition déjà approuvée.

## Fondements documentaires (adaptations non certifiées)

- RST : [Mann & Thompson, introduction](https://www.sfu.ca/rst/01intro/intro.html) et [définitions](https://www.sfu.ca/rst/01intro/definitions.html).
- PDTB 3.0 : [Penn Discourse Treebank, Annotation Manual](https://catalog.ldc.upenn.edu/docs/LDC2019T05/PDTB3-Annotation-Manual.pdf).
- Toulmin : [Purdue OWL, Toulmin Argument](https://owl.purdue.edu/owl/general_writing/academic_writing/historical_perspectives_on_argumentation/toulmin_argument.html).
- Voir [12 — Inventaire scientifique](12_INVENTAIRE_SCIENTIFIQUE_RHETORIQUE.md) pour les autres sources et les distinctions entre standards et théories.
