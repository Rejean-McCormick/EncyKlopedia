# 06 — Campagnes V8 : politique, états et sûreté

## Intention de conception

La V8 vise **une commande de campagne**, au lieu d'une alternance permanente de clics `Découvrir`/`Préparer`. Elle doit réutiliser les quatre voies de découverte disponibles dans les adaptations V6 : graphe Skope, titres/alias, liens Wikipédia et relations du thésaurus. L'ordonnanceur réapprovisionne les dix postes à mesure que les retours sont importés, dans une **fenêtre bornée**.

**Statut de preuve :** comportement décrit pour la distribution V8 de la conversation antérieure. **Pas vérifié dans le ZIP principal du présent audit**. Les constantes, URLs et comportements exacts doivent être contrôlés sur le **code V8 installé**.

## Fenêtre, campagne, révision : trois objets distincts

- **Campagne de branche** : projet de production sur un espace UNESCO, avec préférences et budget.
- **Fenêtre de découverte** : nombre de tours, budget graphe, plafonds et reçu d'arrêt. Elle peut créer un inventaire candidat reproductible sans fermer l'univers des découvertes futures.
- **Mission `SEL`/`ENR`** : pack d'entrées figées et hashé destiné à une conversation ChatGPT.

Un reçu de fin de fenêtre **ne signifie jamais** « branche scientifiquement achevée ». Il signifie qu'on a atteint un budget, des limites, un manque de progression ou un arrêt utilisateur.

## Politique de limites documentée par la distribution antérieure

| Paramètre décrit | Valeur de travail | Ce qu'il limite |
|---|---:|---|
| Nombre de postes globaux | 10 | Missions concurrentes à transférer/importer |
| Budget de graphe par tour V8 | 20 000 par défaut | Voisins inspectés lors d'un appel, à vérifier dans code V8 |
| Tours par fenêtre V8 | 8 par défaut, 15 max | Recherche effectuée au cours d'une fenêtre |
| Plafond de paires PENDING | 20 000 par défaut | Réserve de candidats avant arrêt |
| Cycles automatiques de campagne | 20 décrits | Nombre de nouvelles fenêtres proposées après import |
| Pack SEL V6 | jusqu'à 300 associations | Examen de pertinence, pas 300 pages distinctes |
| Pack ENR | limite de mots souple (~45 000) | Volume documentaire, grands articles isolés |

Ces nombres sont **des politiques rapportées**, non des garanties de capacité scientifique ou de performance sur les 88 branches.

## États et transitions souhaités

```text
NON_ACTIVE → ACTIVE → FENETRE_EN_COURS → PACKS_PREPARES
                     ↘ PAUSE
PACKS_PREPARES → IMPORT_DES_RETOURS → LANE_LIBRE → NOUVELLE_FENETRE
                                     ↘ ÉCHECS_IMPORT → DIAGNOSTIC
ACTIVE → BUDGET_EPUISÉ / AUCUN_PROGRÈS / PLAFOND / PAUSE
```

**Pause** : empêche de nouveaux tours, sans supprimer packs déjà ouverts ni données accumulées. **Arrêt de fenêtre** : consigner le motif. **Changement de branche** : ne pas détourner les jobs des dix postes encore occupés.

## Règles anti-boucle et bonne gestion de ressources

- Le graphe Skope, les index Wikipédia et le dump XML restent en lecture seule.
- Les parcours sont à **curseurs** et bornés (limites par appel et par fenêtre); jamais un `COUNT(*)` global sur Wikidata pour diagnostiquer.
- Quand la réserve PENDING et les dix postes suffisent, éviter une nouvelle découverte coûteuse.
- Mesurer la progression **des curseurs** et **des candidats réellement nouveaux**. Un tour sans nouvelle page peut néanmoins progresser dans une relation utile.
- Ne pas ré-ouvrir un job `READY`/`SENT` ni altérer un ZIP immuable.
- Reprendre les PARTIAL avec nombre de tentatives limité et preuve de gain; ces contrôles avancés demeurent **une cible** si absents du code V8.
- Écrire un reçu explicite pour chaque fenêtre (date, branche, source_epoch, limites, tours, stop reason, statistiques).

## Ce qu'une IA ne doit pas inventer

Le nom d'un endpoint HTTP, une structure de table `campaign_windows`, une migration d'état V32 ou une commande `--apply` ne sont pas vrais simplement parce qu'ils figurent dans un document de conception. Pour agir sur V8 : lire **le vrai** `campagne_v8.py`, l'adaptateur de station et l'installateur; vérifier les tests et configurations locales.
