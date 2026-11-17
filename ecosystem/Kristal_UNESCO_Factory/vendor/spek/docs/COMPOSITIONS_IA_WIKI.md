# Registre de compositions Wiki conçu par IA

## Séparation des responsabilités

- **L’IA** examine les artefacts réels et élabore puis approuve avec l’utilisateur le registre des compositions par Kristal.
- **Arketype** fournit le vocabulaire structurel et les primitives candidates, sans faire de choix de publication.
- **Spek**, dans le fonctionnement cible, n’analysera **jamais** un Kristal pour en déduire un template : il recevra une composition **explicitement assignée**. Le chargement de ce nouveau registre n’est **pas encore raccordé** au moteur Spek dans cette livraison ; le moteur existant vérifie déjà les types et cardinalités des layouts.
- **SemantiK Architect** produit les réalisations linguistiques des unités sémantiques explicitement sélectionnées.
- **Kristal-Manager** coordonne les opérations et les gardes de publication ; `locals` reste canonique.

## État de cette livraison

- **19 compositions éditoriales candidates**, chacune comportant entre 2 et 4 sections composées des **8 layouts actuels**.
- **23 recettes Arketype** référencées comme contexte non normatif et non publiable.
- **18 besoins de nouveaux layouts** explicitement classés « à concevoir », pas implémentés.
- **Aucune affectation spécifique aux 127 Kristals** : le rapport de Kristal-Manager a été annoncé mais pas encore fourni.
- **Aucun rendu réel de Kristal et aucune publication** : seules les structures des 19 archétypes ont été analysées.
- **Intégration du registre au lanceur/au moteur Spek non réalisée** : ce pack fournit les compositions explicites, leur schéma, leur aperçu statique et une vérification de cohérence, sans modifier le code Spek.

## Fichiers

- `Spek/template_library/wiki/composition-registry.json` : index des 19 compositions.
- `Spek/template_library/wiki/compositions/*.json` : ordre, types de slots et provenance structurelle des sections.
- `Spek/template_library/wiki/kristal-assignments.json` : registre **volontairement vide**, à remplir par l’IA après lecture du rapport.
- `Spek/template_library/wiki/kristal-assignment.schema.json` : contrat des affectations individuelles.
- `Spek/template_library/wiki/layouts-a-concevoir.json` : éléments sans contrat de présentation satisfaisant.
- `Spek/template_library/wiki/assemblages-arketype-context.json` : recettes Arketype non normatives.
- `CATALOGUE_COMPOSITIONS_IA.html` : navigation statique des compositions, sans analyse de Kristal.
- `Verifier_Compositions_IA.py` : vérification de cohérence **statique uniquement**.

## Installation

Extraire **ce ZIP à la racine `C:\mycode\Kristal`** (il contient le dossier `Spek/`). Ne remplace aucun fichier existant de Spek : il crée seulement des fichiers dans `template_library/wiki/` et un catalogue à côté.

Pour vérifier : `python Verifier_Compositions_IA.py C:\mycode\Kristal\Spek`

## Ce qui sera ajouté dès réception du rapport des 127

Pour chaque Kristal : identité réelle, chemins des sous-structures, justification éditoriale, composition principale et supplémentaires, ordre des sections, identifiants et références exacts, couverture des layouts, lacunes et validation humaine. Aucune correspondance ne sera déduite par un classificateur Spek.

## Garanties et limites

Une section est **conditionnelle** : elle apparaît seulement si ses unités ont été explicitement retenues et si tous les slots obligatoires du layout sont satisfaits par des informations sourcées. Une section impossible est signalée, **jamais remplie artificiellement**. Les 19 recettes sont des choix de conception fondés sur les primitives Arketype, pas une analyse des 127 Kristals.

### Provenance de cette analyse

- `arketype_Code_snapshot(7).zip` SHA-256 `cc54bd3a8d96497168f49cdbe06faa223c51831c673ffad4f614fb4951ce01de`
- `SPEK_REPO_COMPLET_GESTIONNAIRE_REPARE_2026-11-01.zip` SHA-256 `7523374d26008807d7d5373b2de3b6968e833551281fd48564577e761ec2494c`


## Ajout du moteur spécialisé

Depuis la révision de novembre 2026, **19 layouts typés spécialisés** s’ajoutent aux huit layouts initiaux dans `layouts/`. Les 19 compositions génériques décrites ci-dessus restent fondées sur les huit layouts historiques, tandis que les cinq revues IA approfondies utilisent les nouveaux layouts. L’atelier peut afficher des assertions sources en inspection privée ; les rendus éditoriaux des layouts spécialisés nécessitent toujours des unités sélectionnées et des réalisations explicites. Voir [Atelier structurel privé](ATELIER_COMPOSITION_STRUCTURELLE_PRIVEE_FR.md).
