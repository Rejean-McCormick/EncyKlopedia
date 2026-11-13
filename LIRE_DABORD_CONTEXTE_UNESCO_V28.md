# EncyKlopedia — Packs UNESCO v28 enrichis en preuves

Cette mise à jour ajoute, aux **ZIP téléchargés depuis les postes v30**, un fichier
`CONTEXTES_DOCUMENTAIRES_V28.jsonl` et un manifeste de disponibilité. Elle utilise
les notes du thésaurus UNESCO et, si disponibles, les catégories Wikipédia ainsi
que des extraits vérifiés du dump XML grâce à l’index direct v21.

## Installation (une commande)

Extraire le ZIP **à la racine du dépôt** `C:\mycode\EncyKlopedia\EncyKlopedia`,
fermer d'abord le poste v30, puis lancer :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\mycode\EncyKlopedia\EncyKlopedia\INSTALLER_CONTEXTE_UNESCO_V28.ps1"
```

Cette commande vérifie les empreintes du code existant et des fichiers fournis,
sauvegarde le code existant dans `_SAUVEGARDES_CODE_CONTEXTE_V28`, installe le
correctif puis redémarre le poste v30. Si le code en place a changé depuis le
snapshot fourni, elle **refuse de l’écraser**. Utiliser `-InstallOnly` pour ne pas
relancer le poste.

## Fonctionnement

- Les tâches **déjà en cours** ne sont pas réinitialisées. Pour obtenir leurs
  preuves enrichies, cliquer de nouveau sur `ZIP` ou `Copier + ZIP` dans le poste.
- L'original `REVUE_v28_*.csv` reste octet pour octet identique dans le ZIP
  enrichi. Ni `station_v30.sqlite` ni le catalogue v25, ni les bases v27/v28
  ne sont modifiés.
- Une copie enrichie est conservée dans
  `D:\EncyKlopedia\30_working\poste_chatgpt_v30\review_context_cache` ; le
  pack original reste intact, vérifié par son SHA-256 enregistré dans la station.
- `MANIFEST_CONTEXTE_V28.json` indique le nombre d'extraits XML disponibles.
  Le texte original **n'est jamais inventé** en cas d'absence ou d'incompatibilité
  du XML ou de l'index. La génération conserve alors les preuves de liens et
  les notes UNESCO, et signale ce manque.
- Source prévue pour les textes :
  `D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml`
- Index direct requis pour le texte :
  `D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite`
- La recherche est **indexée page par page**. Aucune lecture séquentielle des
  110 Go de Wikipédia, aucun accès réseau.
- Il faut renvoyer **le même format compact** `DECISIONS_<task_id>.csv` à trois
  colonnes. Le moteur vérifie les preuves et n’autorise aucune admission canonique.
- Cette amélioration ne force pas les anciennes propositions HOLD à revenir en
  revue et ne les approuve pas automatiquement.

## Critère de décision

APPROVE quand le sujet de l'article traite substantiellement du concept UNESCO,
REJECT quand le lien est fortuit ou hors sujet, HOLD quand les preuves restent
insuffisantes ou contradictoires. Une simple mention ne suffit pas.

## Tests locaux réalisés

`python -m unittest discover -s tests -p 'test_contexte_revue_unesco_v28.py' -v`

Deux scénarios : XML absent (absence signalée sans inventer d'extraits), et XML
présent/index v21 correct (extrait source validé). Vérification du CSV original,
des empreintes de la tâche et du ZIP source immuables.
