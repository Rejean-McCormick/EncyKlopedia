# EncyKlopedia v31.5 — Transition Mode Volume + transport groupé

## Objectif

Réduire les manipulations pour les anciens petits packs UNESCO sans jamais reconditionner
une tâche enregistrée et sans contourner le gel probatoire. La production de nouveaux
packs garde les réglages de v31.2 (UNESCO cible 880, seuil souple 650, budget 3 200 ;
Kristal v27 24 articles, 80 000 mots, 12 MiB ; 10 conversations).

## Modifications

1. **Mesure de transition en station** : état et taille des tâches `READY`, volumes
   UNESCO ouverts en trois classes (≤300, 301–649, 650–880), nombre de Kristal
   ouverts. C'est la taille observée, pas la version certaine qui a créé le pack.
2. **Mesure de délai** `sent_utc` → `finished_utc` : médiane de transfert à import,
   globale et par format. Ce délai **inclut les pauses humaines** : ne pas le
   confondre avec le temps effectif de calcul ChatGPT, ni calibrer automatiquement
   la taille des sources sur cette seule mesure.
3. **Tampon multibranche** : la limite `QUEUE_BUFFER=20` s'applique globalement.
   Les branches reçoivent d'abord une opportunité, puis la branche historique
   peut remplir les places qui resteraient vides. Aucun job existant n'est muté.
4. **Transfert groupé** : bouton dans la station pour réunir jusqu'à dix petites
   tâches UNESCO `READY` (≤300 propositions chacune, total ≤880) dans **un ZIP
   de transport**. Les ZIP individuels sont ajoutés bit à bit et restent
   distincts, avec un manifeste contenant leurs empreintes.

## Import groupé sans changement de contrat

Le ZIP de transport contient :

- `MANIFEST_TRANSFERT_MULTI_V315.json` (identifiants, compteurs et empreintes)
- `INSTRUCTIONS_TRANSFERT_MULTI_V315.txt`
- `PACKS/<task_id>.zip` pour chaque tâche originale.

La conversation ChatGPT doit ouvrir chaque ZIP et analyser chaque candidat.
Elle retourne **un ZIP unique** comprenant un fichier indépendant
`DECISIONS_<task_id>.csv` par tâche, UTF-8, trois colonnes
`candidate_id,decision,justification`, une ligne pour chaque candidat.
Le système importe ce ZIP avec **l'importeur multiretour déjà en place**, qui
contrôle chaque tâche individuellement.

Le téléchargement groupé ne marque pas les tâches `SENT` automatiquement : cela
évite une mutation sans garantie que le transfert a réellement été effectué.
**Ne pas redistribuer manuellement les mêmes tâches en parallèle** pendant la
conversation groupée. Seules les tâches encore `READY` sont éligibles ; les
`SENT` et `ERROR` n'entrent jamais dans le groupement.

Si une réponse groupée est incomplète, la station valide ou refuse chaque tâche
indépendamment. Un retour partiel/tout-HOLD peut demander confirmation humaine.
Les ZIP sources de chaque tâche restent toujours disponibles dans la station.

## Installation

1. Fermer la station locale v30 et laisser les moteurs au repos.
2. Déterminer le SHA-256 local de `tools/unesco_pilot/poste_chatgpt_v30.py`.
3. Sélectionner **l'overlay correspondant uniquement à ce SHA** :
   - v31.2 : `2857faf01dc927f7e0222fe3c0d033a5d3750895baf6b179ebda5de704e97629`
   - v31.2.1 : `6c9f2bd2099f3829cedc54c02a15caf1e85ed85b90dd60bb152fcfe3449b4652`
4. Dans l'interface de la station, « Vérifier un overlay logiciel ZIP », puis
   prévalider les empreintes et confirmer l'installation. **Ne pas déposer comme
   retour UNESCO ou Kristal.**
5. Redémarrer la station via `LANCER_POSTE_CHATGPT_V30.ps1`.
6. Utiliser « Regrouper les petits packs UNESCO prêts » uniquement si au moins
   deux tâches UNESCO `READY` de 300 propositions ou moins sont proposées.

La mise à jour logicielle crée une sauvegarde des fichiers remplacés ; le bouton
« Retour arrière » peut restaurer le code précédent sous contrôle d'empreinte.
N'utiliser jamais de `-Force` ou de remplacement manuel si le SHA local diffère.

## Protections

Aucun `candidate_id`, `evidence_sha256`, `source_sha256`, `bundle_sha256`, état
HOLD, décision importée, source Wiki, QID, signature de branche ou pack Kristal
n'est modifié par la mise à jour. Aucun article n'est supprimé de l'inventaire.
Pas d'admission canonique ou de publication. Le gel de la découverte UNESCO
suit les règles existantes.

## Validation

Tests v31 ciblés, non-régression v31.5, `node --check`, suite JS et test isolé
de prévalidation / installation / retour arrière sur les deux bases de version.
La station Windows de production **n'a pas été modifiée ni exécutée ici**.

Attention : deux anciens tests `test_poste_chatgpt_v30.py` supposent les anciens
lots de 110 ; ils échouent **aussi** sur le snapshot v31.2 original, avant ce
correctif. Cette incompatibilité de tests historiques n'est pas un nouveau
échec de v31.5.
