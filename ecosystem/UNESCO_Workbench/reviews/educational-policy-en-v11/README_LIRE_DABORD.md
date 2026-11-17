# Revue des identités et des sources — Educational Policy (EN)

**Répertoire cible après extraction à la racine `C:\mycode\EncyKlopedia` :**
`UNESCO_Workbench\reviews\educational-policy-en-v11\`

Cet ensemble est **un dossier de revue uniquement**. Il ne remplace aucun des neuf fichiers issus de Kristalizer, ne modifie pas le Kristal actif ou candidat, ne valide pas de `exactMatch`, KA ou KS et ne publie rien.

## Ce que le scan a démontré

- Kristalizer `1.2.2`: **V11_ACTIF**, `migration_required=0`.
- **41** concepts UNESCO KQ provisoires, **36** candidats Wikidata QID, **5** sans candidat.
- **36 décisions `pending`**, **0** identité approuvée, **0** nouvelle assertion KA/KS.
- Le scanner est connecté à `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite`.
- Le rapport signale **0 fichier du catalogue de sources**, **Skope absent**, et **0 liaison d'assertion** : l'enrichissement documentaire n'a pas été exécuté par ce scan.
- La colonne `local_label` était vide pour les 36 candidats : ce paquet la complète **dans une copie séparée**, à partir des libellés anglais du dictionnaire v11 déjà fourni.

## Fichiers et usage

- `41_UNESCO_WIKIDATA_IDENTITY_REVIEW_EN.csv`: feuille principale. Les colonnes `editorial_decision`, `reviewer`, `evidence_locator`, `editorial_notes` sont volontairement **vides**. Ne pas importer directement dans Kristalizer.
- `36_SCAN_CANDIDATES_WITH_ENGLISH_LABELS.csv`: les résultats du scan enrichis avec le libellé anglais et l'ID UNESCO; aucune modification à `CANDIDATS.csv`.
- `09_PRIORITY_MANUAL_CHECKS_EN.csv`: cas à examiner avant tout lien exact, dont KQ26, KQ2, KQ17, KQ36.
- `05_WITHOUT_WIKIDATA_CANDIDATE_EN.csv`: cinq concepts qui nécessitent une recherche ciblée.
- `CONCEPT10_SIX_SOURCE_REVIEW_EN.csv`: six pistes de sources publiques déjà décrites dans le brouillon v11, avec localisateur et statut de vérification Web. Aucune capture de source SHA-256 ni KS canonique n'est fournie.
- `AUDIT_SUMMARY.json`: état et empreintes SHA-256 des neuf rapports entrants.
- `quality_gate.py`: contrôle **en lecture seule** la grille de revue; refuse de considérer une décision comme étayée si les justificatifs sont incomplets.

## Réserves et priorités

**KQ26 Global citizenship education → Q3595759 « international education »** : différence de sens manifeste entre les descriptions remises; éviter `exactMatch` sans preuve démontrant une équivalence. **KQ2 Educational policy → Q452348 « politique enseignante »** : vérifier s'il s'agit d'un usage d'étiquette particulier ou d'un concept plus étroit. **KQ17 Church and education** et **KQ36 Study abroad** : la description Wikidata paraît plus étroite que l'intitulé UNESCO. Ces alertes sont **éditoriales**, jamais des décisions automatiques.

Les cinq sans QID sont **Compulsory education (KQ18), Computer uses in education (KQ19), School closure (KQ39), Teacher policy (KQ40) et Multilingual education (KQ41)**. L'absence de candidat ne signifie pas qu'ils n'existent pas dans Wikidata.

## Première passe de contenu : Right to education / concept10 / KQ3

Les six références d'origine couvrent les normes internationales (DUDH art. 26, PIDESC art. 13, CDE art. 28, convention UNESCO de 1960), les obligations des États et les indicateurs SDG 4. Les pages officielles sont accessibles ou indexées; toutefois **une vérification de page n'est pas une preuve canonique archivée**. Avant toute KA/KS, capturer une version datée du texte/source, vérifier son intégrité, attribuer un localisateur précis, préciser territoire et période et faire approuver les formulations. Un énoncé de traité doit être limité aux États parties concernés et ne démontre pas à lui seul la mise en œuvre nationale.

## Prochaine étape sans reconstruire les 88 Kristals

Compléter d'abord les vérifications KQ26/KQ2/KQ17/KQ36, puis traiter KQ3 (Right to education) : saisir les six documents, assigner les références de preuve et construire les KA/KS candidates **dans un workspace v11 de travail soumis à l'Authoring Kit**. Répliquer la méthode aux autres concepts uniquement après qualification.

Le fichier `quality_gate.py` peut être exécuté depuis ce dossier avec `python quality_gate.py`. Il n'effectue aucune écriture.
