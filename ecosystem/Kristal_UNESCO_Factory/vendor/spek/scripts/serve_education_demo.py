"""Launch the isolated Spek v0.5 Ekole preview on localhost only.

This script is part of the optional Windows launcher, and uses stdlib only.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import webbrowser


def main() -> int:
    parser = argparse.ArgumentParser(description="Spek v0.5 local educational preview")
    parser.add_argument("--site", default="dist-education-v05-demo")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--lang", choices=("fr", "en", "it"), default="fr")
    parser.add_argument("--no-browser", action="store_true", help="For automated smoke testing")
    args = parser.parse_args()

    site = Path(args.site).resolve()
    entry = site / args.lang / "index.html"
    if not entry.is_file():
        print(f"[ERROR] Missing generated page: {entry}", file=sys.stderr)
        return 2

    handler = partial(SimpleHTTPRequestHandler, directory=str(site))
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as exc:
        print(f"[ERROR] Cannot open port {args.port}: {exc}", file=sys.stderr)
        print("Another server may already be running. Close it, or use another port.", file=sys.stderr)
        return 3

    url = f"http://127.0.0.1:{httpd.server_port}/{args.lang}/"
    print(f"[READY] Spek v0.5 Ekole demo: {url}", flush=True)
    print("[STOP] Press Ctrl+C in this window. Nothing on port 8000 is modified.", flush=True)
    try:
        if not args.no_browser:
            webbrowser.open(url, new=2)
        httpd.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\n[STOPPED] Spek v0.5 local preview.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
