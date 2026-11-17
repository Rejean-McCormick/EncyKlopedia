# Sources pour finaliser les 122 Kristals restant à examiner

Le rapport Manager constitue un inventaire de 127 Kristals, mais il ne transporte pas leurs graphes complets. L'IA ne peut donc pas établir des compositions optimales des 122 sans de nouvelles sources.

Depuis `C:\mycode\Kristal\Spek` :

```powershell
py -3 scripts\exporter_sources_pour_analyse_ia.py --root C:\mycode\Kristal\locals --out C:\mycode\Kristal\RAPPORTS-SPEK
```

Cela crée un **ZIP manifeste uniquement**, sans assertions.

Après vérification de la confidentialité et si tu veux transmettre les artefacts de lecture choisis :

```powershell
py -3 scripts\exporter_sources_pour_analyse_ia.py --root C:\mycode\Kristal\locals --out C:\mycode\Kristal\RAPPORTS-SPEK --include-content
```

Le second ZIP contient uniquement un ensemble limité de JSONs de lecture, dont les états portables v8 s'ils existent. Il peut contenir des informations privées : **ouvrir et examiner avant partage**. Les fichiers volumineux ou absents sont signalés dans le manifeste. Aucune modification canonique, aucun push, aucun appel réseau.

Ce script ne décide rien pour Spek : il réunit des sources que l'IA pourra étudier hors de l'application, puis le registre éditorial sera rédigé explicitement.
