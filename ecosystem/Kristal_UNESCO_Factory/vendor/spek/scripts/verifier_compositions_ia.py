#!/usr/bin/env python3
"""Portable validation of AI-authored Spek composition registry; no Kristal scans."""
from pathlib import Path
import sys

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/verifier_compositions_ia.py <dossier_Spek>')
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root))
    from spek.composition_registry import read_registry
    data = read_registry(root)
    print(f'OK: {len(data["compositions"])} compositions IA, {len(data["assignments"])} assignations explicites; aucune inférence.')
