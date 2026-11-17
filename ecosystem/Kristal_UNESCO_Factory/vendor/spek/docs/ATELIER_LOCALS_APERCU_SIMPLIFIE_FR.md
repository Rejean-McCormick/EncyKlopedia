# Spek — Accès direct aux sources locales et aperçu Wiki simplifié

## Démarrage

Lance `START_SPEK.bat` depuis le dépôt Spek. Dans la colonne de gauche, choisis un Kristal du **registre IA (127 propositions)**.

Spek cherche alors **uniquement** dans les sous-dossiers directs du dossier `locals` configuré, et lit leurs fichiers `kristal.workspace.json` afin de comparer les identifiants normalisés (par exemple `agriculture`). Le nom du dossier (`Kristal-Agriculture` ou autre) ne suffit jamais à prouver l'identité. Sélectionner un Kristal dans le catalogue **n'ouvre pas ses sources**.

Si `locals` n'est pas détecté, clique sur **Dossier locals…** et choisis la collection. Ce choix est mémorisé dans les préférences locales de ton compte (hors dépôt Git). Le dossier historique `C:\mycode\Kristal\locals` est reconnu s'il existe. Tu peux également utiliser la variable `SPEK_LOCALS_ROOT`.

Dans l'espace **1 · Kristal**, **Ouvrir les sources de ce Kristal** effectue la lecture contrôlée de la source explicitement identifiée. En cas d'identités contradictoires, de doublons ou d'absence de métadonnées, le programme ne devine pas et demande une intervention manuelle.

## Espace « 3 · Aperçu Wiki »

- **Explorer la structure** : pour les cinq Kristals ayant une revue structurelle, le bouton ouvre les sources identifiées si nécessaire, vérifie la correspondance avec la revue, puis construit un aperçu **privé**. Si la source a changé, Spek refuse l'aperçu de cette revue. Les 122 autres Kristals attendent une analyse canonique approfondie.
- **Prévisualiser le Wiki** : demande `article.json` et les réalisations linguistiques SemantiK si ces fichiers ne sont pas déjà chargés, puis compile un HTML **local**, sans publication.
- **Vérifier les fichiers** : commande secondaire activée une fois les deux fichiers chargés.
- **Options de préparation SemantiK** : commandes de correspondance et d'import disponibles sur demande, repliées par défaut.

Quand on change de Kristal dans le catalogue, Spek efface de l'interface la paire article / réalisations de l'ancien contexte pour éviter de la présenter sous un autre Kristal. Les fichiers sur disque ne sont jamais supprimés.

## Limites et sécurité

- La recherche du dossier est une **correspondance d'identité déclarée**, et non une classification par Spek. Les compositions de templates restent celles du registre élaboré par l'IA.
- Une source trouvée n'est **ni une sélection d'assertions, ni une validation éditoriale, ni une autorisation de publication**.
- Les aperçus restent privés. Le passage au GitHub Wiki requiert les validations du pipeline externe, notamment C1/C2/C3.
- Le programme ne modifie pas les Kristals, les fichiers dans `locals`, les registres d'assignations approuvées ni `.git`.
