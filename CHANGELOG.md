## 0.13.8 — Correctif Skope : recherche sans parcours massif (13 octobre 2026)
- `Q192154` cherche directement via l'identifiant, sans scan des noms.
- `Embryophyta` utilise l'index `idx_name_norm` et des plages bornées, sans `ORDER BY e.wid`.
- Interface : message Recherche…, bouton désactivé pendant la recherche et délai de 15 s.
- Conserve le dépôt unique EncyK, le guide Arketype, la sélection de Kristal et la lecture seule sur D:.

## 0.13.7 — Enrichissement Kristal depuis EncyK (13 octobre 2026)
- Sélection du Kristal destinataire dans le lanceur Skope intégré.
- Chemin d'index D: et guide Arketype PRF-03 Botany préremplis.
- Export de proposition lié à l'identité du Kristal, sans chemin privé.
- Boutons explicites `check` et `build-discovery` via Authoring Kit 3.3.1.
- Aucun changement du canon, du dump ou de l'index en arrière-plan.

## 0.13.6 — 2026-10-13 — conserver les données Wikidata enrichies

- Retrait complet de l'option « Supprimer le pilote historique » de l'outil D:.
- Protection ferme des extractions Wikidata, snapshots JSONL, handoffs, provenance, seeds et catalogues d'œuvres candidates, même s'ils résident dans les dossiers anciens.
- Maintien des quatre seuls déplacements de métadonnées de fonctionnement (SHA-256 contrôlés) et suppression limitée aux copies exactes dans `20_evidence/legacy-ingest` ; aucune autre production Wikidata n'est supprimable.
- Si une copie est le seul exemplaire disponible, elle est conservée ; si une destination est différente, nettoyage refusé.
- `10_sources`, `30_working`, `40_kristal` et `50_mediatheque` sont intouchables par ce nettoyeur ; aucune sauvegarde ajoutée.
- Remplace le nettoyeur v0.13.5 qui pouvait détruire les extractions et œuvres candidates.

## 0.13.5 — 2026-10-13

- Le cleaner n'archive pas et ne réécrit aucun manifeste historique.
- Quatre métadonnées utilisées par le moteur courant sont déplacées dans leurs emplacements actifs ; les anciennes copies sont supprimées uniquement après contrôle SHA-256.
- Les artefacts du pilote historique (1 123 entités, 533 œuvres candidates) ont une option de suppression définitive séparée et désactivée par défaut.
- Le cleaner ne modifie jamais `10_sources`, `30_working`, la base SQLite, le dump ni les index ; dossiers inconnus protégés.
- Maintien du dépôt de code et du stockage D: séparés.

## 0.13.4 — 2026-10-13 — nettoyage D: direct, sans copies de secours

- Nouveau cleaner graphique en deux étapes : **Analyser** (sans effet) puis **Déplacer et nettoyer** (confirmation explicite).
- Conserve intégralement `10_sources` et `30_working`; aucun dump, SQLite, index rapide ou lexical modifié.
- Déplace les 14 fichiers historiques utiles vers les zones actives `20_evidence` et `90_runtime`.
- Supprime uniquement les copies SHA-256 identiques de l'ancienne étape `Copier 20_ingest`, les README hérités vérifiés et les dossiers vides.
- Ne crée aucun backup ou dossier d'archive ; bloque les conflits et conserve les fichiers inconnus.
- Préserve les anciens manifestes de provenance sans les réécrire : certains chemins historiques absolus doivent être régénérés par les pipelines actifs pour une nouvelle livraison.

## 0.13.3 — 2026-10-13 — séparation code / données

- Le dépôt Git reste distinct de `D:\EncyKlopedia` ; correction de l'hypothèse v0.13.2.
- Configuration Windows avec jonctions explicites, aperçu par défaut, refus de tout remplacement de contenu existant.
- Cleaner graphique pour D: : audit, création de zones de données, copie vérifiée des preuves historiques ; archivage optionnel du dossier `40_kristal` seulement s'il contient le README attendu.
- `20_ingest`, `50_mediatheque`, dumps, SQLite, index rapides et lexicaux protégés.
- Déplacement des manifestes de référence du paquet vers `docs/historical-data-manifests` pour éviter l'écriture dans le dépôt.

# Changelog

## 0.13.1 — 2026-10-13 — consolidation Skope à dépôt unique

- Prend EncyK 0.13 comme base de référence et abandonne la livraison Skope standalone.
- Conserve une seule CLI/UI, un seul index EncyK en lecture seule et un export EncyK non canonique.
- Ajoute un nettoyage local **facultatif** des fichiers résiduels de la première intégration, liste blanche SHA-256, sans jamais toucher au dépôt Skope externe.
- Ajoute des tests de non-régression de cette consolidation ; aucun changement des responsabilités canoniques.

## 0.13.0 — 2026-10-13

- Intègre l’exploration Skope 0.2 (branches, profondeurs, convergence) comme outil EncyK autonome en UI mais dépendant de l’index global compact partagé.
- Remplace l’export source Skope standalone par une proposition de collecte EncyK non canonique : registre QID + scope v3 sous `staged/`, sans JSON source inventé.
- Prend en charge les guides Arketype v1.4 `arketype.scope-guidance/1.0` en lecture seule, sans injection dans `state_scope`.
- Ajoute `Lancer_Skope.pyw` et `Nettoyer_Fichiers_Obsoletes.pyw` avec manifeste de nettoyage vérifié (aucun fichier supprimable dans cette migration).
- Préserve le handoff Médiathèque `encyk.source-evidence-handoff/2.0.0` et l’extraction Wikidata complète.


## 0.12.0 — 2026-10-03

- Reduces EncyK to `discover → acquire → extract → handoff`.
- Makes Médiathèque kOA `0.2.0` / `koa.source-catalog/2.0.0` the canonical persistent source authority.
- Replaces the old DaaT/Kristal corpus handoff with `encyk.source-evidence-handoff/2.0.0` targeting Médiathèque.
- Removes active `40_kristal` and `50_mediatheque` zones.
- Removes Kristal-shaped candidate Referent Registry publication and replaces it with consumer-neutral external identity candidates.
- Removes the built-in documentary/media candidate catalog; complete source evidence remains available to the source authority.
- Removes the vendored Interaction Kernel snapshot and stale Kristal v5 reference documentation.
- Aligns ecosystem metadata to Interaction Kernel `2.0.0-dev.2`, DaaT/`daat`, portable `kristal_state/6.0`, Kristal/Kristall `7.0.0-draft.3.2`, Médiathèque `0.2.0`, and Kompiler `0.5.0`.
- Moves `20_ingest` to `20_evidence` and optional entity-vault cache authority to `30_working`.
- Renames Kristal-specific launchers to generic harvest commands.

Historical pre-0.12 plans/changelogs are under `docs/history/`.
