# 14 — Réconciliation avec la documentation historique EncyK

Cette documentation **complète** le dossier `docs/v32/docs/` existant; elle ne remplace pas silencieusement les anciennes décisions techniques. Elle explicite ce qui a changé depuis les snapshots et l'archivage du prototype.

| Sujet | Ancienne documentation ou artefact | État opérationnel rapporté au 17/11/2026 | Décision documentaire |
|---|---|---|---|
| Nombre de branches | 87 autres branches après retrait de `mt1.10` dans la V5 | **88** dans le registre V32 après réintégration de la définition vierge de `mt1.10` | Écrire **88 actives, mt1.10 sans données V31 reprises**; `NEUF_87` reste nom historique de dossier |
| Branche 1 | V27/V28/V30 contiennent décisions/HOLD/packs historiques | Archivée dans `D:\EncyKlopedia_ARCHIVES\V31_UNESCO_MT1_10_20261116T202122Z_5614645f` | Ne pas réintroduire son ancien travail dans la nouvelle production |
| Moteur V32.2 source ZIP | `sources.py` décale P31→1e9; découverte d'abord QID | Station V6 a corrigé propriété + titres pour tous les concepts + V28/V31 | Annoter **source snapshot** vs **source Windows effectivement patchée**, ne pas prendre le ZIP comme dernier runtime |
| Taille des missions | V32.2 défaut 150 sélection / 60 articles ENR | V6 300 SEL / ENR cible ~45k mots, XXL isolés | Documenter l'adaptation V6 sans falsifier la valeur par défaut historique |
| Prompt d'enrichissement | V32.2 prompt plus court | V6 réutilise dossier de lecture V27 et protocole six passes V31.8 | Vérifier les prompts **dans chaque ZIP**; ne pas modifier les missions déjà émises |
| Capacités Skope | Index compact et modules d'extraction ciblée | Voisinage actif; extraction de déclarations originales non confirmée sur le D: vivant | Séparer preuve de disponibilité du **code** et preuve de disponibilité des **données** |
| Workflow Kristal | Certaines anciennes propositions évoquent des intégrations immédiates | Décision actuelle : cumul privé par branches et admission différée via Authoring Kit réel | Ne pas coder une admission automatique, ne pas traiter QID comme Kristal |
| Mesure d'avancement | Comptes de candidats/propositions | 2 460 paires, 10 606 propositions Météo lors du dernier journal fourni | Distinguer les **paires concept–article** des pages uniques; ne pas proclamer la branche achevée |

## Stratégie de coexistence documentaire

- Le point d'entrée de cette série est `docs/v32/docs/10_SYSTEME_MASSIF_20261117/00_INDEX.md` **après installation explicite**.
- Les docs `docs/v32/docs/00_INDEX.md`, README, AGENTS et autres références existantes restent intactes : elles sont des témoignages d'architecture/version à préserver.
- Si une instruction ancienne entre en conflit avec l'état actuel, le document de **version opérationnelle la plus récente et qualifiée** prévaut pour la station V6. Le code V32 réel reste l'arbitre des API; les chemins et fichiers Windows doivent être contrôlés sur le poste.
- Toute mise à jour future crée un addendum daté et des exemples de commandes testables au lieu de déplacer des vieux artefacts ou d'effacer leurs auteurs.

## Choses à ne surtout pas déduire

- « 88 branches » ne veut pas dire 88 Kristals physiques identiques à des QID.
- « 10 606 propositions » ne veut pas dire 10 606 faits validés scientifiquement ou admis.
- « PARTIAL » ne veut pas dire que le pack a échoué : les propositions valides sont déjà cumulées.
- « Fenêtre terminée » ne veut pas dire « toute la branche découverte ».
