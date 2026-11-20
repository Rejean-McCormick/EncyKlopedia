# 04 — Workflow explicite pour l'opérateur (état V6 et cible optimisée)

## 1. Ce que fait l'opérateur aujourd'hui avec la station V6

1. **Ouvrir la station 88 branches** avec `OUVRIR_STATION_88.cmd` (installation V6 vérifiée selon le journal). Choisir la branche par **son nom**. Les 10 postes sont globaux et partagés.
2. **Découvrir les articles** si les candidats manquent; budget affiché 20 000 : graphe compact Skope + recherche par titres + liens V28 + relations UNESCO. Vérifier `candidate_routes` et les journaux; 20 000 n'est pas un nombre d'articles.
3. **Préparer la prochaine vague** : jusqu'à 10 postes, aujourd'hui 300 paires candidat/concept par sélection et enrichissement souple environ 45 000 mots par pack (un article au-delà peut être seul, sous 45 Mio).
4. Pour chaque `SEL_...`, **Copier + ZIP** puis une conversation ChatGPT; le prompt doit produire un CSV/ZIP avec SELECT/REJECT/HOLD pour **chaque candidate_id**. Utiliser le transfert groupé pour plusieurs petits packs de sélection, sans fusion des identifiants.
5. Déposer les retours ZIP (plusieurs en un seul glisser-déposer). La station importe, enregistre les décisions, prépare les `ENR_...` et remplit les postes.
6. Pour chaque `ENR_...`, transférer le ZIP avec les **textes originaux** et consignes. ChatGPT produit des faits en français et citations exactes, plus une couverture par article, avec `incomplete` si nécessaire.
7. Déposer les ZIP d'enrichissement. Le validateur conserve les lignes valides, archive les retours et identifie les refus, les PARTIAL et les corrections. **Ne jamais réimporter aveuglément un retour déjà accepté**.
8. Quand des postes se libèrent, traiter les nouvelles sélections, ou **Compléter les articles PARTIAL** sur demande; cela ne garantit pas de nouvelles connaissances à chaque reprise.
9. Quand la découverte de la fenêtre est saturée, consigner son bilan puis **changer de branche**, sans déclarer la branche scientifiquement achevée.

## 2. Ce que l'opérateur ne devrait plus avoir à faire (cible)

- Répéter manuellement découverte puis préparation à chaque paquet.
- Séparer mentalement QID, candidat, article, concept, preuve et Kristal : la station doit les expliquer par des labels.
- Copier dix ZIP individuellement si une enveloppe de transfert peut les regrouper.
- Chercher des erreurs d'import cachées dans une longue console : elles doivent être présentées avec un chemin de réparation ciblé.
- Relancer à l'aveugle 254 PARTIAL sans savoir combien de nouveautés la dernière reprise a apportées.
- Choisir une taille fixe de 60 articles sans connaître leur volume de texte.

## 3. Workflow cible à fort débit (à implémenter par couches)

```text
UNESCO — concepts et mappings candidats
            |
    [PLAN DE CAMPAGNE V32]
            |
     Fenêtre de découverte
            |-- Wikidata compact/Skope (RO) : QID/voisins/aliases, sans preuve originale
            |-- Wikipédia titres/pages/QID (RO)
            |-- liens et catégories V28 (sur vrais index)
            |-- relations thésaurus UNESCO
            v
  Inventaire de candidats versionné (association branche+concept+page)
            |
     Préparation déterministe
            |-- Source article/révision/hash/sections (source exacte)
            |-- données Wikidata structurées originales (si extraction qualifiée)
            v
        ChatGPT PASS 1 (qualifier la pertinence conceptuelle)
            |              ^
            v              |
  décisions+preuves     HOLD/ambiguïtés
            |
  Réutilisation de source déjà traitée ? --Oui--> complément de concept si nécessaire
            |
            Non
            v
        ChatGPT PASS 2 (extraire les faits nouveaux, citations par assertion)
            |
    Vérification déterministe+retour partiel
            |-- ACCEPTÉ -> propositions privées EncyK / occurrences
            |-- INVALIDES -> file réparation ciblée
            |-- PARTIAL -> file complément bornée
            v
     Mémoire documentaire réutilisable + statistiques de rendement
            |
      Nouveaux liens pertinents -> prochaine FENÊTRE de découverte
            |
   LATER : lots d'admission Authoring Kit -> Kristals indépendants
```

## 4. Quand s'arrêter, sans chercher une « perfection » infinie

Une fenêtre s'arrête si : son budget cumulé de lecture est atteint, son plafond de nouveaux candidats est atteint, plusieurs tours consécutifs n'avancent plus les curseurs, les dix postes sont pleins et la réserve de candidats est suffisante, ou la source critique est momentanément indisponible. Le résultat est **FIN_DE_FENÊTRE**, pas **BRANCHE_COMPLÈTE**.

Une campagne de compléments PARTIAL s'arrête si : deux tentatives n'apportent plus de faits nouveaux significatifs, un même profil a déjà couvert les sections ciblées, le texte a changé, ou un opérateur veut d'abord élargir le corpus. Les faits accumulés sont toujours conservés.

## 5. Météorologie — exemple de chronologie observée

- 34 concepts UNESCO, 34 QID candidats uniques; lancement initial 27 pages.
- Problème de `property_id` corrigé : 631 candidats; après V6 2 460.
- Lot initial 27 SELECT puis 759 propositions privées.
- Campagnes suivantes 575 SELECT / 56 REJECT, 10 606 propositions privées, 320 `ENRICHED`, 253–254 PARTIAL (selon l'instant).
- Nouvelle découverte : 1 830 paires en 7 ZIP `SEL_000008` à `SEL_000014`.
- Conclusion : le système peut accroître rapidement la quantité, **mais le nombre de candidats n'est pas celui des articles distincts**, et 506 erreurs ont été recensées sur trois retours. La réparation des pertes doit accompagner l'accélération.

## 6. Les statuts indispensables pour l'opérateur

| Affichage | Signification réelle |
|---|---|
| `PENDING` | Association trouvée, non encore sélectionnée |
| `SELECTED` | Décision favorable, extraction potentielle à préparer |
| `QUEUED_*` | Mission préparée/réservée, **ne pas recréer** |
| `ENRICHED`/`REUSED` | Traitée ou réutilisée selon des règles de source/profil |
| `PARTIAL` | Faits valides conservés, couverture complémentaire possible |
| `SOURCE_BLOCKED`/`OVERSIZE` | Acquisition impossible ou taille hors limites, nécessite stratégie adaptée |
| `NO_FACTS_REVIEW` | Aucun fait exploitable malgré passage; pas preuve de vacuité de l'article |
| `DONE`/`PARTIAL` (mission) | Retour importé; `PARTIAL` ne veut pas dire zéro fait sauvegardé |

## 7. Actions interdites par défaut

- Lancer les anciens producteurs V27/V28/V30 directement sur leurs **SQLite archivées**.
- Supprimer des `-wal`, relancer un reset de branche, réindexer 134 Go sans plan.
- Transformer une relation Wikidata agrégée en une preuve individuelle.
- Déclarer un contenu ChatGPT canonique ou remplacer un îlot Kristal sans Kit.
- Écraser les ZIP `SEL/ENR` d'une mission ouverte; modifier leur contenu après son attribution.
