SPEK - PERMANENT WINDOWS LAUNCHER
=================================

No hardcoded Spek version: launchers are intentionally named START_SPEK.bat.

INSTALL:
1. Extract this ZIP into the ROOT of the Spek repository (the folder that has
   requirements.txt and the spek/ Python package).
2. Keep START_SPEK.bat and scripts/launch_spek.py together.
3. Double-click START_SPEK.bat (or run it in PowerShell).

BEHAVIOR:
- Detects whether the installed Spek CLI supports educational import.
- Prefers the bundled curated Ekole fixture if available.
- Otherwise falls back to a standard Spek example (unless --mode ekole is used).
- Compiles and verifies a FRESH local build in dist-spek-launcher/run-*/site.
- Opens http://127.0.0.1:8050/fr/ or the next free port.
- Does not kill the old server, modify canonical Kristals or publish anything.

OPTIONS:
  START_SPEK.bat --mode ekole
  START_SPEK.bat --mode standalone
  START_SPEK.bat --ekole-file C:\path\to\curated-preview.json
  START_SPEK.bat --lang en
  START_SPEK.bat --port 8070
  START_SPEK.bat --no-browser
  START_SPEK.bat --no-server

NOTE: This launcher is forward-compatible with Spek releases that preserve the
current CLI contracts: 'build', 'verify-site' and optionally 'import-educational'.
If a future release breaks those commands, the launcher reports the incompatibility
rather than claiming all future versions are guaranteed to work.

Local-only: avoid publishing any private educational data. Even a curated export
must be authorized for its intended audience. The bundled example is fictional.
