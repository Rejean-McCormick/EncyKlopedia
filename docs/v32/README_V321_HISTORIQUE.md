# EncyKlopedia V32.1 — dépôt unifié de développement

**Point d'entrée Windows : `EncyKlopedia.pyw`** (ou `LANCER_V32.cmd`).

Ce dépôt assemble les sources déjà fournies et propose un nouveau manager Python local. Il conserve les moteurs historiques v25/v27/v28/v30 corrigés et leurs tests, les 88 espaces UNESCO de référence et les outils auxiliaires. **Il ne remplace pas encore le poste de production Windows installé** et ne contient pas les grands index/dumps situés sur `D:`.

## Démarrage

- Installer **Python 3.10+ avec Tkinter**. Les nouveaux modules utilisent la bibliothèque standard uniquement.
- Décompresser le ZIP en conservant l'arborescence; ouvrir `EncyKlopedia.pyw` ou `LANCER_V32.cmd`.
- Onglet **Sources & index** → *Indexer les 88 branches UNESCO*; puis *Découvrir par QID et graphe* (lorsque les index D: sont disponibles).
- Onglet **Production ChatGPT** → *Préparer la prochaine vague*, sélectionner un poste, *Copier le prompt ChatGPT*, joindre le ZIP de ce poste dans une conversation. Déposer ensuite le ZIP de retour, avec l'identifiant du poste.
- Les données de travail V32 sont stockées dans `D:\EncyKlopedia\30_working\encyk_v32` par défaut sur Windows; elles ne modifient pas les bases de la station v30 ni les espaces Kristal.

Pour diagnostiquer sans lancer l'interface :

```powershell
python encyk_cli.py doctor
python encyk_cli.py index-unesco
python encyk_cli.py discover --branch unesco.mt1.05 --budget 10000
python encyk_cli.py fallback --branch unesco.mt1.05 --budget 2500
python encyk_cli.py prepare --branch unesco.mt1.05
python encyk_cli.py jobs
python encyk_cli.py import D:\retours\reponse.zip --job-id SEL_000001
python encyk_cli.py islands-scan
python encyk_cli.py export D:\ENCYK_PROPOSITIONS_PRIVEES.jsonl
```

### Configuration

Les chemins sont personnalisables dans `config/settings.json` (copier `config/settings.example.json`). Ils peuvent aussi être surchargés par les variables `ENCYK_WORK_ROOT`, `ENCYK_UNESCO_ROOT`, `ENCYK_WIKIPEDIA_SQL`, `ENCYK_WIKIDATA_SQL`, `ENCYK_WIKIPEDIA_XML`, `ENCYK_DIRECT_INDEX` et `ENCYK_KRISTAL_ROOTS`. Les index Wikipédia et Wikidata sont lus **en SQLite read-only**. Les 88 snapshots fournis dans `ecosystem/UNESCO_Kristals` sont des sources historiques : **ne pas confondre une copie de référence avec l'espace canonique vivant**.

### Ce qui est réellement fonctionnel

- Importer les 88 sources UNESCO préparées, leurs 4 500 concepts et 4 289 mappings P3916 candidats.
- Joindre des QID aux pages Wikipédia via `wiki_qid` et explorer `entity_edge` par pagination persistante.
- Générer et réimporter les deux types de packs V32, gérer les 10 postes, préserver des décisions et des propositions privées sans doublons.
- Lire les révisions Wikipédia via le lecteur indexé du moteur v27 lorsqu'elles sont disponibles; enrichir les prompts avec des extraits et les prévisualisations Wikidata dérivées.
- Inventorier des îlots Kristal existants et lire leur `canon/state.index.json` **sans les migrer ni les modifier**.

### Ce qui n'est pas encore qualifié comme production finale

**Aucune admission dans un canon Kristal n'est activée.** Les interfaces de l'Authoring Kit/Framework exigent une qualification sur leurs dépôts réels (qui ne font pas tous partie de ces archives). L'adaptateur refuse explicitement l'écriture. La fédération est actuellement une **vue de lecture dérivée**, pas un parent Kristal publié et épinglé via Framework. La jointure et les performances sur les 125 Go d'index du poste Windows n'ont pas été exécutées ici. Le manager n'exécute aucun agent ChatGPT automatiquement : les dix conversations sont des échanges ZIP manuels, comme l'architecture actuelle.

**Ne pas présenter ce dépôt comme installé et validé en production.** Les étapes correspondantes sont détaillées dans [État de réalisation](docs/v32/IMPLEMENTATION_ET_LIMITES.md).

## Orientation du code

- `encyk_v32/` : noyau refactoré (données, découverte, pipeline à deux passes, UI, fédération de lecture).
- `tools/unesco_pilot/` : moteurs historiques réemployés (v25, v27, v28, v30), avec correctifs jusqu'à v31.12 issus des overlays disponibles.
- `ecosystem/` : sources des dépôts acquis, **sans Skope ni Kristalizer**, conservées à des fins d'examen et de transition.
- `archive/tools/` : anciennes applications de diagnostic/production pour référence; elles ne sont pas lancées automatiquement.
- `docs/v32/` : architecture V32.1 détaillée, atlas de modules, guides de migration et [état actuel](docs/v32/IMPLEMENTATION_ET_LIMITES.md).
- `tests_v32/` : tests de bout en bout sur bases synthétiques, sans besoin du dump Wikipédia.
- `tests/` : suite historique V31; certains tests attendent d'anciens paramètres et ressources absentes du snapshot.

## Tests

```powershell
python -m unittest discover -s tests_v32 -v
python -m unittest discover -s tests -p "test_station_reserve_deferred_v3112.py" -v
```

Les tests ciblés V31 récents passent; l'intégralité de l'ancienne suite historique n'est pas au vert et **ses échecs sont documentés**, pas dissimulés.

**Skope et Kristalizer** restent des applications et dépôts externes : aucune modification, aucun fork, aucune copie de leurs sources dans ce dépôt.
