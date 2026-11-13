# EncyKlopedia V31.1.1 — Correctif de fermeture SQLite sous Windows

## Incident vérifié

L'installation V31.1 copiait le code, puis exécutait les tests. Sur Windows, 6 tests
sur 14 échouaient à la suppression des dossiers temporaires avec `WinError 32` :
`cache.sqlite`, `wiki.sqlite`, `source.sqlite`, `qual.sqlite`, ou la base v28 de découverte.
**Il ne s'agissait pas d'un échec d'écriture sur les énormes bases de production.**

## Cause

En Python, `with sqlite3.connect(...) as conn:` gère la transaction mais **ne ferme pas**
la connexion SQLite. Sous Windows, la suppression d'un fichier encore ouvert est refusée.
Les tests laissaient donc des connexions actives au moment du nettoyage `TemporaryDirectory`.
Trois chemins de lecture de production partageaient également ce problème :
`preuves_xml_v31.read_targets`, `piloter_branches_v311.readable_jobs/run`,
et `contexte_revue_unesco_v28._concepts`.

## Correctif cumulatif

* Fermeture explicite des connexions des 4 modules de tests, avec maintien du commit/rollback.
* Fermeture explicite des connexions de lecture SQLite des trois modules de production.
* Trois tests de régression vérifiant réellement le `close()` sur succès et refus.
* Installation V31.1.1 possible par-dessus le code V31.1 déjà copié sur le poste.
* Aucune transformation des bases, aucun nouveau format de tâche, aucune modification de preuves.

## Validations effectuées

17 tests V31/V31.1/V31.1.1 réussis sur Python/Linux, avec fichiers SQLite temporaires.
Instrumentation complémentaire sur les 14 tests initiaux : 65 connexions ouvertes,
65 explicitement fermées. La validation Windows sera faite lors de l'installation utilisateur.

## Limites

Ce correctif cible les erreurs WinError 32 du journal d'installation transmis. Il n'est pas
un audit de toutes les opérations des énormes bases SQLite, ni une garantie qu'aucune
interférence externe (antivirus, processus tiers) ne puisse jamais verrouiller un fichier.
