# Frontière des instances UCKK / Math

UCKK et Université Math sont des **instances** du même concept Médiathèque, pas deux Engines.

- Engine partagé : `../mediatheque/`.
- Adapter Moodle partagé : `../mediatheque/integrations/moodle/mod_uckkarchive/`.
- Instance UCKK : `../mediatheque-uckk/`, `sitekey = "uckk"`.
- Instance Université Math : `../mediatheque-universite-math/`, `sitekey = "math"`.
- Les données restent dans leur backend Moodle respectif; elles ne sont pas copiées dans l’Engine.
- L’instance privée locale reste filesystem + SQLite et ne partage pas sa DB avec Moodle.
- Les échanges restent explicites et auditables.
