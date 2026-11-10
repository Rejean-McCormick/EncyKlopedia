# UNESCO V22 — Overlay exécutable de correction et mise à jour

**Périmètre :** seul Kristal Educational Policy, `unesco-mt1-10` (41 ancrages), revue IA des 44 propositions du 10/11/2026.

## Corrections réellement exécutées

- Le moteur original `recevoir_lots_atlas_v19.py` est appelé via ses fonctions publiques : le **lot 002 / 25 textes** est contrôlé (hash SHA-256, identifiants de révision, 41 ancrages), puis ses **25 propositions** sont enregistrées dans le registre documentaire privé `atlas_documentaire_v19_candidats`, sans modifier l'original.
- La revue IA du 10 novembre est appliquée à **44 propositions** : **28** approuvées sans reformulation, **10** corrigées, **6** suspendues.
- Parmi les 38 acceptées sur le fond, **36** sont rattachées à un concept compatible; **2** restent retenues éditorialement mais bloquées par leur rattachement (`LOT002-V21-017`, `LOT002-V21-020`).
- Une correction de rattachement est appliquée à `LOT002-V21-018` : `concept1480` -> `concept11264` (Functional illiteracy, `KQ38` provisoire).
- Génère `semantic_stage_v22_revue_ia/` : registre effectif avec corrections, suspensions, article *Right to education*, vue de lecture HTML des **41 concepts**, rapport et manifeste de fichiers.

## Sécurité et gouvernance

L'overlay est **additif** : aucun fichier des dépôts antérieurs, aucune base Wikipédia SQL/XML, aucun index et aucun Kristal canonique n'est remplacé. Les fichiers existants de `semantic_stage_v22_revue_ia` doivent être identiques octet pour octet en cas de relance; sinon l'overlay refuse de les toucher. Le manifeste d'entrée est hashé; un changement au lot V21 ou aux références fait échouer la validation.

Les « approbations » sont **des décisions éditoriales d'IA**, non des signatures humaines. **Aucune création canonique KS/KQ/KP/KA**, aucune autorisation de publication, aucune projection linguistique effectuée. Les six sources R2 sont référencées mais **non capturées/archivées avec SHA-256** : cette étape n'est pas remplacée par des liens web.

## Prérequis sur ton ordinateur

- Dépôt `C:\mycode\EncyKlopedia\EncyKlopedia` avec `tools\unesco_pilot\recevoir_lots_atlas_v19.py`.
- Dossier `D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41` comprenant l'atlas V19, le rapport V18 et le ZIP `atlas_documentaire_v19_LOT_002_CHATGPT_V21.zip`.
- Python 3.9+ accessible avec `py -3` ou `python`.

## Installation

Ne copie **pas** ce ZIP dans ton dépôt à l'aveugle. Décompresse-le dans un dossier temporaire, puis lance, depuis PowerShell 7 :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\INSTALLER_UNESCO_IA_V22.ps1"
```

L'installateur vérifie d'abord tous les hachages et collisions puis ajoute seulement de nouveaux fichiers dans `C:\mycode`. Il exécute ensuite le précontrôle puis le correctif privé sur D:. Pour vérifier sans écrire : `... -DryRun`. Pour installer sans produire le résultat D: : `... -InstallOnly`.

Après installation, on peut relancer à volonté :

```text
C:\mycode\EncyKlopedia\EncyKlopedia\LANCER_UNESCO_CORRECTIONS_IA_V22.cmd
C:\mycode\EncyKlopedia\EncyKlopedia\AUDITER_UNESCO_CORRECTIONS_IA_V22.cmd
```

## Résultat attendu

```text
D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41\semantic_stage_v22_revue_ia\reader_en\index.html
```

Le répertoire `semantic_stage_v22_revue_ia` n'existait pas dans les snapshots du 10 novembre. S'il existe aujourd'hui avec un contenu différent, le correctif **refuse** et demande un examen avant tout écrasement.
