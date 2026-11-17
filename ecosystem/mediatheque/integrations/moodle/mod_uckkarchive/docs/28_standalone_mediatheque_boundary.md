# Médiathèque standalone ↔ Médiathèque UCKK

## Décision

Il existe deux implémentations distinctes :

1. **Médiathèque kOA standalone** — distribution vide; workspace privé optionnel; SQLite et filesystem local.
2. **Médiathèque UCKK (`mod_uckkarchive`)** — Moodle DB, Moodle File API, capabilities et surfaces UCKK.

Le workspace privé n'est pas une instance Moodle et UCKK n'ouvre jamais sa base SQLite.

## Interface

Le format natif d'export UCKK est `uckkarchive_export_v2`. Les échanges avec un système externe doivent rester des imports/exports explicites avec provenance, visibilité, droits et métadonnées de fichiers. Les octets privés locaux ne sont jamais publiés automatiquement.

## Autorités

- standalone/private: catalogue local et fichiers privés;
- UCKK: archive institutionnelle UCKK et permissions Moodle;
- Kristal/Kristall: autorité sémantique des structures Kristal;
- aucune des deux Médiathèques ne remplace l'autre.
