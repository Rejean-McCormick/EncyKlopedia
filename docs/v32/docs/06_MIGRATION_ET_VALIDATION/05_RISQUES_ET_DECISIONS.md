# Registre de risques et décisions de conception

**ARBITRAGE V32.1 PRIORITAIRE :** les lignes historiques qui suggèrent « un Kristal par QID » ou « stock privé EncyK de faits = canon » sont désormais remplacées par [le modèle sujet/îlot/état](../09_FEDERATION_KRISTAL/01_MODELE_IDENTITES_ET_GRANULARITE.md) et les [autorités fédérées](../09_FEDERATION_KRISTAL/02_AUTORITES_FEDERATION_ET_LECTURE.md).


| Risque | Gravité | Réponse proportionnée |
|---|---|---|
| Supposer que « 4 289 QID » signifie « 4 289 articles anglais » | Haute pour dimensionnement | Mesure locale `wiki_qid` avant promesse de débit |
| Confondre espaces UNESCO (88) et Kristals sujets | Haute | Modèle sujet séparé des scopes et des claims |
| Copie/fork de Skope ou Kristalizer | Interdit | Adapter aux interfaces externes, sans modification |
| P279 produit des millions de voisins non pertinents | Haute pour temps d'IA | Propriétés ciblées, budget/path et classement, sans exclusion définitive |
| Boucles N × 4 500 concepts | Haute pour performances | QID, index inversés et pré-calcul, puis fallback |
| Réextraction d'un article par branche | Haute pour coût | Upsert unique par `(subject_id,page_id,revision)`; relations N:N |
| « Fait Wikidata = vérité canonique » | Haute sémantiquement | Proposition EncyK sourcée; état Kristal seulement par admission qualifiée |
| « Sélection ChatGPT = admission officielle » | Haute | Verdict provisoire; aucun flux de publication implicite |
| Réponse ChatGPT trop superficielle | Haute pour débit | Pack avec suffisamment de contenu, consigne de traiter tous les items et couverture détaillée |
| Réponse ChatGPT extrêmement longue mais incohérente | Moyenne | Contrôle des identités et citations; signaler items incertains |
| Triple vérification ralentissante | Haute opérationnellement | Ne pas ajouter de double/triple revue automatique systématique |
| Refus entier d'un ZIP pour item mineur | Haute | Import partiel/réparation ciblée quand transaction le permet |
| Absence des bases sources sur une machine | Moyenne | Mode diagnostics/consultation et message clair, pas crash au lancement |
| Dix lanes concurrencent l'I/O du XML | Moyenne | Petits pools par ressource et préchargement limité |
| Archiver une dépendance encore partagée | Haute | Matrice d'usage, archive après adoption, Skope/Kristalizer exclus |
| Perdre historiques/retours V31 | Moyenne | Archive en lecture seule, nouvelle base V32 à côté |
| Docs vieillissent après le refactor | Haute | Mettre à jour la page de propriétaire, les statuts `OBSERVÉ/CIBLE` et le registre de migration dans la PR correspondante, sans manifeste lourd |

## Arbitrages actés par l'utilisateur

- **Volume et couverture très large plutôt que perfection documentaire immédiate.** Une finition par agent IA est prévue ultérieurement; ne pas transformer l'exhaustivité en barrière.
- **Réutilisation de l'écosystème**, méga-repo unifié, root `.pyw` et un manager central, plutôt que maintenir de nombreux outils autonomes.
- **Skope et Kristalizer externes et intouchés**; index lourds à conserver.
- **Deux passes IA**, sélection puis enrichissement substantiel; travailler directement à partir des articles Wikipédia et des données Wikidata.
- **Pas de surcouche de gouvernance administrative obligatoire** pendant les déplacements de code (hash/manifests/approbations cérémonielles).

## Arbitrages proposés [CIBLE, à tester]

- Monolithe modulaire Python avec SQLite et GUI Windows, adapters pour les dépendances externes.
- Un sujet Wikidata/QID peut appartenir à plusieurs îlots et branches; **pas de création de Kristal par QID comme règle générale**.
- Pack en ZIP et retour local comme protocole utilisateur premier; les extensions automatiques viendront plus tard.
- Sémantique des décisions `select/reject/hold` et claims privés séparée de toute canonisation.
- Mesure de qualité **pragmatique** sur une poignée de lots de référence, pas promesse d'un taux unique de rappel.
