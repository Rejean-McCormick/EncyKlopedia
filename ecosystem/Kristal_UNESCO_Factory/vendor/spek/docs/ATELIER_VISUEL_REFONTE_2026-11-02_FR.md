# Spek — Atelier visuel (refonte opérateur)

## Démarrage

Le lancement normal `START_SPEK.bat`, `OUVRIR_SPEK.cmd` ou `Spek_Template_Manager.pyw` ouvre maintenant un atelier centré sur le Kristal. L'ancien gestionnaire de templates, avec ses 27 layouts, les archétypes et l'éditeur JSON, reste accessible par **Outils avancés**, ou en lançant `Spek_Template_Manager.pyw --advanced`.

## Quatre espaces

1. **Kristal** : choisir un Kristal dans les 127 propositions, filtrer la liste, ouvrir une source locale en lecture seule. La consultation du catalogue ne prouve pas la présence d'une source locale.
2. **Composition** : examiner le plan explicitement fourni par le registre IA. Aucune règle de classification ou de sélection automatique n'a été introduite.
3. **Aperçu Wiki** : ouvrir une inspection structurelle privée uniquement si le Kristal local correspond à un des états canoniques revus ; charger un `article.json` et des `realizations.json` ou importer les résultats SemantiK explicites pour vérifier et prévisualiser un rendu HTML local.
4. **Publication** : comprendre les étapes restant à qualifier. Les validations C1/C2/C3, l'authenticité du RuntimeSet et l'autorisation de publication restent extérieures à Spek.

## Sécurité et confidentialité

- L'accueil ne montre ni empreintes SHA-256, ni références d'assertions ou chemins absolus, ni détails des JSON et contrats internes.
- La vue **Outils avancés** conserve l'accès technique déjà existant : elle n'est pas une vue de publication.
- L'inspection structurelle génère un brouillon privé, pas une page publique.
- Les formulaires de correspondance SemantiK sont remplis explicitement ; Spek ne fabrique ni faits ni traductions.
- Aucune fonction de publication ou d'écriture sur les dossiers `locals/` n'est ajoutée.

## Raccourcis

Ctrl+O : ouvrir un Kristal ; Ctrl+L : charger un article ; F5 : actualiser le catalogue ; F1 : aide.

## Limites

Seuls les cinq Kristals dont l'analyse canonique a été réellement produite disposent de l'inspection source approfondie, sous réserve de correspondance des octets du snapshot étudié. Les 122 autres ont des propositions issues du rapport Manager, non qualifiées. Une paire article + réalisations SemantiK est requise pour le rendu éditorial ; cet atelier ne la génère pas à partir du seul dossier Kristal.
