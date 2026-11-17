# 25 — Médiathèque publique et Explorateur Médiathèque

**Path recommandé:** `docs/25_mediatheque_public_explorer.md`
**Statut:** Final target specification
**Portée:** Page publique **Médiathèque** et composant public **Explorateur Médiathèque**.
**Objectif:** Définir toutes les variables canoniques avant codage afin d’éviter la dérive de noms, responsabilités, routes, templates, classes, services, données, politiques, libellés et styles.

---

## 1. Décision canonique

La page publique s’appelle :

```text
Médiathèque
```

Le composant de navigation, recherche et filtrage s’appelle :

```text
Explorateur Médiathèque
```

Formule canonique :

```text
Médiathèque = surface publique de consultation
Explorateur Médiathèque = composant public de recherche, filtrage, navigation et découverte
mod_uckkarchive = propriétaire des données, règles, médias, collections, advisories et politiques
local_uckk = propriétaire du shell public, de la route publique, de la navigation publique et du style public
```

Règle finale :

```text
local_uckk affiche.
mod_uckkarchive décide ce qui peut être exposé.
```

---

## 2. Variables d’identité

| Variable | Valeur canonique | Règle |
|---|---|---|
| `MEDIATHEQUE_PUBLIC_NAME` | `Médiathèque` | Nom public de la librairie média UCKK. |
| `MEDIATHEQUE_EXPLORER_NAME` | `Explorateur Médiathèque` | Nom public du navigateur. |
| `MEDIATHEQUE_COMPONENT_KEY` | `mediatheque` | Clé stable de page, CSS, configuration, navigation. |
| `MEDIATHEQUE_EXPLORER_KEY` | `mediatheque_explorer` | Clé stable du composant. |
| `MEDIATHEQUE_LANG_PREFIX` | `mediatheque_` | Préfixe des chaînes de langue. |
| `MEDIATHEQUE_ROUTE_SLUG` | `mediatheque` | Slug public. |
| `MEDIATHEQUE_PUBLIC_TITLE` | `Médiathèque UCKK` | Titre de page. |
| `MEDIATHEQUE_PUBLIC_EYEBROW` | `Archives publiques` | Surtitre dans le hero public. |
| `MEDIATHEQUE_PUBLIC_SUMMARY` | `Explorer les médias, collections, œuvres externes et passages documentés de l’archive UCKK.` | Résumé public. |
| `MEDIATHEQUE_EMPTY_MESSAGE` | `Aucun média public ne correspond aux filtres.` | Message d’état vide. |
| `MEDIATHEQUE_RESTRICTED_NOTICE` | `Certains contenus sont masqués ou résumés selon les droits, avis de contenu et protocoles culturels.` | Notice de filtrage responsable. |

---

## 3. Variables de propriété

| Variable | Valeur canonique | Règle |
|---|---|---|
| `MEDIATHEQUE_PUBLIC_OWNER` | `local_uckk` | Possède la page publique, le shell, la navigation, le style public. |
| `MEDIATHEQUE_DATA_OWNER` | `mod_uckkarchive` | Possède les médias, collections, tags, relations, sources, advisories, protocoles. |
| `MEDIATHEQUE_POLICY_OWNER` | `mod_uckkarchive` | Possède les décisions d’accès, visibilité, téléchargement, export, redaction. |
| `MEDIATHEQUE_STYLE_OWNER` | `local_uckk` | Les classes publiques de la Médiathèque sont stylées dans le style public. |
| `MEDIATHEQUE_FILE_OWNER` | `mod_uckkarchive` | Les fichiers restent servis via Moodle File API et politiques du module. |
| `MEDIATHEQUE_EXPORT_OWNER` | `mod_uckkarchive` | Les exports, manifests et téléchargements restent module-owned. |
| `MEDIATHEQUE_NO_DB_DUPLICATION_RULE` | `true` | `local_uckk` ne duplique pas les tables média. |
| `MEDIATHEQUE_NO_DIRECT_FILE_RULE` | `true` | La page publique ne lit pas les fichiers hors File API. |
| `MEDIATHEQUE_NO_CLIENT_AUTH_RULE` | `true` | JavaScript et Mustache ne décident jamais des accès. |

---

## 4. Routes canoniques

| Variable | Valeur canonique | Rôle |
|---|---|---|
| `ROUTE_PUBLIC_MEDIATHEQUE` | `/local/uckk/mediatheque.php` | Route publique principale. |
| `ROUTE_PUBLIC_MEDIATHEQUE_DETAIL` | `/local/uckk/mediatheque.php?item={uuid}` | Détail public d’un média, d’une collection, d’une œuvre externe ou d’un passage. |
| `ROUTE_PUBLIC_MEDIATHEQUE_COLLECTION` | `/local/uckk/mediatheque.php?collection={uuid}` | Vue filtrée collection. |
| `ROUTE_PUBLIC_MEDIATHEQUE_TAG` | `/local/uckk/mediatheque.php?tag={key}` | Vue filtrée tag. |
| `ROUTE_PUBLIC_MEDIATHEQUE_SOURCE` | `/local/uckk/mediatheque.php?source={sourcevalue}` | Vue filtrée source. |
| `ROUTE_PUBLIC_MEDIATHEQUE_SEARCH` | `/local/uckk/mediatheque.php?q={query}` | Recherche publique initiale. |

Règle :

```text
Toutes les routes publiques passent par local_uckk.
Tous les résultats passent par mod_uckkarchive avant affichage.
```

---

## 5. Fichiers canoniques — couche `local_uckk`

| Fichier | Statut | Rôle |
|---|---:|---|
| `local/uckk/mediatheque.php` | requis | Contrôleur mince de la page Médiathèque. |
| `local/uckk/classes/local/public_pages.php` | requis | Ajoute la définition `mediatheque` au registre public. |
| `local/uckk/classes/output/public_page.php` | requis | Transporte les données publiques vers `public_page.mustache`. |
| `local/uckk/templates/public_page.mustache` | requis | Shell public unique; contient la région optionnelle de l’Explorateur Médiathèque. |
| `local/uckk/amd/src/mediatheque_explorer.js` | requis si AJAX | Contrôle filtres, recherche, pagination progressive, historique URL. |
| `local/uckk/styles.css` | requis | Style public de la page et de l’explorateur. |
| `local/uckk/lang/fr/local_uckk.php` | requis | Chaînes françaises publiques. |
| `local/uckk/lang/en/local_uckk.php` | requis | Chaînes anglaises publiques. |

Règle :

```text
Le contrôleur mediatheque.php ne fait pas de logique média.
Il résout la page, appelle le fournisseur public, puis rend public_page.mustache.
```

---

## 6. Fichiers canoniques — couche `mod_uckkarchive`

| Fichier | Statut | Rôle |
|---|---:|---|
| `mod/uckkarchive/classes/local/public_mediatheque_repository.php` | requis | Recherche et agrège les objets exposables publiquement. |
| `mod/uckkarchive/classes/local/public_mediatheque_service.php` | requis | Coordonne filtres, politiques, DTOs, pagination et notices. |
| `mod/uckkarchive/classes/local/media_search.php` | existant/requis | Recherche média interne. |
| `mod/uckkarchive/classes/local/media_policy.php` | existant/requis | Décisions finales média. |
| `mod/uckkarchive/classes/local/content_policy.php` | existant/requis | Décisions finales advisories, protocoles culturels, restrictions. |
| `mod/uckkarchive/classes/local/archive_policy.php` | existant/requis | Décisions finales archive item. |
| `mod/uckkarchive/classes/local/external_work.php` | existant/requis | Références d’œuvres externes. |
| `mod/uckkarchive/classes/local/content_marker.php` | existant/requis | Passages ciblés, locators et repères de contenu. |
| `mod/uckkarchive/classes/external/search_mediatheque.php` | requis si AJAX | Service de recherche filtrée. |
| `mod/uckkarchive/db/services.php` | requis si AJAX | Déclare `mod_uckkarchive_search_mediatheque`. |
| `mod/uckkarchive/lang/fr/uckkarchive.php` | requis | Chaînes métier du module. |
| `mod/uckkarchive/tests/public_mediatheque_test.php` | requis | Tests repository/service/politiques. |
| `mod/uckkarchive/tests/external/search_mediatheque_test.php` | requis si AJAX | Tests du service externe. |

Règle :

```text
mod_uckkarchive fournit des DTOs filtrés.
local_uckk rend la surface publique.
```

---

## 7. Services canoniques

| Variable | Valeur canonique | Rôle |
|---|---|---|
| `SERVICE_SEARCH_MEDIATHEQUE` | `mod_uckkarchive_search_mediatheque` | Recherche publique filtrée. |
| `SERVICE_GET_MEDIATHEQUE_ITEM` | `mod_uckkarchive_get_mediatheque_item` | Détail public filtré. |
| `SERVICE_GET_MEDIATHEQUE_FILTERS` | `mod_uckkarchive_get_mediatheque_filters` | Facettes/filtres publics. |
| `SERVICE_GET_MEDIATHEQUE_COLLECTION` | `mod_uckkarchive_get_mediatheque_collection` | Collection publique filtrée. |

Règles de service :

```text
require_login(false) lorsque l’accès anonyme est permis par configuration.
Résoudre le contexte.
Valider les paramètres.
Appeler les policy classes.
Retourner seulement les champs exportables vers le public.
Ne jamais exposer les notes privées, protocoles non autorisés, métadonnées restreintes ou fichiers directs.
```

---

## 8. Tables canoniques utilisées

Aucune nouvelle table n’est requise pour la Médiathèque publique.

La Médiathèque lit les tables existantes :

```text
uckkarchive_media
uckkarchive_media_version
uckkarchive_media_relation
uckkarchive_media_tag
uckkarchive_media_collection
uckkarchive_media_collection_item
uckkarchive_media_source
uckkarchive_content_tag
uckkarchive_content_tag_set
uckkarchive_content_marker
uckkarchive_content_review
uckkarchive_external_work
uckkarchive_item
uckkarchive_prov
uckkarchive_rev
```

Règle :

```text
La Médiathèque publique est une vue filtrée.
Elle n’est pas un nouveau modèle de stockage.
```

---

## 9. Variables d’objets exposables

| Variable | Valeur canonique | Description |
|---|---|---|
| `MEDIATHEQUE_OBJECT_MEDIA` | `media` | Média interne `uckkarchive_media`. |
| `MEDIATHEQUE_OBJECT_COLLECTION` | `collection` | Collection média `uckkarchive_media_collection`. |
| `MEDIATHEQUE_OBJECT_EXTERNAL_WORK` | `external_work` | Œuvre externe `uckkarchive_external_work`. |
| `MEDIATHEQUE_OBJECT_ARCHIVE_ITEM` | `archive_item` | Item d’archive publié lié à un média. |
| `MEDIATHEQUE_OBJECT_CONTENT_MARKER` | `content_marker` | Passage ciblé public ou résumé de passage. |

Types publics autorisés :

```text
media
collection
external_work
archive_item
content_marker
```

Types non exposables directement :

```text
content_review
private_note
revision_private_note
restricted_cultural_protocol_note
integrity_case_detail
raw_file_record
```

---

## 10. Variables de visibilité publique

| Variable | Valeur canonique |
|---|---|
| `MEDIATHEQUE_ANONYMOUS_VISIBILITY_VALUES` | `public` |
| `MEDIATHEQUE_AUTHENTICATED_VISIBILITY_MODE` | `policy_filtered` |
| `MEDIATHEQUE_PUBLIC_MEDIA_STATUS_VALUES` | `active`, `archived` |
| `MEDIATHEQUE_PUBLIC_ARCHIVE_STATUS_VALUES` | `published`, `archived` |
| `MEDIATHEQUE_EXCLUDED_MEDIA_STATUS_VALUES` | `draft`, `submitted`, `superseded`, `deleted_soft` |
| `MEDIATHEQUE_RESTRICTED_PUBLIC_MODE` | `summary_only_or_hidden` |
| `MEDIATHEQUE_CULTURAL_PROTOCOL_PUBLIC_MODE` | `policy_filtered_summary` |
| `MEDIATHEQUE_CONTENT_ADVISORY_PUBLIC_MODE` | `public_summary_only` |

Règle :

```text
Une carte visible ne donne pas automatiquement accès au fichier original.
Une notice d’avis de contenu visible ne donne pas accès aux notes privées.
Une collection visible ne rend pas tous ses médias visibles.
```

---

## 11. Variables de filtres

| Variable | Paramètre | Valeurs |
|---|---|---|
| `FILTER_QUERY` | `q` | texte libre |
| `FILTER_OBJECT_TYPE` | `type` | `all`, `media`, `collection`, `external_work`, `archive_item`, `content_marker` |
| `FILTER_MEDIA_TYPE` | `mediatype` | `all`, `video`, `audio`, `image`, `pdf`, `document`, `book`, `external_reference`, `other` |
| `FILTER_COLLECTION` | `collection` | UUID collection |
| `FILTER_TAG` | `tag` | tag key |
| `FILTER_SOURCE` | `source` | `produced_by_uckk`, `submitted_to_uckk`, `imported`, `external_reference_only` |
| `FILTER_ADVISORY` | `advisory` | `all`, `none`, `has_advisory`, `has_public_advisory` |
| `FILTER_CULTURAL_PROTOCOL` | `cultural` | `all`, `none`, `has_public_protocol` |
| `FILTER_AUDIENCE` | `audience` | `all`, `general`, `guided`, `mature`, `restricted` |
| `FILTER_LANGUAGE` | `lang` | code langue |
| `FILTER_VALIDATION` | `validation` | `all`, `human_reviewed`, `verified`, `archived` |
| `FILTER_SORT` | `sort` | `relevance`, `newest`, `title`, `type`, `collection`, `validated` |
| `FILTER_PAGE` | `page` | entier positif |
| `FILTER_PERPAGE` | `perpage` | `12`, `24`, `48` |

Valeurs par défaut :

```text
q = ""
type = all
mediatype = all
collection = null
tag = null
source = null
advisory = all
cultural = all
audience = all
lang = null
validation = all
sort = relevance
page = 1
perpage = 12
```

---

## 12. DTO canonique — requête

```json
{
  "q": "string",
  "type": "all|media|collection|external_work|archive_item|content_marker",
  "mediatype": "all|video|audio|image|pdf|document|book|external_reference|other",
  "collection": "uuid|null",
  "tag": "string|null",
  "source": "string|null",
  "advisory": "all|none|has_advisory|has_public_advisory",
  "cultural": "all|none|has_public_protocol",
  "audience": "all|general|guided|mature|restricted",
  "lang": "string|null",
  "validation": "all|human_reviewed|verified|archived",
  "sort": "relevance|newest|title|type|collection|validated",
  "page": 1,
  "perpage": 12
}
```

---

## 13. DTO canonique — réponse

```json
{
  "context": {
    "component": "mod_uckkarchive",
    "surface": "local_uckk",
    "page": "mediatheque",
    "explorer": "mediatheque_explorer",
    "anonymous": true,
    "policyfiltered": true
  },
  "filters": {},
  "facets": [],
  "items": [],
  "pagination": {
    "page": 1,
    "perpage": 12,
    "total": 0,
    "hasmore": false
  },
  "notices": [],
  "empty": {
    "isempty": false,
    "message": ""
  }
}
```

---

## 14. DTO canonique — carte Médiathèque

```json
{
  "uuid": "string",
  "objecttype": "media|collection|external_work|archive_item|content_marker",
  "title": "string",
  "subtitle": "string|null",
  "summary": "string",
  "mediatype": "string|null",
  "mimetype": "string|null",
  "language": "string|null",
  "thumbnailurl": "string|null",
  "detailurl": "string",
  "source": {
    "value": "produced_by_uckk|submitted_to_uckk|imported|external_reference_only|null",
    "label": "string"
  },
  "rights": {
    "license": "string|null",
    "rightsstatement": "string|null",
    "copyallowed": false
  },
  "status": {
    "value": "string",
    "label": "string"
  },
  "visibility": {
    "value": "string",
    "label": "string"
  },
  "validation": {
    "value": "string",
    "label": "string"
  },
  "badges": [],
  "advisories": {
    "haspublicadvisory": false,
    "summary": "string|null"
  },
  "culturalprotocol": {
    "haspublicprotocol": false,
    "summary": "string|null"
  },
  "relations": {
    "collectioncount": 0,
    "markercount": 0,
    "externalworkcount": 0
  },
  "actions": {
    "canviewdetail": true,
    "canviewfile": false,
    "candownload": false,
    "canexport": false
  }
}
```

Règle :

```text
Le DTO de carte est un DTO public filtré.
Il n’est pas un dump de la table uckkarchive_media.
```

---

## 15. DTO canonique — passage ciblé

```json
{
  "uuid": "string",
  "objecttype": "content_marker",
  "targettype": "media|external_work|archive_item",
  "targetuuid": "string",
  "locator": {
    "type": "timecode|timecode_range|page|page_range|chapter|section|paragraph|scene|timestamp|url_fragment|manual_reference",
    "start": "string|null",
    "end": "string|null",
    "label": "string|null"
  },
  "title": "string",
  "summary": "string",
  "advisorysummary": "string|null",
  "culturalprotocolsummary": "string|null",
  "severity": "none|low|moderate|strong|restricted",
  "audiencesuitability": "general|guided|mature|restricted",
  "reviewstate": "draft|under_review|reviewed|approved|contested|archived",
  "detailurl": "string"
}
```

Règle :

```text
Un passage ciblé public peut afficher un locator.
Il ne doit pas afficher de note privée ni de protocole culturel non autorisé.
```

---

## 16. Classes CSS canoniques

Classes racine publiques :

```text
.local-uckk-public-page--mediatheque
.local-uckk-mediatheque
.local-uckk-mediatheque-explorer
```

Explorateur :

```text
.local-uckk-mediatheque-explorer__header
.local-uckk-mediatheque-explorer__search
.local-uckk-mediatheque-explorer__filters
.local-uckk-mediatheque-explorer__facets
.local-uckk-mediatheque-explorer__results
.local-uckk-mediatheque-explorer__pagination
.local-uckk-mediatheque-explorer__notice
.local-uckk-mediatheque-explorer__empty
```

Cartes :

```text
.local-uckk-mediatheque-card
.local-uckk-mediatheque-card--media
.local-uckk-mediatheque-card--collection
.local-uckk-mediatheque-card--external-work
.local-uckk-mediatheque-card--archive-item
.local-uckk-mediatheque-card--content-marker
.local-uckk-mediatheque-card__media
.local-uckk-mediatheque-card__body
.local-uckk-mediatheque-card__eyebrow
.local-uckk-mediatheque-card__title
.local-uckk-mediatheque-card__summary
.local-uckk-mediatheque-card__meta
.local-uckk-mediatheque-card__badges
.local-uckk-mediatheque-card__actions
```

États :

```text
.is-loading
.is-empty
.is-filtered
.is-restricted
.is-external-reference
.has-advisory
.has-cultural-protocol
```

Règle :

```text
Les classes publiques utilisent le préfixe local-uckk.
Les classes internes du module gardent le préfixe uckkarchive.
Ne pas styler la page publique avec .path-mod-uckkarchive.
```

---

## 17. Chaînes de langue canoniques

Chaînes `local_uckk` :

```php
$string['mediatheque_title'] = 'Médiathèque UCKK';
$string['mediatheque_eyebrow'] = 'Archives publiques';
$string['mediatheque_summary'] = 'Explorer les médias, collections, œuvres externes et passages documentés de l’archive UCKK.';
$string['mediatheque_explorer_title'] = 'Explorateur Médiathèque';
$string['mediatheque_search_placeholder'] = 'Rechercher dans la médiathèque';
$string['mediatheque_filter_type'] = 'Type';
$string['mediatheque_filter_mediatype'] = 'Format';
$string['mediatheque_filter_collection'] = 'Collection';
$string['mediatheque_filter_tag'] = 'Mot-clé';
$string['mediatheque_filter_source'] = 'Source';
$string['mediatheque_filter_advisory'] = 'Avis de contenu';
$string['mediatheque_filter_cultural'] = 'Protocole culturel';
$string['mediatheque_filter_audience'] = 'Public';
$string['mediatheque_empty'] = 'Aucun média public ne correspond aux filtres.';
$string['mediatheque_restricted_notice'] = 'Certains contenus sont masqués ou résumés selon les droits, avis de contenu et protocoles culturels.';
```

Chaînes `mod_uckkarchive` :

```php
$string['service_search_mediatheque'] = 'Rechercher dans la médiathèque';
$string['mediatheque_object_media'] = 'Média';
$string['mediatheque_object_collection'] = 'Collection';
$string['mediatheque_object_external_work'] = 'Œuvre externe';
$string['mediatheque_object_archive_item'] = 'Archive liée';
$string['mediatheque_object_content_marker'] = 'Passage ciblé';
$string['mediatheque_source_produced_by_uckk'] = 'Produit par UCKK';
$string['mediatheque_source_submitted_to_uckk'] = 'Soumis à UCKK';
$string['mediatheque_source_imported'] = 'Importé';
$string['mediatheque_source_external_reference_only'] = 'Référence externe seulement';
```

---

## 18. Règles de rendu

Le rendu public doit afficher :

```text
hero Médiathèque
notice d’accès responsable
barre de recherche
filtres principaux
facettes
grille de cartes
pagination
état vide
détail public optionnel
```

Le rendu public ne doit jamais afficher :

```text
notes privées
notes internes de validation
notes culturelles restreintes
détails de cas d’intégrité
fichiers originaux sans autorisation
chemins de fichiers
identifiants internes de base de données
métadonnées non filtrées
```

---

## 19. Règles de détail public

Le détail public peut afficher :

```text
titre
résumé
type
thumbnail ou preview autorisée
source publique
droits et licence
collections visibles
tags publics
passages ciblés publics
avis de contenu publics
résumé de protocole culturel autorisé
relations publiques
lien vers œuvre externe
```

Le détail public ne doit pas afficher :

```text
download original sans politique positive
transcript restreint
caption restreinte
notes de review privées
cultural protocol notes non autorisées
metadata JSON brut
fichiers File API non autorisés
```

---

## 20. Règles de sécurité

Règles obligatoires :

```text
Capabilities are gates.
Policy classes make final access decisions.
Templates do not authorize access.
AMD does not authorize access.
Controllers do not duplicate policy.
Services return permission-filtered data.
```

Classes appelées :

```text
classes/local/media_policy.php
classes/local/content_policy.php
classes/local/archive_policy.php
```

Filtrage obligatoire :

```text
visibility
status
validationstate
restricted state
content advisory policy
cultural protocol policy
file download policy
export policy
privacy/redaction policy
rights/source policy
```

---

## 21. Règles de performance

Variables :

| Variable | Valeur |
|---|---:|
| `MEDIATHEQUE_DEFAULT_PERPAGE` | `12` |
| `MEDIATHEQUE_MAX_PERPAGE` | `48` |
| `MEDIATHEQUE_DEFAULT_SORT` | `relevance` |
| `MEDIATHEQUE_MIN_QUERY_LENGTH` | `2` |
| `MEDIATHEQUE_FACET_LIMIT` | `20` |
| `MEDIATHEQUE_CARD_SUMMARY_LENGTH` | `240` |

Règles :

```text
Ne pas charger les fichiers originaux dans la grille.
Utiliser thumbnails/previews autorisés.
Paginer les résultats.
Limiter les facettes.
Filtrer côté serveur.
Ne pas exposer plus de données au client que nécessaire.
```

---

## 22. Règles de style

Le style doit suivre le canon public UCKK :

```text
rétrofuturisme civique encyclopédique
affiche institutionnelle utopique néo-académique
parchemin
vert pétrole
or vieilli
encre noire-verte
cartes lisibles
bordures fines
hiérarchie documentaire
sobriété institutionnelle
```

Règle :

```text
La Médiathèque publique hérite du shell public local_uckk.
Elle ne crée pas un nouveau système visuel.
```

---

## 23. Tests obligatoires

Tests `local_uckk` :

```text
mediatheque.php loads
public_pages.php registers slug mediatheque
public_page output includes mediatheque region
public_page.mustache renders explorer when provided
local_uckk language strings exist
missing mod_uckkarchive fails with public notice, not fatal leak
```

Tests `mod_uckkarchive` :

```text
public_mediatheque_repository returns only policy-allowed media
anonymous user sees only public records
authenticated user receives policy-filtered records
restricted media are hidden or summary-only
cultural protocol restricted fields are redacted
content markers return only public locators and summaries
external works are reference-only unless policy allows more
collection visibility does not override media visibility
media card visibility does not imply download permission
AJAX service validates params
AJAX service filters output fields
pagination works
facets do not leak hidden records
```

Behat :

```text
anonymous visitor opens Médiathèque
visitor searches media
visitor filters by type
visitor opens public media detail
restricted content notice appears
hidden restricted content does not appear
mobile layout remains usable
```

---

## 24. Anti-dérive finale

Ces noms sont définitifs :

```text
Médiathèque
Explorateur Médiathèque
mediatheque
mediatheque_explorer
public_mediatheque_repository
public_mediatheque_service
mod_uckkarchive_search_mediatheque
.local-uckk-mediatheque-explorer
.local-uckk-mediatheque-card
```

Noms interdits pour cette fonctionnalité :

```text
library
librairie
media browser
public archive browser
media explorer
bibliothèque média
navigateur librairie
explorateur librairie
```

Exceptions :

```text
media library peut rester dans la documentation technique anglophone existante.
uckkarchive_media reste le nom canonique de table.
media_search reste une classe interne existante.
```

---

## 25. Résumé exécutable

```text
Créer /local/uckk/mediatheque.php.
Ajouter slug mediatheque dans public_pages.php.
Rendre la page avec public_page.mustache.
Ajouter la région mediatheque_explorer dans le shell public.
Créer un service public côté mod_uckkarchive.
Retourner seulement des DTOs filtrés.
Afficher les cartes avec classes local-uckk-mediatheque-*.
Servir les fichiers seulement par Moodle File API.
Appliquer media_policy, content_policy et archive_policy à chaque résultat.
Ne jamais dupliquer les tables média dans local_uckk.
Ne jamais autoriser par JavaScript ou Mustache.
```
