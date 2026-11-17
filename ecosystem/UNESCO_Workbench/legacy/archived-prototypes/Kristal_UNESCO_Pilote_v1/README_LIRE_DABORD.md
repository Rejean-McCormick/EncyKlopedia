# Pilote Kristal UNESCO — Spek → SemantiK → GF

**Statut : pilote privé non canonique, non approuvé, non publiable.**

Ce paquet met en place le raccordement technique **sans réexécuter la fabrique UNESCO** et **sans modifier** les dépôts, le RUN existant, un RuntimeSet actif ou un wiki.

## Démarrage sur Windows

1. Décompresser le ZIP **hors des dossiers Git**, par exemple dans `Downloads\Kristal_UNESCO_Pilote_v1`.
2. Double-cliquer sur **`Pilote_Kristal_UNESCO.pyw`** avec Python 3 et Tkinter. Si l'association `.pyw` n'est pas disponible, dans PowerShell 7 :
   ```powershell
   cd "$HOME\Downloads\Kristal_UNESCO_Pilote_v1"
   py -3 Pilote_Kristal_UNESCO.pyw
   ```
3. Vérifier les chemins préremplis :
   - `C:\mycode\Kristal` ;
   - `C:\mycode\SemantiK_Architect\SemantiK_Architect` (le programme détecte également le sous-dossier si nécessaire) ;
   - dossier `RUN-*` dans `C:\mycode\Kristal\Kristalizer\SORTIE\UNESCO\FABRIQUE` (auto-détection possible) ;
   - **compilateur `gf.exe`** si disponible (sélectionner avec le bouton `…`).
4. Choisir `concept10` et français (anglais facultatif), puis cliquer sur **Préparer et tester le pilote**.
5. Dans **Téléchargements**, ouvrir l'archive `Kristal_UNESCO_Pilote_*.zip`. Consulter `report.json`, `journal.log`, les requêtes et, si les tests GF réussissent, `wiki_prive/concept10.fr.md`.
6. Envoyer l'archive produite après inspection des noms de chemins et des éventuelles informations sensibles.

Le programme fait ses contrôles dans un fil secondaire, pour garder la fenêtre réactive. La compilation GF est limitée à **45 secondes par langue**. L'annulation est contrôlée entre étapes, et la compilation externe se termine au plus tard à son délai d'expiration.

## Mécanisme effectif

1. Lire `01_INVENTAIRE/concepts.jsonl` et `groupes.csv` du RUN, puis retrouver `concept10` **sans inventer de source ni de définition**.
2. Charger l'instance `07_DISCOURS/instances/{lang}/concept10.json`, résoudre les feuilles via **la bibliothèque native Spek**, vérifier les slots attendus (`claim`, `scope`).
3. Construire, via l'ACL expérimentale `unesco-pilot`, une *CommunicationRequest* SemantiK 1.0 pour chacune des deux assertions **explicitement fondées sur l'inventaire UNESCO** : concept répertorié et appartenance au microthésaurus. Les phrases sont limitées à ces deux informations. Aucun fait Wikidata ni définition n'est inféré.
4. Restreindre chaque requête avec le contrat officiel de formulation **`spek.slot_dialogue.compose_request`**, puis la valider avec `CommunicationRequest` et `RequestValidator` réels de SemantiK.
5. Préparer un **RuntimeSet candidat** `unesco-pilot-{lang}-1` : grammaire GF, lexique, bridge, profil, suite de conformité, et empreintes SHA-256 des artefacts (`pipeline.lock.json`).
6. Si `gf.exe` est disponible : appeler **GF `-make`** avec un délai d'expiration, puis exécuter le vrai `CandidateConformance` de SemantiK avec son adaptateur GF (backend Python `pgf` ou CLI GF configurée).
7. Si la suite de conformité réussit : réaliser chaque requête à travers le **candidat SemantiK**, vérifier les couples avec **`spek.composition.semantik_adapter.import_results`**, composer avec le moteur natif Spek et produire un aperçu Markdown/HTML privé.
8. Sinon : conserver **les requêtes et les logs**, déclarer un blocage et **ne jamais créer une fausse page GF**.

## Statuts attendus

- `CANDIDATE_VERIFIED_PRIVATE_NOT_RELEASED` : GF réel + SemantiK candidat + Spek vérifiés, **mais ce n'est pas une approbation/activation**, et la qualité encyclopédique n'est pas validée.
- `BLOCKED_OR_PARTIAL` : une ou plusieurs langues manquent (p. ex. aucun `gf.exe`) ; voir `report.json` et `candidates/{lang}/compilation.log`.
- `ERROR` : source ou contrat absent/incompatible ; **aucune publication**, pas de remplacement inventé.
- `CANCELLED` : arrêt demandé ; zip du diagnostic conservé.

## Ce que le pilote ne fait volontairement pas

- Ne reconstruit pas les 88 Kristals / 4 500 concepts.
- N'ajoute pas de définition inexistante et ne transforme pas un candidat P3916 en identité canonique.
- N'active pas un RuntimeSet ni ne marque une grammaire `RELEASED` ; cela demande une étape de qualification indépendante.
- Ne publie aucune page wiki.
- Ne produit pas encore une encyclopédie complète : **c'est une preuve de liaison pour deux phrases strictement sourcées**, ensuite généralisable.

## Exécution sans UI

```powershell
py -3 pilot.py --kristal "C:\mycode\Kristal" --semantik "C:\mycode\SemantiK_Architect\SemantiK_Architect" --concept concept10 --languages fr,en --gf "C:\CHEMIN\VERS\gf.exe"
```

Sans `--gf`, le programme recherche GF dans le PATH, `SEMANTIK_GF_EXECUTABLE`, puis dans quelques emplacements Windows courants. Pour un autre RUN : ajouter `--run "C:\...\RUN-*"` (indiquer **un dossier réel**, pas un joker). Pour une autre sortie : `--output "D:\..."`.

Pour exécuter les tests sources : `py -3 -m pytest -q tests`. Ce sont des tests structurels et des doubles de test explicitement identifiés, **pas une preuve d'exécution GF** ; ils utilisent les dépôts locaux du projet. Des tests sur une vraie grammaire nécessitent `gf.exe`.

## Prérequis / provenance

- Python 3 avec Tkinter et les dépendances nécessaires à **la version existante** de SemantiK.
- Sources locales de **Kristal_UNESCO_Factory/vendor/spek** et **SemantiK_Architect/src** (pas une copie réinterprétée de leurs API).
- Dernier RUN UNESCO contenant l'inventaire complet et les instances Spek.
- Le compilateur Grammatical Framework `gf.exe` pour la réalisation réelle. Il n'était pas disponible dans l'environnement de développement du présent paquet ; aucune compilation GF réelle n'est donc revendiquée pour ce paquet.

Les fichiers des sources ne sont jamais effacés ni écrits. Les sorties sont dans un dossier horodaté sous `Downloads`, accompagné de son ZIP. Avant de partager ce ZIP, vérifier les journaux et chemins locaux.
