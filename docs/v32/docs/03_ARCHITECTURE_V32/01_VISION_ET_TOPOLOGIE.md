# Architecture V32.1 — manager unifié sur fédération Kristal

**Statut [CIBLE] — décision du 16 novembre 2026.** V32.1 remplace le modèle de canon privé autonome proposé le 15 novembre. Voir [arbitrages](../09_FEDERATION_KRISTAL/00_DECISIONS_V321.md).

```text
 EncyKlopedia.pyw  — manager local / UX / file durable / coûts
     │
     ├── UNESCO SKOS + alignements P3916 (88 branches)
     ├── Wikidata local via Skope EXTERNE + Wikipédia via wiki_qid
     ├── passe 1 : candidats → SELECT / REJECT / HOLD
     ├── passe 2 : articles sélectionnés → PROPOSITIONS sources
     │      └── registre EncyK privé, exploratoire, révisable
     ├── îlots existants → états Kristal fédérés, lecture
     ├── admission optionnelle → Kit supporté → état Kristal (reçu)
     └── lecture → snapshots épinglés → Kompiler/adaptateur
```

## Déploiement initial

Monolithe modulaire Python + SQLite de travail. Code sur C:, index lourds sur D:, workspaces Kristal à leur emplacement existant, dépôts Skope et Kristalizer **externes/intouchés**. Le manager n'écrit pas directement dans les états d'autres propriétaires.

## Propriétés d'autorité

| Objet | Autorité | EncyK stocke |
|---|---|---|
| UNESCO / P3916 | Snapshot/version UNESCO et crosswalks indiqués | Index et statut des mappings |
| QID / page / révisions | Wikidata et Wikipédia locaux | Références et caches |
| Sélection / propositions IA | EncyK | Historique de travail et sources |
| Contenu admis d'un îlot | État Kristal de son propriétaire | Reçu et projection, **pas** une copie canonique concurrente |
| Composition parent / enfants | État de fédération à références épinglées | Cache de résolution/version |
| Jobs et coûts | EncyK | Registre opérationnel |

La lecture exploratoire peut réunir propositions et états admis **en les distinguant**. La lecture d'un snapshot reste épinglée aux états exacts, y compris après évolution d'un enfant. Aucune publication implicite.

## Forme cible du méga-repo, sans duplication des dépendances

```text
EncyKlopedia/
  EncyKlopedia.pyw
  AGENTS.md
  README.md
  docs/
  config/
  app/             # pyw, use cases, UI
  core/            # sujet, proposition, décision, campagne
  adapters/        # UNESCO, Wikipédia, Skope, Framework, Kit, Kompiler
  jobs/            # deux passes, reprise, compteurs
  storage/         # registre EncyK (pas nouveau canon)
  prompts/         # sélection et enrichissement
  tests/           # sources simulées et trois modèles réels
  tools/           # utilitaires de production réemployés
  legacy/          # copies de référence si nécessaire, pas Skope/Kristalizer
```

## Priorité de conception

Adapter les fonctions existantes avant de les déplacer; faire [les lots A–E](../09_FEDERATION_KRISTAL/07_LOTS_A_E.md). Le `Framework`, le `Kit` et `Kompiler` apparaissent dans le rapport utilisateur mais leurs API doivent être revérifiées dans les dépôts originaux. Ne pas simuler une admission d'état si aucun auteur qualifié n'est disponible.
