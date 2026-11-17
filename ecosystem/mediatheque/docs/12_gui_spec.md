# 12 — GUI Specification

**Project:** Médiathèque kOA
**Technical name:** `koa-mediatheque`
**Status:** AI-only final target specification
**Audience:** AI coding conversations only
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Design principle

The GUI must be small, table-first, and practical.

It must not become a heavy content-management system.

Workflow screens must avoid unnecessary vertical distance between fields that are used together.

---

## 2. Required screens

```text
Dashboard
Library Table
File Preview
ChatGPT Intake
XLSX Export/Import
Settings
Logs
```

These may be tabs in one window.

---

## 3. Library Table screen

Required features:

```text
search
filter by UCKK relevance
filter by public state
filter by visibility
filter by review queue
filter by tags
filter by collections
filter by export_to_uckk
filter by export_to_public
open file
open folder
edit metadata
mark review required
export current filter to XLSX
```

Visible default columns:

```text
title
filename
media_type
uckk_relevance
public_state
visibility
rights_status
restriction_state
ai_validation_state
human_review_required
collections
tags
```

---

## 4. ChatGPT Intake screen

Required controls:

```text
selected file path
copy template button
paste response box
validate JSON button
validation result panel
preview mapped row
validate and integrate button
copy PS7 command button
```

Required layout behavior:

```text
selected file path and paste response box must be visible close together
copy template button must be near selected file path
copy template button must copy only the ChatGPT prompt/template text
copy template button must not expose a large fallback text area by default
template preview, options, and PS7 fallback may be collapsed by default
```

Preferred top layout:

```text
left column:
selected file path
copy template button
optional collapsed template preview

right column:
paste response box
```

The ChatGPT Intake screen must support the fast repeated workflow:

```text
paste selected file path
copy ChatGPT prompt
paste ChatGPT JSON response
validate
integrate
```

The interface must minimize scrolling between the file path input and the ChatGPT response input.

---

## 5. Recommended first stack

```text
Python
Streamlit
sqlite3
pandas
openpyxl
```

Streamlit is acceptable because the app is local, table-first, and workflow-focused.
