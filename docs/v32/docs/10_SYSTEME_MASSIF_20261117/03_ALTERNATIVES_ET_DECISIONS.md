# 03 — Alternatives évaluées AVANT le choix de système

## Critères

1. Rendement : nouveaux faits **exacts et sourcés** par transfert ChatGPT, pas simple compte brut de lignes.
2. Couverture : articles uniques, diversité des concepts, branches UNESCO sous-représentées.
3. Exploitabilité : citations vérifiables, QID/page/révision et contexte de source reconstituables.
4. Robustesse : pas de perte de ZIP/transactions en cas d'interruption, reprise idempotente.
5. Coût : limites de lecture de centaines de Go, volumes de texte par mission, temps humain.
6. Non-interférence : ni Skope ni Kristalizer ni Médiathèque C: ni Kristals modifiés.

## Options comparées

| Option | Avantages | Défauts observables | Décision |
|---|---|---|---|
| **A. Découvrir absolument tout, figer définitivement, traiter** | Planification simple; lots stables | « Tout » impossible à prouver pour un graphe ouvert, sources évolutives; liens des articles sélectionnés peuvent créer de nouveaux sujets; très longue latence initiale | **Rejetée comme règle générale** |
| **B. Continuer l'enchaînement manuel `Découvrir` → `Préparer`** | Fonctionne déjà; contrôlable | Cliquer souvent; plans opacité; saturation de quelques concepts; erreurs/partiels sans reprise priorisée | **État V6, à dépasser** |
| **C. Boucle automatique illimitée, tout importer et recommencer** | Peu de clics | Risque de parcours sans fin, textes gigantesques, relectures/doublons, ressources D: saturées | **Rejetée** |
| **D. Orchestrateur unique réécrivant Skope, Méd., Kristalizer et EncyK** | Contrôle apparent | Détruit les frontières d'autorité, reproduit des moteurs, migrations risquées | **Rejetée** |
| **E. Ordonnanceur de campagnes évolutives + lots source figés + mémoire documentaire commune** | Pipeline continu, budget borné, provenance, réemploi, reprise, rendement mesurable | Exige quelques interfaces additionnelles V32 et tests sur D: | **Choisie comme CIBLE** |

## Architecture choisie : « campagnes à fenêtres »

- **Découverte ouverte dans le temps** : une campagne peut être prolongée par des fenêtres successives; jamais prétention d'exhaustivité absolue.
- **Inventaire de travail figé par fenêtre/lot** : chaque `candidate_id`+concept+page+révision+routes a un état daté; les ZIP individuels restent immuables.
- **Deux niveaux de mémoire** : (1) relation éditoriale branche/concept/article ; (2) document/page/révision/propositions sourcées, réutilisables quand le profil/association le justifie.
- **Ordonnancement sous pression** : ne découvrir davantage que quand la file utile baisse; avoir une réserve de candidats suffisante pour alimenter 10 postes, sans figer l'univers.
- **Missions dimensionnées par volume effectif** : sélection peut être large (actuellement 300); enrichissement adaptatif aux mots, et article XXL plus tard découpé par sections (NON IMPLÉMENTÉ dans V6).
- **Voies différenciées** : routes Wikidata compact, titres/alias Wikipédia, liens Wikipédia V28, ontologie UNESCO; extractions lossless Wikidata plus tard et seulement avec conditions prouvées.
- **Récupération sélective** : faits invalides réparables (sans falsification), PARTIAL reprenables en nombre borné; pas de relecture infinie.

## Ce qui doit rester inchangé

- Station **dix postes** avec `Copier + ZIP`, importation par glisser-déposer, 88 noms français.
- Registre V32/2 et tables déjà qualifiées; pas de migration préventive de 10 606 propositions.
- Code historique V27/V28 accessible en tant que **bibliothèque de fonctions**, données V31 arquivées isolées.
- Texte original Wikipédia dans le ZIP ENR, révision et hash exacts; ne jamais demander à l'IA d'inventer une citation.
- Frontière privée → canon : aucune admission dans les îlots par simple import ChatGPT.

## Politique de deux passes : ni dogme, ni suppression prématurée

Le premier lot de 631 candidats a donné 575 SELECT / 56 REJECT, soit ~91 % de SELECT. Cela **suggère** qu'un chemin de sélection plus rapide pour certains candidats très fiables mérite une expérimentation; cela **ne prouve pas** que toute sélection est superflue. Le gain théorique doit être confronté au taux de mauvais appariements conceptuels et à la qualité des enrichissements. En absence de mesure, conserver les deux passes.

## Priorité d'implémentation

**P0** : observabilité, inventaire, refus explicites, métriques et anomalies.  
**P1** : ordonnanceur progressif borné, sans interférence avec les 10 postes, enregistrant époque et décision.  
**P2** : traitement ciblé des erreurs d'import, reprise PARTIAL avec seuil de gain, découpage par section.  
**P3** : cache documentaire interbranches avec vérification des concepts, extraction lossless ciblée Wikidata, profils adaptatifs.  
**P4** : campagnes d'intégration canonique, uniquement quand le Kit et les îlots exacts sont qualifiés.

**Cette livraison réalise P0 et un sous-ensemble de P1 :** documentation, observateur RO et commande opt-in d'une fenêtre bornée réutilisant les fonctions V6; **pas encore d'ordonnanceur permanent automatique ni P2–P4**.
