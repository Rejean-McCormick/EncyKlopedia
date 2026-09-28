#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from common import load_json

UA = "EncyKlopedia-Wikidata-Local-Manager/0.4 (local research tool)"


def curl_download(url: str, dest: Path, curl: str) -> int:
    cmd = [curl, "-L", "--fail", "--retry", "20", "--retry-all-errors", "--connect-timeout", "30",
           "--continue-at", "-", "--output", str(dest), url]
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.call(cmd)


def urllib_download(url: str, dest: Path) -> int:
    existing = dest.stat().st_size if dest.exists() else 0
    headers = {"User-Agent": UA, "Accept-Encoding": "identity"}
    if existing:
        headers["Range"] = f"bytes={existing}-"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        if existing and getattr(r, "status", None) != 206:
            print("Serveur sans reprise Range; téléchargement recommencé.", file=sys.stderr)
            existing = 0
            mode = "wb"
        else:
            mode = "ab" if existing else "wb"
        total = int(r.headers.get("Content-Length") or 0) + existing
        done = existing
        with dest.open(mode) as f:
            while True:
                b = r.read(8 * 1024 * 1024)
                if not b:
                    break
                f.write(b); done += len(b)
                if total:
                    print(f"download {done}/{total} ({done*100/total:.2f}%)", flush=True)
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--dest-dir", required=True)
    ap.add_argument("--curl", default="")
    args = ap.parse_args()
    snap = load_json(args.snapshot)
    if not snap:
        raise SystemExit("snapshot metadata absent")
    d = Path(args.dest_dir); d.mkdir(parents=True, exist_ok=True)
    dest = d / snap["filename"]
    curl = args.curl or shutil.which("curl.exe") or shutil.which("curl")
    rc = curl_download(snap["url"], dest, curl) if curl else urllib_download(snap["url"], dest)
    if rc:
        raise SystemExit(rc)
    actual = dest.stat().st_size
    expected = int(snap.get("content_length") or 0)
    if expected and actual != expected:
        raise SystemExit(f"taille incomplète: {actual} != {expected}")
    print(json.dumps({"path": str(dest), "bytes": actual, "complete": not expected or actual == expected}, indent=2))

if __name__ == "__main__":
    main()
