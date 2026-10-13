# Cleaner D: v0.13.6 — Conservation de Wikidata et des données traitées

## Décision

L'utilisateur veut conserver toutes les données déjà tirées, extraites, enrichies et formatées depuis Wikidata. **Les appeler « historiques » ne signifie PAS qu'elles sont supprimables.** Ce cleaner ne supprime donc jamais le pilote ni les 533 œuvres candidates. L'option de purge du pilote présente en v0.13.5 a été retirée.

## Conserver impérativement

- `D:\EncyKlopedia\10_sources` — dumps Wikidata et lexicaux ;
- `D:\EncyKlopedia\30_working` — index compact SQLite, index QID rapide, bases lexicales, scopes et graphes ;
- `20_ingest/daat-handoff`, `20_ingest/scope-snapshots`, leurs manifestes, JSONL/GZ et provenance ;
- `50_mediatheque/catalog/candidates`, notamment `*.works.jsonl` : 533 œuvres candidates ;
- les fichiers actuellement présents dans `40_kristal` ainsi que tout fichier inconnu/modifié.

Ces données restent à leur emplacement actuel tant qu'un contrat explicite ne prévoit pas une migration préservant les dépendances.

## Opérations autorisées

Seuls quatre fichiers de métadonnées peuvent être repositionnés sans modification du contenu :

1. `20_ingest/checkpoints/wikidata-index-state.json` → `90_runtime/checkpoints/wikidata-index-state.json` ;
2. `20_ingest/manifests/wikidata-dump-verified.json` → `20_evidence/manifests/wikidata-dump-verified.json` ;
3. `20_ingest/manifests/wikidata-lexemes-fr-en-sq.json` → `20_evidence/manifests/wikidata-lexemes-fr-en-sq.json` ;
4. `20_ingest/snapshots/wikidata/latest.json` → `20_evidence/acquisition-snapshots/wikidata/latest.json`.

Les fichiers **strictement identiques** créés par l'ancien outil dans `20_evidence/legacy-ingest` peuvent être effacés **uniquement si l'original ou la métadonnée déplacée existe encore avec la même empreinte SHA-256**. Si la copie est seule, on la garde. Aucun dossier de sauvegarde ou archive n'est généré.

## Utilisation

1. **Ne pas utiliser** `Nettoyer_Donnees_EncyK.pyw` v0.13.5 ou les versions précédentes pour nettoyer D:.
2. Fermer les outils EncyK/Skope qui écrivent dans le disque.
3. Utiliser `Nettoyer_Donnees_EncyK.pyw` de **v0.13.6** (dans le dépôt de code sur C:) ou son exécutable autonome `.pyw`.
4. Cliquer sur **Analyser** et vérifier les deux compteurs : déplacements de métadonnées et copies identiques.
5. Cliquer sur **Replacer / nettoyer les copies** puis confirmer en saisissant `VALIDER`.

Le nettoyeur refuse les jonctions/redirections dans les zones ciblées et les fichiers non conformes. La comparaison SHA-256 ne constitue pas une sauvegarde : aucun retour arrière automatique n'est garanti après exécution. Ces opérations ont été testées dans des dossiers simulés, pas sur le D: réel.
