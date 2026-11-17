# EncyKlopedia — Guide opérationnel local (v30 + correctifs v31.x)

**Référence :** ENC-OPS-2026-11-15/1  
**Date :** 15 novembre 2026  
**Nature :** documentation du fonctionnement **constaté dans le code** et les rapports Windows ; pas une migration ni une qualification éditoriale.  
**Lire avec :** [index d'architecture](00_INDEX_ARCHITECTURE_V31.md), [données et sauvegarde](11_DONNEES_ET_SAUVEGARDE_LOCALE_V31.md), [diagnostic](12_DIAGNOSTIC_COUVERTURE_ET_GOULOTS_V31.md), [maintenance](13_CHECKLIST_MAINTENANCE_V31.md).

## 1. Deux périmètres à ne pas confondre

- **Application de lecture publique (Node.js / démo alpha)** : décrite dans le `README.md` historique et les portes de publication. Son statut alpha n'atteste aucune publication autorisée.
- **Station privée de production (Python + PowerShell + SQLite, UI « Production v30 »)** : pilote la découverte UNESCO v28, le catalogue v25, les packs et imports Kristal v27 et dix conversations ChatGPT. L'interface peut afficher « v30 » même si des correctifs de code `v31.x` sont appliqués.

Le dépôt est sous `C:\mycode\EncyKlopedia\EncyKlopedia`. Les données de la station se trouvent sous `D:\EncyKlopedia`. Le launcher de production est `LANCER_ENCYKLOPEDIA.cmd` (ne pas confondre avec le démarrage du lecteur de démonstration).

## 2. Sources d'autorité : qui a le droit de faire quoi ?

| Composant | Rôle et stockage durable | Frontière |
|---|---|---|
| Wikipédia, index SQL et offsets XML v21 | Pages, liens, catégories, révisions et textes intégraux | Sources **en lecture seule** durant production ; aucun rescannage XML massif pour diagnostiquer les lots |
| UNESCO / catalogue v25 | Branche et concepts, affectations concept–article après revue | Ne pas modifier par recherche de candidats ; plusieurs concepts peuvent référencer une page |
| Découverte v28 | Explore pages/liens/catégories et conserve des couples candidats et leur provenance | Une **piste** n'est pas une décision ; conserver les empreintes de révision |
| Station v30 | Tâches, postes, états, index des revues, décisions, preuves figées, historique | **Unique propriétaire des tâches distribuées et des `candidate_id`** |
| Kristal v27 | File de packs, visites des articles, faits privés et citations | Pas de canonisation, pas de publication automatique |
| ChatGPT dans les conversations | Examine chaque pack : `APPROVE`, `REJECT`, `HOLD` UNESCO ou faits sélectionnés Kristal | Les retours sont des **données**, jamais du code |

## 3. Cycle autorisé

1. La station synchronise le catalogue et prépare des packs Kristal v27 des articles catalogués **non encore empaquetés**. En mode synthèse approfondie v31.8 : `MaxArticles=120`, `TargetWords=400000`, `TargetBytes=62914560` dans le batch v30. Un article exceptionnel reste intégral, jamais tronqué pour tenir dans le pack.
2. **Uniquement si aucune revue UNESCO n'est ouverte**, elle exécute la découverte v28 (graines historiques, puis chemins additionnels selon les correctifs installés). Les candidats entrent dans le magasin de découverte.
3. Le poste indexe les couples, reconnaît les affectations et les revues déjà traitées, puis prépare des revues UNESCO de **4 000 propositions au maximum**. La quantité observée peut être plus petite : les 10 postes sont une **capacité**, pas un quota de packs.
4. L'opérateur envoie un ZIP immuable dans chaque conversation ChatGPT. Le ZIP contient ses textes ou preuves/identifiants/révisions figés ; ne jamais le « mettre à jour » après envoi.
5. Les retours sont importés par validation native. UNESCO : CSV à trois colonnes `candidate_id,decision,justification` ; les preuves reviennent **de la base immuable**, non du CSV. Kristal : delta JSON v27 conforme, citations source et bilan par article, avec refus si couverture requise absente.
6. Le dépôt du retour libère le poste ; la prochaine découverte reprend quand **toutes les revues UNESCO** sont closes. Le réexamen HOLD est **volontaire**, jamais un nettoyage de file automatique.

**Ne pas appuyer sur « Préparer toute la prochaine vague » dans l'espoir de débloquer la découverte quand des revues UNESCO sont ouvertes** : la protection du gel doit refuser la découverte. La production Kristal peut encore avancer si le catalogue contient de nouveaux articles.

## 4. Versions : fonction et statut connu

| Étiquette | Portée | État vérifié au 15-11-2026 |
|---|---|---|
| v25 / v26 | Catalogue UNESCO, inventaires de catégories et ponts | Présents dans le dépôt/snapshots ; opérations réelles observées dans les journaux |
| v27 / v31.8 | Kristal privé, import et couverture « synthèse approfondie » | Journal : 44 262 faits privés ; règles de couverture v31.8 actives |
| v28 / v31.7 | Découverte et revues UNESCO, lots jusqu'à 4 000 | Actifs dans la station |
| Station v30 / v31.9 | Pilotage, gel des preuves, rotation HOLD, diagnostics de file | Empreintes v31.9 vérifiées auparavant, puis moteur modifié par v31.10 |
| v31.10 | Découverte par préfixes indexés des titres/catégories et leurs membres | **Installation confirmée** par le rapport de goulets du 15-11, empreintes conformes |
| v31.11 **« rappel ontologique »** | Candidats issus de relations UNESCO documentées et d'articles affectés aux concepts voisins | **Overlay livré, installation Windows non confirmée** au moment de cette documentation |

**Important :** les autres documents nommés « V311 », « V3111 » ou « V312 » appartiennent à des sous-systèmes/anciennes conventions de numérotation. Toujours vérifier le **chemin du fichier et son SHA-256**, pas interpréter le seul numéro de version.

## 5. Découverte : trois chemins différents

- **Historique v28** : depuis les pages déjà affectées au catalogue, relire les preuves de liens, catégories et sous-catégories pertinentes, à révision suivie.
- **Additif v31.10** : depuis les libellés anglais et variantes **présents dans le référentiel** (pas de synonymes inventés), recherche B-tree des titres et catégories de Wikipédia puis des membres des catégories. Curseurs `v3110_probe_cursor` et `v3110_category_roots` persistants, plafond de **800 nouvelles paires par concept et par passage**, non un rejet définitif.
- **Additif v31.11, si installé** : réutilise comme pistes les pages affectées à des **concepts liés par le graphe UNESCO** (chemins documentés à 1 ou 2 relations). Curseur `v3111_relation_cursor` ; 800 nouvelles paires par concept et par passage ; les chemins sont des **signaux de rappel**, ni preuves que l'affectation est correcte, ni admissions automatiques.

**L'amélioration du rappel n'est pas démontrée par le simple nombre de packs.** Un concept peut conserver 0 proposition lorsque le parcours lexical est épuisé ; un concept source voisin peut fournir des candidats non pertinents. Dans les deux cas, ChatGPT doit faire l'examen documentaire.

## 6. Règles non négociables

- Pas d'admission canonique (`canonical_admissions=0`), pas de publication autorisée par une revue ou un delta.
- Préserver `candidate_id`, `page_id`, `revision`, `bundle_sha256`/SHA-256 de preuve, branche et concept ; ne jamais fabriquer de citation.
- Aucun écrasement de preuves existantes, aucune reconstruction d'un ZIP envoyé ; les lots déjà distribués survivent aux correctifs de code.
- Aucun `REJECT` local par simple faiblesse lexicale, aucun article retiré définitivement à cause d'un score ; différer si nécessaire et conserver la traçabilité.
- **HOLD reste provisoire** ; un réexamen explicite doit préserver les décisions précédentes et la rotation historique.
- Installer le **code** par « Mises à jour logicielles » (manifeste v30, SHA de précondition, confirmation et sauvegarde des fichiers), **jamais** dans « Déposer des ZIP corrigés ».
- Ne pas modifier les bases lors d'un audit. Une lecture de plusieurs SQLite n'est pas une photographie atomique ; pour une sauvegarde cohérente, fermer les producteurs avant copie SQLite contrôlée.

## 7. Où vérifier les faits avant un nouveau correctif

1. `docs/UNESCO_DECOUVERTE_ARTICLES_RELIES_V28.md` : détails du moteur v28 + addenda v31.10/v31.11 **si l'overlay correspondant est installé**.
2. `tools/unesco_pilot/decouvrir_articles_relies_v28.py` : implémentation effective des parcours et curseurs.
3. `tools/unesco_pilot/poste_chatgpt_v30.py` : orchestration, quotas, indexation, gel, imports et overlays.
4. `tools/unesco_pilot/production_kristals_v27.py` et `PRODUIRE_KRISTALS_V27.ps1` : sélection des articles, pack, delta et import.
5. Les **SQLite du poste Windows** et le diagnostic en lecture seule : statuts/données actuels ; un snapshot de code ne contient pas forcément ces bases.

Les détails d'une architecture cible `docs/architecture/01..09` ne prouvent pas qu'un module est réellement installé. Toujours opposer **cible**, **code**, **installation vérifiée**, **résultat mesuré**.
