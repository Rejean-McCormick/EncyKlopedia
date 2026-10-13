# EncyK 0.13.3 — Validation de la séparation code et données

Base : snapshot `znapshot_EncyKlopedia_10131257.zip`, avec la fixture Skope `demo.wikidata.jsonl` restaurée depuis l'archive consolidée 0.13.1.

- Révision : `VERSION`, `MANIFEST.json`, baseline et schéma handoff acceptent `0.13.3`.
- `configure_data_on_D.ps1` : aperçu par défaut, le dossier du script comme racine de code, jonctions uniquement ; refus des répertoires locaux non vides et des redirections inattendues.
- Cleaner D: : tests de copie hashée, immutabilité des originaux, conflits, refus de liens, refus de contenus inconnus dans `40_kristal`, audit sans écriture.
- Données existantes protégées : aucun déplacement ni effacement des SQLite, dumps, index lexicaux, historique 20_ingest et catalogue 50_mediatheque.
- Les fichiers de référence auparavant placés dans `20_evidence/` sont conservés sous `docs/historical-data-manifests/`; les README de zones sont déplacés sous `docs/historical-zone-readmes/`.

**Tests dans l'environnement de préparation : 30 tests pytest réussis et validateur EncyK PASS.**

**Non testé sur le PC cible :** opérations de jonction avec PowerShell 7/Windows, interface Tkinter avec affichage natif, lecture du SQLite de 125 Gio et état effectif de l'index Wikidata. Le `.pyw` ne doit pas être considéré comme une migration complète vers les contrats Kristal ou Médiathèque.
