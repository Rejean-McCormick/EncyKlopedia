# Installer le correctif identité et confidentialité

1. Fermer Spek.
2. Préserver tout changement local non commité (`git status`).
3. Extraire le ZIP correctif dans le **dossier parent** du dépôt Spek :
   `C:\mycode\Spek_Semantic-publishing` dans le poste montré précédemment.
4. Vérifier que les fichiers sont sous `Spek/assets/` et `Spek/spek/`, sans sous-dossier `Spek/Spek`.
5. Relancer `Spek/Spek_Template_Manager.pyw` ou `Spek/START_SPEK.bat`.
6. Ouvrir Agriculture, puis « Voir l’aperçu structurel privé ».

Pour vérifier le moteur, à partir du dossier Spek :

```powershell
py -3 -m unittest discover -s tests -q
```

Les aperçus **déjà générés** sont des fichiers statiques et ne changent pas
quand le logiciel est mis à jour. Regénérer les aperçus concernés et supprimer
ou archiver les anciennes copies contenant les empreintes, selon vos règles
de conservation. Le correctif ne supprime aucun fichier utilisateur.

Aucune publication GitHub, aucun changement dans `locals` et aucun contournement
C1/C2/C3 ne font partie de cette installation.
