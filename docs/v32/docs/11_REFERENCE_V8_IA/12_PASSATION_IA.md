# 12 — Dossier de passation à une nouvelle conversation ou une autre IA

## Message de démarrage recommandé

> Nous reprenons EncyKlopedia, encyclopédie privée massive à **88 branches UNESCO**. Le système exploite les sources UNESCO et P3916 candidates, le graphe Wikidata via Skope, les index/texte Wikipédia, les outils historiques V27–V31 et la station ChatGPT à dix postes. Les deux missions de base sont la **sélection des relations article/concept**, puis l'**enrichissement sourcé du contenu des articles**. Les connaissances entrent dans un **registre privé EncyK**, sans admission canonique dans les Kristals.
>
> Lis d'abord `AGENTS.md`, `docs/v32/docs/11_REFERENCE_V8_IA/00_INDEX.md`, puis les chapitres en rapport avec la tâche. La documentation V7 est dans `docs/v32/docs/10_SYSTEME_MASSIF_20261117`; le code V32.2 se trouve dans `encyk_v32/`. Une distribution V8 autonome a été créée séparément : **demande/inspecte son ZIP effectif avant d'affirmer qu'un module ou endpoint V8 existe sur ce poste**.
>
> Ne crée pas de nouveau canon, ne modifie pas Skope, Kristalizer, la Médiathèque ni les gros index D:. Ne confonds pas QID, article Wikipédia, concept UNESCO, proposition privée et îlot Kristal. Ne relance pas la production encyclopédique si la demande porte uniquement sur la documentation ou l'architecture. Fournis des changements testés, traçables, avec distinction entre code vérifié, données observées, plans et inconnues.

## Pièces à joindre selon la mission

- **Mettre à jour la documentation** : snapshot du dépôt, overlay appliqué ou proposé, et **distribution V8 exécutable** si elle est la référence de comportement.
- **Modifier l'ordonnanceur** : `station_v32_adaptateur.py`, `campagne_v8.py`, code source V8, tests, configuration effective, petits logs. Ne pas envoyer les gigaoctets d'index.
- **Traiter une sélection SEL** : **seul le ZIP de mission** et son `INSTRUCTIONS_CHATGPT.md` peuvent suffire; le traiter entièrement.
- **Traiter un ENR** : ZIP avec les Wikitext originaux, manifeste des révisions et contrat de retour. Ne pas le remplacer par une description orale.
- **Auditer un import** : journal avec job_id, SHA de retour, détails `import_errors`, pack source correspondant, version du validateur.
- **Qualifier le canon** : snapshot explicite des API Authoring Kit et des autorités d'îlots, en **copie de test**. Aucun passage direct par retour ChatGPT.

## Questions auxquelles une IA doit répondre sans inventer

1. Quelles sources étaient réellement fournies ou montées ?
2. Quelles fonctions a-t-elle examinées dans le code et quelle version ?
3. Est-ce une décision de conception, un résultat de test synthétique, ou une observation Windows ?
4. Quels identifiants/fichiers précis sont autorisés par le pack ?
5. Qu'est-ce qui reste privé vs admis ?
6. Quel test montre que les documents et outils livrés correspondent bien à l'installation ?

## Plan de rapport attendu

**Résumé du changement → Sources inspectées → Différences trouvées → Fichiers livrés → Tests → Limites/conflits non résolus → Marche à suivre.** Si le ZIP V8 manque, cela doit apparaître sous les limites, pas être passé sous silence.
