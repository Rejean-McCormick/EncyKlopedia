# Application sélective des deux codex joints

Cette documentation tient compte des deux archives fournies par l'utilisateur : **`senior-architecture-patterns.zip`** (patrons architecturaux) et **`guide-architecture-interfaces-ia-v2(1).zip`** (interfaces centrées sur les tâches). Les textes des codex ne sont pas copiés dans le méga-repo; leurs règles pertinentes sont traduites ici en décisions propres à EncyKlopedia.

## Patrons architecturaux retenus — le minimum utile

| Patron du codex | Pourquoi pour V32 | Limite assumée |
|---|---|---|
| **31 Modular Monolith** | Un seul manager local Windows, déploiement et transactions simples, modules métier distincts | Pas de microservices par dossier UNESCO |
| **10 Hexagonal Architecture** | App/UI indépendantes de SQL, Skope, XML, formats hérités | Ports simples en Python, pas une interface par méthode triviale |
| **08 Anti-Corruption Layer** | Transformer « espace UNESCO »/`wiki_qid`/Wikidata/Skope en identités V32 sans propager leurs schémas | Pas de couche d'adaptation là où les données sont déjà identiques |
| **15 Idempotency** | Dépôt répété de ZIP et reprise après arrêt : ne jamais doubler les claims | Contrainte SQL logique, pas manifeste mondial de SHA |
| **02 Bulkhead** | Limiter séparément XML, SQLite Wikidata, préchargement des ZIP | Peu de workers, pas une flotte d'orchestrateurs |
| **04 Graceful Degradation** | Continuer imports/lecture si graphe ou XML est indisponible | L'item sans source complète reste à réparer |
| **29 Metrics & Alerting** | Débit réel des sessions, erreurs de sources, files en attente | Quelques compteurs métiers, pas plateforme d'observabilité |
| **18 Cache-Aside (optionnel)** | Mémoriser QID→page et profils de candidats coûteux | Seulement si le coût des requêtes est mesuré |

## Patrons non retenus pour la première refonte

- **13 Event Sourcing** : on possède déjà un état durable SQL et des événements de diagnostic; le rejouer intégralement n'apporte pas de valeur immédiate.
- **14 Saga** et **16 Transactional Outbox** : à envisager seulement si une vraie opération transactionnelle traverse plusieurs systèmes mutables; ici les index externes sont lus et la majorité des écritures sont locales.
- **21 Pub-Sub**, service mesh, tracing distribué, cell architecture et data mesh : inappropriés à un manager de poste de travail piloté par une personne.
- **23 Blue/Green**, **24 Canary** : système local; préférer copies isolées, base V32 indépendante et migration progressive, plutôt que pipelines de déploiement sophistiqués.

Une architecture dite « senior » choisit les patrons qui retirent des problèmes réels; elle ne les additionne pas pour faire impression.

## Principes UX appliqués depuis `AI_INGESTION.md`

1. Définir le flux normal utilisateur **avant** de dessiner des onglets : sélectionner, préparer, transférer, importer, voir le résultat.
2. Les 3–6 actions habituelles vivent dans une seule vue de production. Un module technique n'obtient pas un onglet parce qu'il existe.
3. Auditer les actions des UIs V30, V313/V314 et audit avant de les fusionner; repérer les chemins concurrents.
4. Distinction entre réel `ready`, `sent`, `done`, `unknown` : aucune preuve locale n'autorise à déclarer qu'une conversation ChatGPT travaille ou a terminé.
5. Diagnostic, maintenance, édition des chemins et archives sont secondaires. Aucune suppression des capacités sous prétexte de simplification visuelle.
6. Pas de scan coûteux au démarrage ni « reprise » qui lance une deuxième préparation.

## Traduction directe en critères de revue de code

- Où est **l'unique source de vérité** des jobs, du stock candidat et des claims ?
- Quelle action précise de l'utilisateur déclenche l'opération coûteuse ?
- La même fonctionnalité existe-t-elle dans un ancien outil ? Si oui, quel adaptateur la réutilise ?
- Peut-on perdre la connexion à une source sans bloquer les imports prêts ?
- Si une conversation rend un ZIP incomplet, voit-on les éléments manquants ?
- Les prompts ont-ils donné assez de matière à traiter et produit un retour quantifiable ?
- Un même QID/une même page apparaît-il en plusieurs branches sans duplication d'enrichissement ?
- Quelle preuve démontre que le chantier n'a **pas touché** Skope/Kristalizer ?

Ce sont des tests de comportement, non un comité de gouvernance ni des formulaires pour chaque fichier.
