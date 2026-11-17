# Recoverable canonical v11 artifact registration (draft.3)

## Mechanism

`apply-v11-plan` now stages the **new validated graph** under `.kristal/v11/transactions/<id>.artifact`, writes a durable journal, installs the new graph without overwriting existing files, then replaces the `canon/state.index.json` atomically. The same mechanism registers a newly imported diK lexical catalog. All transactions record source/target and both index hashes. Existing canon bytes are not rewritten. **This is a recoverable two-file protocol, not a fully atomic filesystem transaction.**

A crash before the index update can leave a new unregistered artifact. A crash after index update may leave a pending journal. No step deletes/overwrites a previously registered canonical graph or catalog.

## Commands

```bash
python tools/kristal.py recover-v11 ./MyKristal --mode status
# After confirming no concurrent writer and checking the journal:
python tools/kristal.py recover-v11 ./MyKristal --mode finish
# Or only before the state index has been updated:
python tools/kristal.py recover-v11 ./MyKristal --mode rollback
```

`finish` ensures the staged artifact and pending registration are correctly installed or refuses if any bytes changed. `rollback` removes an *unregistered* newly added artifact **only when the state index still matches the prior hash**. It refuses if the state index has been committed. After completion, transaction metadata is retained for auditing.

A `.kristal/v11/transactions/writer.lock` is an exclusive writer guard. A hard process crash may leave a stale lock. **Verify no live writer is running** before removing one manually. Do not run separate legacy writers concurrently: v9 `register-artifact` does not share the new lock.

## Guarantees and caveats

- Journal plus staged bytes are immutable during pending transaction; changing either causes fail-closed recovery.
- Source plan, approval, registered KS evidence, typed identity-role map, KQ/KP registry and complete v11 graph validation are still mandatory.
- Output and state index are verified by digest. Existing target paths cannot be overwritten; existing registrations cannot be reused.
- Atomic `os.replace` does not guarantee *simultaneous* visibility of two files. Cross-platform power-loss integrity still requires fsync on parent directories, platform-specific disk tests and multi-process concurrency qualification. These tests simulate failure after artifact install and after index commit; they do not emulate an actual machine power cut.
- An artifact that was registered successfully must **never** be rolled back silently. Adoption of a new active graph or catalog remains a separate explicit operation.
