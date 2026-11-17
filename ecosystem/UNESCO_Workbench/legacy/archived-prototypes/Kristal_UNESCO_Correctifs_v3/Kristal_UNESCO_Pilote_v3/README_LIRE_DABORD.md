# Kristal UNESCO — Pilote GF v3, chemins corrigés

## Ce qui change

Le dernier inventaire Windows fourni confirme notamment les chemins suivants :

| Élément | Chemin par défaut |
|---|---|
| Kristal | `C:\mycode\Kristal` |
| SemantiK Architect (projet réel) | `C:\mycode\SemantiK_Architect\SemantiK_Architect` |
| Artefact PGF français existant | `C:\mycode\SemantiK_Architect\SemantiK_Architect\runtime\konstellation-fr-3\grammar.pgf` |
| Adaptateur GF de SemantiK | `...\src\semantik_architect\adapters\realization\gf\pgf_runtime.py` |
| Python 3.12 | `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`, si présent |
| RUN UNESCO | détection automatique dans `C:\mycode\Kristal\Kristalizer\SORTIE\UNESCO\FABRIQUE\RUN-*` |
| Sortie | `Downloads` |

Le champ **`GF.exe` reste vide si aucun compilateur réel n'est trouvé**. Il serait incorrect de le remplir avec `grammar.pgf` : un `.pgf` **précompilé** est un artefact de réalisation; `gf.exe` est requis pour **compiler** les nouvelles grammaires candidates UNESCO livrées dans ce paquet.

## Démarrage

1. Décompresser `Kristal_UNESCO_Outils_v3.zip` dans Téléchargements.
2. Ouvrir `Kristal_UNESCO_Pilote_v3` puis lancer `LANCER_UI.cmd`. Le lanceur privilégie le `pythonw.exe` Python 3.12 identifié par le diagnostic (sinon essaie les interpréteurs disponibles).
3. Vérifier les champs préremplis; cliquer sur **Vérifier PGF existant (Python pgf)**. Cela lance un contrôle limité à 10 s avec le Python sélectionné et tente de charger le PGF Konstellation via le module Python `pgf`.
4. Cliquer sur **Rechercher GF**. La recherche inspecte `GF_Wordbench` près de SemantiK, quelques emplacements classiques et le `PATH`, sans scanner le disque entier.
5. Si le compilateur n'est pas trouvé, le pilote prépare toujours les requêtes `concept10` FR/EN et crée une archive **avec statut bloqué**; aucun texte grammatical n'est inventé.
6. Si un véritable `gf.exe` existe, cliquer sur **Vérifier GF** puis **Compiler GF + tester concept10**. Cette étape compile *les grammaires UNESCO du pilote*, vérifie les contrats SemantiK et matérialise les slots Spek uniquement en cas de conformité réussie.
7. Envoyer l'archive produite dans Téléchargements après inspection.

## Limitations essentielles

- Le PGF `konstellation-fr-3` n'est **pas** une grammaire UNESCO et ne garantit pas le support anglais.
- Le contrôle Python `pgf` ne constitue pas une réalisation GF dans le RUN UNESCO.
- La compilation et le runtime SemantiK s'exécutent dans l'interpréteur qui lance le pilote, d'où le lanceur Python 3.12 recommandé.
- Les opérations sont limitées (compilation GF 45 s/langue, contrôle PGF 10 s, vérification compilateur 8 s). Aucune source du projet, aucun RuntimeSet actif n'est modifié; pas de publication.
- Aucun binaire `gf.exe` ni fichier `.pgf` issu de ton ordinateur n'est inclus dans ce ZIP.

## Test automatisé

`pytest -q tests` depuis le dossier du pilote, avec les sources Spek et SemantiK accessibles. Les tests unitaires couvrent les chemins, la recherche bornée et les statuts « aucune réussite fictive ». Ils **ne remplacent pas** une compilation GF Windows réelle.
