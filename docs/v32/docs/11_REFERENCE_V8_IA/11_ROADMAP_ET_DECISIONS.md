# 11 — Décisions d'architecture, alternatives et prochaines étapes

## Alternatives réellement discutées

| Option | Gain | Coût et faiblesse | Verdict |
|---|---|---|---|
| Tout découvrir puis figer **définitivement** | Simplicité apparente | Les liens ouvrent de nouvelles pages et le corpus évolue; « tout » n'a pas de borne vérifiable | Rejetée comme règle générale |
| Découvrir et préparer manuellement à chaque vague | Fonctionne déjà | Trop de clics, file opaque, tâches répétées | Héritage V6 à dépasser |
| Orchestration autonome illimitée | Débit apparent | Risque de parcours sans fin et surcharge des dix postes | Rejetée |
| Réécrire Skope, Médiathèque, Kristalizer dans EncyK | Tout sous un nom | Duplication de code et violation d'autorité | Rejetée |
| **Fenêtres bornées + mémoire documentaire + dix postes + contrôle qualité** | Débit, reprise, source versionnée | Plusieurs couches à qualifier | **Choisie**, sous conditions |

## Décisions figées jusqu'à nouvelle justification

1. **Une base privée EncyK** pour les propositions, les missions et les décisions; pas un second registre concurrent.
2. **Les sources restent externes et en lecture seule**, avec adaptation indexée.
3. **La copie locale du moteur V8**, si installée, n'emporte pas le code des projets Skope/Kristalizer.
4. **Campagnes à fenêtres** : inventaires de lots figés, nouvelle découverte ultérieure permise.
5. **Deux passes ChatGPT comme contrat de base**. Un passage combiné peut être testé pour des relations fiables, mais pas généralisé sans comparer la précision.
6. **Enrichissement profond, pas quotas artificiels** ; `PARTIAL` accepté et récupérable.
7. **Réemploi document/révision** avec rattachement conceptuel indépendant.
8. **Canon différé** : aucune admission via simple ZIP.

## Priorités après consolidation documentaire

| Priorité | Chantier | Livrable technique | Test décisif |
|---|---|---|---|
| P0 | Requalifier distribution V8 sur Windows | Manifest code/ABI, chemins, tests, statut réel | 88 branches neuves, zero ancien job, UI démarre |
| P1 | Observabilité et campagnes | Découverte bornée, reçus, pause/reprise, reprise idempotente | Pas de job dupliqué, 10 lanes globales respectées |
| P2 | Réparation des refus d'import | File par `import_errors` avec contexte et preuves | Sauver des lignes sans falsifier les citations |
| P3 | Traitement de grands articles | Missions subdivisées par sections, offsets/empreintes | Plus de faits sourcés et moins de PARTIAL inutiles |
| P4 | Mémoire documentaire interbranches | Cache `(page,révision,SHA,profil,segments)` et liens concepts | Réutiliser sans faire disparaître les concepts spécifiques |
| P5 | Extraction Wikidata originale | Contrat source explicite avec references/qualifiers | Pas de fausse preuve issue de `entity_edge` |
| P6 | Qualification du Kit et intégration | Handoff autorisé et transactionnel | Aucune admission ou mutation canonique non autorisée |

## Ce qui doit être mesuré plutôt que promis

La réussite sur Météorologie seule ne prouve pas la capacité et la précision sur 88 branches. Les statistiques de production anciennes ne sont pas la V8 neuve. L'exhaustivité d'une branche n'est pas définie par zéro poste occupé. Une extraction lossless disponible dans le code Skope ne signifie pas que son dump original et son index aléatoire soient correctement montés sur Windows.

## Ce que cet overlay apporte — et ce qu'il n'apporte pas

**Livré :** documentation, cohérence des points d'entrée, contrats corrects, consignes IA, références croisées, installateur sûr et tests de cette documentation. **Non livré :** modifications au moteur de production, extraction Wikidata complète raccordée, ordonnanceur V8 testé à nouveau, nouvelle base SQLite, admission canonique.
