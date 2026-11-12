# EncyKlopedia v27 — Production massive par packs, Kristals cumulatifs de travail

## Objectif

Découpler trois opérations :

1. **Catalogue** : la base SQLite dérivée v25/v26 contient les articles et leurs rattachements UNESCO. Pas de nouvelle indexation Wikipédia.
2. **Packs** : le moteur utilise l'index d'offsets XML v21 pour conserver **chaque texte intégral** de l'article sélectionné, wikitext compris, sans couper le texte pour tenir dans une limite.
3. **Deltas IA et cumul** : ChatGPT renvoie des unités sémantiques sélectionnées; le moteur les ajoute à un **Kristal privé de travail cumulatif**. Il déduplique exactement les triples et conserve les citations source. Il ne canonise pas et ne publie pas.

**Politique de complétude** : l'article source est intégral; l'extraction de connaissances peut être partielle, rapide et améliorée plus tard. Aucune garantie d'avoir extrait tous les faits.

## Installer l'overlay racine

Décompresser le ZIP **dans** `C:\mycode\EncyKlopedia\EncyKlopedia` en respectant les dossiers. Pas d'installateur. Tous les chemins sont relatifs à la racine du dépôt; les données sont créées sur D:.

### Étape 1 — Générer les prochains packs

Depuis la racine du dépôt (PowerShell) :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\PRODUIRE_KRISTALS_V27.ps1" -Action Packs -MaxPacks 5
```

Cible de départ : **12 articles, ~35 000 mots, ~6 Mio de texte** par pack. Ce sont des seuils de découpage *entre* articles, **jamais à l'intérieur**. Un article dépassant seul ces seuils est mis en pack individuel intégral. Le moteur garde les échecs d'extraction éventuels à l'état `FAILED` pour inspection plutôt que de les masquer.

Les archives seront dans :

```text
D:\EncyKlopedia\30_working\production_kristals_v27\packs\PACK_V27_000001.zip
D:\EncyKlopedia\30_working\production_kristals_v27\packs\PACK_V27_000002.zip
...
```

La sortie console indique pour chaque archive son **SHA-256 du ZIP**, qui doit être reporté tel quel dans le delta IA. Une nouvelle exécution produit les packs suivants, sans dupliquer les précédents. Les états sont sauvegardés dans `FILE_PACKS_V27.sqlite`.

### Étape 2 — Envoyer un pack à ChatGPT

Transmettre **un pack ZIP à la fois**. Le ZIP contient tous les wikitexts intégraux, un manifeste des concepts et révisions, et un `MODELE_DELTA_KRISTAL_V27.json`. Demander à ChatGPT d'analyser une sélection raisonnable de connaissances et de générer un **fichier JSON v27 complet**, pas uniquement un rapport ni 25 propositions prose.

Un delta v27 contient des faits structurés : `subject_ref`, `predicate`, objet typé, `statement_en`, article/revision source, localisateur et confiance. Les relations **ne sont pas des KP canoniques**, les identités restent candidates. L'analyse peut être lacunaire; c'est voulu.

### Étape 3 — Cumuler le delta IA

Sauvegarder le JSON retourné dans un dossier de travail, par exemple `D:\EncyKlopedia\30_working\production_kristals_v27\retours_ia\delta_000001.json`.

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\PRODUIRE_KRISTALS_V27.ps1" -Action Import `
  -Pack 'D:\EncyKlopedia\30_working\production_kristals_v27\packs\PACK_V27_000001.zip' `
  -Delta 'D:\EncyKlopedia\30_working\production_kristals_v27\retours_ia\delta_000001.json'
```

La fusion ajoute les faits au fichier :

```text
D:\EncyKlopedia\30_working\production_kristals_v27\KRISTAL_CUMULATIF_PRIVE_V27.sqlite
```

Le même delta réimporté ne crée pas de doublons. Les connaissances des packs suivants s'additionnent. Un fait identique avec une autre source conserve une citation supplémentaire. Les valeurs différentes pour une relation donnée sont **signalées comme valeurs concurrentes potentielles**, pas automatiquement déclarées fausses.

### Étape 4 — Voir le cumul ou exporter

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\PRODUIRE_KRISTALS_V27.ps1" -Action Status
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\PRODUIRE_KRISTALS_V27.ps1" -Action Export
```

L'export écrit des JSONL complets et un manifeste SHA-256 sous `exports/SNAPSHOT_KRISTAL_V27_XXXXXXXX/`. Ils sont adaptés à une chaîne aval de Kristalizer. Les statuts prévoient un contrôle et une admission ultérieurs, **mais aucun outil v27 n'active automatiquement les contrats canoniques v11–v23**.

## Limites et garanties

- **Lecture seule** : catalogue SQLite v25/v26, index offsets v21 et XML Wikipédia décompressé; aucune réimportation de Wikimedia SQL.
- **Mémoire** : extraction d'une page XML à la fois, lots déterminés par cibles flexibles. Un article exceptionnellement volumineux peut toujours nécessiter de la RAM.
- **Réseau** : aucun accès Internet, uniquement les sources locales.
- **Reprise** : catalogue synchronisé par curseur; packs déjà produits conservés; orphelins ZIP complets et vérifiables récupérés après interruption.
- **Périmètre** : tous les articles catalogués, toutes les branches UNESCO, chaque article identifié une seule fois. Plusieurs affectations possibles.
- **Provenance** : SHA-256 du texte complet, révision Wikipédia, SHA-256 du pack, localisateur, score de classification candidat.
- **Qualité** : Wikipédia est un point de départ documentaire, pas une preuve institutionnelle indépendante. Les éventuelles erreurs et omissions seront améliorées par les agents IA.
- **Droits** : vérifier les obligations d'attribution, CC BY-SA et éventuelles exceptions avant de publier du contenu dérivé de Wikipédia.
- **Publication** : aucune canonisation KQ/KP/KA/KS, aucun remplacement de Kristal existant, aucun push Git.

## Sécurité d'exploitation

Ne pas supprimer les bases `FILE_PACKS_V27.sqlite` et `KRISTAL_CUMULATIF_PRIVE_V27.sqlite` : elles contiennent l'historique cumulatif. Il n'est pas nécessaire de nettoyer après chaque lot.

Si le catalogue v25 change (de nouveaux articles via les ponts UNESCO), le moteur reprend le référencement au prochain lancement. Si le XML Wikipédia change de version, la v27 refuse de mélanger les sources; conserver l'ancien espace de travail et utiliser un nouveau `-WorkRoot`.

## Vérifier le ZIP reçu

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\PRODUIRE_KRISTALS_V27.ps1" -Action VerifyPack `
  -Pack 'D:\EncyKlopedia\30_working\production_kristals_v27\packs\PACK_V27_000001.zip'
```

La v27 **ne remplace pas** la revue éditoriale des sources institutionnelles. Elle inaugure une production cumulative privée à grande échelle.
