# Sources de cette étude : provenance des ZIP et limite de conservation

La documentation a été créée **après lecture du contenu**, non à partir des seuls noms de fichiers. Les sources avaient été fournies dans la même conversation et extraites dans un environnement d'audit éphémère. Les chemins de travail de cette analyse ne sont pas des chemins de production.

## Grandes sources de code/données examinées

| Archive/famille fournie | Contenu effectivement utilisé pour la documentation |
|---|---|
| `SmartDump_20261115_173446.zip` | Plusieurs ensembles : `EncyKlopedia`, `UNESCO_Kristals`, `Kristal_UNESCO_Factory`, `UNESCO_Workbench`, `LinkedDataHub-UNESCO`, `mediatheque-references`, `mediatheque`, `LevelUpDiag_EncyK`, `scan_engine`, `scan_test` |
| `znapshot_EncyKlopedia_11151207.zip` et snapshots ultérieurs de source | Architecture, pilotes v25/v27/v28/v30/v31.x, tests et code du lecteur |
| `znapshot_Skope_11151714.zip` (deux copies identiques selon l'audit antérieur) | `Skope/skope/db.py`, `Skope/skope/extraction.py`, index compact et contrat de lecture |
| `ENCYK_CENTRE_PILOTAGE_V313_Code_snapshot.zip` | UI V313/V314, audit, stats et triage |
| `EncykAudit_Code_snapshot.zip` | Audit v31.2/GUI et scénario d'automatisation |
| `ENCYKLOPEDIA_EXPORT_CHATGPT_Code_snapshot.zip` | Exporteur de diagnostic et contexte pour ChatGPT |
| `OUTIL_AUDIT_GOULOTS_ENCYKLOPEDIA_V3110_Code_snapshot.zip` | Diagnostic source/filtre/station/découverte et limites |
| `OUTIL_SAUVEGARDE_RESULTATS_ENCYKLOPEDIA_V2_Code_snapshot.zip` et V3 corrigée | Routines de sauvegarde du stock résultat SQL |
| `PACK_V27_000289.zip` et `RETOUR_KRISTAL_PACK_V27_000289.zip` | Exemple de format d'une mission volumineuse et de son delta structuré |
| `guide-architecture-interfaces-ia-v2(1).zip` | `AI_INGESTION.md` et matrice UX-01…UX-18 |
| `senior-architecture-patterns.zip` | Patrons 31, 10, 08, 15, 02, 04, 29; ceux non pertinents sont explicitement exclus |

## Ce qui n'a pas été transféré dans ce ZIP documentaire

- Aucun dépôt source complet : ce dossier est la **documentation avant déplacement de code**.
- Aucune base SQL de production, aucun dump Wikipédia/Wikidata, aucun XML géant, aucun pack utilisateur source.
- Aucune copie de Skope ni de Kristalizer, même pour « faciliter » le méga-repo.
- Aucun token, clé, profil personnel ni état de compte.

## Politique de révision de cette documentation

Lorsque le futur code V32 remplace une fonction, actualiser le propriétaire dans `docs/01_ECOSYSTEME/02_MATRICE_REEMPLOI.md` et, au besoin, le statut dans `docs/08_REFERENCES/01_PREUVES_ET_STATUTS.md`. Les inventaires CSV sont **des photos historiques** : ne pas les traiter comme un cache synchronisé de tous les futurs commits. Une nouvelle extraction simple peut les régénérer lorsque nécessaire; elle ne doit pas bloquer une fonctionnalité par une signature de fichier.

## Limite de portée

Cette étude est une cartographie architecturale solide du **code et des données de référence fournis**. Elle n'est pas un test end-to-end de V32, encore inexistant, ni une certification de l'état live des gros index Windows. Les valeurs de taille et de fraîcheur des sources réelles doivent être vérifiées sur le poste lors du premier prototype, sans refaire les imports géants.
