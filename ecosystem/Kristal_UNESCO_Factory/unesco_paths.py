"""Relocated UNESCO Factory default paths (stdlib only).

The older LinkedDataHub 2025 TTL is comparison input, NOT the Factory's
2026 authoritative import source. Never switch to it silently.
"""
from __future__ import annotations
import os
from pathlib import Path


def _choose(candidates):
    return next((p for p in candidates if p.is_file()),candidates[0])


def default_factory_paths(base:Path, environ=None):
    env = os.environ if environ is None else environ
    home=Path(env.get('KRISTAL_ROOT') or base.parent)
    data=Path(env.get('ENCYKLOPEDIA_DATA_HOME') or r'D:\EncyKlopedia')
    legacy=Path(r'C:\mycode\Kristal')
    ttl=_choose([
        data/'10_sources/unesco/unesco-thesaurus.ttl',
        home/'Sources/UNESCO/unesco-thesaurus.ttl',
        legacy/'Sources/UNESCO/unesco-thesaurus.ttl',
    ])
    claims=_choose([
        data/'10_sources/wikidata/wikidata-p3916.csv',
        home/'Sources/Wikidata/UNESCO-P3916/wikidata-p3916.csv',
        legacy/'Sources/Wikidata/UNESCO-P3916/wikidata-p3916.csv',
    ])
    return {
        'root':home,'ttl':ttl,'claims':claims,
        'index':data/'30_working/wikidata/wikidata.compact.sqlite',
        'output':data/'90_runtime/unesco/factory',
    }
