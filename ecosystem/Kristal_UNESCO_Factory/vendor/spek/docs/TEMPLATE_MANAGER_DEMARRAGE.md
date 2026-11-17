# Démarrage du gestionnaire Spek sur Windows

Le lanceur est `Spek_Template_Manager.pyw` à la racine du dépôt Spek. Il requiert **Python 3.10 ou plus récent**, avec **Tkinter** (habituellement inclus dans l'installation Python pour Windows).

## Si un double-clic ne montre aucune fenêtre

1. Place `Spek_Template_Manager.pyw` à la racine de `C:\mycode\Kristal\Spek`, ou utilise le sélecteur de dépôt qu'il affiche.
2. Double-clique `OUVRIR_TEMPLATES.cmd` pour voir les éventuelles erreurs dans une console. Cette commande conserve la fenêtre ouverte jusqu'à la fermeture de l'application.
3. Lance `DIAGNOSTIC_TEMPLATES.cmd` : il confirme le dépôt sélectionné et le nombre de catégories, de layouts et de profils.
4. Si cela échoue, ouvre `%LOCALAPPDATA%\Spek\TemplateManager\launcher-errors.log` et conserve son contenu pour le diagnostic.

Tu peux également lancer dans PowerShell :

```powershell
cd C:\mycode\Kristal\Spek
py -3 .\Spek_Template_Manager.pyw --diagnostic
py -3 .\Spek_Template_Manager.pyw
```

## Installation du correctif

Le ZIP correctif est organisé **par rapport à la racine Spek** (il ne contient pas de sous-dossier `Spek/`). Extraire directement dans `C:\mycode\Kristal\Spek` et accepter le remplacement des fichiers.

Si tu utilises le ZIP du dépôt complet, son contenu est sous `Spek/` : extraire dans `C:\mycode\Kristal` ou par-dessus un clone dans ce répertoire. Ne supprime pas `.git` pour appliquer un correctif.

## Comportement

Le lanceur détecte désormais aussi le dépôt dans `C:\mycode\Kristal\Spek` lorsqu'il est exécuté depuis le dossier Téléchargements. En cas d'erreur d'import, de Python incompatible ou d'échec Tkinter, il crée un journal et tente d'afficher une erreur Windows. Il ne publie rien sur Internet.
