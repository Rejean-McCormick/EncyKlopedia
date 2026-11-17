# Qualification v11 — Kristal Authoring Kit 4.0.0-draft.2

- Baseline : snapshot complet 4.0.0-draft.1, plus les 14 artefacts v9 du ZIP `authkit.zip` dont 13 étaient absents. Aucun conflit de contenu détecté sur le fichier déjà présent.
- Source normative : Kristal Framework `11.0.0-draft.3`, vérifié avec le pin **identique à l'Integration Pack 0.2.0-alpha.1**.
- Nouveau vérificateur : `tools/kristal.py qualify-v11` ou `scripts/qualify_framework_v11.py`, pure lecture, sans réseau.
- Validations : véritables schémas/validateurs du Framework, audit d'intégrité lexical, couverture diK comparée, comparaison avec Integration Pack, rejet du Framework altéré.
- Les anciens graphes ne sont pas réécrits ; plans diK relus et approuvés restent obligatoires pour toute migration.
- LIMITES : journalisation crash-safe multi-fichier à finaliser ; migration des modèles anciens arbitraires absente ; qualification réseau/Konstellation et performances de 300 langues non réalisées.

Les résultats de test détaillés sont conservés dans les journaux de cette livraison. Cette version est une **candidate locale draft.2**, pas une certification finale ni une modification GitHub.

## Exécutions attestées dans cet environnement

- `tests.test_v11_qualification`: **3/3 réussis** avec `KRISTAL_FRAMEWORK_ROOT` et `KRISTAL_INTEGRATION_PACK_ROOT` définis (rapport d'égalité avec Framework/Pack, test de pin, refus d'une modification SHA).
- `tests.test_v11_authoring.V11Authoring.test_opt_in_and_build_preserves_legacy_contracts`: **réussi**, incluant `build-v9` d'un nouveau workspace v11 et rapport direct/repli.
- CLI `check` sur les quatre exemples fournis (`demo-open`, `demo-v9-small`, `demo-hosted-v10`, `demo-semantic-v11`) : **4/4 réussis**.
- Rejet des labels Wikidata dont le `exactMatch` n'est pas accepté : **réussi**.
- Test de corruption de dictionnaire et reste des anciennes suites : **non conclus dans cette exécution**, limite de temps atteinte. La qualification complète et les tests de migration doivent être relancés en CI avant tout statut stable.
