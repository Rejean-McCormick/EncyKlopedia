# EncyKlopedia / UNESCO — Integrated private research release 0.2

> **FR — Installation au niveau `C:\mycode\EncyKlopedia`, PAS dans le sous-dossier `EncyKlopedia\EncyKlopedia`.**
>
> La « version totale » signifie ici *intégration technique privée de la branche*, **pas** une encyclopédie mondiale terminée, une publication autorisée ni des assertions certifiées.

## Lancer sur Windows

1. Extraire l'overlay **EncyKlopedia racine** dans `C:\mycode\EncyKlopedia` et l'overlay **Factory** dans `C:\mycode\EncyKlopedia\Kristal_UNESCO_Factory`.
2. Double-cliquer sur `C:\mycode\EncyKlopedia\UNESCO_Workbench\LANCER_VERSION_TOTALE.cmd`.
3. Cliquer sur **1. Analyser les entrées**, **2. Construire la vue privée**, **3. Vérifier les empreintes**, puis **4. Ouvrir EncyKlopedia**.
4. Ouvrir `http://127.0.0.1:8787` (Node.js 22 ou ultérieur). Le nouveau lanceur garde un serveur local ouvert jusqu'à fermeture de sa console.

Sans GUI :

```powershell
py -3 C:\mycode\EncyKlopedia\UNESCO_Workbench\pipelines\unesco_total.py build
py -3 C:\mycode\EncyKlopedia\UNESCO_Workbench\pipelines\unesco_total.py check
```

Le script n'installe rien, ne télécharge aucune donnée, ne lit pas les gros index Wikidata et ne touche pas aux 88 Kristals canoniques. Il crée des fichiers **dérivés uniquement** sous `UNESCO_Workbench\output\private\educational-policy-en`.

## Entrées, avec priorité aux workspaces existants

Le pipeline choisit, si présents et structurés, les fichiers réels de :
- `UNESCO_Workbench\candidates\educational-policy-en-v11\unesco-mt1-10` (source et identités v11);
- `UNESCO_Workbench\reviews\educational-policy-en-v11\round2-knowledge-en` (19 propositions + six sources + article EN).

Sinon, il utilise des **copies figées et attribuées** des mêmes snapshots fournis lors de ce chantier, sous `UNESCO_Workbench\reference`. Ces copies ne sont **pas** des preuves canoniques, ni de nouvelles sources internet. Le manifeste de construction contient leurs empreintes SHA-256 exactes. Les éventuelles versions plus récentes des fichiers primaires sont contrôlées avec une règle stricte : si elles ne sont plus « candidates en revue », le script échoue au lieu de les traiter implicitement comme autorisées.

Le fichier `reference\ldh_2025_educational_policy.json` est un **extrait de 40 entrées** du RDF fourni dans `LinkedDataHub-UNESCO` : il contient les libellés et les relations SKOS nécessaires à la comparaison, et l'empreinte SHA-256 du RDF original à 88 636 triplets. Le RDF complet n'est pas copié dans le Workbench. Pour vérifier l'intégrité du dépôt LinkedDataHub présent sur ton PC :

```powershell
py -3 C:\mycode\EncyKlopedia\UNESCO_Workbench\pipelines\unesco_total.py rdf-check
```

Si le dépôt RDF a changé, `rdf-check` le signale : l'ancien extrait n'est **jamais présenté comme une lecture fraîche** du nouveau RDF.

## La frontière des responsabilités

| Couche | Propriétaire | État de cette version |
|---|---|---|
| LinkedDataHub-UNESCO | Snapshot RDF/SKOS comparatif daté 2025 | Extrait compact + contrôle de hash, aucune modification du dépôt |
| Factory | Extraction UNESCO/Wikidata, 88 Kristals v9 | Chemins de l'interface réalignés après déplacement; **ne pas relancer le RUN mondial pour le pilote** |
| Kristalizer | Identités KQ/KP candidates v11 | 41 KQ provisoires, 36 crosswalks *candidats*, aucune approbation |
| Workbench | Comparaison, sélection, preuves candidates, rapports | Pipeline privé testable, déterministe, SHA-256 |
| Spek / SemantiK / GF | Réalisation/composition future d'articles qualifiés | **Inchangés**; ne pas maquiller un brouillon en résultat qualifié |
| EncyKlopedia | Lecteur HTTP et navigation | Nouveau mode **private-research**, loopback-only; démo synthétique inchangée |

## Résultat et limites

- 88 branches repérées quand `UNESCO_Kristals\branches` est présent, et 41 notions dans la branche EN.
- 40 notions correspondantes dans le RDF historique, une notion de plus dans la source récente (`concept17189`, Multilingual education), avec différences SKOS documentées.
- 36 correspondances Wikidata en attente de revue, **zéro `exactMatch` approuvé**.
- Un vrai brouillon anglais de recherche *Right to education*, 19 propositions d'assertions atomiques, six URL et localisateurs de sources institutionnelles. Les 40 autres pages sont explicitement des **notices de thésaurus sans article encyclopédique approuvé**.
- **Zéro source capturée avec une empreinte de contenu, zéro KS/KA créée ou approuvée.** La validation humaine, l'Authoring Kit v11, la qualification, les droits, la confidentialité et l'autorisation indépendante de publication C2/C4 restent à faire.

**Ne pas publier la vue JSON** de `output\private`. Elle contient du matériel documentaire candidat. Le site n'accepte que `ENCYKLOPEDIA_MODE=demo` ou `research`; un mode `public`, un hôte non-local, une déclaration d'approbation, ou une modification du fichier sans mise à jour du manifeste est refusé.

## Tests

```powershell
cd C:\mycode\EncyKlopedia
py -3 -m unittest discover -s UNESCO_Workbench\tests -v
cd C:\mycode\EncyKlopedia\EncyKlopedia
npm run verify
```

Les diagnostics historiques LevelUpDiag et les RUNs existants ne sont pas modifiés. Le Workbench produit un résultat de diagnostic de construction distinct; ne pas considérer un code `OK` comme une qualification éditoriale.
