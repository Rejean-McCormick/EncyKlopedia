# EncyKlopedia v27 — Nouveaux Kristals 084–088

## Résultat de la sélection

- 5 packs source, 85 articles distincts (13 + 15 + 24 + 24 + 9).
- 203 connaissances candidates extraites et conservées après révision éditoriale.
- Les liens UNESCO ne sont inscrits que lorsqu’un passage de l’article les motive; certaines connaissances ont des concepts vides.
- Certaines assertions décrivent des jugements historiques : aucune conclusion juridique actuelle n'en découle.
- Source Wikipédia : identifiants de page, révision et section conservés; les citations sont des extraits facultatifs.
- Les textes Wikipédia des packs d'origine sont intacts; la sélection n'est pas exhaustive et n'est pas une vérification indépendante.

## Validation technique effectuée

- SHA256 des 5 packs source vérifiés contre les journaux utilisateur.
- Les 5 deltas ont passé le validateur et l'importeur v27 réel.
- Tests sur une base SQLite privée temporaire : 203 claims uniques, 203 citations, 85 visites d'articles et 5 deltas importés.
- Une deuxième importation n'a introduit aucun doublon.
- Aucun accès en écriture au catalogue, à Wikipedia, ou au Kristal canonique.

## Importation locale

Décompresser le ZIP dans la racine `C:\mycode\EncyKlopedia\EncyKlopedia` puis lancer :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\IMPORTER_DELTAS_KRISTAL_V27_084_088.ps1"
```

Le script vérifie les empreintes, copie les deltas dans `D:\EncyKlopedia\30_working\production_kristals_v27\deltas`, lance les 5 imports privés et affiche le statut. Il refuse toute collision avec un delta différent déjà présent.

## Résultat attendu si la base antérieure reste inchangée

- Articles visités : 1 134
- Claims et citations : 3457
- Deltas importés : 88
- Admissions canoniques : 0
