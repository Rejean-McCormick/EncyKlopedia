from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from scope_common import *


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    ap.add_argument('--min-free-gib', type=float, default=50.0)
    a = ap.parse_args()
    root = find_root(a.root or None)
    status_script = Path(__file__).resolve().parent / '08_status.py'
    result = subprocess.run(
        [sys.executable, str(status_script), '--root', str(root)],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    try:
        rep = json.loads(result.stdout)
    except Exception:
        rep = {'generated_at': utc_now(), 'error': result.stdout + result.stderr}
    rep['maintenance'] = {'min_free_gib': a.min_free_gib, 'disk_ok': free_gib(root) >= a.min_free_gib}
    out = root / '90_runtime/reports/status-latest.json'
    save_json(out, rep)
    log = root / '90_runtime/maintenance.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({'at': utc_now(), 'disk_free_gib': rep.get('disk_free_gib'), 'disk_ok': rep['maintenance']['disk_ok']}) + '\n')
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    raise SystemExit(0 if rep['maintenance']['disk_ok'] else 2)


if __name__ == '__main__':
    main()
