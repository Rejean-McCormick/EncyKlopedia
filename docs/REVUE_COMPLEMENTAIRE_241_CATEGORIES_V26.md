# Sélection UNESCO ↔ catégories Wikipédia v26 — complément après inventaire complet

## Nature de l'overlay

**À décompresser à la racine `C:\mycode\EncyKlopedia\EncyKlopedia`**. Fichiers de données et documentation uniquement, **aucun installateur**, aucune modification du moteur, de la base SQL Wikipédia ou du Kristal.

Ce ZIP remplace le registre de décisions v26 existant par une **version consolidée**, qui conserve mot pour mot les 213 décisions de la première revue et y ajoute la revue du fichier `RESULTATS_REQUETES_V26_a0fe7a1f3c77_11888463.zip`. Il ne recrée pas l'inventaire local.

### Résultat de l'analyse

- Inventaire local déclaré terminé : **11 888 463 entrées parcourues, 9 241 036 catégories uniques**.
- Requête ciblée : **241 catégories distinctes**, dont **32** déjà présentes dans la première sélection (sur d'autres concepts ou avec les mêmes correspondances).
- Décisions initiales : **213**, dont **12 ponts INCLUDE** conservés.
- Décisions nouvelles : **210**, dont **16 ponts INCLUDE** supplémentaires.
- Registre consolidé : **423 couples (concept UNESCO, catégorie Wikipédia)** et **28 ponts INCLUDE** au total.
- Le tableau `docs/REVUE_COMPLEMENTAIRE_241_CATEGORIES_V26.csv` justifie la décision concernant chacune des 241 catégories retournées ; il contient les exemples et les motifs.
- La profondeur des 28 ponts est **0** : seuls les membres directs sont proposés, et non les sous-arbres entiers.

Ces nombres comptent des **ponts de classement**, pas des articles validés. Les échantillons fournis comptent au maximum 14 membres, pas le nombre total d'articles d'une catégorie.

### Ponts supplémentaires retenus

- `concept10` : **Education rights**
- `concept1137` : **School segregation in the United States**
- `concept1487` : **After school programs**
- `concept17163` : **Language teacher training**, **Mathematics teacher training programs in the United States**, **Teacher education in India**, **Teacher training**, **Teacher training programs**
- `concept2107` : **Alternative education**
- `concept2112` : **Experimental schools**
- `concept3894` : **Bilingual education**, **Bilingual education in the United States**, **Intercultural bilingual education**
- `concept3898` : **Intercultural bilingual education**
- `concept5999` : **Compulsory education**
- `concept6020` : **Educational technology projects**, **Educational technology standards**
- `concept7282` : **Education reform**, **Education reform in California**, **Education reform in the United States**, **Mathematics education reform**
- `concept9343` : **Medium of instruction**
- `concept9344` : **Connecticut State Department of Education**, **State boards of education in the United States**, **State departments of education of the United States**, **State secondary education boards of India**, **State secondary education boards of Nigeria**
- `concept9345` : **Study abroad programs**

### Critères de sélection

- **INCLUDE** : catégorie spécifique, exemples cohérents, profondeur nulle ; la pertinence de chaque article reste à contrôler.
- **HOLD** : concept proche, mais la catégorie est vide dans l'échantillon, trop vaste ou centrée sur des organismes/établissements ; revue ultérieure.
- **EXCLUDE** : non pertinent pour **le concept UNESCO indiqué**, sans exclusion du futur catalogue mondial.
- Les associations entre descripteurs UNESCO sont **thématiques**, non des déclarations d'équivalence de sens.
- Les catégories de ministères par pays, d'éducation religieuse par pays et d'entreprises EdTech ne sont pas activées massivement : elles nécessitent une règle de familles et des concepts plus appropriés.

### Commandes

Depuis la racine du dépôt :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1" -DecisionsFile ".\tools\unesco_pilot\v26_data\DECISIONS_CATEGORIES_UNESCO_MT110_V26.json"
```

Résultat attendu : `V26_DECISIONS_PREPAREES` avec `included: 28` et `reviewed: 423`. Cela produit un **nouveau CSV de ponts** dans `D:\EncyKlopedia\30_working\inventaire_categories_wikipedia_v26`, **sans modifier le catalogue v25**.

Pour la prochaine recherche ciblée (facultatif, après examen des 28 ponts) :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\INVENTORIER_CATEGORIES_WIKIPEDIA_V26.ps1" -QueriesFile ".\tools\unesco_pilot\v26_data\REQUETES_CIBLEES_UNESCO_MT110_V26_PHASE3.json"
```

### Limitation du catalogue v25 à respecter

Le moteur v25 déjà utilisé a **enregistré une signature immuable de configuration** pour la branche `unesco.mt1.10`. Remplacer son CSV de ponts puis relancer v25 avec le même identifiant de branche provoque à juste titre un **refus de configuration**, et ne doit pas être contourné en supprimant la base globale. Ce ZIP produit les décisions validées ; il **n'annonce pas que les 28 ponts sont déjà actifs dans le catalogue v25**. Leur activation incrémentale nécessitera une action d'ajout explicite, avec provenance et idempotence, ou une version distincte de branche testée.

### Traçabilité

Source : export local `RESULTATS_REQUETES_V26_a0fe7a1f3c77_11888463.zip`, signé par l'empreinte `source_signature = 425489ba0d600f064ef797922295980c7ae6298d0bcd7ce2d0edb3d6d16fd2fb` ; référence UNESCO `unesco_sha256 = d767bf401f4053355a61aa05573d4882143cc63492d843eb113e0213560b338c`. Les 213 décisions antérieures ont été conservées sans changement. Aucune base Wikipédia ou source externe n'a été consultée pour inventer des catégories.
