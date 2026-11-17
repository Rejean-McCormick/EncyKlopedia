# Identité visuelle et séparation des données — Spek (2026-11-02)

## Identité visuelle

- Couleur principale : `#1E6864` ; tons de support : `#154D4A` et `#E4F2EF`.
- Logo : `assets/spek-logo.svg` (source SVG fournie par l’utilisateur) et `assets/spek-logo.png` (déclinaison locale pour Tkinter). La forme du SVG est reproduite telle quelle, sans approximation picturale.
- Interface : le lanceur `Spek_Template_Manager.pyw` conserve le workflow et utilise des contrôles d’interface harmonisés. Les conseils de démarrage sont regroupés en une barre compacte et dans l’onglet « Guide pas à pas ».
- Documents : aperçu structurel local et sorties HTML, PDF, LaTeX de lecture reçoivent la couleur principale. Le SVG du logo est intégré à l’HTML sans lien vers un service externe.

## Separation de confidentialité et de publication

Les empreintes SHA-256 servent à vérifier les entrées **dans le moteur**, pas à informer le lecteur d’un aperçu. Elles ne doivent plus apparaître dans :

- Le bandeau et le code HTML de l’aperçu structurel.
- Le manifeste `inspection-manifest.json` associé à cet aperçu privé ; celui-ci garde un digest de la *page générée* pour contrôle interne, mais aucune empreinte de la source canonique.
- Les pages de lecture HTML, PDF et LaTeX générées par Spek.

Les empreintes et autres traces complètes peuvent toujours exister dans les entrées, le modèle documentaire machine lisible, les fichiers de contrôle du pipeline et les sources canoniques. Cette modification ne supprime ni n’affaiblit la vérification d’intégrité : une source différente continue d’être bloquée avant création de l’aperçu.

L’aperçu structurel garde les relations source sous un volet refermable, car il reste un outil **privé de travail**. Il n’y inscrit plus les identifiants d’assertion, positions de fichiers, statuts techniques, empreintes ou références de preuve brutes. Cela **ne rend pas** le fichier HTML publiable : les relations elles-mêmes peuvent être sensibles. Ne jamais copier cet aperçu dans le Wiki GitHub.

Les contenus destinés à publication exigent toujours les sélections éditoriales, les réalisations SemantiK et les contrôles C1/C2/C3.

## Tests et limites

Les tests de non-divulgation assurent l’absence de hash source et d’identifiants d’audit dans le HTML privé. Les contrôles de syntaxe, les tests Spek et la fenêtre Tk sous affichage simulé sont exécutés dans l’environnement de préparation. L’apparence sur Windows réel reste à confirmer sur le poste de l’utilisateur.
