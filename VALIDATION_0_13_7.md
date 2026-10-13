# Validation v0.13.7 — sélection de Kristal / Skope

- Lanceur EncyK : sélection explicite de `kristal.workspace.json`, scanner local limité aux enfants de `C:\mycode\Kristal\locals` ou `KRISTAL_LOCALS_ROOT`.
- Par défaut sur Windows : index `D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite`, si présent.
- Pour `Kristal-Botany` : guide Arketype PRF-03 dans `00_system/tools/skope/config/arketype/botany.scope-guidance.json` et amorce `Embryophyta`, sans déduire un QID.
- Export Skope : attache `review/target-kristal.json`, aucune modification canonique, aucune copie de données à partir de D:.
- Bouton Kit : `check` lecture seule ; `build-discovery` exige un clic et une confirmation, écrit uniquement les données non canoniques via le Kit.
- Vérifications locales : suite Skope (14 tests), Scope Builder (5 tests), validation `validate_repo.py` et syntaxe JS.
- Limite : interface Windows et exécution contre le vrai index de 125 Gio non testées dans ce conteneur.
