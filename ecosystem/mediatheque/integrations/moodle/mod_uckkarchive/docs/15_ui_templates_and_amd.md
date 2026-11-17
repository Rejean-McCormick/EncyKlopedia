# 15 — UI, Templates and AMD

**Path:** `docs/15_ui_templates_and_amd.md`  
**Plugin:** `mod_uckkarchive`  
**Component:** `mod_uckkarchive`  
**Status:** Final target specification  
**Scope:** User interface, Mustache templates, output classes, Moodle renderer, AMD modules, and client-side behavior for the self-contained UCKK Archive, Media Library, and Content Advisory subsystem.

---

## 1. Purpose

This document defines the final UI architecture for `mod_uckkarchive`.

The UI must support:

```text
archive browsing
archive item cards
archive item detail views
media library browsing
media upload and edit workflows
media cards
media collections
media version lists
media relation lists
content advisory panels
cultural protocol indicators
external work cards
proof cards
Kristal cards
provenance panels
validation panels
export previews
restricted access messaging
```

The UI is Moodle-native and uses:

```text
PHP output classes
Moodle renderer
Mustache templates
AMD JavaScript modules
external services
Moodle language strings
Moodle capabilities and context-aware policy filtering
```

The UI must never be the authority layer.

---

## 2. Core UI decision

Canonical rule:

```text
Server-side policy decides what data exists in the render payload.
Templates render only.
AMD modules enhance interaction only.
```

The UI may:

```text
display archive/media data
display policy-filtered actions
display content advisories
display cultural protocol notices
display external work metadata
refresh cards through AJAX
submit forms
open panels
filter lists
request export previews
show upload progress
show media version lists
show collection membership
```

The UI must not:

```text
authorize access
decide restricted visibility
decide cultural protocol access
decide validation authority
decide export authority
reconstruct hidden data
expose hidden metadata in the DOM
store policy-sensitive state in JavaScript
trust client-side filtering for security
```

---

## 3. UI architecture layers

The UI architecture has five layers:

```text
controller
output class
renderer
template
AMD module
```

Layer responsibilities:

| Layer | Responsibility |
|---|---|
| Controller | Resolve context, require login, call domain/service logic, pass renderable objects to output. |
| Output class | Build permission-filtered render payloads. |
| Renderer | Connect output classes to Moodle page rendering and Mustache templates. |
| Template | Display already-filtered data. |
| AMD module | Add client-side behavior and call external services. |

Authority rule:

```text
Policy belongs in classes/local.
Renderable filtering belongs in classes/output.
Templates and AMD modules are not authority layers.
```

---

## 4. Required output classes

Required output classes:

```text
classes/output/archive_item_card.php
classes/output/archive_view.php
classes/output/content_advisory_panel.php
classes/output/external_work_card.php
classes/output/kristal_card.php
classes/output/media_card.php
classes/output/media_collection.php
classes/output/media_library.php
classes/output/media_version_list.php
classes/output/provenance_panel.php
classes/output/renderer.php
```

Optional but recommended output classes:

```text
classes/output/export_preview.php
classes/output/media_relation_list.php
classes/output/restricted_notice.php
classes/output/validation_panel.php
```

Output class rule:

```text
Output classes prepare display data only after policy checks have been applied.
```

Output classes must not expose:

```text
raw restricted metadata
hidden cultural protocol notes
private review notes
unfiltered file URLs
unfiltered external service parameters
unredacted personal data
unapproved content marker details
hidden integrity-related metadata
```

---

## 5. Renderer

Canonical renderer:

```text
classes/output/renderer.php
```

The renderer owns the connection between output classes and templates.

Renderer methods should include:

```text
render_archive_view
render_archive_item_card
render_media_library
render_media_card
render_media_collection
render_media_version_list
render_content_advisory_panel
render_external_work_card
render_kristal_card
render_provenance_panel
render_validation_panel
render_export_preview
```

Renderer rule:

```text
The renderer formats renderable objects.
The renderer does not perform final access decisions.
```

---

## 6. Required templates

Required Mustache templates:

```text
templates/archive_item_card.mustache
templates/archive_view.mustache
templates/content_advisory_panel.mustache
templates/external_work_card.mustache
templates/kristal_card.mustache
templates/media_card.mustache
templates/media_collection.mustache
templates/media_library.mustache
templates/media_relation_list.mustache
templates/media_upload.mustache
templates/media_version_list.mustache
templates/proof_card.mustache
templates/provenance_panel.mustache
templates/validation_panel.mustache
```

Optional but recommended templates:

```text
templates/export_preview.mustache
templates/restricted_notice.mustache
templates/empty_state.mustache
templates/filter_bar.mustache
templates/action_menu.mustache
```

Template rule:

```text
Templates render pre-filtered data.
Templates do not enforce access.
Templates do not contain hidden restricted data for later client-side display.
```

---

## 7. Required AMD source modules

Required AMD source files:

```text
amd/src/archive.js
amd/src/content_advisory.js
amd/src/export.js
amd/src/external_work.js
amd/src/kristal.js
amd/src/media.js
amd/src/media_collection.js
```

Required AMD build files:

```text
amd/build/archive.min.js
amd/build/content_advisory.min.js
amd/build/export.min.js
amd/build/external_work.min.js
amd/build/kristal.min.js
amd/build/media.min.js
amd/build/media_collection.min.js
```

AMD build rule:

```text
amd/src is source.
amd/build is generated.
Generated AMD build files are not edited by hand.
```

AMD security rule:

```text
AMD modules do not authorize access.
AMD modules do not reveal restricted data.
AMD modules do not infer permissions.
AMD modules call external services that re-check all policy server-side.
```

---

## 8. Page controllers using UI components

Main UI controllers:

```text
view.php
item.php
media.php
add.php
validate.php
export.php
index.php
```

Controller roles:

| Controller | UI role |
|---|---|
| `view.php` | Main activity view: archive dashboard, media entry points, primary navigation. |
| `item.php` | Archive item detail view. |
| `media.php` | Media library view. |
| `add.php` | Archive item/media creation controller. |
| `validate.php` | Validation and review controller. |
| `export.php` | Export preview and export request controller. |
| `index.php` | Course-level list of UCKK Archive activities. |

Controller rule:

```text
Controllers coordinate request flow.
Controllers do not contain duplicated rendering or authorization logic.
```

---

## 9. Archive view UI

The archive view displays:

```text
activity title
intro
archive summary
archive filters
archive item list
media library entry point
collections entry point
validation queue entry point
export entry point
restricted access indicators
```

Required output/template pair:

```text
classes/output/archive_view.php
templates/archive_view.mustache
```

Required AMD module:

```text
amd/src/archive.js
```

Archive view rules:

```text
Only visible archive items are included in the render payload.
Restricted item counts must not leak details to unauthorized users.
Actions are shown only when the user can perform them.
```

---

## 10. Archive item card UI

Archive item cards display policy-filtered summary data.

Required output/template pair:

```text
classes/output/archive_item_card.php
templates/archive_item_card.mustache
```

Archive item card may display:

```text
title
summary
type
status
visibility
validation state
provenance indicator
media count
proof count
content advisory indicator
restricted indicator
last modified date
available actions
```

Archive item card must not display:

```text
hidden restricted notes
private validation notes
integrity-only details
unapproved cultural protocol notes
unfiltered file URLs
```

---

## 11. Media library UI

The media library UI is the main interface for managed media objects.

Required output/template pair:

```text
classes/output/media_library.php
templates/media_library.mustache
```

Required AMD module:

```text
amd/src/media.js
```

The media library must support:

```text
media search
media filtering
media cards
media upload entry
media edit entry
media collection browsing
media version access
media relation access
content advisory indicators
external work indicators
source and rights indicators
restricted state labels
audience suitability labels
```

Media library filters should include:

```text
media type
status
visibility
collection
tag
content advisory tag
audience suitability
source kind
external work
language
rights/license
provenance
creator
date
```

Media library rule:

```text
Search and filter results are server-filtered before display.
Client-side filters only refine already-permitted result sets.
```

---

## 12. Media card UI

Media cards display a policy-filtered summary of a media object.

Required output/template pair:

```text
classes/output/media_card.php
templates/media_card.mustache
```

Media cards may display:

```text
thumbnail
title
media type
status
visibility
audience suitability
source kind
license/rights summary
version label
content advisory indicator
cultural protocol indicator
collection membership
available actions
```

Media cards must not display:

```text
restricted thumbnails to unauthorized users
hidden cultural protocol notes
private content review notes
unapproved advisory details
original download links unless authorized
raw file identifiers as authority
```

Media card action examples:

```text
view
edit
download
add version
add to collection
view versions
view relations
view advisories
export
delete soft
```

Actions are present only when policy allows them.

---

## 13. Media upload UI

Required template:

```text
templates/media_upload.mustache
```

Required AMD module:

```text
amd/src/media.js
```

Upload UI must collect:

```text
title
description
media type
source kind
ownership kind
license/rights statement
visibility
audience suitability
initial file
caption/transcript files when relevant
collection assignment
content advisory draft markers when relevant
```

Upload UI must respect:

```text
Moodle File API draft areas
configured file limits
allowed MIME types
media policy
content advisory policy
external work rules
cultural protocol rules
```

Upload UI rule:

```text
Client-side validation improves usability only.
Server-side validation is mandatory.
```

---

## 14. Media collection UI

Required output/template pair:

```text
classes/output/media_collection.php
templates/media_collection.mustache
```

Required AMD module:

```text
amd/src/media_collection.js
```

Media collection UI must support:

```text
collection list
collection detail view
media membership
sort order
membership roles
add media to collection
remove media from collection
collection visibility
collection audience suitability
collection export
```

Collection UI rule:

```text
A collection does not own media.
A collection displays only media objects the user can access.
```

---

## 15. Media version list UI

Required output/template pair:

```text
classes/output/media_version_list.php
templates/media_version_list.mustache
```

Media version UI must show:

```text
version number
version label
created date
created by
reason
change summary
file type
file size
hash indicator
status
available actions
```

Media version UI must hide:

```text
restricted files
restricted version notes
download links for unauthorized users
file areas unavailable to the current user
```

Version action examples:

```text
view
download
compare metadata
restore as current
archive version
```

Version UI rule:

```text
Version visibility is policy-filtered independently from the parent media object.
```

---

## 16. Media relation list UI

Required template:

```text
templates/media_relation_list.mustache
```

Optional output class:

```text
classes/output/media_relation_list.php
```

Relation UI must support:

```text
source relation
target relation
relation type
direction
related object label
related object type
available actions
```

Relation types include:

```text
belongs_to_item
belongs_to_kristal
belongs_to_collection
is_derivative_of
is_translation_of
is_excerpt_of
is_proof_for
is_source_for
replaces
references
duplicates
references_external_work
contains_content_marker
```

Relation UI rule:

```text
Relations to inaccessible targets must be hidden or shown only as redacted placeholders.
```

---

## 17. Content advisory panel UI

Required output/template pair:

```text
classes/output/content_advisory_panel.php
templates/content_advisory_panel.mustache
```

Required AMD module:

```text
amd/src/content_advisory.js
```

The content advisory panel must support:

```text
content advisory tags
cultural protocol tags
audience suitability
severity
locator display
review state
review notes when authorized
context notes
restricted state
available actions
```

Canonical user-facing labels:

```text
Content advisory
Content warning
Cultural advisory
Cultural protocol
Audience suitability
```

Avoid system-facing use of `trigger` as the primary term.

Allowed user-facing phrase:

```text
Trigger warning
```

Content advisory UI rule:

```text
A content advisory does not ban media.
It describes conditions for responsible access, teaching, warning, review, restriction, or contextualization.
```

---

## 18. Content marker locator UI

Content marker UI must support these locator types:

```text
timecode
timecode_range
page
page_range
chapter
chapter_range
section
section_range
paragraph
paragraph_range
scene
track
timestamp
url_fragment
manual_reference
```

Examples displayed by the UI:

```text
01:12:30-01:15:10
page 42-45
chapter 3
section 2.4
#section-3
manual note
```

Locator UI rule:

```text
Locators must be useful without storing unauthorized copies of external content.
```

---

## 19. Content review UI

Required form/output components:

```text
classes/form/content_review_form.php
classes/output/content_advisory_panel.php
templates/content_advisory_panel.mustache
amd/src/content_advisory.js
```

Content review UI must support review states:

```text
draft
pending_review
reviewed
approved
contested
retired
```

Content review UI must support decisions such as:

```text
approve advisory
request changes
mark contested
retire marker
adjust severity
adjust audience suitability
add context note
require cultural permission
```

Content review UI rule:

```text
AI may suggest tags or markers.
Human review is required before advisory state becomes approved.
Cultural protocol access cannot be approved by AI.
```

---

## 20. External work UI

Required output/template pair:

```text
classes/output/external_work_card.php
templates/external_work_card.mustache
```

Required AMD module:

```text
amd/src/external_work.js
```

External work UI must display:

```text
title
work type
creator
publisher
publication year
citation
identifier
URL when allowed
rights statement
license summary
content advisory count
available actions
```

External work types:

```text
film
book
article
podcast
website
external_video
external_image
public_archive_item
third_party_pdf
other
```

External work UI rule:

```text
The module may reference foreign media without copying it.
The UI must not imply UCKK ownership over third-party works.
```

---

## 21. Provenance panel UI

Required output/template pair:

```text
classes/output/provenance_panel.php
templates/provenance_panel.mustache
```

The provenance panel may display:

```text
origin
source component
source identifier
created by
modified by
validation actor
file hash
manifest reference
import metadata
AI-assistance indicator
external work reference
content review reference
```

Provenance values:

```text
human
ai_assisted
imported
system
archive
assembly
challenge
integrity
media
external_work
content_review
```

Provenance UI rule:

```text
Provenance explains origin.
Provenance does not grant authority.
```

---

## 22. Validation panel UI

Required template:

```text
templates/validation_panel.mustache
```

Optional output class:

```text
classes/output/validation_panel.php
```

Validation panel must support:

```text
validation state
review summary
contestation state
revision link
restricted state
available validation actions
```

Validation states:

```text
unverified
human_reviewed
verified
contested
invalidated
archived
```

Validation UI rule:

```text
Validation is human-final.
AI cannot validate archive records.
AI cannot invalidate archive records.
AI cannot close contestations.
AI cannot approve cultural protocol access.
```

---

## 23. Kristal card UI

Required output/template pair:

```text
classes/output/kristal_card.php
templates/kristal_card.mustache
```

Required AMD module:

```text
amd/src/kristal.js
```

Kristal UI may display:

```text
title
summary
source items
linked media
proof indicators
provenance indicators
validation state
restricted state
available actions
```

Kristal UI rule:

```text
Kristal display must not bypass archive, media, proof, or content advisory policy.
```

---

## 24. Proof card UI

Required template:

```text
templates/proof_card.mustache
```

Proof card may display:

```text
proof title
proof type
summary
linked archive item
linked media
validation state
provenance state
restricted state
available actions
```

Proof UI rule:

```text
Proof data is filtered by archive policy and media policy before rendering.
```

---

## 25. Export preview UI

Required AMD module:

```text
amd/src/export.js
```

Optional template/output pair:

```text
classes/output/export_preview.php
templates/export_preview.mustache
```

Export preview must show:

```text
selected archive items
selected media
selected media versions
collections
content markers
external work references
file count
manifest inclusion
redaction level
restricted exclusions
cultural protocol exclusions
estimated package scope
```

Export preview rule:

```text
Export preview must reflect actual server-side export authority.
It must not list hidden items as detailed exclusions for unauthorized users.
```

---

## 26. Restricted notice UI

Optional template/output pair:

```text
classes/output/restricted_notice.php
templates/restricted_notice.mustache
```

Restricted notices may appear for:

```text
restricted media
restricted archive item
restricted cultural material
restricted integrity material
unapproved content advisory details
hidden external work references
missing permission
retention-limited records
```

Restricted notice rule:

```text
A restricted notice may explain that access is limited.
It must not reveal the protected content itself.
```

---

## 27. Language strings

Language files:

```text
lang/en/uckkarchive.php
lang/fr/uckkarchive.php
```

UI strings must cover:

```text
archive labels
media labels
collection labels
relation labels
version labels
content advisory labels
cultural protocol labels
external work labels
source/rights labels
validation labels
restricted notices
export labels
empty states
form labels
error messages
capability names
```

Language rule:

```text
Every public UI string has matching English and French keys.
Templates and AMD modules use language strings, not hard-coded display text.
```

---

## 28. Accessibility

UI must support:

```text
keyboard navigation
semantic headings
ARIA labels where needed
accessible form labels
visible focus state
screen-reader-friendly advisory labels
non-color-only restricted indicators
caption/transcript display where available
clear error messages
```

Accessibility rule:

```text
Content advisory and cultural protocol warnings must be understandable without relying only on color, icon, or hover text.
```

---

## 29. Responsive design

The UI must support:

```text
desktop
tablet
mobile
narrow Moodle content regions
drawer navigation
course format constraints
```

Responsive behavior:

```text
cards stack on narrow screens
filters collapse into panels
action menus remain keyboard accessible
tables become cards or scrollable regions
media previews fit the available region
```

---

## 30. Empty states

Empty states should exist for:

```text
no archive items
no media
no collections
no versions
no relations
no content markers
no external works
no search results
no exportable items
restricted/no access
```

Empty state rule:

```text
Empty states must not reveal that hidden restricted records exist unless the user is authorized to know that.
```

---

## 31. Error states

UI error states should handle:

```text
permission denied
service failure
invalid sesskey
invalid context
missing media
missing archive item
missing external work
restricted media
restricted cultural protocol
unsupported file type
upload failure
export failure
validation failure
```

Error state rule:

```text
Error messages must be useful but must not leak restricted metadata.
```

---

## 32. Loading states

AMD modules should support loading states for:

```text
card refresh
search
filter change
media upload
collection update
version list load
content marker load
export preview
export status
```

Loading state rule:

```text
Loading states improve usability only.
They do not cache protected data beyond the current authorized request.
```

---

## 33. Client-side service calls

AMD modules may call external services declared in:

```text
db/services.php
```

Service calls must include:

```text
context id
course module id when needed
record id or uuid
sesskey through Moodle request handling
operation-specific parameters
```

Service call rule:

```text
Every external service re-checks context, capability, policy, visibility, lifecycle state, and redaction server-side.
```

---

## 34. Data attributes

Templates may include safe data attributes such as:

```text
data-region
data-action
data-media-id
data-media-uuid
data-item-id
data-collection-id
data-external-work-id
```

Templates must not include unsafe data attributes such as:

```text
hidden restricted notes
raw file paths
unredacted private metadata
unapproved cultural protocol notes
server-only capability assumptions
secret tokens outside Moodle request patterns
```

Data attribute rule:

```text
DOM data is not private storage.
Anything rendered to the DOM is considered visible to the current user.
```

---

## 35. File preview UI

File preview UI may display:

```text
thumbnail
preview image
media player
transcript link
caption availability
document preview link
download action when authorized
```

File preview UI must respect:

```text
media policy
file area permissions
restricted state
content advisory policy
cultural protocol restrictions
Moodle pluginfile access checks
```

Preview rule:

```text
Preview access and original download access are separate decisions.
```

---

## 36. Content advisory display patterns

Content advisory display may include:

```text
small indicator on cards
full advisory panel on detail pages
warning banner before viewing media
context note before playback
locator list for specific scenes/pages
restricted cultural protocol notice
review state indicator for staff
```

Display rule:

```text
The UI should warn responsibly without unnecessarily exposing sensitive details to audiences that should not see them.
```

---

## 37. Cultural protocol UI

Cultural protocol UI may include:

```text
restricted cultural indicator
requires context label
requires permission label
not for public export label
elder review required label
community permission required label
seasonal/contextual access label
```

Cultural protocol UI rule:

```text
Cultural protocol details are themselves potentially sensitive.
The UI must distinguish between public-facing notices and restricted protocol notes.
```

---

## 38. External work locator UI

External work locator UI may display:

```text
film timestamp
book page range
article section
website fragment
manual reference
citation
```

Examples:

```text
Movie Maïna — content advisory — 01:12:30-01:15:10
Book The Body Keeps the Score — content advisory — page 42-45
```

External work locator rule:

```text
Locators identify where advisory-relevant content occurs.
Locators do not require storing or copying the external work.
```

---

## 39. Privacy-aware UI

Privacy-aware UI must:

```text
hide personal metadata unless authorized
redact reviewer notes when required
avoid exposing user IDs unnecessarily
avoid exposing private source metadata
filter content review history
respect privacy provider rules
```

Privacy UI rule:

```text
If data would not be available through a permitted server response, it must not appear in UI payloads, templates, or JavaScript.
```

---

## 40. Backup/restore-aware UI

UI labels and admin screens should make clear that the module owns:

```text
archive records
media records
media versions
collections
relations
tags
content markers
content reviews
external work references
export manifests
```

Backup/restore UI rule:

```text
Restored media remains subject to restored visibility, restricted state, content advisory policy, and cultural protocol rules.
```

---

## 41. Testing requirements

UI and AMD tests must cover:

```text
archive view rendering
archive item card rendering
media library rendering
media card rendering
media upload UI
media collection UI
media version list UI
media relation list UI
content advisory panel UI
content marker locator UI
content review UI
external work card UI
restricted notice UI
export preview UI
language string coverage
permission-filtered actions
restricted data not rendered
cultural protocol data not leaked
AJAX service error handling
```

Required Behat files:

```text
tests/behat/uckkarchive.feature
tests/behat/uckkarchive_media.feature
tests/behat/uckkarchive_content_advisory.feature
```

Testing rule:

```text
Tests verify final target behavior, not historical transitions.
```

---

## 42. Final rule

The UI is a Moodle-native presentation and interaction layer for a self-contained archive, media library, and content advisory system.

The UI must render only policy-filtered data, call server-side services for state changes, and avoid leaking restricted archive, media, cultural protocol, content review, or external work metadata.

This document defines the final target behavior for implementation. Code, tests, services, UI, backup/restore, privacy, content advisory governance, and packaging must conform to this specification.
