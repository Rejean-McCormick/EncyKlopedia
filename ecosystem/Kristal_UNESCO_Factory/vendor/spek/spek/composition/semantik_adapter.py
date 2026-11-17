"""Anti-corruption layer: validate real SemantiK request/results for vNext.

The pairing is explicit by leaf's communication_request_ref. We never build
semantic_graph or obligations or run a language model. Status remains private.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from spek.core import ValidationError
from spek.slot_dialogue import KIND_POLICY, compose_request, verify_result_shape
from spek.semantik_transfer import _verify_pair
from .engine import Resolved
from .commands import read_instance


def import_results(resolved: Resolved, requests_dir: Path, results_dir: Path, language: str) -> dict[str, Any]:
    requests_dir = Path(requests_dir)
    results_dir = Path(results_dir)
    for d in (requests_dir, results_dir):
        if d.is_symlink() or not d.is_dir():
            raise ValidationError('Dossier local de communication SemantiK absent ou symbolique')
    bundle: dict[str, Any] = {'format':'kristal.layout-realizations/0.1',
                             'note':'PRIVATE: SemantiK pairs checked; not a publication approval', 'entries':{}}
    for leaf in resolved.leaves:
        filename = Path(leaf.request_ref).name
        reqfile = requests_dir / filename
        resfile = results_dir / filename
        for p,d in ((reqfile,requests_dir),(resfile,results_dir)):
            if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(d.resolve()):
                raise ValidationError('Paire SemantiK absente ou fichier non sûr')
        request = read_instance(reqfile)
        result = read_instance(resfile)
        _, force, kinds, limit = KIND_POLICY[leaf.kind]
        # Request already authorized by upstream; restrict shape only.
        restricted = compose_request(request,{'force':force,'block_kinds':kinds,'max_length':limit},language=language)
        # No need to assume the external tool applied Spek constraints; verify it.
        verify_result_shape(result,{'block_kinds':restricted['constraints']['allowed_block_kinds']},request=restricted)
        record = _verify_pair(restricted,result,language,leaf.key)
        bundle['entries'][leaf.key] = {language:record}
    return bundle
