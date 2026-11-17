# EncyKlopedia — Checklist obligatoire avant diagnostic, patch et publication documentaire

**Référence :** ENC-MAINT-2026-11-15/1.  
**Objet :** éviter de redécouvrir le projet à chaque conversation et de refaire des correctifs guidés par le seul nombre de postes occupés.

## Démarrage rapide d'un nouveau travail

1. **Lire d'abord** [guide opérationnel](10_GUIDE_OPERATIONNEL_LOCAL_V31.md), [données](11_DONNEES_ET_SAUVEGARDE_LOCALE_V31.md), [diagnostic](12_DIAGNOSTIC_COUVERTURE_ET_GOULOTS_V31.md) et les invariants des documents d'architecture `01..06`.
2. **Lire le module précis** et son test : `poste_chatgpt_v30.py`, `decouvrir_articles_relies_v28.py`, `production_kristals_v27.py`, scripts `.ps1`, contrats v25, modules de branches et états SQLite ; ne pas s'en tenir à la table des matières.
3. **Distinguer quatre états de vérité** : ce que prévoit la cible, ce qui existe dans un snapshot du code, ce qui est installé sur Windows (SHA), ce qui est observé dans les bases/dans les journaux.
4. **Demander des éléments nouveaux seulement si nécessaires** : dernier snapshot de code si les SHA ont changé, diagnostic JSON ciblé si une observation de base manque, log de déploiement. Ne pas faire traiter des dizaines de packs pour obtenir une information que peut fournir un audit en lecture seule.
5. **Fixer un diagnostic réfutable** : file vide, preuve gelée, parcours lexical terminé, candidats perdus par synchronisation, corpus inaccessible, alias incomplet, etc. Associer à chaque hypothèse une mesure et un test.
6. **Privilégier le rappel** : construire des candidats à provenance explicite, préserver les candidats non retenus, jamais inventer une citation ou un lien sémantique, laisser à ChatGPT les décisions APPROVE/REJECT/HOLD.
7. **Geler les preuves** : si un job UNESCO existe, les nouvelles découvertes doivent attendre. Les interventions de code ne changent ni les IDs ni les ZIP existants.
8. **Tester** SHA pré/post, installation et retour arrière sur copie, tests de reprise/idempotence, absence d'altération des sources, vérification des états v27/v28/v30. Signaler franchement les tests non exécutés ou échoués.
9. **Sauvegarder les résultats** avant code/migration à risque et conserver une copie sur un autre support. Les ZIP d'articles ne font pas partie de la sauvegarde légère choisie par l'utilisateur.
10. **Livrer un overlay vérifiable** pour le code et, dans le même correctif ou immédiatement après, actualiser ce guide, la matrice de versions, les tests et l'historique. Ne pas copier manuellement dans le dépôt si le mécanisme v30 est disponible.

## Règles de mise à jour de la documentation

- Un changelog historique ne suffit pas. Mettre à jour l'**index d'entrée**, les **contrats opérationnels**, la **matrice des versions vérifiées** et **ce qui reste inconnu**.
- Chaque constat porte son statut : **CIBLE**, **CODE VÉRIFIÉ**, **INSTALLATION CONFIRMÉE**, **OBSERVATION WINDOWS**, **HYPOTHÈSE**.
- Éviter les chiffres intemporels (p. ex. « il y a 7 700 articles ») sans date/source. Les totaux de production évoluent à chaque import.
- Lorsque l'interface garde une ancienne étiquette (`Production v30`), préciser explicitement le numéro du moteur modifié et le SHA attendu ; ne pas transformer le titre d'interface en preuve de version.
- Différencier les documents historiques v27/v28 des addenda `v31.x` ; **ne pas supprimer** l'historique de conception et les ADR non déployés.
- Si la version installée ne correspond plus à cette documentation, **indiquer l'écart**, obtenir les nouveaux SHA et réconcilier avant toute modification.

## Contrôle final d'une livraison documentaire

- [ ] Fichiers uniquement `.md`, `.txt` ou documentation permise : aucun code, aucune base SQLite.
- [ ] Liens internes résolus et noms de fichiers vérifiés.
- [ ] Manifeste `encyklopedia.safe-overlay.v30/1` avec SHA-256 et préconditions sur les fichiers modifiés.
- [ ] Installation et retour arrière vérifiés sur une copie isolée ; **installation Windows à confirmer par l'utilisateur**.
- [ ] Aucun document modifié par un patch logiciel plus récent sans le rebaser.
- [ ] Le prochain assistant peut décrire l'architecture et expliquer « 3/10 postes » **sans demander de nouveaux packs**.

## Références historiques conservées

- `docs/architecture/00_INDEX_ARCHITECTURE_V31.md` et `01..09` : vision cible, cartographie et décisions de conception.
- `docs/UNESCO_DECOUVERTE_ARTICLES_RELIES_V28.md` : mécanismes v28 et addenda du code installé.
- `docs/UNESCO_PRODUCTION_KRISTALS_V27.md` : contrat de données v27 avec addenda v31.8.
- `docs/POSTE_CHATGPT_V30_ARCHITECTURE.md` : station et contrôles d'import.
- `docs/historique_mises_a_jour/` : chronologie, **pas** l'état actuel du poste.
