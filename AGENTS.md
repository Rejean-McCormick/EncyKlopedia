## Référence documentaire enrichie V8 / instructions aux IA (17 novembre 2026)

**À lire en priorité pour toute nouvelle conversation :** [référence enrichie EncyK V8 et IA](docs/v32/docs/11_REFERENCE_V8_IA/00_INDEX.md), puis [règles locales aux agents](docs/v32/docs/11_REFERENCE_V8_IA/AGENTS.md) et [passation à une nouvelle IA](docs/v32/docs/11_REFERENCE_V8_IA/12_PASSATION_IA.md).

Ce dépôt snapshot contient le **noyau V32.2 et les docs V7**, alors que la **distribution autonome V8** a été livrée séparément. Ne pas annoncer que le code V8 se trouve ici sans vérifier son ZIP. Le reste de cette page reste valable pour les contraintes V32.2 et l'historique. Les 88 branches UNESCO sont le périmètre visé ; l'expression « 87 restantes » dans des documents historiques ne doit pas être reprise comme état d'un registre V8 neuf. **Aucune tâche documentaire ne lance de production ni ne modifie le canon.**

---

# Instructions aux agents IA — EncyKlopedia V32.2

Commencer par `MISE_A_JOUR_V32_2.md`, puis `README.md`, `docs/v32/PLAN_V321.md`, `docs/v32/docs/00_INDEX.md` et `docs/v32/IMPLEMENTATION_ET_LIMITES.md`.

**Décision V32.2 sur la cadence :** [cumul privé puis promotion différée vers les Kristals UNESCO préparés](docs/v32/docs/09_FEDERATION_KRISTAL/09_CUMUL_PRIVE_PROMOTION_DIFFEREE.md). La boucle des packs ne doit pas déclencher d’écriture Kristal; l’intégration est une phase secondaire par vague ou campagne mûre.

1. Ne pas remplacer le Framework Kristal par un canon EncyK indépendant. EncyK possède le registre privé des propositions, les tâches et les décisions de sélection; chaque îlot détient ses états admis.
2. Ne pas créer un Kristal par QID de manière automatique; conserver sujet / îlot / état / branche / assertion comme concepts distincts. Relations N:N.
3. Réutiliser les 88 espaces et mappings P3916 dans `ecosystem/UNESCO_Kristals`, les index locaux `wiki_qid` et `entity_edge`. Ne pas scanner les dumps entiers pour des recherches indexables.
4. **Ne pas modifier Skope ou Kristalizer**. Les utiliser uniquement comme dépendances externes par leurs surfaces publiées.
5. Priorité à la quantité de propositions distinctives **sourcées**, sans triple vérification rituelle, sans citation inventée et sans défaut de pertinence transformé en APPROVE. Aucun quota de complétude à 100 %.
6. Deux passes explicites : `SELECTION` (`SELECT/REJECT/HOLD`) puis `ENRICHMENT` (faits + citations exactes + couverture des articles). Ces décisions ne valent pas admission canonique.
7. La V32 doit rester rapide et reprenable : keyset cursors par branche, idempotence des ZIPs et propositions, aucune perte de candidats `DEFERRED` ou partiels.
8. Avant de programmer une écriture Framework : lire les signatures et contrats effectifs du Kit/Framework source, vérifier l'état attendu, garantir l'exclusivité, puis réaliser des tests de crash/reprise. Le code courant refuse toute admission.
9. Les données `ecosystem/UNESCO_Kristals` dans cette archive sont des références extraites, pas forcément des états canoniques de production. Ne pas modifier leur `canon/` dans ce dépôt.
10. Aucun manifeste de hash ou relecture intégrale de 125 Go obligatoire au début de chaque tâche; seuls identités, versions et citations utiles sont préservés aux frontières.

Suivre le plan A→E, reconnaître honnêtement les blocs réellement qualifiés et ne jamais affirmer qu'un test synthétique valide les bases Windows vivantes.

Pour le noyau V32.2, préserver les retours bruts, les contextes et les réservations. Toute correction doit être couverte par les tests `tests_v32`. La migration sauvegardée et les verrous locaux sont obligatoires. Ne pas réactiver l’admission Kit sans qualification.

## Interface fédérée diK V5.9 — règle additive candidate

Ne jamais traiter `dik.federated-semantic-registry/0.1-candidate` comme une source d’autorité canonique ou une permission de publier. Toute identité locale exige `namespace_id+KQ/KP`; un Q/P Wikidata n’est qu’un alignement externe revu. Le précontrôle vérifie uniquement l’intégrité. Consulter `docs/v32/docs/13_DIK_INTEROP/00_REGISTRE_FEDERE_V59.md`. Les contraintes propriétaire existantes prévalent.
