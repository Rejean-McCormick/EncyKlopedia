# Plan de réalisation, migration et tests d'acceptation v31

**Statut :** feuille de réalisation documentaire, **code non modifié**.  
**Priorité absolue :** aucun arrêt ni corruption de la production existante ; conservation intégrale des preuves et tâches en cours.

## 1. Cadence de livraison : petites étapes vérifiables

La production UNESCO v28 et Kristal v27 peut continuer pendant les étapes de lecture seule et de préqualification en observation. Pour chaque étape : produire un diff source ciblé, une sauvegarde, un rapport de tests, un mécanisme de rollback et un journal de migration. Toute fonction future doit pouvoir être désactivée indépendamment du poste v30.

| Phase | Livrable de code | Risque en production | Critère d'acceptation |
|---|---|---|---|
| **0. Audit** | Rapport de code et couverture, schémas/jointures, signatures XML | Aucun si lecture seule | Contrats natifs et sources observés ; aucun fichier source modifié |
| **1. Mesure** | Statistiques globales dérivées des bases existantes | Faible | Dénominateurs documentés ; exact/estimé/inconnu ; absence de double compte |
| **2. Profils** | Cache de profils à la révision, en mode observation | Faible | Profils reproductibles ; pas de faux extraits ; aucun clone de la base Wikipédia |
| **3. Routage** | Plusieurs branches candidates et qualification article–concept, en observation | Faible | Aucun article non classé supprimé ; tests sur plusieurs branches ; traçabilité complète |
| **4. Pilotage** | Priorisation sur une fraction des futurs candidats libres, groupe témoin | Moyen | Identities/proofs préservées ; qualité et rappel audités ; rollback immédiat |
| **5. Packs** | Pilotage 150–200, puis 300 si budget et import compatibles | Moyen | 100 % des décisions reçues, importables et idempotentes ; aucun pack scellé retouché |
| **6. Extension** | Activation graduelle des 10 files, puis d'autres branches | Moyen | KPIs stables par branche ; aucun incident de diffusion/canonique |

## 2. Phase 0 — audit des mécanismes déjà écrits

### 2.1 Ordre d'inspection recommandé

1. `catalogue_global_v25.py`, `generer_branches_unesco_v25.py`, tests `test_catalogue_global_v25.py` : contrats de branches/concepts/assignments et test multibranche.
2. `semantic_candidate_stage_v4.py`, `semantic_candidate_stage_v6.py` et leurs tests : fonctions déjà disponibles pour du staging documentaire, garanties d'immutabilité.
3. `local_wikipedia_bridge.py`, `inventaire_categories_v26.py`, `decouvrir_articles_relies_v28.py` : structure des requêtes, résolution des cibles, catégories, stratégies de découverte.
4. `contexte_revue_unesco_v28.py` et tests : sélecteur d'extraits XML, contrôle de signature, extraction de passages.
5. `poste_chatgpt_v30.py`, tests `test_poste_chatgpt_v30.py` : création des tâches, statut libre, gel, dix files, validation des retours et upgrade.
6. `production_kristals_v27.py` et tests : circuits privés et citations.

Le diagnostic fourni identifie l'existence de ces modules, **mais ne contient pas leur source**. Demander un export **ciblé des scripts et tests**, pas les bases de 125 Go ni le dump XML.

### 2.2 Tests des données sans balayage massif

- Vérifier les compteurs et le dernier `ingest_state` ; comparer le nombre de pages en `ns=0` non-redirections avec une source de même snapshot, pas avec les statistiques publiques courantes.
- Exécuter des résolutions ciblées `wiki_pagelinks.target_id → wiki_linktargets(ns,title) → wiki_pages`; inclure alias, redirections, caractères spéciaux et cibles manquantes.
- Sur 20 à 50 pages échantillonnées et vérifiées à divers offsets du dump, rapprocher `page_id`, `revision_id`, `title` et octets lus. Toute incohérence critique interdit les extraits par offset pour ce couple dump/index.
- Vérifier les index disponibles avant des requêtes inverses de liens ; pas de `COUNT(*)` complet de la base de 125 Go sans fenêtre dédiée et justification.
- Vérifier qu'une même page peut être affectée à deux branches sans être créée deux fois dans le catalogue ; vérifier clé composée de `assignments` et collisions de concepts.

**Sortie :** `AUDIT_CODE_ET_DONNEES_V31.md`, énumérations natives, carte des fonctions et décision *réutiliser / étendre / remplacer* pour chaque module.

## 3. Phase 1 — statistiques sans migration invasive

Un tableau de bord global agrège des **snapshots cohérents** avec `source_db`, timestamp et périmètre. Les grandes bases sont lues via métadonnées d'ingestion/counters validés et requêtes bornées. Les petites bases actives sont lues par transaction courte ou copie SQLite cohérente, sans copie brute d'un fichier WAL en cours d'écriture.

Tests : rapport généré même si une base manque ; statut « inconnu » plutôt que zéro ; somme des statuts = total de l'univers approprié ; distinction candidates uniques / preuves / jobs / décisions importées ; écart explicitement signalé si des sources sont à des dates différentes. Sorties JSON (machine), HTML et CSV/texte (humain), toutes avec une version de schéma.

## 4. Phases 2–3 — évaluation de la qualification

### 4.1 Constitution des jeux de contrôle

Réutiliser les décisions historiques comme premier matériau de travail, sans confondre l'existence d'un `REJECT` avec l'absence d'intérêt d'une page dans toute autre branche. Les 5 lots analysés précédemment ne couvrent qu'une branche (`unesco.mt1.10`) et restent insuffisants pour valider une généralisation.

- **Validation par groupes** : séparer les mêmes pages/concepts/familles de liens entre apprentissage et test afin de limiter les fuites.
- **Échantillon par branche** : sélectionner explicitement des domaines autres que la branche initiale, incluant des cas multi-affectation et des articles à thème général.
- **Audit des différés** : échantillonnage stratifié à probabilités de sélection connues, avec suréchantillonnage des catégories faibles, articles géographiques et entrées sans extrait.
- **HOLD** : état d'incertitude distinct, pas une étiquette négative d'entraînement par défaut.
- **Éviter les biais** : inclure profils courts/longs, catégories génériques/spécifiques, homonymies, redirections et pages difficiles.

### 4.2 Mesures

- **Précision** dans les candidats effectivement envoyés en revue.
- **Rappel** des bonnes correspondances dans le stock éligible, estimé à partir des revues et de l'audit probabiliste des différés.
- **Rappel par domaine / type / voie de découverte**, non seulement global.
- **Taux de revue utile** (APPROVE importés par volume de preuves et coût de traitement) ; `HOLD` par cause.
- **Qualité des preuves** : proportion de décisions avec extrait à révision vérifiée ; concordance citation/source.
- **Couverture** : concepts desservis, pages distinctes, diversité des branches et cas multi-branches.

**Cible de sûreté indicative :** rappel estimé très élevé, p. ex. 98 %, **avec intervalle d'incertitude et taille d'échantillon explicités** avant d'envisager de priver un candidat de revue. Ce n'est pas un seuil mathématiquement prouvé par nos 58 APPROVE historiques. A défaut de preuves suffisantes, autoriser le **classement** mais pas le filtrage destructif.

### 4.3 Test anti-appauvrissement

Lancer deux sélections sur le même stock libre : `baseline_v28` et `priorisation_v31`. Vérifier quels candidats approuvés la politique nouvelle aurait dépriorisés et expliquer chaque catégorie de faux négatifs. Ne pas compter comme amélioration le seul gain en taux APPROVE lorsque le nombre absolu d'APPROVE retrouvé s'effondre.

## 5. Phase 4 — canari et isolation des tâches

Un **flag de fonctionnalité** pilote la sélection :

```text
qualification.mode = off | observe | canary | on
prioritisation.enabled = false
packs_adaptatifs.enabled = false
exploration.part = 0.25              # paramètre de départ à étudier, non figé
packs.fallback_candidates = 110
packs.pilot_candidates = 150         # à étendre ensuite à 200 puis 300
```

Paramètres illustratifs ; ils ne correspondent pas à un fichier de configuration déjà branché.

En `observe`, la sélection native ne change pas. En `canary`, sélectionner une petite partie des **futures tâches libres**, garder une file témoin intacte ; journaliser chaque candidat retenu, différé et récupéré par exploration. Les tâches existantes restent immuables. La bascule se fait à un point de génération vérifié dans le code, sous un verrou natif, et non en modifiant les ZIP après émission.

### Conditions d'arrêt immédiat

- Un `candidate_id` absent/dupliqué, un CSV incomplet, une empreinte modifiée ou une tâche figée retouchée.
- Une désynchronisation entre les 10 lanes et les tâches, ou un pack retourné non importable.
- Un passage inventé, un décalage de révision ou un contournement de signature XML.
- Une hausse substantielle inexpliquée du HOLD ou un rappel inférieur au seuil de sûreté établi.
- Une écriture non autorisée dans la base Wikipédia, le catalogue ou les claims Kristal.

**Rollback :** `qualification.mode=off`, retrait de l'adaptateur de sélection, restauration du code natif depuis sauvegarde, conservation des logs de qualification pour audit. Les jobs déjà scellés continuent sur leur contrat initial.

## 6. Phase 5 — validation des packs élargis

Ne pas modifier l'importateur à l'aveugle. Créer un pack **natif de test** avec 150 candidats, puis 200 ; seulement ensuite 300 si les tests sont concluants. Vérifier :

1. Contrat CSV/JSONL/manifeste respecté et toutes les preuves rattachées par `candidate_id`.
2. Volume documentaire et tokens compatibles avec une revue approfondie, **avec marge suffisante pour les 300 justifications de sortie**.
3. Retour contenant **exactement** les 150, 200 ou 300 IDs attendus, sans omission, duplication ou réécriture.
4. Import v28 `APPLY_OK`, signatures préservées, idempotence du second import, pas d'admission canonique ni de publication.
5. Aucun dépassement de délai ou troncature silencieuse, ni baisse de qualité par rapport au groupe témoin.
6. Les 10 conversations peuvent maintenir plusieurs tâches sans invalider les preuves gelées.

Si un test échoue, revenir à 110 ; les packs adaptatifs doivent pouvoir choisir une taille **plus petite** selon les preuves, jamais imposer 300.

## 7. Etapes de livraison de code retenues

- **Livraison A :** ajustement / réutilisation d'adaptateurs de lecture et preuves XML, tests ciblés ; pas d'évolution de la production.
- **Livraison B :** statistiques cohérentes et rapports par branche ; première base de pilotage.
- **Livraison C :** profils et qualification en observation ; analyses de rappel.
- **Livraison D :** canari de priorisation avec conservation des différés et logs exhaustifs.
- **Livraison E :** packs élargis natifs après validation de toutes les contraintes de retour et d'import.
- **Livraison F :** généralisation multibranche et mise à l'échelle par lots locaux reprenables.

Chaque livraison doit comprendre : diff source minimal, test unitaire + intégration, contrôle des schémas avant/après, sauvegardes, vérification d'empreintes, plan de retrait, note de version et rapport de métriques avant/après.

## 8. Définition de « terminé » pour la documentation et pour le code

**Documentation prête** quand les responsabilités, interfaces, règles de sécurité, métriques et choix d'architecture sont décrits, avec les inconnues identifiées. **Code prêt** seulement quand tous les tests d'intégration, import, sauvegarde et rollback ont été exécutés sur la station réelle. La livraison de ce dossier ne signale **aucune** activation du système cible.
