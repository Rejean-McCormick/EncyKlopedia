# V11 Test

**Type:** Local Kristal · **Workspace:** `kristal.local-workspace/3.2.0` · **State:** `kristal.state/9.0`

## Local workflow

```bash
python tools/kristal.py check .
python tools/kristal.py build-v9 .
```

Optional derived AI reader:

```bash
python tools/kristal.py build-ai .
python tools/kristal.py check-ai .
python tools/kristal.py read-surface . --require-ready
```

A local build, valid reader projection or successful check is not independent qualification or permission to sync/publish publicly.


## v11 demonstration

This is a fictional, local-only semantic identity demonstration, **not** a certified data corpus or production KQ allocation. `KQ1001` and `KQ1002` are illustrative in namespace `test:project`; `Q8018` is an external Wikidata item referenced solely by a demonstrative reviewed crosswalk. The dictionary lacks `KP2001` and `KQ1002` translations by design, to demonstrate honest coverage reporting.

```bash
python tools/kristal.py check .
python tools/kristal.py coverage-v11 . --locales fr,fr-CA
python tools/kristal.py build-v9 .
```
