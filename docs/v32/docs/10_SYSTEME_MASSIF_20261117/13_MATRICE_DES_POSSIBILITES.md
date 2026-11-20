# 13 — Atlas des possibilités, opportunités, contraintes et décisions

Cette matrice compare **les capacités du code existant**, leur faisabilité de raccordement et leur rendement probable. Elle n’est pas une liste de fonctionnalités toutes déjà livrées. **Présent dans un snapshot** ≠ **branché en production V32**.

| Piste | Point d’appui réel | Gain souhaité | Coût/risque | Choix proposé et vérification préalable |
|---|---|---|---|---|
| Skope — voisinages du compact | `skope/db.py`, `entity_edge`, `WikidataGraph.page` corrigé V6 | Beaucoup de candidats QID reliés | Bruit sémantique, prépondérance des classes dominantes | **EXPLOITER** avec budgets, curseurs et mesures par concept; Skope RO |
| Skope — labels/aliases indexés | Skope `name`, index et `discover_fallback` | Rappels de titres hors graphe, classes rares | Faux amis, homonymes, gros index | **EXPLOITER** avec quotas, article/extrait et sélection IA |
| Skope — déclarations originales | `skope/extraction.py` et contrats source | Faits structurés avec qualificatifs/provenance réelle | Dump lossless et index rapide **non vérifiés** sur Windows | **PRÉVOL AVANT RACCORDEMENT**, aucune preuve inventée depuis compact |
| Wikipédia — texte complet, révision | XML + index direct et `pipeline.make_enrichment` | Enrichissement riche, vraies citations | Textes XXL, fatigue de contexte et vérification | **GARDER** source intégrale; sectionner missions complexes à terme |
| Wikipédia — liens internes | `decouvrir_articles_relies_v28.py`, V6 `discover_v28_wikilinks` | Découverte itérative à partir de pages SELECT | Biais des hubs, pertinence parfois indirecte | **ACTUEL V6**, borner et diversifier les graines |
| Wikipédia — catégories/sous-catégories | Acquis V28/V31; atlas V25 et index locaux | Candidats hors Wikidata, profondeur thématique | Index/couverture sur D: **non requalifiés** | **ÉVALUER EN PILOTE**, ne pas réindexer 110 Go sans preuve de gain |
| Catalogue V25 partagé | `catalogue_global_v25.py`, index partagé D: | Réutiliser routes et recherches déjà faites | Schéma versionné, partagé, risque d'incompatibilité | **LECTURE SEULE + AUDIT DES TABLES** avant tout port V32 |
| UNESCO — broader/related | `unesco-source.json`, V6 `discover_v3111_ontology` | Couvrir concepts sous-explorés | Relations thématiques ≠ équivalence | **ACTUEL V6** comme pistes seulement, jamais auto-SELECT |
| Wikipédia — révision réutilisée | `article_sources`, `source_results`, `proposal_occurrences` | Ne pas payer deux fois l’IA pour même révision/profil | Lien conceptuel non automatique | **CONSTRUIRE** index de couverture documentaire partagé sans fusion canonique |
| Préparation déterministe | `_reading_guide` V27, sections et infobox | IA concentrée sur interprétation, provenance | Parser wikitext incomplet, légendes ambiguës | **EXPLOITER V6** et produire des avertissements sur données incertaines |
| Sélection IA en amont | `SEL` V32 + retour CSV | Filtrer faux QID et homonymies | Un aller-retour ChatGPT | **GARDER**, mesurer essai one-pass seulement sur profil fiable |
| Enrichissement six passes | Prompts V31.8 adaptés V6 | Faits riches, concepts précis, exclusions justifiées | Trop de mots peuvent saturer l’IA | **GARDER** et tester mission par profil/volume plutôt que longueur du prompt |
| Reprise `PARTIAL` | `source_results`, `retry_candidates`, V6 bouton | Extraire connaissances restantes | Reprises sans rendement, doublons | **ACTUEL MANUEL**, automatiser après seuil de gain et fenêtre de cooldown |
| Réparation erreurs | `import_errors` et `source_quotes` | Récupérer faits rejetés plutôt que les abandonner | Besoin de prouver chaque citation, pas de correction aveugle | **PRIORITÉ P2**, inspecter les 506 rejets réels avant stratégie |
| 10 postes et enveloppes groupées | V30 UI + V6 `transport_groupe_v6.py` | Réduire copier-coller | ChatGPT reste un transfert manuel | **PRÉSERVER** et distribuer les 10 lanes sans doublon |
| Kristalizer/Authoring Kit | snapshot Kristalizer, staging, Kit externe | Lots mûrs plus tard | Canon/identités/provenances sous autorités distinctes | **DIFFÉRER**, ne pas injecter directement les propositions V32 |

## Décision fondée sur cet inventaire

**Court terme :** exploiter entièrement les capacités V6 **déjà raccordées**, mesurer les vrais articles uniques, la couverture des concepts et les retours refusés. L'outil de lecture seule de cette livraison sert à préparer ces mesures. Une fenêtre bornée volontaire permet de tester l'enchaînement découverte+préparation sans installer un autre manager.

**Moyen terme :** un ordonnanceur persistant à fenêtres, un outil de réparation des erreurs et le découpage de textes longs, **dans V32**. Aucun besoin de réinventer Skope, le parser du XML, la station V30 ou le canon.

**Avant tout gros raccordement :** confirmer sur le poste Windows le schéma et la présence du dump original Wikidata, du catalogue V25 et des index de catégories. Le présent inventaire est un **inventaire de codes/snapshots**, pas un scan vivant du disque D:.

## Mesure de succès

La cible n'est pas « produire 100 000 lignes ». C'est augmenter **les nouveaux faits distincts avec citation exacte, contexte et rattachement éditorial utile**, par heure opérateur et par unité de texte ChatGPT, sans sacrifier l'exploration de branches sous-couvertes. La publication canonique reste une autre campagne.
