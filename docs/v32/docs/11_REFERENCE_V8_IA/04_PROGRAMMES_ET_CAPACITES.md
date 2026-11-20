# 04 — Programmes, état réel et stratégie de réemploi

## Noyau V32.2 **vérifié dans le snapshot**

| Module | Fonctions/types présents dans code | Rôle | Notes de version |
|---|---|---|---|
| `encyk_v32/config.py` | `Settings.load` et paramètres de budgets | Configurer les chemins et les dix postes | Ne jamais supposer D: accessible depuis un autre système |
| `encyk_v32/sql.py` | Schéma `/2`, `open_work`, `read_source` | Registre SQLite, sources RO | WAL, reçus, migrations contrôlées |
| `encyk_v32/sources.py` | `import_unesco`, `discover`, `discover_fallback`, `WikidataGraph`, `WikipediaIndex` | Concepts, candidats, routes, curseurs | Snapshot V32.2 ≠ nécessairement patches V6/V8 |
| `encyk_v32/pipeline.py` | `make_selection`, `make_enrichment`, `make_wave`, `import_for_job` | Packs ZIP, contrats, réutilisation, validation | API exacte dans le fichier source |
| `encyk_v32/federation.py` | Lecture fédérée, refus admission | Lire des îlots identifiés | Ne pas ouvrir l'admission canonique par défaut |
| `encyk_v32/cli.py`, `ui.py`, `doctor.py` | Diagnostics, commandes, UI | Production et introspection | Peut ouvrir le registre en écriture : pour audit RO, outil qualifié séparé |

## Acquis historiques réutilisables

- `production_kristals_v27.py` : lecture via offsets/index du XML Wikipédia, inventaire des sections, dossier de lecture, extraction souple.
- `decouverte_articles_relies_v28.py` : liens, pistes de catégories/sous-catégories, expansion à partir des pages retenues.
- `poste_chatgpt_v30.py` : dix postes, transfert manuel, ZIP groupés, import, reprise.
- V31 : prompts étendus/six passes, diagnostics, priorités, archivage et gestion `PARTIAL`.
- V7 : inventaire statique de 5 901 occurrences de fichiers et 889 occurrences de scripts dans quatre snapshots **de l'époque** (ne pas annoncer 889 modules actifs).

## V8 : description de la distribution antérieure, **à requalifier**

La V8 déjà créée dans la conversation précédente a été décrite comme **autonome**, avec `code_v8/`, `station/`, `INSTALLER_V8.py`, 88 branches vierges et un pilote `campagne_v8.py` raccordé à la station à dix postes. Les actions `campaign-start` et `campaign-pause` et les reçus `FENETRE_*.json` sont décrits dans la livraison antérieure. **L'archive V8 exécutable n'est pas présente dans le snapshot du dépôt analysé pour cet overlay** ; les endpoints, valeurs et protections doivent donc être contrôlés avant qu'une IA les modifie ou les recommande comme installés.

## Gains déjà à portée vs nouvelles fonctions

| Capacité | Statut | Priorité |
|---|---|---|
| Découverte Skope/titres et import deux passes | **Code V32 vérifié** | Stabiliser et mesurer |
| Guides de sections, sélection équilibrée, six passes | **Ancien code V6/V31 décrit, non revérifié ici** | Vérifier dans vrai V8 |
| Campagne à fenêtres, pause et reprise | **Distribution V8 antérieure rapportée** | Tests réels sur Windows |
| Extraction lossless Wikidata avec références | **Skope dispose d'un moteur ciblé, raccordement EncyK non vérifié** | Prévol sources/index |
| Déduplication sémantique interbranches | **CIBLE** | Ne pas supprimer automatiquement |
| Découpage physique de textes XXL en missions | **CIBLE** | Forte valeur documentaire |
| Réparation guidée des 506 erreurs historiques | **CIBLE** | Ne pas confondre correction de fait déjà accepté et récupération d'un rejet |
| Admission via Kit qualifié | **CIBLE DIFFÉRÉE** | Rien d'automatique |

## Règle anti-réécriture

Avant tout nouveau programme : chercher sa fonction dans les sources historiques et l'API V32/V8, définir un test fonctionnel et son autorité de donnée. Les **programmes externes** restent externes. Le composant du manager ne doit pas recréer un second registre indépendant.
