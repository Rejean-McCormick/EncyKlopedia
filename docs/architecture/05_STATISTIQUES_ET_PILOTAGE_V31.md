# Statistiques globales et pilotage : définitions vérifiables

**Statut :** contrat de tableaux de bord cible, non déployé.  
**Principe :** afficher le périmètre, l'unité, la période, le dénominateur, la provenance et la fiabilité de chaque indicateur. Ne jamais remplacer `inconnu` par zéro.

## 1. Tableau de bord en six domaines

| Domaine | Compteurs proposés | Source prioritaire identifiée |
|---|---|---|
| Corpus Wikipédia | Pages du snapshot, pages `ns=0`, redirections, listes/homonymies si détectables, révisions accessibles, couverture QID | `wiki_pages`, `ingest_state`, index direct v21 validé |
| Qualification globale | Pages profilées, versions de profil, pages multi-branches, pages sans proposition de branche, qualité de l'accès au texte | Couche profil cible, reconstruite sur index existants |
| Branches UNESCO | Branches configurées, concepts actifs, concepts sans article validé, pages proposées par branche, affectations multiples | Catalogue `branches`, `branch_concepts`, `assignments` + propositions |
| Découverte v28 | Candidats uniques par clé, sources `WIKILINK/CATEGORY/SUBCATEGORY`, preuves, nouveaux seeds, révisions divergentes | `candidates`, `evidence`, `seed_queue`, `seed_revision_mismatches` |
| Station/revues | Candidats libres / figés / retournés / importés, tâches par état et lane, décisions importées, erreurs/retry, extraits vérifiés | `station_v30.sqlite`, `reviewed_article_links_v28` |
| Kristal privé | Articles visités, claims privés, citations vérifiées, relations aux branches/concepts, imports delta | `KRISTAL_CUMULATIF_PRIVE_V27.sqlite` |

**Règle de comptage :** les pages sont comptées en `DISTINCT(wiki,page_id)` au périmètre concerné, les concepts en clés `(vocabulary,concept_id)`, les couples en clés définies par le moteur natif, les tâches en ID de job natif et les preuves en identifiants/empreintes propres. Les totaux multibranches **ne sont pas additionnables** sans déduplication explicite.

## 2. Mesures exactes, estimées et inconnues

Chaque champ du rapport contient une qualité :

- `exact` : requête déterministe sur un snapshot cohérent, unité et filtres connus.
- `estimated` : extrapolation d'un échantillon avec plan et incertitude publiés.
- `unknown` : aucun dénominateur fiable, source indisponible, ou comparabilité impossible.
- `stale` : information exacte à une date antérieure, qu'on ne doit pas présenter comme état actuel.

Les compteurs extraits du diagnostic du 13 novembre 2026 représentent une **photographie historique** : par exemple 2 115 articles catalogue, 2 358 assignments, 39 301 candidats, 100 096 preuves, 36 786 lignes station et 4 119 claims Kristal. Ne pas les présenter comme « maintenant » sans relecture de sources récentes.

## 3. Les pourcentages de progression

### 3.1 Productivité d'une série de packs

```text
revues_tranchees = APPROVE_importes + REJECT_importes
revues_importees = APPROVE_importes + REJECT_importes + HOLD_importes
part_tranchee = revues_tranchees / revues_importees   si revues_importees > 0
rendement_approve = APPROVE_importes / revues_importees  si revues_importees > 0
```

Ces taux ne mesurent **ni** les nouveaux articles créés, **ni** l'avancement de toute la branche.

### 3.2 Progression du stock connu de candidats

```text
avancement_stock_connu = nb_candidats_distincts_du_stock_dont_import_confirme
                          / nb_candidats_distincts_du_stock_eligible
```

Exiger un **snapshot gelé du stock et de ses règles d'éligibilité**. Une découverte en continu change le dénominateur, donc afficher la version et la date du stock ; les HOLD importés sont comptés séparément comme *revus mais non tranchés*.

### 3.3 Couverture de la branche UNESCO

Plusieurs métriques non interchangeables :

- **Couverture des concepts :** concepts ayant ≥1 affectation documentaire validée / concepts actifs dans la branche.
- **Profondeur de couverture :** distribution d'affectations/articles distincts par concept, avec objectifs de couverture explicités.
- **Saturation exploratoire :** candidats nouveaux pertinents et APPROVE supplémentaires pour N nouvelles expansions de recherche, avec stabilité sur plusieurs campagnes.
- **Avancement opérationnel :** tâches importées / tâches planifiées pour une campagne définie.

**Ne pas annoncer « la branche est terminée à X % »** tant qu'une définition contractuelle de *terminée* et un dénominateur ne sont pas fixés. Préférer « 85 % de la campagne A examinée » ou « 37/41 concepts possèdent au moins une affectation » quand cela est effectivement observé.

### 3.4 Monde Wikipédia et multibranche

```text
couverture_profilage = pages_ns0_profils_valides / pages_ns0_eligibles_snapshot
couverture_routage = pages_ns0_avec_au_moins_une_branche_candidate / pages_ns0_eligibles_snapshot
part_multibranche = pages_avec_2_ou_plus_branches / pages_avec_branche_candidate
```

La proportion de pages sans branche n'est pas une « erreur de classification » par elle-même. Les redirections et homonymies doivent être représentées séparément.

## 4. Qualité de la présélection

### 4.1 Mesures

- `precision` : APPROVE / (APPROVE + REJECT) sur les candidats **tranchés** de la strate observée ; présenter aussi le taux HOLD.
- `recall` : proportion de toutes les bonnes correspondances retrouvées parmi l'univers éligible. Il ne peut être établi par les seuls candidats présélectionnés ; exige une référence ou un audit des différés.
- `yield_per_cost` : APPROVE importés pour un coût de revue explicite (nombre de paires, preuves, tokens, durée mesurée).
- `enrichment_success` : dossiers nécessitant une preuve ciblée pour lesquels un extrait à révision vérifiée a réellement été obtenu.
- `false_negative_audit` : APPROVE retrouvés dans l'échantillon différé, par strate et par politique ; corriger l'estimation selon les probabilités d'échantillonnage.
- `staleness` : proportion de preuves périmées ou de `revision_id` contradictoires.

Un score de priorisation améliorant fortement les premières dizaines d'APPROVE peut **diminuer le rappel global** s'il écarte les cas atypiques. Le tableau de bord doit afficher les deux.

### 4.2 Test A/B équitable

Le contrôle doit suivre le même corpus, une fenêtre temporelle comparable, des quotas par concept et une politique d'échantillonnage connue. Afficher le nombre brut de nouvelles affectations, pas seulement le taux d'APPROVE. Répéter les essais sur plusieurs branches au lieu de généraliser la seule `unesco.mt1.10`.

## 5. Rapport machine proposé

```json
{
  "schema": "encyklopedia.stats_globales.v31/1",
  "created_utc": "horodatage-iso8601",
  "sources": [
    {"id": "catalogue_v25", "snapshot_utc": "horodatage-iso8601", "consistent": true}
  ],
  "metrics": [
    {
      "id": "catalogue.articles_uniques",
      "scope": "all_configured_branches",
      "value": null,
      "unit": "distinct_page_ids",
      "quality": "unknown",
      "definition": "Nombre d'articles uniques du catalogue au snapshot choisi",
      "source": "catalogue_v25.articles",
      "denominator": null,
      "warning": "Exemple de format ; aucune valeur observée"
    }
  ],
  "warnings": []
}
```

Ce JSON est un **exemple de schéma**, pas une statistique réelle. Lorsque `quality=unknown`, la valeur est `null`, jamais `0`. La représentation finale devra être validée et documentée avant de devenir une API.

## 6. Cohérence et performance

- Effectuer les lectures sur petits snapshots cohérents lorsqu'il existe des écritures concurrentes ; éviter le téléchargement naïf de fichiers SQLite actifs avec sidecars WAL non pris en compte.
- Sur l'index Wikipédia massif, s'appuyer sur tables d'état ou compteurs officiels d'ingestion vérifiés, index existants et échantillons ciblés. Ne pas lancer de jointures globales coûteuses à chaque rafraîchissement.
- Les résultats sont enregistrés avec le `run_id`, le schéma, la provenance et le timestamp de chaque source ; signaler explicitement les snapshots incomparables.
- Les dix lanes sont des moyens de production, pas des univers de comptage différents : dédupliquer les candidats/révisions selon les contrats natifs.
- Les retours ZIP non importés, les claims Kristal et les affectations UNESCO ne s'additionnent pas.

## 7. Tableau de bord attendu

L'écran d'accueil doit répondre en moins d'une minute d'interaction à cinq questions :

1. Combien de pages du corpus choisi sont inventoriées, profilées et classées (avec date et qualité) ?
2. Quelles branches UNESCO existent, quels concepts sont couverts, et lesquelles ont le plus d'incertitude ?
3. Combien de candidats libres, différés, enrichissables, scellés, examinés et importés ?
4. Quels sont le rendement des sélections et le rappel estimé parmi les candidats différés ?
5. Existe-t-il des alertes de données : signature XML, statut de tâches, preuves manquantes, import en erreur ou divergence de révision ?

En l'absence de données fiables, afficher « **inconnu / à mesurer** » avec la cause et la source à vérifier, jamais un taux arbitraire.
