#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html.parser
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from common import human_bytes, save_json

UA = "EncyKlopedia-Wikidata-Local-Manager/0.4 (local research tool)"


class Links(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    self.hrefs.append(v)


def get_text(url: str, timeout: int = 40) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def head(url: str, timeout: int = 40) -> dict:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return {
            "content_length": int(r.headers.get("Content-Length") or 0),
            "last_modified": r.headers.get("Last-Modified"),
            "etag": r.headers.get("ETag"),
            "final_url": r.geturl(),
        }


def discover(base_url: str, dump_format: str = "auto") -> dict:
    if not base_url.endswith("/"):
        base_url += "/"
    p = Links(); p.feed(get_text(base_url))
    dirs = sorted({h.strip("/") for h in p.hrefs if re.fullmatch(r"20\d{6}/?", h)}, reverse=True)
    candidates: list[dict] = []
    for d in dirs[:8]:
        u = f"{base_url}{d}/"
        q = Links(); q.feed(get_text(u))
        files = q.hrefs
        for f in files:
            m = re.fullmatch(r"wikidata-(\d{8})-all\.json\.(bz2|gz)", f)
            if not m:
                continue
            date, compression = m.group(1), m.group(2)
            if dump_format in {'gz','bz2'} and compression != dump_format:
                continue
            sha_name = f"wikidata-{date}-sha1sums.txt"
            sha1 = None
            if sha_name in files:
                txt = get_text(u + sha_name)
                for line in txt.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[-1].lstrip("*") == f:
                        sha1 = parts[0].lower()
                        break
            meta = head(u + f)
            candidates.append({
                "dump_date": date,
                "compression": compression,
                "directory": d,
                "filename": f,
                "url": u + f,
                "sha1": sha1,
                **meta,
            })
    if not candidates:
        raise RuntimeError(f"Aucun dump JSON daté trouvé pour format={dump_format} dans l'index Wikimedia.")
    if dump_format == 'auto':
        try:
            import rapidgzip  # noqa:F401
            preferred='gz'
        except Exception:
            preferred='bz2'
        newest=max(x['dump_date'] for x in candidates)
        same=[x for x in candidates if x['dump_date']==newest]
        best=next((x for x in same if x.get('compression')==preferred),same[0])
    else:
        best = max(candidates, key=lambda x: x["dump_date"])
    best.update({
        "schema_version": "encyklopedia-wikidata-snapshot/v1",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "human_size": human_bytes(best["content_length"]),
    })
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="https://dumps.wikimedia.org/wikidatawiki/entities/")
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", choices=["auto","gz","bz2"], default="auto")
    args = ap.parse_args()
    info = discover(args.base_url, args.format)
    save_json(Path(args.out), info)
    print(json.dumps(info, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
