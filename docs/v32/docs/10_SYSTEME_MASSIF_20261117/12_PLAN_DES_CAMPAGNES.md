# 12 — Spécification cible : ordonnanceur de campagnes à fenêtres (non encore codé)

## Pourquoi une « fenêtre » ?

L'inventaire complet initial n'est pas une opération ponctuelle finie : les liens des articles retenus débouchent sur d'autres candidats et les dumps changent. Pour obtenir **débit et reproductibilité**, il faut geler chaque **lot d'entrées IA** en préservant la liberté de produire de nouveaux lots plus tard.

## API fonctionnelle envisagée

```text
prepare_campaign(branch, policy) -> campaign_id
advance_discovery(campaign_id, max_budget, max_seconds) -> new_candidate_count, cursor_progress
freeze_window(campaign_id) -> manifest_sha256, candidate_ids, epoch, routes
feed_lanes(campaign_id, max_lanes=10) -> existing_or_new_jobs
import_return(job_id, zip) -> receipt, accepted, invalid, partial
on_import_finished(campaign_id) -> feed_lanes; maybe request_discovery_when_low_watermark
pause_campaign(campaign_id) -> durable_pause_state
resume_campaign(campaign_id) -> last_window_checkpoint
stop_campaign(campaign_id) -> report; NO statement of scientific completeness
```

Ce sont des **contrats cibles**, pas des fonctions V6 déjà disponibles.

## Politique exemple (à calibrer)

```json
{
  "id": "encyk.campaign-policy.experimental/1",
  "scope": "one_unesco_branch",
  "graph_budget_per_window": 20000,
  "title_pages_per_window": 6000,
  "max_new_candidate_pairs_per_window": 6000,
  "pending_high_watermark": 3000,
  "pending_low_watermark": 450,
  "max_global_lanes": 10,
  "selection_pack_candidates_target": 300,
  "enrichment_word_target": 45000,
  "max_no_progress_rounds": 2,
  "partial_retry_limit_per_source_profile": 2,
  "status": "PROPOSED_NOT_ACTIVE"
}
```

Les nombres viennent des ordres de grandeur V6/Météorologie, pas d'un benchmark complet des 88 branches. Ne pas convertir ce fichier en paramétrage actif sans un test.

## Algorithme choisi, en grandes lignes

1. Lire les ten lanes et les états; s'il existe un job ouvert, **ne jamais le refaire**.
2. S'il y a des `SELECTED` et une lane libre, générer les enrichissements adaptés en premier, puis les sélections.
3. Si les `PENDING` passent sous un seuil bas, que les sources sont stables et que le budget de fenêtre le permet, avancer une voie de découverte. Répartir le budget selon le gain des routes et les concepts peu couverts. Ne pas déclencher un scan global.
4. Chaque nouvelle route est archivée avec son origine. Figer les éléments transmis en pack, mais ne pas clore définitivement le graphe.
5. Importer les retours, conserver les valides/invalides, libérer les lanes, réapprovisionner automatiquement.
6. Un PARTIAL déclenche **une opportunité de complément**, pas un retour automatique systématique : quota, cooldown, profil, couverture, seuil de gain.
7. Après budget ou saturation, enregistrer un reçu de fin de fenêtre, les métriques et le digest de la source.
8. Au changement de branche, les jobs d'une autre branche **restent occupés** jusqu'à import ou annulation explicite.

## Conditions d'arrêt et anti-boucle

- **Borne absolue** sur coûts DB et nombre de pages traitées par fenêtre; aucun ordre « trouver tous les articles du monde ».
- **Progression de curseur** (pas seulement nombre de nouveaux candidats) pour décider si une voie a travaillé utilement.
- **Fenêtres de campagne** distinctes : `FIN_FENETRE` n'est pas `UNESCO_COMPLET`.
- **Backpressure** : pas de découverte massive si 10 postes pleins + réserve suffisante sans bénéfice attendu.
- **Perte de qualité** : si hausse de REJECT, baisser priorité de route faible; s'il y a 0 accepted/mission, changer méthode.
- **Exhaustivité du sujet** non revendiquée sans définition scientifique indépendante.

## Mesures non négociables

`unique_wiki_articles`, `candidate_pairs`, `candidate_routes_by_origin`, `branch_concepts_covered`, `SELECT/REJECT/HOLD`, `accepted_proposals`, `import_errors`, `new_proposals_per_source`, `partial_with_gain`, `job_count`, `human_transfers`, `source_epoch` et `reused_document_work`. Un tableau de bord avec seulement « 10 606 propositions » favorise l'inflation de texte plutôt que l'exhaustivité utile.

## Étape pratique actuelle : deux outils livrés

1. **OBSERVATEUR_CAMPAGNES_V32.py** : lecture strictement RO et plan d'action, avec manifeste optionnel de candidats par branche. Aucune modification SQLite.
2. **CAMPAGNE_BORNEE_V32.py** : simulation par défaut, puis **opt-in** si `--apply --confirm` et station V6 fermée. Réutilise `discover()`, `discover_fallback()`, `discover_v28_wikilinks()`, `discover_v3111_ontology()` et `make_wave()` **existants**, répartit un budget TOTAL de 20 000 voisins par défaut sur au plus 4 tours, s'arrête à réserve PENDING de 3 000 ou absence de progression, et écrit un reçu dans un dossier externe. Cela peut **précharger une fenêtre** et remplir les postes; ce n'est ni une automatisation de ChatGPT ni un moteur de campagne persistant. Après import des retours, la station V6 continue de remplir les postes, mais ne relance pas la prochaine fenêtre automatiquement.

**Limitations de la commande active** : la fermeture de la station est obligatoire pour éviter deux orchestrateurs concurrents; contrôle best-effort Windows en mémoire, échec fermé s'il est indisponible. Ce mode doit être qualifié sur le vrai Windows avant une généralisation. La détection de source changeante, les écarts de curseurs et la qualité des candidats restent gérés par le code V32/V6 de l'installation.

Le lot suivant pourra raccorder la politique à `Station._perform` avec stockage de fenêtres durable, interface web et ordonnanceur permanent qualifié sur 88 branches.
