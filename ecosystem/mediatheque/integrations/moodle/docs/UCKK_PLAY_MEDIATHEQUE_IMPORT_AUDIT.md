# UCKK Médiathèque — import du catalogue /play

## Statut

Les cinq inventaires `/play` sont maintenant **embarqués dans le snapshot UCKK** sous `data/play_inventory/` et constituent la source d’import reproductible pour les références externes de la Médiathèque.

Le runtime public reste gouverné par `mod_uckkarchive` et sa base Moodle. Les fichiers JSON ne court-circuitent pas les règles de visibilité, droits, advisories ou bridges. Ils alimentent le runtime uniquement via `tools/Import-UckkPlayExternalRefs.ps1`.

## Inventaire importable

| Catalogue | Références |
|---|---:|
| YouTube | 66 |
| Articles / livres / PhilPapers | 41 |
| Spotify + SoundCloud | 11 |
| GitHub / code-tech | 11 |
| **Total** | **129** |

Répartition plateforme : `amazon` 5, `github` 11, `medium` 31, `philpapers` 5, `soundcloud` 3, `spotify` 8, `youtube` 66.

Contrôles de l’inventaire embarqué : **0 ID dupliqué, 0 URL dupliquée, 0 entrée sans titre ou URL**.

## Collections YouTube reconnues

| Clé | Libellé | Éléments | Playlist |
|---|---|---:|---|
| `barok` | Barok | 6 | https://www.youtube.com/playlist?list=PLLBzJ-PjZQP50-11EWP3XovVtiKbAMCKH |
| `knowledge_pact` | The Knowledge Pact | 7 | https://www.youtube.com/playlist?list=PLLBzJ-PjZQP5ByokC3BYBsLIIzn21Ltaw |
| `pi_etherisme_cosmique` | Pi, fondement de l’Éthérisme Cosmique | 8 | https://www.youtube.com/playlist?list=PLLBzJ-PjZQP5lXDSA1hynNsolC-jBrwuc |
| `raoul_et_colin` | Raoul et Colin | 10 | https://www.youtube.com/playlist?list=PLLBzJ-PjZQP5CUAl3pysrTjPhi5FJFU77 |
| `le_rire_cosmique` | Le Rire Cosmique | 11 | https://www.youtube.com/playlist?list=PLLBzJ-PjZQP4q3ZE8Nt3qttQqlAvnHTfT |
| `pohenecoco_crepuscule_des_masques` | Pohénécoco et le Crépuscule des Masques | 8 | https://www.youtube.com/playlist?list=PLLBzJ-PjZQP5dzwoekUIEIbDJnMaCiFcb |
| `rap_konscient` | Rap Konscient | 13 | https://www.youtube.com/playlist?list=PLLBzJ-PjZQP6YMA4wDzL_wmTZfiXdofrt |

## Audio reconnu

Spotify : **8 références** (1 show + 7 épisodes). SoundCloud : **3 sets** (`Le Ninja Arc-en-Ciel`, `Lumière Blanche`, `Le Rire Cosmique`).

## Import

Dry-run avec les catalogues embarqués :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\Import-UckkPlayExternalRefs.ps1 `
  -MoodleRoot "C:\mycode\UCKK\moodle\moodle\public" `
  -OutputDir "C:\mycode\UCKK\uckk-play-import-check"
```

Application explicite :

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\Import-UckkPlayExternalRefs.ps1 `
  -MoodleRoot "C:\mycode\UCKK\moodle\moodle\public" `
  -OutputDir "C:\mycode\UCKK\uckk-play-import-check" `
  -Apply
```

`-SourceDir` reste disponible pour remplacer temporairement le catalogue embarqué.

## Contrat d’import

L’importeur crée ou met à jour des `external_work`, `media`, `media_source`, tags et collections. Les médias tiers **ne sont pas téléchargés ni copiés** dans Moodle : seuls les liens et métadonnées sont enregistrés. Les métadonnées `/play` originales sont conservées pour provenance et idempotence.

## Fichiers ajoutés / modifiés

- `data/play_inventory/inventory.root.json`
- `data/play_inventory/inventory.youtube.catalog.json`
- `data/play_inventory/inventory.articles.catalog.json`
- `data/play_inventory/inventory.audio.catalog.json`
- `data/play_inventory/inventory.code-tech.catalog.json`
- `data/play_inventory/inventory.manifest.json`
- `data/play_inventory/uckk_play_reference_registry.json` (index dérivé d’audit, non autorité runtime)
- `tools/Import-UckkPlayExternalRefs.ps1`
- `tools/Import-UckkPlayExternalRefs.final-working.ps1`
- `docs/README_import_uckkarchive_media.md`
- `UCKK_PLAY_MEDIATHEQUE_IMPORT_AUDIT.md`

## Limite du snapshot

Un SmartSnap contient le code et les registres, **pas la base Moodle déployée**. L’inventaire est donc prêt et intégré au mécanisme d’import, mais le passage effectif des 129 références dans la DB de production exige l’exécution avec `-Apply` sur l’instance UCKK.
