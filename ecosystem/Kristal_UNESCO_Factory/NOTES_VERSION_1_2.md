# Kristal UNESCO Factory v1.2 — Correction des conclusions et audit

## Constat sur l'exécution de l'utilisateur (2026-11-02)

- L'inventaire UNESCO est valide : 4 500 concepts, 88 microthésaurus, 7 domaines, SHA-256 source `fa78145d189776bfb97e1635200060012b853684b9f7d542d41804c37c5178c3`.
- 88 kristals v9 candidats et 88 volumes Spek ont été produits. Le total des sections est égal à 4 500.
- 4 289 concepts ont un QID P3916 candidat unique, 134 sont ambigus, 77 sans P3916. Un des 4 289 QID candidats n'est pas présent dans l'index SQLite local. L'export contient 4 lignes invalides et 1 identifiant hors du thésaurus courant.
- Les avertissements Kit concernant les métadonnées dérivées précèdent des états v9 construits ; leur présence ne prouve pas une erreur de construction, mais la validation de vérité/qualification n'est pas faite.
- Le rapport v1.1 disait `wikidata_mapping_complete: true` alors que la jointure ne couvre pas tous les concepts. Ce booléen signifiait en réalité « export CSV présent » : correction v1.2.

## Correctifs

1. `mapping_quality` dans `RAPPORT_FINAL.json`, avec chiffres complets et couverture (la présence de source n'est pas confondue avec la résolution d'identités).
2. `wikidata_mapping_complete` n'est vrai que si tous les concepts ont un candidat unique, sans ambiguïté, sans absence ni anomalie d'export. Cela ne signifie toujours PAS une qualification sémantique.
3. `06_AUDIT/audit_p3916.html`: tableau navigable de chaque concept, QID candidats, provenance UNESCO, état local, recherche et filtres. Liens vers fichiers bruts et Spek.
4. Bouton **Ouvrir audit** dans l'application. Le catalogue Spek contient également un accès direct à l'audit.
5. `PYTHONIOENCODING=utf-8` dans les sous-processus pour réduire les caractères corrompus dans les journaux Windows.
6. Vérification stricte de l'égalité entre le nombre de concepts UNESCO et le nombre de sections Spek produites (pas seulement >=).
7. Tests de régression pour le cas P3916 ambigu et le cas avec concept sans correspondance.

## Frontières inchangées

La fabrique produit un aperçu de concepts UNESCO, **pas** 4 500 articles encyclopédiques rédigés. Aucune importation de toutes les assertions de Wikidata, génération GF qualifiée, promotion canonique des rapprochements ou publication n'est implémentée. L'IA locale est facultative, reste hors canon et n'a pas été exécutée lors de l'essai transmis.
