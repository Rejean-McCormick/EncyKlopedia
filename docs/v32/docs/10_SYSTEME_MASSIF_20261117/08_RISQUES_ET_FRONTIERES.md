# 08 — Périmètres, risques, droits et règles anti-corruption

## Frontières de propriété des données

| Ensemble | Lecture | Écriture depuis ce pack | Pourquoi |
|---|---|---|---|
| `D:\EncyKlopedia\30_working\...\etat_v32\encyk_v32.sqlite` | **Oui** via observateur en mode RO | **Jamais** | Registre privé en production; pas de migration silencieuse |
| `D:\...\wikidata\wikidata.compact.sqlite` | Code V32/Skope en RO, non ouvert par l'observateur | Jamais | Gros index source |
| `D:\...\wikipedia_en.sqlite`, `...direct_pages_v21.sqlite`, XML | Code d'extraction de V32 en RO | Jamais | Source et index partagés |
| Catalogue UNESCO–Wikipédia V25 | Inventorié, usage lecteur spécifique | Jamais | Héritage partagé |
| `C:\mycode\EncyKlopedia\Skope` | Snapshot ZIP inspecté | Jamais | Dépôt indépendant |
| `C:\mycode\EncyKlopedia\scan_engine` / Kristalizer | Snapshot ZIP inspecté | Jamais | Préparation du canon, pas producteur ChatGPT |
| `C:\mycode\EncyKlopedia\mediatheque[-references]` | Inventaire par snapshot seulement | Jamais | Environnement protégé |
| `C:\mycode\EncyKlopedia\UNESCO_Kristals` | Lecture des états **si autorisée dans V32**, non par ce pack | Jamais | 88 îlots préexistants indépendants |
| `D:\EncyKlopedia_ARCHIVES\V31_UNESCO_MT1_10_...` | Référence historique | Jamais | Pilote MT1.10 archivé, pas à restaurer |
| `C:\mycode\EncyKlopedia\EncyKlopedia\docs/v32/docs/10_...` | Oui | **Installation documentation explicitement opt-in** | Nouveaux `.md/.csv/.json` seulement |

## Risques de workflow et règles de réduction

1. **Tâches déjà ouvertes** : ne jamais changer les sources, annuler ou re-générer `SEL_000008` etc. Le pack de documentation n'effectue pas cette opération.
2. **Erreur d'index Skope** : V32.2 brut utilisait un offset artificiel `property_id`; station V4+ répare `P31/P279/P921/P361`. Vérifier la correction installée, éviter l'écrasement par un ZIP d'origine.
3. **Révision** : l'index `latest_revision` peut différer du XML extrait; le pack doit annoncer la vraie révision/texte haché. Une proposition doit pointer vers celle qu'elle cite.
4. **Exact quote ≠ preuve sémantique** : garder une chaîne de provenance sans fausse confiance. Les cas à haut risque demandent une analyse ciblée.
5. **Répétitions conceptuelles** : un article peut apparaître sous plusieurs concepts. La dédup ne doit pas supprimer de rattachements valides ni créer une île unique par QID.
6. **Source lossless non qualifiée** : ne pas extrapoler les références de Wikidata depuis `entity_edge`; utiliser extraction Skope conditionnelle.
7. **PARTIAL persistant** : ne jamais convertir `PARTIAL` en `PROCESSED` par défaut pour faire joli; expliciter les domaines restants.
8. **WAL** : ne jamais déplacer ou supprimer un `-wal` SQLite actif sans procédure SQLite cohérente. Pour sauvegarde : SQLite Backup API.
9. **Packs trop lourds** : 60 articles peut représenter 140 000 mots. La limite pertinente est le contenu réel traité et la qualité de l'extraction.
10. **Épuisement de budget** : `remaining_graph_budget` ne mesure pas l'exhaustivité Wikipédia; une nouvelle route peut encore apparaître via titres/ontologie/liens.
11. **Licence et attribution** : préserver les provenances et respecter les licences des sources Wikipédia/Wikidata lors de toute future diffusion. Le présent pack est pour le cumul privé.

## Règle des versions et du rollback

Chaque mise à jour future du moteur doit avoir : signatures de code attendues, sauvegarde avec SHA-256, portée réduite et refus sur version inattendue. **Cette livraison ne modifie aucun `.py` existant**. Son installateur ne copie que le dossier de documentation, avec une sauvegarde des fichiers remplacés éventuels dans un dossier distinct à l'intérieur du dépôt.

## Frontière entre EncyK et Kristalizer

EncyK accumule des `proposals` DRAFT/UNASSIGNED, rattachées à `subject_key`, concept UNESCO, source et citation. Kristalizer rapproche des projets et peut préparer des *staging workspaces*. L'Authoring Kit autorisé représente un autre niveau. Les 88 branches UNESCO ne sont ni 88 QID ni 88 Kristals automatiquement : **fédération d'îlots indépendants**. `admit_proposals()` du V32.2 échoue volontairement; conserver ce refus jusqu'à une qualification réelle des contrats.
