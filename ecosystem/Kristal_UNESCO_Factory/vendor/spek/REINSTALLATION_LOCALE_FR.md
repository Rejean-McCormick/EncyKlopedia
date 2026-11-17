# Remise en place de Spek sur Windows

Ce dossier est le dépôt **Spek** reconstruit à partir de l’archive locale fournie, avec
l’overlay `template_library` intégré. Ce n’est pas un simple patch.

## Pour remplacer ton dossier local sans perdre la liaison Git

1. Sauvegarder les éventuels changements personnels non poussés et les fichiers locaux
   avant de supprimer l’ancien dossier `C:\mycode\Kristal\Spek`.
2. Après suppression, ouvrir PowerShell dans `C:\mycode\Kristal` et cloner
   le dépôt GitHub existant :

   ```powershell
   cd C:\mycode\Kristal
   git clone https://github.com/Rejean-McCormick/Spek.git Spek
   ```

3. Extraire le ZIP de livraison **par-dessus** `C:\mycode\Kristal` avec
   `Expand-Archive -LiteralPath <chemin-du-zip> -DestinationPath 'C:\mycode\Kristal' -Force`.
   Le ZIP contient `Spek/` à sa racine et **aucun `.git/`** ; ainsi, le dossier
   `.git` créé par `git clone` est conservé.
4. **Dans le cas d’un nouveau clone GitHub** uniquement, retirer l’ancien dossier
   `wiki-templates/` que le clone a encore apporté. Les fichiers correspondants se
   trouvent déjà dans `template_library/wiki/` grâce au ZIP :

   ```powershell
   Remove-Item -LiteralPath 'C:\mycode\Kristal\Spek\wiki-templates' -Recurse -Force
   ```

   Ne fais pas cette suppression sur un ancien dossier contenant des templates
   personnalisés ; utilise ici exclusivement le clone neuf de l’étape 2.

5. Vérifier les commandes :

   ```powershell
   cd C:\mycode\Kristal\Spek
   python -m pip install -r requirements.txt
   python -m unittest discover -s tests -q
   python -m spek list-template-categories
   python -m spek list-wiki-templates
   git status --short
   ```

6. Examiner `git diff`, puis décider toi-même si tu veux créer un commit et pousser.
   **L’archive n’effectue aucun push.**

## Installation sans Git

Tu peux aussi simplement décompresser le ZIP sous `C:\mycode\Kristal` :
le code fonctionnera, mais le dossier ne disposera pas de son historique Git.
Dans ce cas, `GitSink.bat` ne pourra pas pousser tant que le dépôt Git n’aura pas
été rétabli.

## Organisation

```text
Spek/
  template_library/
    wiki/            (fonctionnel, 19 profils Arketype)
    educational/     (réservé)
    scientific/      (réservé)
    report/          (réservé)
    book/            (réservé)
  layouts/           (8 composants communs)
  spek/              (moteur Python et CLI)
  tests/
  docs/
  wiki/              (documentation de Spek, pas le Wiki public Kristal)
```

Les anciennes définitions de `wiki-templates/` ont été placées dans
`template_library/wiki/`. Aucun doublon n’est conservé à l’ancien emplacement.
Le code Spek ne publie pas de lui-même les Kristals ; les validations,
réalisations SemantiK et autorisations appartiennent au pipeline externe.

L’archive reprend les sources du ZIP fourni, ainsi que les fichiers `.github`
et `.gitignore` du snapshot correspondant à la révision GitHub vérifiée.
Le lanceur local `ZmartZnap.pyw` n’était pas présent dans le ZIP fourni :
le clonage GitHub proposé ci-dessus le récupérera si tu en as besoin.
