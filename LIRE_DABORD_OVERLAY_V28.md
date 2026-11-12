# EncyKlopedia — Overlay v28, racine du dépôt

Décompresse ce ZIP **directement** dans `C:\mycode\EncyKlopedia\EncyKlopedia`.
Tous les fichiers fournis sont nouveaux dans le snapshot du 11 novembre 2026.

## Préparer le premier export d'articles reliés

Dans PowerShell, à la racine du dépôt :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Preflight
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Discover -MaxSeeds 1000
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Export -MaxExport 1500
```

Envoie-moi le **ZIP indiqué dans le champ `export_for_chatgpt`** du résultat final. Je pourrai trier les candidats et préparer le CSV de décisions avant que tu modifies le catalogue.

`Preflight`, `Discover` et `Export` ne modifient pas les 782 articles du catalogue v25, les 2 420 connaissances candidates v27, ou les index Wikipédia. Le nouvel état de découverte est enregistré séparément sur D:.

## Après la revue

L'action `Apply`, avec un fichier CSV explicitement revu, ajoute les nouveaux articles uniques et leurs associations UNESCO au catalogue existant et enregistre un audit. Le producteur v27 les récupère au prochain `-Action Packs` sans repartir de zéro.

**Ne lance pas `-Action Apply` avec le CSV initial** : toutes ses décisions valent `HOLD` et aucune addition n'est autorisée. Le CSV doit d'abord être revu.

Détails techniques et commandes avancées : `docs\UNESCO_DECOUVERTE_ARTICLES_RELIES_V28.md`.

## Correctif v28.1 — Reprise apres divergence de revision

Si la v28 initiale a affiche `Revision XML differente du catalogue pour graine ...`,
la nouvelle version traite la divergence comme une information de provenance,
pas comme une erreur d'integrite de l'index XML. Les deux revisions sont
consignees dans le registre prive. Les 100+ graines deja terminees restent
marquees `DONE` et la decouverte reprend au prochain `PENDING`.

Apres avoir decompresse **ce correctif** a la racine du depot, en remplacant
les fichiers existants, relancer :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Discover -MaxSeeds 1000
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Status
pwsh -NoProfile -ExecutionPolicy Bypass -File '.\DECOUVRIR_ARTICLES_RELIES_V28.ps1' -Action Export -MaxExport 1500
```

Ne pas effacer la base de travail v28 et ne pas reindexer Wikipedia.
Les sources SQL et XML, le catalogue v25 et les Kristals v27 demeurent inchanges.
