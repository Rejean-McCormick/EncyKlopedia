# Ports et adaptateurs V32.1 — ne pas inventer les contrats externes

La GUI appelle des use cases; elle ne lance ni SQL/CLI/XML directement dans ses widgets. EncyK utilise ses adaptateurs pour les corpus et composants existants.

| Port proposé | Opérations de travail | Source/limite |
|---|---|---|
| `UnescoRegistryPort` | Branches, concepts, SKOS, P3916 et statuts | 88 dossiers `UNESCO_Kristals`, v25 |
| `WikidataGraphPort` | `node`, arêtes typées entrantes/sortantes | Skope externe, lecture seule |
| `WikidataFullPort` | Extraction ciblée des QID / qualifiers | Skope externe, capacité live à mesurer |
| `WikipediaIndexPort` | `pages_by_qids`, recherche indexée | `wiki_qid` et SQL local |
| `WikipediaTextPort` | `read_page` par ID/révision | Offsets/XML existants |
| `CandidatePort` | Routes, curseurs, campagne | SQLite EncyK |
| `SelectionPort` | Packs, décisions et retours | Réemploi station v30/v31 |
| `ProposalPort` | Extraction, provenance, conditions, statut | Nouvelle SQLite EncyK privée |
| `IslandInventoryPort` | Lister/résoudre îlots et capacités | Manager/Framework à confirmer |
| `IslandReadPort` | Lire `island_ref/state_ref`, état exact | Framework à confirmer |
| `IslandAuthorPort` | Préparer/appliquer une **opération supportée**, recevoir la preuve d'effet | Authoring Kit à confirmer (lot C seulement) |
| `FederationPort` | Snapshots parents et pins enfants | Framework à confirmer |
| `ContextPort` | Compiler contexte sur états/scope/budget | Kompiler ou adaptateur à mesurer |
| `ReportPort` | Tâches, coûts, sources absentes, gaps | EncyK |

**Contrats non présumés :** aucun `generic_import` universel, aucune atomicité multi-SQLite/files, aucune compatibilité v11 par simple succès d'un diagnostic v10. Les fonctions exactes restent à lire dans les repos externes avant implémentation; le rapport du 16 novembre ne fournit pas leurs signatures.

**Règle de résilience** : si Skope, Kit ou un îlot est absent, dégrader **seulement** les fonctions qui en dépendent; continuer la consultation disponible, la production provisoire ou l'import des ZIP recevables. Le manager n'essaie pas de reconstruire automatiquement un dump géant.

**Concurrence** : lecture de grands index bornée; file d'appels IA séparée; une écriture coordonnée par workspace quand auteur activé. Skope et Kristalizer restent intouchés. Voir [admission/reprise](../09_FEDERATION_KRISTAL/04_ADMISSION_KIT_REPRISE.md).
