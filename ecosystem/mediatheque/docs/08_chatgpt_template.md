# 08 — ChatGPT Template

**Project:** Médiathèque kOA  
**Technical name:** `koa-mediatheque`  
**Status:** AI-only final target specification  
**Audience:** AI coding conversations only  
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Template source rule

The app must store the current template in a file or database setting:

```text
chatgpt_template_current
```

The GUI button `Copier template ChatGPT` copies this exact template.

---

## 2. Canonical template

```text
Analyse le fichier joint comme une entrée pour Médiathèque kOA.

Objectif : produire une fiche JSON stricte, directement importable dans la base locale SQLite de Médiathèque kOA.

Contexte :
- Médiathèque kOA est une médiathèque locale générale.
- Certains documents sont liés à UCKK, d'autres non.
- Certains documents sont publics, d'autres non publics, privés, restreints ou confidentiels.
- Le classement doit rester compatible avec une future exportation vers une médiathèque de type mod_uckkarchive.
- L'IA peut valider localement la classification.
- La validation canonique finale doit rester canonical_validation_state = "unverified", sauf instruction humaine explicite.
- Ne pas inventer de droits, de source ou de statut public si le fichier ne le démontre pas clairement.
- En cas d'incertitude, utiliser "unknown", human_review_required = true, ou review_queue = "needs_review".

Retourne uniquement un objet JSON valide. Aucun commentaire avant ou après. Pas de bloc Markdown.

Schéma JSON attendu :
{
  "title": "",
  "subtitle": "",
  "description": "",
  "summary": "",
  "media_type": "document",
  "language": "fr",
  "library_scope": "koa",
  "uckk_relevance": "unknown",
  "target_system": "none",
  "target_export_allowed": false,
  "public_state": "unknown",
  "visibility": "private",
  "access_level": "private",
  "ownership_scope": "unknown",
  "source_type": "unknown",
  "source_ownership": "unknown_source",
  "rights_status": "unknown",
  "rights_note": "",
  "restriction_state": "none",
  "restriction_reason": "",
  "redaction_required": false,
  "status": "active",
  "provenance": "ai_assisted",
  "ai_validation_state": "ai_uncertain",
  "ai_confidence": 0.0,
  "canonical_validation_state": "unverified",
  "human_review_required": true,
  "review_queue": "needs_review",
  "review_reason": "",
  "collections": [],
  "tags": [],
  "relations": [],
  "content_flags": [],
  "audience_suitability": "unknown",
  "export_to_uckk": "review_required",
  "export_to_public": "review_required",
  "export_policy_note": "",
  "notes": ""
}

Valeurs autorisées : utiliser exactement les valeurs de docs/01_alignment_variables.md.

Règles :
- Si le document n'est pas lié à UCKK, mettre uckk_relevance = "not_uckk" et export_to_uckk = "no".
- Si le document est non public, mettre public_state = "non_public" ou plus restrictif.
- Si le document est privé, confidentiel, sensible, culturel, lié à l'intégrité, ou contient des données personnelles, mettre human_review_required = true.
- Si les droits sont incertains, mettre rights_status = "unknown" et human_review_required = true.
- Si la source est incertaine, mettre source_type = "unknown" et source_ownership = "unknown_source".
- Ne jamais mettre canonical_validation_state = "verified" sauf instruction explicite.
- Utiliser des tags courts, en minuscules, sans accents, séparés par underscores si nécessaire.
- Utiliser des collections lisibles, stables, en minuscules, sans accents, séparées par underscores si nécessaire.
```

---

## 3. Template versioning

The app must store the template version used for each intake in `chatgpt_intake_log.prompt_template`.
