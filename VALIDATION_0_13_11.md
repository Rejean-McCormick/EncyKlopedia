# 0.13.11 — Scope géographique Skope

- Le Wizard 5 expose la région et la priorité QID, en mode annoté ou strict.
- Comptes calculés par SQLite indexé, sur les entités sélectionnées ; pas de généralisation géographique sans preuve.
- Liens des lieux P17/P131/P30 limités à deux sauts ; autres régions toujours classées inconnues si pas de signal.
- Export non canonique seulement, sans ingestion ni écriture dans le canon Kristal.
- Tests unitaires, smoke navigateur Chromium et validation du dépôt effectués avant livraison.
