# EncyKlopedia v31.6 — Mode Synthèse ×5

## But

Réduire **les interventions humaines** sans prétendre à une lecture exhaustive de Wikipédia. Les 10 conversations continuent à traiter des packs autonomes, et un seul ZIP de retour est attendu par tâche.

## Configuration des futurs packs Kristal

- Maximum : **120 articles** (au lieu de 24).
- Budget : **400 000 mots** (au lieu de 80 000).
- Budget texte brut : **60 MiB** (au lieu de 12 MiB).
- Le moteur v27 accepte 120 articles, sans changer son contrat, ses identifiants, son schéma SQL ou ses règles d'import.
- Un article seul dépassant une limite continue à être transmis sans troncature, conformément à l'ancien contrat.
- Le ZIP garde **tous les wikitexts complets et SHA-256**. Le dossier `DOSSIER_PRIORITAIRE_KRISTAL_V316.jsonl` ajoute des extraits exacts pour la navigation, non pas une source nouvelle.

## Stratégie documentaire

Une bonne encyclopédie de synthèse conserve : définition, importance, événements, dates et relations structurants. Elle n'a pas vocation à copier les listes complètes de Wikipédia. Les citations courtes restent obligatoirement présentes dans le texte original et les connaissances restent candidates et privées. Aucun article ne disparaît du manifeste ou du bilan de couverture lorsqu'il n'a pas de fait retenu.

Les extraits dans le dossier de lecture sont construits par un algorithme déterministe sur le wikitext et ne remplacent pas une analyse sémantique. Les grands packs ne garantissent pas l'examen de 400 000 mots par un modèle en une seule fenêtre de contexte; ChatGPT doit exploiter les fichiers pour travailler par article sans demander de sous-tâches humaines.

## Opérations et sécurité

- Installer uniquement via **Mises à jour logicielles** après prévalidation, confirmation explicite et sauvegarde de la station.
- **Ne pas** déposer ce ZIP dans **Retours encyclopédiques**.
- Les nouveaux paramètres ne concernent que les futurs packs. Les anciennes tâches, ZIP, preuves UNESCO et bases SQLite sont inchangés.
- UNESCO v28 conserve 880 propositions et le gel des preuves.
- Si une précondition SHA-256 échoue, ne pas forcer : le code local est différent du snapshot.

## Vérifications

Tester `python -m unittest discover -s tests -p 'test_kristal_synthese_v316.py' -v` et les tests historiques v27 / station. Les tests ont été exécutés sur le code extrait du snapshot, pas sur la base Windows de production.
