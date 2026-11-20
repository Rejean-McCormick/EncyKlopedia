# EncyKlopedia — Chaîne massive, inventaire et contrat de travail

**Statut :** documentation nouvelle fondée sur snapshots locaux et journaux de production jusqu'au **17 novembre 2026**. **Source V32.2** + **station V6 appliquée localement selon les journaux**. Les chemins D: n'ont pas été ouverts directement lors de cette étude : leur taille/existence courantes restent à confirmer sur Windows par l'observateur et les outils natifs.

## Navigation

| Document | Question à laquelle il répond |
|---|---|
| [01_INVENTAIRE_DONNEES](01_INVENTAIRE_DONNEES.md) | Quelles données possédons-nous réellement ? Qui les détient ? |
| [02_INVENTAIRE_PROGRAMMES](02_INVENTAIRE_PROGRAMMES.md) | Quels programmes réutiliser et quelles responsabilités ? |
| [03_ALTERNATIVES_ET_DECISIONS](03_ALTERNATIVES_ET_DECISIONS.md) | Pourquoi cette architecture plutôt qu'une découverte figée ou une boucle infinie ? |
| [04_WORKFLOW_OPERATOR](04_WORKFLOW_OPERATOR.md) | Que fait l'opérateur, de la nouvelle branche au cumul privé ? |
| [05_ARCHITECTURE_TECHNIQUE](05_ARCHITECTURE_TECHNIQUE.md) | Quels modules, tables, API et états ? |
| [06_CONTROLES_DONNEES_ET_PROMPTS](06_CONTROLES_DONNEES_ET_PROMPTS.md) | Comment obtenir beaucoup de faits sourcés sans inventer de preuves ? |
| [07_PROCHAINES_OPTIMISATIONS](07_PROCHAINES_OPTIMISATIONS.md) | Qu'améliorer, dans quel ordre, et comment qualifier ? |
| [08_RISQUES_ET_FRONTIERES](08_RISQUES_ET_FRONTIERES.md) | Ce qui ne doit jamais être touché et les erreurs à éviter |
| [09_RECETTES_ET_DIAGNOSTICS](09_RECETTES_ET_DIAGNOSTICS.md) | Commandes concrètes, diagnostic, incidents et reprises |
| [10_PROVENANCE_DES_PREUVES](10_PROVENANCE_DES_PREUVES.md) | Observé, rapporté, démontré, hypothèse : ne pas confondre |
| [11_CONTRATS_PACKS_ET_ETATS](11_CONTRATS_PACKS_ET_ETATS.md) | Consignes IA, ZIP, états, sources et identifiants |
| [12_PLAN_DES_CAMPAGNES](12_PLAN_DES_CAMPAGNES.md) | Contrats du futur ordonnanceur et politique de saturation |
| [13_MATRICE_DES_POSSIBILITES](13_MATRICE_DES_POSSIBILITES.md) | Quelles ressources méritent un raccordement; ordre, risques, conditions et preuves ? |
| [14_RECONCILIATION_DES_DOCUMENTS_EXISTANTS](14_RECONCILIATION_DES_DOCUMENTS_EXISTANTS.md) | Que faire des documents 87/V32.2/prototype devenus historiquement datés ? |
| [inventaires/](inventaires/) | Référentiel CSV de 5 901 fichiers et 889 scripts de quatre archives |

## Les cinq principes non négociables

1. **Cumul massif d'abord, admission canonique ensuite**, et seulement par lots mûrs, via un Authoring Kit autorisé.
2. **Skope/index Wikidata compact = découverte, pas preuve d'une déclaration Wikidata originale.** Une source Wikipédia exacte et une révision sont un autre niveau de preuve ; la véracité de l'affirmation reste à juger.
3. **Un candidat est une association branche–concept–article**, non une entité isolée ni un Kristal. Une révision Wikipédia n'est pas un QID ; **un QID n'est pas un Kristal**.
4. **Éviter le double travail** : une extraction documentaire d'une même révision peut être réutilisée lorsque le profil, les sujets et les concepts couverts le permettent; un PARTIAL réclame un complément ciblé, non un effacement.
5. **Borner les boucles, pas le potentiel** : découverte progressive et inventaires de lots figés, mais nouveaux lots autorisés; 10 postes ne sont que la capacité concurrente de transfert ChatGPT.

## Où se trouve la source de vérité aujourd'hui ?

- Données de production EncyK V32 : `etat_v32/encyk_v32.sqlite` **sur D:** (registre privé cumulatif).
- ZIP originaux et retours : `etat_v32/packs/` et `etat_v32/returns/`; préserver leurs SHA.
- Textes de référence : XML Wikipédia et index directs D:, consultés en lecture seule.
- Index découverte Wikidata : SQLite compact D:, lecture seule ; **Skope reste indépendant**.
- Kristals et état canonique : îlots autonomes sur C:; pas de mutation depuis EncyK.

## Lecture des états de maturité

**ACTUEL** = vérifié dans le code et confirmé au moins partiellement par les journaux Météorologie.  
**CODE PRESENT** = fonction présente dans snapshot, activité live non démontrée.  
**CIBLE** = choix d'architecture, non livré comme moteur dans ce paquet.  
**INCERTAIN** = accès au poste, performance/qualité réelles ou dépendances non vérifiés.

L'inventaire exhaustif *des fichiers présents dans les archives examinées* est dans les CSV. Il ne représente **pas un inventaire exhaustif des 134 Go Wikidata ni des 110 Go de XML** ni le volume actuel d'une source D:.
