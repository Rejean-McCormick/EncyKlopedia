# Installation — Atelier Spek refondu

1. Fermer Spek et conserver les modifications locales non poussées.
2. Décompresser le correctif **dans le dossier parent du dossier `Spek`**. Les chemins de l'archive commencent par `Spek/`.
3. Remplacer les fichiers du même nom. Ne pas supprimer `.git`, `template_library/` ni aucun fichier personnel.
4. Lancer `Spek/START_SPEK.bat` ou `Spek/Spek_Template_Manager.pyw`. Ce lanceur ouvre maintenant les quatre espaces de travail.
5. Pour administrer les 27 layouts et éditer les JSON, utiliser **Outils avancés**, ou lancer `py -3 Spek_Template_Manager.pyw --advanced` depuis le dossier Spek.

## Vérifications

`py -3 Spek_Template_Manager.pyw --diagnostic` confirme le dépôt et les layouts.

`py -3 -m pytest -q` exécute la suite de tests depuis le dossier `Spek` (si pytest est installé).

## Invariants

La consultation du registre IA ne vaut pas une analyse du Kristal local. L'ouverture du dossier n'accorde aucune autorisation de publication. Spek ne choisit pas les faits et ne rédige pas les réalisations SemantiK. La publication GitHub Wiki relève d'un autre pipeline avec C1/C2/C3.
