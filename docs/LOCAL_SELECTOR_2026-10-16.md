# Konstellation — démarrage neutre / choix local (prototype)

- **Un seul lanceur à la racine :** `Konstellation.cmd`.
- Aucun Kristal choisi à l'ouverture, pas de retour implicite à Théophile ni à `active-reader.json`.
- `config/local-catalog.json` définit explicitement la racine locale `C:/mycode/Kristal/locals` et une recette de lecture dérivée optionnelle pour Catho.
- L'interface « Mes Kristals » liste seulement les **sous-dossiers immédiats** présentant `kristal.workspace.json`; les dossiers non pris en charge restent indisponibles.
- Le catalogue est une **fonction locale privée** (loopback). Aucune découverte sur internet ou qualification C1/C2 n'est supposée.
- Au clic « Ouvrir dans l'explorateur », le serveur relit et vérifie la structure de l'état et, s'il y a lieu, les empreintes déclarées par le lecteur local.
- Un lecteur générique non spécialisé présente la structure v9 conservée sous le Framework v10; il ne promet pas une projection sémantique spécifique à tous les Kristals.
- `tools/legacy-root/` contient des copies historiques des anciens lanceurs et outils, **non nécessaires pour démarrer Konstellation**. Pour les anciens scripts de maintenance, rétablir leur environnement original avant utilisation.
- `tools/maintenance/Ranger_anciens_lanceurs.cmd` peut déplacer les anciens fichiers de la racine vers une sauvegarde, après confirmation explicite. Ne touche ni aux Kristals, ni à `config`, ni aux fichiers du projet.
- Les tests unitaires du sélecteur et les contrôles de structure passent dans le conteneur; le navigateur Windows et le build Astro complet ne sont pas vérifiés ici, faute de dépendances npm installées.
