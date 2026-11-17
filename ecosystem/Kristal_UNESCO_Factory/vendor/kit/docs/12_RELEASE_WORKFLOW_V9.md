# 12 — Local v9 lifecycle and hosted v10 publication

## Local / offline

```bash
python tools/kristal.py check PATH
python tools/kristal.py build-v9 PATH
python tools/kristal.py publish-v9 PATH
python tools/kristal.py activate-v9 PATH --channel current   # optional local channel
```

A local build or release does not automatically authorize a hosted GitHub publication or any operational action.

## Hosted v10

The normal owner workflow is Framework-pinned build → read-surface (if appropriate) → Manager validation → C1 independent qualification → C2 exact owner grant → policy-approved synchronization → C3 collection verification → immutable release → optional activation. GitHub writes to public repositories are disclosures and must be reviewed **before** push/merge.

The Kit's `github-*` commands are advanced compatibility utilities, not proof of external qualification or a replacement for Bootstrap.

## Activation

Activation is a distinct mutable channel transition. Do not activate by default when building, synchronizing or publishing, and do not alter v9 State Commitments to change host channels.
