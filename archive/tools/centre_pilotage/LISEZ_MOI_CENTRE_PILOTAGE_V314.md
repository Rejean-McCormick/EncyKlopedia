# EncyKlopedia — Centre de pilotage v31.4 (lecture seule)

## Objet

Mettre en évidence, à côté du centre de pilotage v31.3, **les écarts de suivi
UNESCO par concept et page**. Le diagnostic n'infère jamais qu'une paire non
suivie a été perdue, n'a jamais été validée, ou mérite une nouvelle tâche.

## Installation Windows, sans modifier la station

1. Décompresser ce ZIP **dans un nouveau dossier**, par exemple
   `D:\CENTRE_PILOTAGE_ENCYK_V314` ; ne pas écraser l'installation v31.3.
2. Double-cliquer sur `CENTRE_PILOTAGE_ENCYK_V314.pyw` avec Python 3.12 et
   Tkinter, présents sur le poste d'après le diagnostic partagé.
3. L'audit démarre automatiquement. Consulter **Triage des écarts**.
4. Cliquer **Exporter les rapports** pour obtenir des fichiers complets dans
   `Documents\EncyKlopedia_Audits` ; aucun CSV n'est importé automatiquement.

Commande facultative PowerShell 7, en remplaçant le dossier d'installation :

```powershell
python D:\CENTRE_PILOTAGE_ENCYK_V314\CENTRE_PILOTAGE_ENCYK_V314.pyw --once
```

Tests hors des bases de production :

```powershell
Set-Location D:\CENTRE_PILOTAGE_ENCYK_V314
python -m unittest TEST_CENTRE_PILOTAGE_V314.py TEST_AUDIT_AUTOMATIQUE_V312.py TEST_TRIAGE_ENCYK_V314.py -v
```

## Nouveautés v31.4

- L'onglet **Triage des écarts** répartit les candidats découverts absents
  du registre des décisions et de la station en deux sous-ensembles :
  **avec affectation historique dans le catalogue** et **sans affectation
  historique**.
- Un compteur distinct affiche les divergences d'identifiants ou d'empreintes
  **déjà stockés** dans le registre et la station ; aucune reconstruction
  d'identifiants/empreintes n'est effectuée.
- Le rapport par concept distingue les concepts sans APPROVE de ceux
  sans candidat découvert, des HOLD et de ceux à rapprocher.
- Les fichiers `TRIAGE_UNESCO_V314_*_ECARTS.csv`,
  `TRIAGE_UNESCO_V314_*_CONCEPTS.csv`, et `TRIAGE_UNESCO_V314_*.json`
  s'ajoutent aux cinq fichiers déjà exportés en v31.3.
- Les 300 premières paires en écart sont visibles dans l'interface ;
  **l'export CSV conserve la totalité**.

## Précautions et interprétation

- Le rapprochement utilise la clé **(concept_id,page_id)** dans une branche.
  Les articles présents dans la table historique `assignments` ne sont pas
  assimilés automatiquement à des décisions APPROVE v28.
- Pour une paire absente du registre et de la station, la table de découverte
  **ne fournit pas à elle seule son `candidate_id` ni son `evidence_sha256`** :
  les champs restent vides dans l'export plutôt que de créer de fausses valeurs.
- Trois lectures SQLite sont réalisées indépendamment : les changements
  simultanés peuvent produire des écarts temporaires. Les changements de
  génération et la réserve de candidats sont à vérifier avant toute action.
- Les compteurs de version v31.3 mentionnés dans la conversation (667 écarts,
  22 concepts sans APPROVE, 6 197 HOLD, 4 tâches READY) ne sont **pas codés en dur**.
  Le nouveau triage les recalcule sur les bases locales lors de chaque audit.
- `saturation_demontree` et `achevement_reel_pct` restent **inconnus** (`null`).
  Ni un taux de décisions tranchées ni zéro tâche ouverte n'établit la
  complétude encyclopédique.
- Pas de modification de la station v30, du catalogue v25, de la découverte
  v28 ni des bases Kristal v27. Connexions `mode=ro` + `query_only=ON`.
  Rapports enregistrés seulement dans le dossier explicitement choisi.
- Pas de création/réinitialisation de tâche, de dégel des preuves UNESCO,
  d'édition des HOLD, d'admission canonique ni de publication.
- Les métadonnées et titres figurent dans certains rapports ; conserver les
  exports en local. Les textes/citations Kristal privés ne sont jamais lus.

## Validation

Les 12 tests synthétiques (8 hérités + 4 de triage) doivent réussir ; le code
est compilé et l'archive vérifiée. La GUI n'est **pas validée sur l'installation
Windows réelle** et n'est pas déclarée intégrée à la station de production.
