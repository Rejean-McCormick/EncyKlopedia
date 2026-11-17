# Admission éventuelle dans Kristal : auteur qualifié et reprise

**Statut [CIBLE / CONTRATS À CONFIRMER].** Le rapport du 16 novembre attribue à l'Authoring Kit v11 un journal récupérable et au Framework des exigences d'état/identité. Ce dépôt n'est pas dans les archives EncyK ouvertes pour cette mise à jour : **ne pas inventer d'API `generic_import()` ni promettre une transaction multi-fichiers atomique**.

## Préconditions minimales à l'admission, sans bureaucratie de masse

**Cadence V32.2 :** l’admission est une **phase de sortie différée**, par lots de propositions EncyK mûres, et non une transaction au fil de chaque import ZIP. Voir la [décision complète](09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md). L’intégration dans les états UNESCO préparés ne se fait que si le workspace est réellement un propriétaire approprié et si son chemin d’auteur est supporté.

Il existe une proposition exacte (ID/version), un îlot cible reconnu avec ses capacités, un profil adopté, une politique applicable, une source révisable, un **état précédent attendu**, et un écrivain supporté. Une politique bornée peut admettre automatiquement les assertions ordinaires conformes; les conflits d'identité, changement de périmètre, perte de qualification ou droits incertains sont mis en attente pour décision ciblée.

**Note de terminologie :** « admis dans un état privé Kristal » n'implique ni vérité absolue, ni publication externe, ni admission dans un canon EncyK séparé.

## Séquence de traitement

1. Conserver immuablement la proposition et sa décision de politique.
2. Prendre l'exclusivité **par workspace**, compatible avec les écrivains déjà présents.
3. Relire l'état exact de l'îlot et comparer à `expected_state`.
4. Préparer l'opération **dans un chemin d'auteur réellement supporté par le Kit**.
5. Appliquer; obtenir/récupérer l'identité de l'opération et le nouvel état observé.
6. Enregistrer un **reçu d'admission** reliant proposition, politique, ancien état, artefacts et état résultant.
7. Relâcher le verrou puis rafraîchir les vues dérivées.

## Reprise après interruption

| Point d'arrêt | Traitement |
|---|---|
| Avant écriture | Reprendre depuis proposition et décision enregistrées |
| Après artefact, avant index | Récupération Kit, sans seconde écriture |
| Après index, avant reçu EncyK | Réconcilier l'effet observé et compléter le reçu |
| État modifié concurremment | Conflit ; ne jamais appliquer aveuglément |
| Reçu présent, vue manquante | Réparer la projection, ne pas rejouer l'admission |

**Aucune transaction globale magique** entre SQLite EncyK et les fichiers Kristal. Le verrou v11 du Kit, d'après le rapport, n'est pas partagé par l'ancien `register-artifact`; l'adaptateur doit coordonner ou exclure ces écritures. Ne pas activer des écritures concurrentes tant que cette propriété n'est pas démontrée.

## Règles d'idempotence

Le `job_id` ne suffit pas : la reprise doit reconnaître l'**effet** produit, y compris si la réponse ou la commande précédente a abouti sans que le manager reçoive le reçu. L'idempotence concerne l'état final; elle n'interdit pas qu'un appel externe ait été effectué plusieurs fois à cause d'une interruption.

## Frontières de phase

**Lot A** peut lire sans Kit écrivain. **Lot B** produit des propositions utiles sans admission. **Lot C** démontre une **seule** opération d'auteur end-to-end sur Education, puis Soil. La campagne massive ne doit pas attendre une migration des centaines d'îlots anciens, mais l'écriture ne doit pas être simulée si son chemin exact est absent.
