# 07 — ChatGPT Intake Workflow

**Project:** Médiathèque kOA
**Technical name:** `koa-mediatheque`
**Status:** AI-only final target specification
**Audience:** AI coding conversations only
**Rule:** All implementation conversations must start from `01_alignment_variables.md`.

---

## 1. Purpose

The app must make ChatGPT usable as a classification interface without giving ChatGPT direct access to the database.

ChatGPT only produces structured metadata suggestions. The local app remains responsible for validation, file facts, duplicate checks, storage behavior, SQLite writes, and audit/intake logging.

---

## 2. Required GUI area

The GUI must include an area named:

```text
Entrée ChatGPT
```

Required controls:

```text
Select current file
Copy ChatGPT prompt
Paste ChatGPT response
Validate JSON
Preview row
Validate and integrate
Copy PS7 fallback command
Open file
Open folder
```

Implementation labels may be French, but the workflow meaning must remain equivalent:

```text
Sélectionner fichier courant
Copier prompt ChatGPT
Coller réponse ChatGPT
Valider JSON
Prévisualiser entrée
Valider et intégrer
Copier commande fallback PS7
Ouvrir fichier
Ouvrir dossier
```

---

## 3. Required layout behavior

The ChatGPT Intake screen must optimize the repeated human copy/paste loop.

The following elements must be visually close together and available near the top of the screen:

```text
Selected file path
Copy ChatGPT prompt button
Paste ChatGPT response box
```

There must not be large panels, long templates, validation output, preview tables, fallback commands, or advanced options between the selected file path input and the ChatGPT response paste box.

Recommended layout:

```text
Left column:
- Select/current file path
- Compact Copy ChatGPT prompt button
- Optional collapsed prompt preview

Right column:
- Paste ChatGPT response box
```

Secondary controls must be placed below this primary input area or inside collapsed expanders:

```text
Options intake
Prompt preview
Validation result details
Normalized JSON
Preview row
PS7 fallback command
```

---

## 4. Copy prompt behavior

The app must provide a compact button named:

```text
Copy ChatGPT prompt
```

or, in French:

```text
Copier prompt ChatGPT
```

The button must copy only the generated ChatGPT prompt/template content to the clipboard.

The UI must not require the user to manually select/copy from a large text area during normal use.

The full generated prompt may be viewable for inspection, but it must be hidden by default in a collapsed expander:

```text
Voir le prompt généré
```

Fallback behavior for older Streamlit versions must remain compact. It must not render a large always-visible text area between the file path and the response input.

---

## 5. Workflow

```text
1. User selects or pastes the current local file path in the app.
2. User clicks Copy ChatGPT prompt.
3. App copies instructions, selected file context, and expected JSON schema to clipboard.
4. User opens a new ChatGPT conversation.
5. User pastes the prompt and drops/uploads the file.
6. ChatGPT returns JSON only.
7. User copies JSON.
8. User pastes JSON into the app in the nearby response box.
9. App validates structure and values.
10. App recalculates file facts locally.
11. App displays preview and warnings.
12. User clicks Validate and integrate.
13. App inserts/updates SQLite and writes chatgpt_intake_log.
```

---

## 6. Local validation

The app must validate:

```text
JSON parse success
required fields
controlled values
array fields
booleans
confidence range
public/export consistency
review requirements
file existence
technical file facts
possible duplicate by sha256
```

The app must recalculate technical facts locally and must not trust ChatGPT for:

```text
sha256
filesize
mimetype
filename
extension
original_path
storage_path
created_at
updated_at
```

---

## 7. Validation authority

ChatGPT output is treated as a suggestion.

The app must normalize values, apply blocking rules, enforce safety defaults, and prevent unsafe export states.

Default validation rule:

```text
canonical_validation_state = unverified
```

AI may set local AI validation fields, but AI must not set:

```text
canonical_validation_state = verified
```

unless there is an explicit human override.

---

## 8. Integration result

When the user validates and integrates, the app must:

```text
insert or update library_rows
write chatgpt_intake_log
preserve raw ChatGPT response
record validation status
record warnings and errors
recalculate local file facts
detect duplicate sha256 when possible
respect selected copy/storage mode
```

The app must display a clear result message after integration.

---

## 9. PS7 fallback

The PS7 fallback command must remain available for debugging or recovery.

It must not interrupt the primary GUI copy/paste workflow.

The fallback command should be hidden by default in a collapsed expander:

```text
Fallback PS7
```
