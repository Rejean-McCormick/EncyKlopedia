# Revue des catégories Wikipédia — UNESCO MT 1.10 (v26)

**Base examinée :** `EXPORT_INVENTAIRE_V26_POUR_CHATGPT_001.zip`, inventaire complet déclaré par l’outil local du 10 novembre 2026. Le fichier homonyme sans suffixe correspond à un export partiel antérieur.

## Bilan

- **11 888 463** entrées parcourues (`linktarget` et `page`) ; **9 241 036** titres de catégories distincts.
- **213** paires *concept UNESCO / catégorie Wikipédia* suggérées lexicalement dans cet export (ce n’est pas le nombre total de correspondances existantes).
- **980** familles générales fournies pour exploration, limitées par la logique d’échantillonnage de l’exporteur.
- **12 ponts retenus provisoirement**, sur **6 concepts UNESCO** (tous à profondeur **0**, sans exploration automatique des descendants).
- **29 à approfondir**, **172 écartés**.
- Les exemples ne représentent qu’un **maximum de 14 membres directs** par catégorie et ne mesurent pas sa taille totale ; la présence d’un article périphérique empêche d’affirmer que tous les membres sont pertinents.

## Constat sur le classificateur

Le score est **lexical**, non une preuve sémantique. Il confond notamment les catégories de suivi Wikipédia avec des familles encyclopédiques, les États territoriaux avec le rôle de l’État, et `International education` avec `Global citizenship education`.

De nombreux concepts du pilote ont **zéro correspondance proposée**, mais cela ne signifie pas qu’aucune catégorie Wikipédia pertinente n’existe. Les suggestions résultent de requêtes limitées à 90 résultats par nom et de cinq étiquettes alternatives au maximum. Les autres microthésaurus UNESCO ne sont pas couverts par cet export.

## Règles de sélection

- `INCLUDE` : le titre et les exemples disponibles montrent un lien thématique direct. **Activation proposée seulement**, non preuve que chaque article appartient au concept. `depth_limit = 0` pour tous les ponts, le temps de contrôler les sous-catégories.
- `HOLD` : proximité réelle mais périmètre trop large, correspondance conceptuelle imparfaite ou absence d’exemples ; aucune activation.
- `EXCLUDE` : faux positif, catégorie de maintenance, homonymie, lien géographique ou administratif trop indirect.

Les deux rattachements à **Intercultural bilingual education** sont conservés séparément (bilingue et interculturel) : le catalogue mondial garde un **article unique** malgré plusieurs attaches sémantiques.

## Prochain passage automatisé, sans nouvel inventaire

Lancer une **recherche FTS sur l’inventaire déjà construit** à partir de `REQUETES_COMPLEMENTAIRES_UNESCO_MT110_V26.json`. Ce fichier rassemble 50 expressions ciblées pour les concepts vides ou sous-couverts. Renvoyer seulement le nouveau `RESULTATS_REQUETES_V26_*.zip` pour une seconde sélection.

## Limites

- Ce n’est ni une validation de toutes les catégories Wikipédia ni une revue du texte des articles.
- Les ponts retenus ne déclenchent **aucune admission canonique**, aucune publication et aucun enrichissement automatique de Kristal.
- L’import v26 transforme les décisions en **CSV de ponts** mais **ne modifie pas** automatiquement le catalogue global v25. Cette étape d’intégration devra être contrôlée séparément.
- Ne pas effacer l’inventaire SQLite : sa construction a réussi et il est réutilisable pour les 88 microthésaurus si leur référence complète est fournie.

## Commandes après extraction à la racine du dépôt

Depuis `C:\mycode\EncyKlopedia\EncyKlopedia` :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1 -DecisionsFile .\tools\unesco_pilot\v26_data\DECISIONS_CATEGORIES_UNESCO_MT110_V26.json
```

Puis, sans réinventorier :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1 -QueriesFile .\tools\unesco_pilot\v26_data\REQUETES_COMPLEMENTAIRES_UNESCO_MT110_V26.json
```

En cas de doublon d’export déjà présent, la commande de requête refuse de remplacer le fichier existant ; elle ne touche pas aux sources Wikipédia.
