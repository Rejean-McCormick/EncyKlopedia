# Fédération Kristal et autorités par catégorie de données

## Pas de « source unique de vérité » universelle

| Type d'information | Autorité cible | Rôle d'EncyK |
|---|---|---|
| Corpus Wikipédia/Wikidata acquis | Source versionnée et entrepôt d'acquisition | Lire, référencer, éventuellement cacher à l'identique |
| Concepts, relations SKOS et versions | Snapshot UNESCO approprié | Indexer, classer, préparer des parcours |
| Alignements candidats | Crosswalk identifié et versionné | Qualifier, conserver la provenance, ne pas certifier par proximité |
| Proposition extraite | **Registre de propositions EncyK** | Stockage durable et consultable avec statut provisoire |
| Décision de sélection | Registre de décision EncyK | Historique de revue par couple/portée |
| Décision d'admission | Reçu de politique et opération d'auteur | Tracer et réconcilier |
| Contenu **admis** d'un îlot | **État Kristal propriétaire** | Index dérivé, jamais écriture indépendante du « même fait canonique » |
| Composition d'états Kristal | État parent avec enfants épinglés | Résoudre et afficher les snapshots de fédération |
| Positions de workspace | Inventaire/Manager respectant son contrat | Résolution/configuration, pas nouvel allocateur mondial |
| Progression, quotas, coût | Registre opérationnel EncyK | Pilotage et diagnostics |
| Recettes Arketype | Bibliothèque versionnée **non normative** | Conseil de conception, puis profil explicitement adopté |

## Les deux parcours de consultation

**Exploratoire (rapide)** : inclure les propositions provisoires EncyK et les états Kristal lisibles, mais exposer clairement `proposition` vs `admis`, version, provenance et limites. On peut obtenir tôt une encyclopédie vaste et utile sans déclaration de canonisation.

**Admis / état épinglé (reproductible)** : afficher uniquement les états Kristal inclus dans le périmètre résolu; pour un snapshot parent, épingler la référence exacte des enfants. Si un enfant évolue, un ancien snapshot continue de référer l'ancien état. Un îlot manquant est signalé, jamais remplacé silencieusement par un autre.

Aucune synthèse IA générée par la vue ne revient comme nouvelle source indépendante : conserver sa lignée et empêcher les cycles d'auto-citation.

## Projections et caches

Les index de lecture d'EncyK sont des **dérivés**. Ils peuvent être reconstruits. Leur clé de cache doit tenir compte des états sources réellement consultés, du profil/compilateur, des paramètres, de la langue et du périmètre d'accès. Une modification de droits peut invalider un cache sans modification des faits.

La composition parent–enfants ne copie pas le canon enfant. **Le rapport fourni attribue ce contrat au Framework**; sa sémantique exacte et les commandes correspondantes sont à revalider dans le dépôt Framework avant de coder.

## Bords de sécurité

- Les états d'autres îlots sont lus avec les permissions et conditions propres à leurs propriétaires.
- Les propositions ne sont pas « promues » par simple inclusion dans une réponse.
- Une admission interne n'autorise pas automatiquement la **publication externe**.
- Une réponse indique les omissions liées au budget de contexte, sans prétendre que ces connaissances n'existent pas.
