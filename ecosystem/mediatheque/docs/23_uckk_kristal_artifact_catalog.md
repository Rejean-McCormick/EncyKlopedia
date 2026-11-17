# 23 — Catalogue d’artefacts Kristal dans la Médiathèque UCKK

## Décision

Les Kristals UCKK sont **eux-mêmes des artefacts stockés et versionnés dans la Médiathèque UCKK**. Ils peuvent simultanément référer d’autres médias/sources de cette Médiathèque.

Cette relation est volontaire :

```text
Médiathèque UCKK
├── médias / documents / sources
└── Kristals versionnés
       └── source/media refs -> autres objets Médiathèque
```

La Médiathèque ne devient pas l’autorité sémantique du Kristal.

## Deux concepts Kristal dans le plugin

Le plugin contenait déjà `uckkarchive_kristal`, historiquement un objet d’insight/archive rattaché à une activité Moodle. Cette table n’est **pas** réutilisée pour les Kristals canoniques.

La 0.4.0 a introduit, et la 0.5.0 conserve/enrichit :

```text
uckkarchive_kartifact
  identité stable / hiérarchie / binding vers média

uckkarchive_kversion
  version immutable / SHA-256 / binding vers media_version
```

Les octets sont stockés dans `uckkarchive_media` + `uckkarchive_media_version` via la Moodle File API, avec `mediatype = kristal_artifact`.

## Hiérarchie UCKK

```text
1 université
└── 10 voies
    └── 10 cours chacune
```

Les liens de parenté n’autorisent aucun recouvrement de propriété sémantique :

- le Kristal UCKK possède la topologie ordonnée des voies;
- un Kristal de voie possède la topologie ordonnée de ses cours;
- un Kristal-cours possède son propre périmètre épistémique;
- un parent référence ses enfants sans embarquer leur contenu.

## Identités

```text
kristal_ref      != catalog UUID
catalog UUID     != media UUID
media UUID       != media version UUID
media version UUID != KQ/KP/KA/KS
```

`kristal_ref` est la clé sémantique stable et reste sous autorité Kristal/Kristall.

## Cycle de vie

```text
stub -> building -> candidate -> validated -> crystallized -> published
```

Chaque changement d’octets publié devient une nouvelle version immutable dans Médiathèque. Un vrai Kristal publié remplace progressivement le stub comme version courante, sans changer `kristal_ref`.

## Korpus

Le Korpus est importé comme 64 médias normaux. Ses fichiers ne sont pas copiés dans le dépôt Engine; ils sont lus au déploiement puis stockés dans la File API Moodle. Les SHA-256 de préparation sont enregistrés dans `mediatheque-uckk/bootstrap/import-plan.json`.

## Univers-Cité

Univers-Cité ne lit pas directement Korpus pour définir la structure pédagogique. Une fois les Kristals construits/publiés :

```text
Kristal UCKK -> Kristal voie -> Kristal cours -> interprétation IA -> Univers-Cité/Moodle
```

Moodle reste l’état transactionnel; le Kristal reste la source d’information.
