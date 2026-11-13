# EncyKlopedia v31.2 — Mode VOLUME (880 / 24 / 80 000)

## But
Prioriser le débit de production pour une revue ultérieure par agent. Ce paquet est **un overlay ciblé** appliqué à la station, pas une nouvelle base ni un remplacement de Kristal v27.

## Paramètres effectifs sur les **nouveaux** packs
- UNESCO v28 : objectif **880 candidats**, cap 880 ; seuil documentaire 3 200 unités, donc certains lots riches en preuves peuvent descendre vers ~800, sans couper les preuves. Le dernier lot peut être plus petit.
- Kristal v27 : maximum **24 articles**, cible **80 000 mots** de source, **12 MiB** de texte. Un article unique plus grand reste transmis intégralement conformément au contrat v27.
- La station conserve dix postes et son tampon de tâches ; les lots déjà créés ne sont pas reconstruits. Les ZIP UNESCO gelés de 110 restent valides.
- Le contrat d'importation ne change pas : un `DECISIONS_v28_*.csv` complet avec 3 colonnes ; un delta JSON Kristal avec les citations requises.
- Le taux de REJECT ne doit pas être artificiellement réduit ; l'agent de revue vérifiera ensuite les décisions.

## Limites et débit réel
Ces paramètres augmentent la taille des nouvelles unités de travail ; **ils ne divisent pas nécessairement par huit le temps total** et ne garantissent pas qu'un grand pack puisse être lu intégralement dans une seule conversation. Les retours partiels ou invalides restent refusés. Des lots de 80 000 mots sont très exigeants ; si un pack ne peut pas être intégralement traité, il doit être divisé côté source, jamais approuvé de façon fictive.

## Installation
Depuis le dossier ZIP extrait : `pwsh -NoProfile -ExecutionPolicy Bypass -File .\INSTALLER_MODE_VOLUME_V312.ps1`.
L'installation valide les empreintes du code v31.1.1 de départ, remplace uniquement la station et deux fichiers de tests, ajoute les tests v31.2. **Aucune base SQLite et aucun ZIP de travail n'est modifié par l'installateur.**

## Après installation
Redémarrer `LANCER_POSTE_CHATGPT_V30.ps1`. Le poste continuera à servir les tâches existantes ; la taille augmentera à mesure que les anciennes tâches sont consommées. Le bouton « préparer la vague » peut continuer à alimenter Kristal même pendant le gel UNESCO.

## Vérification
`python -m unittest discover -s tests -p 'test_*v31*.py' -q` doit réussir. Les tests inclus vérifient également 880 candidats sur une base synthétique, les tâches multibranches et l'absence de doublons.
