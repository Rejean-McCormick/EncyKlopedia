"""Lecture d'un guide Arketype 1.4 non canonique, jamais injection dans state_scope."""
from pathlib import Path
import json

def load_guidance(path):
    if not path:return None
    x=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(x,dict) or x.get('format')!='arketype.scope-guidance/1.0' or x.get('status')!='draft_requires_review':
        raise ValueError('Guide Arketype 1.4 de conception attendu')
    if x.get('publication_authorized') is not False or x.get('activation_authorized') is not False:
        raise ValueError('Un guide Arketype ne peut autoriser ni publication ni activation')
    for k in ('structure','dimensions'):
        if not isinstance(x.get(k),dict):raise ValueError('Guide Arketype mal formé: '+k)
    for k in ('inclusions','exclusions','coverage_questions','limitations'):
        if not isinstance(x.get(k),list):raise ValueError('Guide Arketype mal formé: '+k)
    if not isinstance(x.get('profile_slug'),str):raise ValueError('profile_slug manquant')
    return x
