# 02 — Cartographie détaillée de l'écosystème EncyK

## Les trois cercles d'autorité

**A. Données sources, référentiels et index (à lire, ne pas réécrire)** : UNESCO/Factory/Workbench, Wikidata/Skope, Wikipédia/Médiathèque et catalogues/index locaux.

**B. Production éditoriale privée (EncyK)** : import des concepts, découverte, candidats, routes, sélection ChatGPT, ENR, couverture des pages, propositions, reçus, erreurs, dossiers de campagne.

**C. Admission canonique (Kristalizer, Authoring Kit, îlots Kristals)** : préparation d'un lot mûr, contrôle des autorités et écritures via Kit réel, **jamais par simple import d'un ZIP**.

```text
UNESCO_Kristals / Factory ─ concepts SKOS + P3916 candidats ─┐
Skope (Wikidata) ─ index compact et services RO ─────────────┤
Médiathèque + refs ─ Wikipédia XML, wiki_qid, index direct ─┤
                                                              ▼
              EncyK — recherche / sélection / propositions privées
                         │             ▲
                SEL / ENR ZIP ↔ ChatGPT (transfert manuel)
                         │
                  registre privé V32/2
                         │   [lots mûrs, revue explicite]
                         ▼
                  Kristalizer / Kit autorisé
                         ▼
                  îlots Kristals indépendants
```

## Inventaire de responsabilités

| Projet/dépôt | Donnée ou compétence principale | Ce qu'EncyK doit faire | Ce qu'EncyK ne doit pas faire |
|---|---|---|---|
| `EncyKlopedia` | Orchestration, SQLite privé, ZIP, UI, code V27–V32 | Posséder missions et propositions, gérer sources et reprises | Remplacer tous les projets externes |
| `UNESCO_Kristals` | 88 workspaces, concepts UNESCO, correspondances P3916, états de branches | Consommer la taxonomie et les mappings candidats | Écraser `canon/` ou confondre workspace et îlot |
| `Kristal_UNESCO_Factory` | Fabrication des sources et mappings UNESCO | Lire des sorties versionnées comme entrée | Refaire sa logique dans le noyau de production |
| `UNESCO_Workbench` | Révisions et validations thématiques historiques | Réutiliser concepts et diagnostics utiles | Réimporter implicitement les décisions V31 |
| `LinkedDataHub-UNESCO` | Ancien environnement RDF/SKOS et comparaisons | Consulter si pertinent | Le transformer en dépendance de production obligatoire |
| `Skope` | Navigation Wikidata, compact, extraction originale ciblée | Consommer ses sorties et API autorisées en lecture | Modifier sa base compacte ou inventer des références |
| `mediatheque-references` | Index de pages, QID, catégories et offsets Wikipédia | Accéder au XML via les index existants | Refaire un scan XML mondial par article |
| `mediatheque` | Préservation et références partagées | Garder provenance/version/locator | Aspirer et modifier le moteur partagé |
| `production_kristals_v27` | Extraction de texte Wikipédia, guide et sorties historiques | Réutiliser fonctions de lecture/sections | Rebrancher la base historique de propositions |
| `decouverte_articles_relies_v28` | Liens et catégories, expansion documentaire | Réutiliser les bons lecteurs de liens/catégories | Parcourir sans limite les hubs encyclopédiques |
| `poste_chatgpt_v30` | Dix postes, transports, retour ZIP | Préserver les gestes UX éprouvés | Importer les vieux jobs dans une V8 neuve |
| Systèmes V31 | Pilotage, diagnostic, six passes, compléments | Reprendre acquis de prompts, état et observabilité | Restaurer les bases V31 dans V8 |
| `Kristalizer` | Audit et staging de lots canoniques | Préparer un handoff explicitement qualifié | Modifier le code externe |
| `Authoring Kit` | API d'écriture des îlots et contrats | Vérifier APIs/schemas réels avant admission | Utiliser une API devinée |
| Kristals / `build/v9` | États/artefacts indépendants | Référencer, lire quand autorisé | Réécrire depuis les packs ChatGPT |

## Frontières concrètes

- **C:** code, projets et références (y compris UNESCO/Kristalizer) ; **D:** grosses bases Wikidata/Wikipédia, XML, index et workspaces EncyK. Les racines exactes peuvent varier et doivent être confirmées sur le poste.
- Un dossier du snapshot `ecosystem/UNESCO_Kristals/` n'est **pas automatiquement** l'état canonique vivant sur C:.
- Skope n'est pas « une extension d'EncyK » : c'est un propriétaire externe des outils Wikidata.
- La Médiathèque conserve les **sources** ; EncyK décide la **pertinence conceptuelle**.
- Un moteur autonome V8 peut contenir une **copie locale du code EncyK**, pas une copie des gros index ni un fork de Skope.
- Les archives v25–v31 sont un patrimoine de code, d'études et de preuves historiques ; pas une source silencieuse de tâches à importer.

## Parcours de provenance

Un fait produit par EncyK doit être traçable de la **proposition → travail ENR → page/révision/texte → extrait source**. La route de découverte `Wikidata P31` ou le mapping `P3916` sert à expliquer **pourquoi la page a été proposée**, pas à prouver le contenu de toutes ses affirmations.

Pour une extraction Wikidata *originale* future, conserver statement ID, référence, qualifiers, version du dump, type et licence ; **ne pas substituer** une citation de Wikipédia inventée.

## Voir aussi

[Sources](03_SOURCES_ET_INVENTAIRE.md), [programme](04_PROGRAMMES_ET_CAPACITES.md), [fédération](../09_FEDERATION_KRISTAL/09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md), [matrice V7](../10_SYSTEME_MASSIF_20261117/13_MATRICE_DES_POSSIBILITES.md).
