# Spek — Atelier de publication et gestion de templates

**Lancement recommandé** : `OUVRIR_SPEK.cmd` ou `Spek_Template_Manager.pyw` (Windows + Python 3.10+, Tkinter). Ancien raccourci `OUVRIR_TEMPLATES.cmd` conservé comme alias.

Le parcours principal tient dans **Mon travail** : ouvrir explicitement un article Spek et son fichier de réalisations, vérifier avec le compilateur actuel et ouvrir un aperçu HTML privé. **Ouvrir un Kristal** affiche ses seules métadonnées déclarées, sans interpréter ni sélectionner de faits.

La bibliothèque à gauche comprend cinq catégories, les huit layouts partagés, les 19 profils Arketype, les 19 **compositions éditoriales IA** et le registre d'assignations. Sélectionner une composition en montre les sections ordonnées, les layouts et les obligations. Ce n'est pas un Wiki déjà rempli.

La gestion existe toujours en bas de l'arbre, **dans le contexte de l'élément sélectionné** : créer catégorie/gabarit, dupliquer, enregistrer, valider, supprimer un layout non référencé et ouvrir son dossier. L'édition brute se fait sous **Avancé · Éditeur JSON**. Les sauvegardes et la protection contre les modifications concurrentes sont conservées.

**Important** : Spek ne choisit pas les templates d'un Kristal; l'IA externe établit `kristal-assignments.json` à partir des preuves réelles. Le registre ne donne pas d'autorisation de publication. SemantiK Architect doit fournir les réalisations, et le Manager vérifier séparément les autorisations C1/C2/C3.

[Parcours, source des états et scénarios](ATELIER_OPTIMISE_IA_V2.md) · [Diagnostic Windows](TEMPLATE_MANAGER_DEMARRAGE.md)
