# EncyKlopedia V32.1 — plan opérationnel révisé

**Décision du 16 novembre 2026 · Document de cadrage, pas une implémentation.**

## 1. Le produit final

Un seul **EncyKlopedia.pyw**, un manager local cohérent et une seule file de tâches durable, orchestrant les sources UNESCO, Wikidata et Wikipédia déjà indexées, la boucle à dix conversations ChatGPT, un registre de propositions privées et la **lecture fédérée d'états Kristal existants**. Skope et Kristalizer sont des dépendances externes : on ne les modifie ni ne les copie.

**On ne fabrique pas un nouveau canon EncyK en parallèle de celui des îlots Kristal.** EncyK possède ses propositions, décisions et projections; chaque îlot possède ses assertions admises, dans ses états versionnés. Les propositions restent accessibles pour la recherche exploratoire, explicitement identifiées comme provisoires. Admission et publication externe sont deux décisions distinctes.

## 2. Les identités à respecter

- **Branche UNESCO** = navigation thématique versionnée ; **concept** = descripteur et relations SKOS.
- **Sujet** = entité (QID ou namespace local) ; **îlot Kristal** = unité d'auteur, de modèle, de gouvernance et de cycle de vie.
- **État** = version exacte d'un îlot ; **assertion** = énoncé contextualisé avec conditions, qualifications et provenance.

**Un QID ne donne pas obligatoirement un Kristal.** Un îlot peut concerner plusieurs sujets, un sujet plusieurs îlots, un îlot plusieurs branches. Le modèle doit garder ces cardinalités naturellement.

## 3. La construction massive reste une priorité

**Passe 0** : utiliser les alignements UNESCO P3916 candidats, les QID, les index relationnels Wikidata, puis `wiki_qid` pour retrouver les pages Wikipédia anglaises déjà indexées. Ajouter SKOS et recherches complémentaires uniquement pour les manques. Pas de relecture du dump XML entier par branche.

**Passe 1** : ChatGPT sélectionne largement les couples concept–sujet–article réellement pertinents (`SELECT/REJECT/HOLD`) avec leurs routes de provenance. Les liens de graphe seuls n'approuvent rien.

**Passe 2** : donner les articles complets aux agents, plus les faits Wikidata ciblés, pour produire **beaucoup de propositions distinctives, sourcées et contextualisées**, notamment chiffres, étapes, définitions, évolutions, mécanismes et controverses attribuées. Éviter la triple vérification automatique, les quotas de faits arbitraires et le remplissage factice des dix postes.

La sortie **n'est pas un état Kristal admis**. Une extraction générique peut être partagée entre branches; une interprétation de domaine peut être distincte si Education, Soil ou Accounting n'ont pas les mêmes conditions de vérité.

## 4. Admission qualifiée, sans freiner la production

Une proposition exacte et versionnée, un état attendu, une politique explicite et un auteur **réellement supporté par l'Authoring Kit** précèdent toute écriture d'îlot. Le manager coordonne la reprise : détection de conflit d'état, exclusivité par workspace, effet observé, reçu d'admission. Les interruptions entre SQLite EncyK et fichiers Kristal ne forment pas une transaction globale magique. Un reçu de retour ZIP n'est pas un reçu d'admission.

La politique peut autoriser des admissions automatiques bornées et documentées; conflit d'identité ou perte de contexte = escalade ciblée. Aucun clic humain systématique sur les assertions ordinaires. **La production de propositions ne dépend pas de la disponibilité de l'auteur.**

## 5. Le lecteur fédéré

Deux modes : **exploratoire** (propositions EncyK signalées comme telles + états Kristal disponibles) et **états admis/snapshots** (uniquement états enfants exacts épinglés par un parent). Les résumés produits par IA ne se re-citent pas comme sources indépendantes. Les omissions du contexte et les permissions doivent rester visibles. Kompiler est un outil de lecture à tester, pas une source indépendante de faits.

## 6. Programme de réalisation

| Lot | Livrable minimal | Condition de sortie |
|---|---|---|
| **A — Lire** | Un manager racine capable d'inventorier et consulter les îlots existants, sans les migrer | Education et Soil lisibles, troisième modèle reconnu avec limitations |
| **B — Produire** | Jointures indexées UNESCO/Wikidata/Wikipédia, deux passes IA, ZIPs, file et registre de propositions | Source acquise réutilisée, reprise sans duplication, retour partiel réparable |
| **C — Admettre** | Adaptateur Kit et politique, première admission réelle Education puis Soil | État attendu, verrou, reprise après interruption et reçu vérifiés |
| **D — Fédérer** | Snapshots épinglés et contexte compilé | Un ancien snapshot lit son ancien état malgré modification d'enfant |
| **E — Étendre** | Campagnes mesurées sur trois modèles puis 87 branches | Gain de connaissance, coût, pertinence et performances mesurés, sans 100 % de rappel obligatoire |

Le manager est construit **dès A/B**, pas après toutes les fonctions. L'archivage porte sur les vieux outils devenus inutiles, **pas sur les îlots et leurs états**. `unesco.mt1.10` peut rester un historique non migré.

## 7. Les éléments à vérifier, sans redemander de gigantesques dumps

**Directement établis dans les snapshots EncyK** : 88 branches préparées, 4 500 concepts, 4 289 QID P3916 candidats uniques, 134 ambigus, 77 non mappés, présence des index `wiki_qid` et Wikidata/Skope, moteur ZIP à dix lanes et reprise. La jointure réelle des QID vers les pages sur D: est à mesurer.

**Rapportés dans la nouvelle note, mais non revérifiés dans cette livraison** : contrats exacts de Kristal Framework, Authoring Kit, Integration Pack, Arketype, Manager, Kompiler, KristalDiag, LOT-K50 et Kristal-Wikidata-Workflow. Leurs dépôts doivent être relus avant de programmer l'admission ou le lecteur fédéré. Arketype est une bibliothèque locale non normative, et les contrôles techniques d'îlots ne prouvent pas la vérité scientifique ni un alignement Wikidata.

Aucune migration du patrimoine en masse; aucun microservice, graphe spécialisé, nouveau système d'identité universel ou manifeste obligatoire à ce stade.

**Référence exhaustive :** `docs/09_FEDERATION_KRISTAL/` dans le paquet V32.1, et `docs/08_REFERENCES/07_RAPPORT_DECISION_20261116.md` pour la note source intégrale.
