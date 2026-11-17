# Inventaire des ensembles sources — synthèse pour futurs agents

Compilation à partir des ZIPs fournis et extraits en lecture seule. « Dépôt » signifie ici un ensemble de fichiers, sans présumer de l’existence d’un dépôt Git distinct dans chaque cas. Certains ensembles sont sous SmartDump, certains proviennent du snapshot Skope.

| Ensemble | Fichiers | Python | Markdown | JSON | Bases incluses |
|---|---:|---:|---:|---:|---:|
| `EncyKlopedia` | 384 | 112 | 70 | 84 | 0 |
| `UNESCO_Kristals` | 3346 | 176 | 1321 | 1232 | 0 |
| `UNESCO_Workbench` | 201 | 23 | 48 | 69 | 0 |
| `Kristal_UNESCO_Factory` | 688 | 110 | 230 | 270 | 0 |
| `LinkedDataHub-UNESCO` | 25 | 0 | 3 | 0 | 0 |
| `mediatheque` | 416 | 88 | 69 | 9 | 0 |
| `mediatheque-references` | 72 | 19 | 8 | 3 | 0 |
| `LevelUpDiag_EncyK` | 58 | 36 | 3 | 11 | 0 |
| `scan_engine (Kristalizer external)` | 7 | 6 | 0 | 0 | 0 |
| `scan_test` | 10 | 0 | 0 | 1 | 0 |
| `Skope (external)` | 505 | 94 | 197 | 137 | 0 |

**Total :** 5712 fichiers inventoriés ; 488 modules Python analysés statiquement.

Attention : une partie des 88 branches compte de nombreux fichiers dérivés; le nombre de fichiers ne mesure ni la quantité de fonctionnalités ni le coût de refactor.

La présence d’une source dans cette table **n’autorise pas** son déplacement. Les ensembles Skope/Kristalizer sont exclus des modifications; la médiathèque peut être partagée.

Détail machine : [`inventaire_depots.csv`](inventaire_depots.csv).
