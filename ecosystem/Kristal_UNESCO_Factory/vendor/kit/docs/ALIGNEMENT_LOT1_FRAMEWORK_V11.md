# Lot 1 — Framework v11 draft.4 pin alignment (2026-10-27)

The `4.0.0-draft.4` Authoring Kit consumes the **exact** 13-file `11.0.0-draft.4` pin shared with Integration Pack `0.3.0-alpha.1`.
Only Framework `VERSION` differs from the previous common draft.3 files; `tools/v11/interop_preflight.py` is newly covered by the Kit's reviewed pin.

The v11 authoring and historical v9/v10 contracts are not changed. All pinned bytes are verified before loading Framework validator code; no migration or semantic promotion is implied.

### Independent qualification

```shell
KRISTAL_FRAMEWORK_ROOT=/path/to/Kristal-Framework KRISTAL_INTEGRATION_PACK_ROOT=/path/to/Kristal-Integration-Pack python -m unittest -v tests.test_v11_qualification
python tools/kristal.py qualify-v11 ./examples/demo-semantic-v11 --framework /path/to/Kristal-Framework --integration-pack /path/to/Kristal-Integration-Pack --locales fr,fr-CA
```

No real Windows workspace, arbitrary legacy conversion, distributed crash recovery, or production publication is certified by this check.
