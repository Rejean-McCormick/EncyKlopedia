# Version 1.5 — Grammaire discursive Spek (3 novembre 2026)

**Livraison intégrée** basée sur le dépôt utilisateur `SPEK_REPO_COMPLET_GRAMMAIRE_DISCURSIVE_2026-11-03(1).zip`.

## Fonctionnalités

- Remplacement du moteur Spek embarqué par son code vNext (62 contrats rhétoriques versionnés et le modèle `spek.discourse-model/1.0`). Les commandes historiques `build` et `verify-site` restent fonctionnelles.
- Un seul lancement continue de produire les 88 kristals v9 et les 88 volumes classiques Spek. L'étape finale `GRAMMAIRE DISCURSIVE SPEK` génère dans `07_DISCOURS/` les **instances éditoriales privées** pour chaque concept, en français et en anglais, ainsi que les plans de dialogue aux contraintes SemantiK.
- Un nouveau bouton **Ouvrir discours Spek** permet de consulter 176 pages d'aperçu (88 microthésaurus en FR et EN), filtrables par libellé ; le catalogue classique Spek et l'audit P3916 possèdent un lien vers ces pages.
- Texte de l'aperçu : les définitions UNESCO littérales quand elles sont présentes, sinon deux unités factuelles de présentation : libellé/métadonnée UNESCO, éventuellement description candidate Wikidata non révisée. Le rendu HTML est composé via le moteur natif Spek vNext.
- `07_DISCOURS/instances/fr|en` : instances de templates versionnées, **sans inférence de liens argumentatifs**.
- `07_DISCOURS/dialogue/fr|en` : plans de communication Spek → SemantiK pour les slots, sans créer de `CommunicationRequest` ni d'assertion canonique.
- `07_DISCOURS/source_bindings.jsonl` : traçabilité de la source UNESCO, et de la correspondance Wikidata candidate si disponible.
- `07_DISCOURS/manifest_discourse.json` : nombre exact de plans, prévisualisations, définitions disponibles et de résultats GF qualifiés (0 tant qu'aucun n'a été vérifié).

## Frontières essentielles

**Spek n'est pas un LLM génératif ni un moteur d'inférence de faits.** Il assemble, selon des modèles rhétoriques, des **unités de texte déjà fournies**. Les aperçus intégrés ici utilisent uniquement des littéraux de sources et de courtes formules d'interface marquées **fixture** ; ils ne sont pas des réalisations SemantiK/GF. Un lien rhétorique de type causalité, preuve, objection, concession ou argument ne saurait être choisi automatiquement à partir de l'ordre des faits. Les 60 autres modèles restent disponibles pour sélection éditoriale lorsqu'on dispose des assertions, relations et requêtes approuvées.

La version 1.5 **ne réalise pas** elle-même les paires `CommunicationRequest`/`CommunicationResult` via un RuntimeSet GF/PGF qualifié. L'import de résultats existants par le Spek vNext est disponible dans le code livré, mais aucun résultat fictif ne sera présenté comme GF. Les 88 Kristals restent candidats, les correspondances P3916 ne sont pas des identités approuvées et aucune publication n'est autorisée.

## Installation

Décompresser l'archive au-dessus de `C:\mycode\Kristal`, en remplaçant uniquement le dossier `Kristal_UNESCO_Factory` puis double-cliquer sur `LANCER_FABRIQUE.cmd`. Conserver `Sources/UNESCO/unesco-thesaurus.ttl` et le dump Wikidata hors de la Fabrique. Aucun ancien RUN n'est modifié.

## Validation de développement

`python -m unittest discover -s tests -v` : **12 / 12** tests réussis sur l'environnement de développement, y compris le pipeline natif Kit v9, Spek vNext, import Wikidata et modèles discursifs.

Test d'inventaire discursif à l'échelle de la copie UNESCO de référence (juin 2025) : 4 490 concepts, **8 980** instances FR/EN résolues, **176** pages de groupes; 62 modèles rhétoriques validés. La version officielle utilisateur (4 500 concepts, août 2026) n'a pas été exécutée ici. L'exécution Windows réelle demeure à vérifier.
