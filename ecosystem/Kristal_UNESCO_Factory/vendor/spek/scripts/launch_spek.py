"""Start a local Spek preview without pinning a Spek version.

Supported capabilities are detected from the installed CLI and example files.
The launcher never modifies Spek source data or publishes to the internet.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import webbrowser

ROOT = Path(__file__).resolve().parent.parent


def spek(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "spek", *map(str, args)]
    print("\n> " + " ".join(command), flush=True)
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )
    return result


def fail(message: str) -> int:
    print("\n[ERROR] " + message, file=sys.stderr, flush=True)
    return 1


def newest_run_dir() -> Path:
    base = ROOT / "dist-spek-launcher"
    base.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for suffix in range(100):
        folder = base / f"run-{stamp}-{suffix:02d}"
        if not folder.exists():
            folder.mkdir()
            return folder
    raise RuntimeError("Could not allocate a distinct preview folder")


def choose_profile(requested: str, supports_education: bool, fixture: Path | None) -> str:
    if requested == "ekole":
        if not supports_education:
            raise RuntimeError("This Spek CLI has no import-educational command; select --mode standalone")
        if fixture is None or not fixture.is_file():
            raise RuntimeError("No curated Ekole export was found; use --ekole-file PATH")
        return "ekole"
    if requested == "standalone":
        return "standalone"
    if supports_education and fixture is not None and fixture.is_file():
        return "ekole"
    return "standalone"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Version-independent Windows launcher for the local Spek demo"
    )
    parser.add_argument("--mode", choices=["auto", "ekole", "standalone"], default="auto")
    parser.add_argument("--ekole-file", type=Path, help="A curated, authorized Ekole projection JSON")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--lang", choices=["fr", "en", "it"], default="fr")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-server", action="store_true", help="Build/verify only, leave output on disk")
    args = parser.parse_args(argv)

    if not (ROOT / "spek" / "__main__.py").is_file():
        return fail(f"No Spek source package at {ROOT}. Install this launcher next to requirements.txt")
    if not (1 <= args.port <= 65535):
        return fail("Port must be between 1 and 65535")

    help_result = spek("--help", capture=True)
    if help_result.returncode:
        detail = (help_result.stderr or help_result.stdout or "Unable to invoke Spek").strip()
        return fail(detail)
    help_text = help_result.stdout
    for command in ("build", "verify-site"):
        if command not in help_text:
            return fail(f"The installed Spek CLI does not expose '{command}'; launcher needs an update")
    supports_education = "import-educational" in help_text

    default_fixture = ROOT / "examples" / "education" / "ekole-curated-preview.json"
    fixture = (args.ekole_file.resolve() if args.ekole_file else default_fixture)
    try:
        mode = choose_profile(args.mode, supports_education, fixture)
        workdir = newest_run_dir()
    except (RuntimeError, OSError) as exc:
        return fail(str(exc))

    print("\n========================================")
    print("    SPEK - LOCAL PREVIEW")
    print("========================================")
    print(f"Project: {ROOT}")
    print(f"Detected profile: {mode}")
    print(f"Run directory: {workdir}")
    print("Demonstration/local preview only; not a public release.", flush=True)

    site = workdir / "site"
    if mode == "ekole":
        export_dir = workdir / "imported"
        if spek("import-educational", "--adapter", "ekole", "--input", str(fixture),
                "--out-dir", str(export_dir)).returncode:
            return fail("Educational import failed. Verify that the export is curated and authorized")
        source = export_dir / "article.json"
        realizations = export_dir / "realizations.json"
    else:
        source = ROOT / "examples" / "article.json"
        realizations = ROOT / "examples" / "realizations.json"
        if not source.is_file() or not realizations.is_file():
            return fail("Standalone examples not found. Pass --mode ekole with a curated export")

    if spek("build", "--source", str(source), "--realizations", str(realizations),
            "--out", str(site), "--formats", "html,pdf,tex").returncode:
        return fail("Compilation failed. No preview server was started")
    if spek("verify-site", str(site)).returncode:
        return fail("Artifact verification failed. No preview server was started")

    entry = site / args.lang / "index.html"
    if not entry.is_file():
        return fail(f"Compiled site has no page for '{args.lang}': {entry}")

    print(f"\n[VERIFIED] {mode} output: {site}", flush=True)
    if args.no_server:
        print("[DONE] Use --no-server only for building, or rerun without it to preview.")
        return 0

    handler = partial(SimpleHTTPRequestHandler, directory=str(site))
    server = None
    chosen_port = None
    for port in range(args.port, min(args.port + 30, 65536)):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), handler)
            chosen_port = port
            break
        except OSError:
            continue
    if server is None:
        return fail(f"No available localhost port in {args.port}..{min(args.port + 29, 65535)}")
    url = f"http://127.0.0.1:{chosen_port}/{args.lang}/"
    print(f"\n[READY] {url}")
    if chosen_port != args.port:
        print(f"[NOTE] Port {args.port} was occupied; using {chosen_port} instead.")
    print("[STOP] Press Ctrl+C in this window. Other servers are not touched.", flush=True)
    try:
        if not args.no_browser:
            webbrowser.open(url, new=2)
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\n[STOPPED] Local Spek preview", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
