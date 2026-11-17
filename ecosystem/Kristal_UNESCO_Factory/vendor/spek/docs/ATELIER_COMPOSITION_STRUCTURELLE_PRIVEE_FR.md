# Atelier Spek — exploration des compositions prescrites (inspection privée)

## Ce qui est désormais exécutable

Le registre conserve **127 propositions IA**, dont **5 revues structurelles approfondies** (AI, Accounting, Aerospace, Aging et Agriculture). Spek **n'analyse pas les Kristals pour choisir des templates** : l'IA a rédigé `kristal-ai-proposals.json` et `kristal-structure-reviews.json`, incluant les sections ordonnées et les positions d'assertions observées.

Les **19 gabarits spécialisés** de `specialized-template-designs.json` disposent désormais de **contrats d'aperçu structurel privés**, versionnés dans `structural-preview-contracts.json`. Ces contrats permettent de consulter les relations et les preuves déclarées de l'état effectivement étudié, avec sept familles visuelles (réseaux, chaînes, matrices, écritures, hiérarchies, trajectoires et provenance).

**Deux modes distincts sont désormais implémentés :**

- **Inspection immédiate sans SemantiK**, à partir de revues IA et d'états v8 identiques au snapshot. Elle affiche les triples bruts dans un HTML privé ; elle n'est jamais un article publiable.
- **Rendu de layouts Spek spécialisés**, avec **19 nouveaux contrats typés** dans `layouts/`, en plus des huit historiques. Ils disposent de rendus HTML, LaTeX, PDF et Markdown Wiki. Leur contenu exige un `article.json` rempli par un **mappage explicite et approuvé** et un `realizations.json` contenant les textes réalisés par SemantiK. Aucun de ces fichiers n'est créé à partir du seul Kristal ouvert. Les prototypes de présentation ne démontrent pas la topologie d'un graphe, l'équilibrage comptable ni l'autorité des sources.

Les 19 contrats spécialisés sont admis par liste explicite pour les deux profils Arketype rencontrés dans les cinq revues (`modele-multiplexe` et `referentiel-semantique`). Les autres profils n'ont pas été élargis arbitrairement. Spek ne classe jamais un Kristal à l'exécution.

## Procédure depuis l'interface graphique

1. Ouvrir `Spek_Template_Manager.pyw` dans le dépôt.
2. Cliquer sur **Ouvrir un Kristal…** puis choisir un dossier local, par exemple `C:\mycode\Kristal\locals\Kristal-Aerospace`.
3. Le panneau affiche son **slug canonique** (`aerospace`), sa proposition IA et sa revue structurelle, si elle existe.
4. Si l'empreinte SHA-256 des octets de `.kristal/v8/portable-state.kristal-state.json` correspond exactement à la revue, le bouton **Explorer les assertions dans la composition (aperçu privé)** s'active.
5. Cliquer sur ce bouton. Un fichier HTML temporaire s'ouvre localement, avec une navigation par section et l'inspection des triples et des références déclarées.

Si le Kristal n'a pas de revue approfondie (122 cas), si la source est absente ou si ses octets ont changé, l'exploration est refusée. Il faut alors **une nouvelle étude éditoriale par l'IA**, pas une classification automatique de Spek.

## Procédure PowerShell (sans GUI)

```powershell
cd C:\mycode\Spek_Semantic-publishing\Spek
py -3 -m spek preview-structure --kristal C:\mycode\Kristal\locals\Kristal-Aerospace
```

Le programme écrit `inspection-structurelle.html` et `inspection-manifest.json` dans un dossier temporaire privé (le chemin apparaît dans la sortie). On peut choisir un dossier **nouveau, vide, hors des dépôts Git** avec `--out C:\Temp\aerospace-inspection-privee`.

## Contrôles et garanties

- L'état source lu est obligatoirement le fichier explicitement désigné dans la revue IA.
- La comparaison est une empreinte **brute des octets**, jamais présentée comme un engagement canonique v9 qualifié.
- Les indices d'assertions sont ceux **sélectionnés pour l'inspection par l'IA**, non une autorisation de publier ces assertions.
- Les données source et l'HTML ne sont **jamais envoyés sur le réseau** par l'atelier.
- Le HTML échappe les valeurs source, désactive les scripts et n'embarque aucun chargement réseau.
- Le manifeste déclare `publication_eligible: false`, `semantik_realized: false`, `approval: NONE`.
- Le rendu ne produit **ni `Home.md`, ni `_Sidebar.md`, ni `Kristal-<slug>.md`** : ces fichiers appartiennent au pipeline Wiki soumis aux validations.

## Chaîne Wiki retenue et composants disponibles

| Étape | Composant | Contrat / sortie | État |
|---|---|---|---|
| Source | `locals` + Kristal-Manager | état v8/v9, références, assertions explicites | source locale, à vérifier |
| Décision éditoriale | analyse IA + registre Spek | `kristal-ai-proposals.json`, `kristal-structure-reviews.json` | 127 proposées, 5 approfondies, non approuvées |
| Plan approuvé | Kristal-Manager, contrôle C1/C2/C3 | `kristal.wiki-editorial-plan/1.0` + collection C3 | toujours requis |
| Communication | SemantiK Architect / RuntimeSet GF/PGF | `semantik.kristal-v6.communication-projection/1.0` → résultats de réalisation validés | code snapshot disponible ; disponibilité d'un RuntimeSet qualifié non confirmée |
| Contenu Spek | Adaptateur explicite, non heuristique | `kristal.layout-article-source/0.1` + `kristal.layout-realizations/0.1` | 27 layouts typés et rendus ; peuplement des unités par une sélection SemantiK encore requis |
| Brouillon privé | Spek Wiki | `Home.md`, `_Sidebar.md`, `Kristal-<slug>.md`, `manifest.json` | moteur de brouillon existant ; ne confère pas d'autorisation |
| Publication | `kristal-public` + GitHub Wiki séparé | dépôt `Rejean-McCormick/kristal-public.wiki.git` | uniquement après contrôles, revue et push séparé |

Les snapshots des composants SemantiK et du pipeline sont fournis séparément. **Spek n'installe pas SemantiK ni ne prétend avoir des autorisations GitHub.**

## Points à développer pour une publication complète

1. Le **mappage éditorial approuvé** des assertions pertinentes vers les requêtes SemantiK et les slots requis par chaque layout spécialisé.
2. La validation externe du RuntimeSet, de la couverture des obligations de communication et de l'équivalence linguistique.
3. Des visualisations structurelles de haut niveau (graphes interactifs, contraintes de débits/crédits, matrices équilibrées), impossibles à déduire des simples chaînes de texte `realizations.json`.
4. La génération des pages finales par Spek avec contrôles C1/C2/C3 et vérification des manifests dans `kristal-public`.
5. La révision structurelle des 122 Kristals pour lesquels seul le rapport Manager était disponible.

La comparaison d'empreinte sur cinq snapshots constitue une condition d'inspection, **pas** une approbation de publication.
