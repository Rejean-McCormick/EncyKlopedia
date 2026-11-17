# UNESCO Educational Policy EN — Lot de revue 2

**Installation :** extraire ce ZIP à la racine de `C:\mycode\EncyKlopedia` (PAS dans `EncyKlopedia\EncyKlopedia`). Ce paquet n’ajoute que des fichiers dans `UNESCO_Workbench\reviews\educational-policy-en-v11\round2-knowledge-en`.

**Contenu livré :** 41 décisions éditoriales laissées ouvertes mais dotées de recommandations explicites; 19 assertions de recherche atomiques en anglais avec 6 sources primaires, localisateurs et limitations de portée; article encyclopédique de recherche; contrôle en lecture seule.

**Vérification locale :** dans ce dossier, exécuter `py -3 validate_round2.py` ou `python validate_round2.py`. Le contrôle est une vérification structurelle, pas une approbation scientifique.

**Pas de fusion automatique :** aucune écriture dans `UNESCO_Kristals`, dans `canon/domain/v11`, dans les décisions Kristalizer, dans Spek ou dans le site public. Les identifiants `RTE-KA-PROP-*` ne sont pas des KAs : ils sont des identifiants de **propositions**. Les références `SRC-*` ne sont pas des KS. Toutes les décisions `editorial_decision` restent vides et la capture locale de chaque source reste absente.

**Pour promouvoir une assertion plus tard :** (1) capturer la source et son empreinte, (2) comparer la proposition à sa portion exacte, (3) fixer la portée temporelle/géographique et la modalité, (4) faire approuver humainement la décision, (5) définir des KP explicites et créer KS/KA avec le vrai Authoring Kit v11 sur copie, (6) valider, qualifier, puis envisager la publication.

**Contrôle des identités :** il faut distinguer recommandation d’analyste et décision formelle. La suggestion `KQ2 → Q452348` est maintenant jugée cohérente après vérification de la fiche anglaise, mais demeure candidate. `KQ26 → Q3595759` doit rester en revue; la présence d’« International education » comme terme d’entrée UNESCO n’établit pas l’égalité des concepts.

**Sources :** UN UDHR art.26, OHCHR ICESCR art.13 et art.2, UNICEF CRC art.28, UNESCO Convention 1960, UNESCO obligations de l’État, UIS indicateurs SDG4. URLs et localisateurs dans `source_register_en.json`.

**Prochaine action de contenu :** qualification source par source des 19 propositions, puis intégration v11 dans une copie candidate sans toucher aux 88 Kristals actifs.
