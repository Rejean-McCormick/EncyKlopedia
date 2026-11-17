# Spek — Atelier optimisé selon le guide UX v2

**Référence de conception** : `guide-architecture-interfaces-ia-v2(8).zip`, principalement `AI_INGESTION.md` et les principes UX-01 à UX-18. La refonte privilégie le parcours réel et conserve les moteurs, contrats, validations et formats existants.

## Travail principal

> Ouvrir un article de projection sélectionné, vérifier ses formulations déjà réalisées par SemantiK, prévisualiser le rendu final; ou inspecter les métadonnées d’un Kristal pour consulter une recette IA explicitement assignée.

Les quatre actions courantes sont réunies **dans la même fenêtre**, au-dessus du même espace de travail :

1. **Ouvrir un article…** : choisir explicitement `article.json` puis `realizations.json` (aucune traduction automatique).
2. **Ouvrir un Kristal…** : sélectionner le dossier local d’un Kristal. Lecture de `kristal.workspace.json` et/ou `canon/state.index.json` uniquement, sans exploration des données ni inférence de templates.
3. **Vérifier** : lancer le **compilateur Spek existant** en mode `check`, dans la langue choisie; aucune sortie publique.
4. **Prévisualiser en HTML** : lancer `spek build --formats html` dans un répertoire temporaire privé, puis ouvrir la page locale. Le statut n'annonce jamais une publication.

Si le Kristal n'a pas encore de `article.json` et de `realizations.json` réalisés et validés, l'atelier montre les **structures déclarées**, pas un faux Wiki rempli. Il ne parle pas à SemantiK Architect et ne sélectionne pas de faits.

## Vue principale, occasionnel, avancé

| Ancien emplacement | Organisation de l'atelier | Principe |
| --- | --- | --- |
| Barre globale avec huit actions de gestion | Groupes contextuels **Gérer l’élément sélectionné**, sous l’arbre de bibliothèque | UX-06 / UX-12 |
| Aperçu des seuls contrats | **Aperçu et contexte** : projet, Kristal, compositions IA, layouts | UX-05 / UX-11 |
| Pas de point de départ « ouvrir un projet » | **Mon travail** en premier; ouvrir, vérifier, prévisualiser | UX-07 / UX-15 |
| Aucun catalogue IA de compositions intégré à l'arbre | **Wiki → Compositions IA** : 19 recettes éditoriales lisibles | UX-01 / UX-17 |
| Éditeur JSON affiché comme une facette aussi importante que le travail | Onglet secondaire **Avancé · Éditeur JSON** | UX-09 / UX-12 |
| Ancien raccourci `OUVRIR_TEMPLATES.cmd` | Alias vers **OUVRIR_SPEK.cmd** et `Spek_Template_Manager.pyw`, une même interface | UX-16 |
| `START_SPEK.bat` | Alias vers l’atelier unique; ancienne démonstration préservée sous `DEMO_SPEK_LOCAL.bat` | UX-16 / UX-18 |

## Composition éditoriale : autorité et non-inférence

- Les 19 recettes se trouvent sous `template_library/wiki/compositions/`.
- Leurs IDs et contrats sont dans `template_library/wiki/composition-registry.json`.
- `kristal-assignments.json` reste vide tant que les 127 Kristals n'ont pas été analysés par l'IA à partir des sources réelles.
- **Spek ne choisit jamais une recette à partir d'un nom, d'un type, d'un graphe ou d'un archétype deviné.** Le seul rattachement possible est une identité explicite déclarée dans le registre; son empreinte d’état doit être revérifiée avant toute projection ou publication.
- Le logiciel lit les recettes et peut afficher leurs sections et slots, mais ne substitue pas cette vue structurelle à une page réelle.
- Les catégories `educational`, `scientific`, `report`, `book` restent réservées : aucun moteur n'a été inventé.

## Sécurité et états

- **Non chargé** : aucune donnée de travail.
- **Ouvert, non vérifié** : les chemins sont connus, mais aucun contrôle n'a été exécuté.
- **En cours** : un seul contrôle ou build à la fois, sans doublon.
- **Vérifié localement** : le compilateur accepte les fichiers de la langue sélectionnée; cela n'atteste ni le RuntimeSet SemantiK, ni les gates C1/C2/C3.
- **Aperçu construit, non publié** : HTML local temporaire ouvert via navigateur, jamais poussé vers GitHub.
- **Refusé** : erreur réelle du compilateur affichée; pas de réussite fictive.

Les protections de modification sont conservées : sauvegardes hors dépôt, contrôle d'empreinte des modifications concurrentes, interdiction de supprimer les layouts référencés par les compositions IA, et édition stricte des contrats.

## Scénarios vérifiés

1. Démarrage depuis la racine Spek et lecture des cinq catégories, 19 compositions et huit layouts.
2. Ouverture de métadonnées d’un Kristal sans assignation : aucune proposition automatique de templates.
3. Vérification d'un couple `article.json`/`realizations.json` du dépôt ; refus si données invalides.
4. Construction d'un aperçu HTML en français avec les **fixtures** du dépôt, sans publication ni appel SemantiK.
5. Tentative de suppression/modification incompatible d'un layout référencé : refus.

### Lancement

Double-cliquer sur `OUVRIR_SPEK.cmd` (ou `Spek_Template_Manager.pyw`) depuis le dépôt complet. `DIAGNOSTIC_TEMPLATES.cmd` reste disponible en cas d’échec Windows. Python 3.10+ / Tkinter requis. Pas de connexion distante nécessaire.

### Commandes sans interface

```powershell
python -m spek check-wiki-compositions
python -m spek list-wiki-compositions
python -m unittest discover -s tests -v
```

Le fichier `docs/COMPOSITIONS_IA_WIKI.md` documente la construction initiale des recettes. Le rapport global des 127 Kristals est toujours nécessaire pour produire les assignations individuelles et les éventuels nouveaux layouts spécialisés.

Le dossier historique `wiki-templates/` présent dans les anciens clones GitHub n’est **plus actif**. Après extraction sur un clone neuf, le supprimer manuellement si aucun fichier personnalisé n’y est conservé ; les profils actuels sont sous `template_library/wiki/`.
