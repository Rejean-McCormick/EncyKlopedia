# EncyKlopedia V32.2 — mise à jour du moteur privé

Livraison du 16 novembre 2026, issue du ZIP V32.1 fourni. Le noyau est corrigé et testé sur fixtures locales. Il ne constitue pas une qualification des index Windows réels ni de l’écriture Kristal.

## Changements effectifs

- Préparation d’enrichissement limitée à la branche demandée. Les campagnes toutes branches restent possibles sans filtre.
- Un ordonnanceur à la fois par base : verrou système local Windows/Linux, relâché par le système à la mort du processus. Contrainte de réservation active unique par candidat et transitions vérifiées. Les conversations ChatGPT restent parallèles.
- Pagination bornée de la file ; sources illisibles isolées en `SOURCE_BLOCKED` avec motif et délai. Une tête de file invalide ne masque plus les articles suivants. Articles hors budget isolés en `OVERSIZE`, sans troncature ou dépassement implicite du premier article.
- Nombre de postes configurable respecté, de 1 à 10. Connexions à l’index direct et au XML réutilisées pendant une préparation.
- Conservation du retour brut par empreinte dans le dossier de travail `returns/`, y compris les retours refusés après lecture. Les propositions conservent leurs payloads, qualificatifs, extensions, citations et occurrences.
- Déduplication exacte conservatrice incluant le texte et le contexte. Aucun rapprochement sémantique automatique entre formulations différentes.
- Types d’objets contrôlés. Faits invalides isolés dans `import_errors` ; les faits valides d’un lot mixte peuvent être conservés. Un lot entièrement invalide reste refusé et sa réservation reste active. `--strict` demande un import intégral valide avec couverture complète.
- Résultats sans fait distingués : `NO_FACTS_REVIEW` si le bilan est insuffisant ; `NO_RELEVANT_CLAIM` si l’absence de connaissance pertinente est explicitement motivée. Un lot entier vide ne devient plus un lot enrichi ordinaire.
- Une répétition exacte n’a pas de second effet. Un retour différent sur une tâche terminée produit `RETURN_CONFLICT`, pas un faux succès. Corrections explicites par `--correction` et `supersedes`, avec historique et invalidation du cache d’extraction concerné.
- Extraction réutilisée seulement si révision, empreinte, profil, sujet et concept sont couverts par un résultat explicitement `processed`. Un nouveau concept reçoit un `TARGETED_COMPLEMENT` avec les propositions antérieures en contexte. Aucun nouveau lien sémantique entre fait et concept n’est inventé par la réutilisation.
- Les retours historiques sans statut de couverture sont acceptés, mais leur couverture n’est pas éligible au cache de réutilisation.
- Réexamen de HOLD, rejets, résultats partiels et blocages ; historique des décisions conservé. Annulation explicite des tâches actives et refus des retours tardifs.
- Détection légère de changement d’index, remise à zéro des curseurs concernés et journalisation. Champ `source_epoch` pour déclarer une version sans hachage global du corpus.
- Plusieurs emplacements d’un îlot sont recensés. Un emplacement externe vivant est préféré à une référence embarquée. Deux emplacements vivants concurrents produisent un conflit visible ; `island-use` fixe l’autorité explicitement.
- Export enrichi avec toutes les citations enregistrées, occurrences, extensions et relations de remplacement. Les propositions remplacées restent exportées avec leur statut `SUPERSEDED` : le lecteur doit le respecter.
- Diagnostic de colonnes réelles, plans de requête et lecture d’un échantillon XML ; configuration d’exemple débarrassée des chemins de construction Linux.

## Démarrage Windows

1. Décompresser dans un nouveau dossier ; conserver la station V31 séparée.
2. Utiliser Python 3.10+ avec Tkinter. Le noyau V32 utilise uniquement la bibliothèque standard.
3. Copier `config/settings.example.json` vers `config/settings.json` et adapter les chemins D: aux index existants. Les chemins internes UNESCO et les références Kristal utilisent par défaut l’emplacement du dépôt : il est inutile de les recopier.
4. Pour un pilote séparé, définir `work_root` vers un nouveau répertoire local. Éviter une base SQLite de travail sur un partage réseau : le protocole de verrouillage vise un poste et un disque local.
5. Lancer `python encyk_cli.py doctor`, puis `EncyKlopedia.pyw` ou `LANCER_V32.cmd`.

L’interface possède maintenant les boutons Réexaminer, Annuler et Diagnostic de reprise. Les corrections structurées restent disponibles par CLI. Le navigateur et les conversations ChatGPT ne sont pas automatisés.

## Migration de la base V32.1

Le schéma passe de `encyk.local-manager.v32/1` à `/2` lors de la première ouverture par V32.2. Fermer l’ancien manager avant cette ouverture ; une version V32.1 ne connaît pas le nouveau verrou d’ordonnanceur.

Avant migration, une sauvegarde SQLite cohérente est créée sous `encyk_v32.sqlite.before-v32-2.sqlite`. La migration du schéma s’effectue dans une transaction. Les identifiants et lignes de propositions existants restent conservés ; leurs qualifier/payload nouveaux sont vides lorsque la V32.1 ne les avait pas stockés. **La migration ne reconstitue pas les informations déjà perdues par l’ancien importeur.** Il faut les réextraire ou les restaurer à partir des retours originaux disponibles.

Si une base ancienne possède déjà plusieurs tâches actives sur un même candidat, la contrainte de réservation bloque la migration et la transaction est annulée. Ne pas supprimer des lignes au hasard : conserver la sauvegarde et résoudre les jobs concernés sur une copie. Aucun doublon historique n’est arbitrairement déclaré gagnant.

La base migrée n’est pas compatible avec l’ancien manager. Pour revenir à V32.1 : fermer tous les processus, conserver l’ensemble du répertoire de travail V32.2 (y compris WAL/SHM éventuels) dans un autre dossier, puis restaurer la sauvegarde sous un nouveau chemin de travail. Ne pas déposer une sauvegarde sur un ensemble base/WAL encore ouvert.

## Commandes opérationnelles

```powershell
python encyk_cli.py doctor
python encyk_cli.py index-unesco
python encyk_cli.py discover --branch unesco.mt1.05 --budget 10000
python encyk_cli.py prepare --branch unesco.mt1.05
python encyk_cli.py jobs
python encyk_cli.py candidates --branch unesco.mt1.05 --limit 100
python encyk_cli.py import D:\retours\reponse.zip --job-id ENR_000001
python encyk_cli.py recover
python encyk_cli.py retry V32_C_IDENTIFIANT --reason "Source complémentaire disponible"
python encyk_cli.py cancel-job ENR_000001 --reason "Retour perdu, nouvelle tentative nécessaire"
python encyk_cli.py export D:\retours\ENCYK_PROPOSITIONS.jsonl
python encyk_cli.py islands-scan
python encyk_cli.py island-use urn:kristal:IDENTIFIANT D:\Kristals\MON_ILOT
```

Remplacer les identifiants des exemples par ceux de votre base. Le paramètre global `--config CHEMIN` se place avant la sous-commande.

### Correction d’une proposition

Exporter les propositions pour récupérer l’identifiant exact. Le nouveau retour contient les faits corrigés avec `supersedes: "PROP2_..."` (ou un identifiant historique), le même sujet, des preuves valides provenant du pack d’origine, et le `job_id` d’origine. Appeler :

```powershell
python encyk_cli.py import D:\retours\correction.zip --job-id ENR_000001 --correction
```

Il ne s’agit pas d’une resoumission générale du lot. Chaque fait de correction désigne une proposition active qu’il remplace. Une source nouvelle relève d’une nouvelle extraction ; ne pas modifier le pack ancien. Les corrections n’écrivent toujours aucun canon Kristal. Le cache des extractions utilisant la proposition remplacée est invalidé.

### Retours partiels et reprise

Les faits valides d’un retour mixte sont conservés ; les erreurs sont en base avec leur payload et leur numéro de ligne logique. Les articles touchés restent PARTIAL. Réexaminer leurs candidats crée un nouveau job : ne pas renvoyer silencieusement un autre contenu sous un job terminé. Un résultat accepté avec des lignes invalides reste visible comme partiel.

Un processus interrompu libère son verrou système. Les réservations publiées restent durables. `recover` détecte les ZIP sans job, les packs actifs absents/modifiés et les candidats en file sans réservation. Il ne supprime rien. Un ZIP orphelin est conservé pour diagnostic ; la préparation suivante avance avec un nouvel identifiant. Pour un job actif inutilisable, `cancel-job` libère les unités et les postes, puis `prepare` reconstruit une tentative. Les retours de l’ancien job annulé sont refusés.

### Versions de sources et profils

`source_epoch` peut être une date de dump ou un identifiant de livraison. Changer cette valeur lors d’une mise à jour en place conservant taille et date des fichiers. Sinon, le moteur détecte les changements par chemin, taille et mtime des index et WAL, sans lire le corpus entier. Terminer ou annuler les jobs actifs avant changement d’index. Garder les sources en lecture seule pendant une campagne.

`extraction_profile` identifie le besoin de traitement. Il est épinglé dans le pack. Ce champ prépare la connexion à Arketype ; **ce n’est pas encore un moteur de profils Arketype qualifiés**. Changer de profil déclenche une nouvelle extraction. Un nouveau concept dans un même profil produit un complément explicite plutôt qu’une réutilisation abusive.

## Validation effectuée

- 30 tests V32 : 6 d’origine + 24 nouveaux, tous réussis sur Linux/Python 3.12.
- 15 exécutions de tests historiques ciblés (v31.8, v31.9, v31.12), toutes réussies.
- Tests de deux connexions, verrou interprocessus et libération après arrêt brutal du processus détenteur.
- Tests d’injection d’échec avant validation finale d’import et après création de ZIP ; rollback et reprise vérifiés.
- Migration d’une base V32.1 de fixture, sauvegarde et contrôle SQLite vérifiés.
- Vérification de compilation des modules et de l’interface de commande.
- CI Python ajoutée pour Ubuntu/Windows et Python 3.10/3.12 ; cette matrice est configurée mais n’a pas été exécutée ici sur Windows.

Les anciens fichiers de validation décrivent leur propre livraison. La suite historique complète n’a pas été relancée ; ses échecs documentés dans V32.1 ne sont pas annoncés comme résolus.

## Limites conservées explicitement

L’admission Framework/Authoring Kit reste désactivée ; le code source qualifié de ces contrats n’est pas fourni pour cette intégration. La fédération reste un inventaire et une lecture d’artefacts, pas un parent canonique épinglé ni un lecteur complet des assertions. Les identités d’îlots déduites des artefacts restent à qualifier avec Framework ; les workspaces sans identité reconnue conservent une identité locale dépendant du chemin.

La récupération ne garantit pas une transaction atomique globale fichiers + SQLite ni un test de coupure électrique. La branche Windows du verrou et l’interface graphique modifiée nécessitent une recette sur Windows ; elles ne sont pas déclarées testées sur ce poste. Les mesures de débit, de pertinence et de coût sur les grands index restent à effectuer. Aucun montant économisé ni rendement global optimal n’est annoncé.

La sélection s’appuie encore sur les extraits disponibles. HOLD est désormais réexaminable, mais l’acquisition automatique de sections supplémentaires n’est pas implémentée. Le découpage automatique des articles géants et les profils de domaine Arketype restent à réaliser. Les faits sur de nouvelles entités secondaires demandent encore un parcours d’alignement séparé. La comparaison sémantique de formulations différentes n’est pas automatisée.

Les snapshots UNESCO embarqués et les sources historiques sont conservés. Aucun fichier de canon ni code de Skope/Kristalizer n’a été modifié. Commencer par un pilote séparé sur quelques branches, mesurer puis étendre.
