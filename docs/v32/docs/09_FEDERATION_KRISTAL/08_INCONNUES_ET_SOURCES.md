# Inconnues, preuves et sources à récupérer avant les adaptateurs

## Ce qui est directement établi dans les snapshots EncyK déjà fournis

- 88 branches UNESCO, 4 500 fiches de concepts, 4 289 QID candidats uniques, 134 ambiguïtés et 77 sans P3916, selon les inventaires de `UNESCO_Kristals`.
- `wiki_qid` est construit/consulté par les modules Wikipédia/v25; le taux de jointure dans l'index réel de D: reste **inconnu**.
- Le moteur historique a des packs persistants, dix lanes, validations/retours ZIP, import cumulatif; la conception V32.1 vise à réemployer ces fonctions.
- Skope fournit des index Wikidata locaux et une extraction ciblée, mais est une dépendance extérieure à ne pas modifier.

## Ce qui est **rapporté**, pas revalidé dans ce paquet

La décision d'architecture remise le 16 novembre décrit Framework v11, Authoring Kit, Integration Pack, Arketype, Manager, Kompiler, KristalDiag, LOT-K50 et Kristal-Wikidata-Workflow. Elle mentionne des qualifications de deux îlots Education/Soil, des pins Kit–Pack et des vérifications d'intégrité antérieures. **Les archives contenant ces dépôts et états ne sont pas incluses dans le SmartDump EncyK fourni dans cette conversation.** Il faut les relire avant de choisir des symboles API, opérations d'auteur, formats ou engagements de compatibilité.

## Mesures strictement utiles, sans gros chantier de vérification

| Question | Où répondre | Décision éclairée |
|---|---|---|
| Combien des 4 289 QID trouvent une page `enwiki` ? | `wiki_qid` local sur D: | Volume réel de candidats directs par branche |
| Quelles propriétés Wikidata sont indexées et rentables ? | Skope compact + échantillon | Expansion 1–2 sauts ciblée, éviter bruit |
| Quels îlots sont réels et quelles copies sont historiques ? | Inventaire Manager + workspaces | Dédoublonner et lister les capacités |
| Quelle API d'auteur Kit est réellement supportée ? | Dépôts Framework + Kit + Pack | Lot C, sans fonction inventée |
| Les snapshots parents épinglent-ils leurs enfants comme prévu ? | Référence Framework + fixture | Lot D |
| Kompiler reconstruit-il des vues disproportionnées ? | `kristal_v11.py` + benchmark | Projection sélective si le gain est réel |
| Les profils Arketype sont-ils adoptables ? | Documentation Arketype + tests natifs | Première admission Education/Soil |
| Le modèle des propositions conserve-t-il conditions et conflits ? | Fixtures multi-domaines | Ne pas aplatir toutes les assertions |

## Ce qu'il NE faut PAS demander pour commencer

Ni une copie de l'index Wikipédia de 125 Go, ni un nouveau dump Wikidata, ni l'ensemble des 87 branches réextrait, ni une certification de 100 % de la branche historique, ni un manifeste de SHA de chaque sortie intermédiaire.

## Source de référence de la révision

[Rapport de décision architectural du 16 novembre](../08_REFERENCES/07_RAPPORT_DECISION_20261116.md) : texte utilisateur, source des arbitrages V32.1. Les tests qu'il décrit sont **rapportés dans ce texte**, et ne sont pas présentés ici comme nouvellement exécutés.
