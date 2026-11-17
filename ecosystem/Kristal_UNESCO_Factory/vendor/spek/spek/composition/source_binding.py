"""Read-only source-anchor existence checks for explicit Spek composition leaves.

Only checks IDs against a locally supplied v11 semantic-graph artifact. This
is not a semantic entailment, proof of rhetorical relations, v9 state-pin check
or permission to publish. No local source text is included in reader outputs.
"""
from __future__ import annotations
import json
from pathlib import Path
from spek.core import ValidationError
from .engine import Resolved

MAX_STATE_BYTES = 20_000_000


def verify_v11_assertion_refs(resolved: Resolved, graph_path: Path) -> dict:
    path = Path(graph_path)
    if (not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_STATE_BYTES):
        raise ValidationError('Graphe v11 introuvable, non sûr ou trop volumineux')
    try:
        graph=json.loads(path.read_text(encoding='utf-8'))
    except (ValueError,OSError) as exc:
        raise ValidationError('Graphe v11 illisible') from exc
    if (not isinstance(graph,dict) or graph.get('schema_version')!='11.0' or
        graph.get('artifact_type')!='kristal_semantic_graph' or
        not isinstance(graph.get('assertions'),list)):
        raise ValidationError('Un graphe canonique v11 explicitement fourni est requis')
    ids=[]
    for assertion in graph['assertions']:
        if not isinstance(assertion,dict) or not isinstance(assertion.get('id'),str):
            raise ValidationError('Identifiant d’assertion v11 invalide')
        ids.append(assertion['id'])
    if len(set(ids))!=len(ids):
        raise ValidationError('Identifiants d’assertions v11 dupliqués')
    existing=set(ids)
    anchored=[leaf for leaf in resolved.leaves if leaf.source_assertion_refs]
    if not anchored:
        raise ValidationError('Aucune assertion explicitement liée aux champs Spek')
    missing={ref for leaf in anchored for ref in leaf.source_assertion_refs if ref not in existing}
    if missing:
        # Never echo private assertion IDs in errors or reader UI.
        raise ValidationError('Certaines références explicites n’existent pas dans le graphe fourni')
    return {'format':'spek.source-binding-check/1.0','status':'private_existence_only_unqualified',
            'anchored_fields':len(anchored),
            'anchored_references':sum(len(leaf.source_assertion_refs) for leaf in anchored),
            'assertions_in_supplied_graph':len(existing),
            'meaning_or_relation_verified':False,
            'publication_authorized':False}
