# 09 — Recettes opérateur, diagnostic et reprise

## A. Observer la base V32 actuelle (sans modifier aucune table)

Sur Windows, depuis le dossier extrait du pack :

```powershell
py -3 outils\OBSERVATEUR_CAMPAGNES_V32.py `
  --db 'D:\EncyKlopedia\30_working\encyk_v32_NEUF_87_20261116T202136Z_e2e3c56\etat_v32\encyk_v32.sqlite' `
  --branch unesco.mt2.45 `
  --out 'D:\EncyKlopedia\30_working\rapports_observateur'
```

Résultat : `BILAN_CAMPAGNES.json`, `BILAN_CAMPAGNES.md` dans un dossier de rapports externe. Le script refuse un chemin de sortie égal au répertoire de la base et n'ouvre aucune source Wikidata géante.

Pour tout voir, retirer `--branch`. Pour obtenir un manifeste de fenêtre **lecture seule**, ajouter `--manifest-candidats` **avec une branche** : le JSONL fixe la liste `candidate_id`, `page_id`, `revision_id`, concept et état **à l'instant de lecture**. Il ne réserve aucun poste et ne fige pas la source vivante.

## A bis. Précharger une fenêtre et remplir les postes (facultatif)

Fermer la station V6 au préalable. Une **simulation** sans aucune écriture :

```powershell
py -3 outils\CAMPAGNE_BORNEE_V32.py --branch unesco.mt2.45 --out 'D:\EncyKlopedia\30_working\rapports_observateur'
```

Un seul ordre actif explicite, budget global **20 000 voisins au total**, au plus **quatre tours**. Le chemin V6 est à adapter :

```powershell
py -3 outils\CAMPAGNE_BORNEE_V32.py --branch unesco.mt2.45 `
 --station-dir 'D:\ENCYK_STATION_88_V6' --out 'D:\EncyKlopedia\30_working\rapports_observateur' `
 --budget 20000 --rounds 4 --apply --confirm 'PRODUIRE unesco.mt2.45'
```

Cela **ajoute** des candidats et packs ordinaires au registre V32 via le code du moteur déjà installé; aucune migration, aucun scan des 134 Go. Un `RECU_FENETRE_...json` et un manifeste d'inventaire sont écrits hors de l'état V32. Pour utiliser les nouveaux postes, **relancer ensuite la station normale**.

Cette fenêtre active est un **outil optionnel non testé sur le Windows réel**. Elle ne surveille pas les retours en permanence et ne traite aucun message ChatGPT. Le garde-processus refuse l'opération si la station/manager est détectée ou si le contrôle n'est pas disponible. Pour une production régulière, la station V6 actuelle reste le chemin qualifié par les journaux.

## B. Diagnostic après import

- Vérifier `jobs.status`, `receipts`, `return_archives` et `import_errors`, pas seulement le nombre affiché sur le bouton.
- Un `new_proposals` non nul prouve l'insertion d'entrées privées distinctes selon le schéma, pas leur validation scientifique exhaustive.
- Si le ZIP est `PARTIAL`, examiner `source_results` pour identifier quels textes demandent une reprise.
- Si `invalid_facts > 0`, extraire et classer les motifs. Ne jamais réimporter le même ZIP tel quel.
- Si les 10 postes sont pleins, le problème n'est pas la découverte : finir/importer les retours des postes occupés.
- Si `PENDING=0`, postes libres et graph cursors encore ouverts, redécouvrir; si aucun chemin actif, changer de stratégie ou compléter les PARTIAL.

## C. Exemples de commandes V32 existantes

Le code source V32.2 expose (dans un shell où le bon workspace est activé) :

```powershell
python encyk_cli.py doctor
python encyk_cli.py jobs
python encyk_cli.py recover
python encyk_cli.py candidates --branch unesco.mt2.45 --limit 100
python encyk_cli.py export 'D:\export_encyk\propositions.jsonl' --branch unesco.mt2.45
```

Attention : `encyk_cli.py` appelle `open_work` pour la plupart de ses commandes; sur une base d'une autre version, cela peut effectuer une **migration prévue par le moteur**. Pour un diagnostic strict RO, **préférer notre observateur**.

## D. Si la station ne découvre plus rien

1. Vérifier les source paths réels D: et la présence du correctif `property_id` (`31`, pas `1000000031`).
2. Vérifier `graph_cursors` et `fallback_cursors` — existence de lignes **n'implique pas** parcours exhaustif de toutes les clés.
3. Regarder les routes par origine : Wikidata, titres, liens V28, relations UNESCO; si une seule origine domine, rééquilibrer les campagnes.
4. Vérifier le nombre de `PENDING` vs `READY` et les 10 lanes : un message `TERMINÉ batch : []` peut simplement signifier « aucune unité distribuable », pas panne du moteur.
5. Ne jamais déclencher une **réindexation complète** du compact/du XML pour diagnostiquer une colonne absente de 27 candidats.

## E. Incident connu : historique Météorologie

- V32.2 initial : 27 candidats seulement, budget graphe non utilisé à cause du décalage P31; V4 répare et réouvre des curseurs déclarés terminés.
- V6 : 2 460 candidats; campagnes de sélection prêtes, 10 606 propositions accumulées.
- Trois missions ont signalé **506 lignes invalides** dans `import_errors` au total. Leur contenu exact n'est pas fourni dans les journaux; il faut consulter les erreurs par ordinal avant d'attribuer la cause.
- Les 253–254 PARTIAL nécessitent une stratégie mesurée, pas une boucle de réarmement sans seuil.

## F. Vérifications après installation de la documentation

```powershell
py -3 outils\INSTALLER_DOCS_ENCYK.py --repo 'C:\mycode\EncyKlopedia\EncyKlopedia'
py -3 outils\INSTALLER_DOCS_ENCYK.py --repo 'C:\mycode\EncyKlopedia\EncyKlopedia' --apply
```

Le second ne touche que `docs/v32/docs/10_SYSTEME_MASSIF_20261117`. Pour nettoyer les docs, utiliser la sauvegarde de l'installateur ou supprimer ce **seul** dossier après avoir conservé une copie, jamais le dépôt entier. Une suppression n'est pas effectuée par le pack.
