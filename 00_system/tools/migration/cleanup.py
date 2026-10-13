"""Nettoyage local explicitement listé, jamais automatique, racine EncyK uniquement."""
from pathlib import Path
import hashlib
import json
import re

FORMAT='encyk-obsolete-files/1.0'
HASH=re.compile(r'^[a-f0-9]{64}$')

def candidates(root,manifest):
    root=Path(root).resolve(strict=True)
    data=json.loads(Path(manifest).read_text(encoding='utf-8-sig'))
    if data.get('format')!=FORMAT or not isinstance(data.get('files'),list):
        raise ValueError('Manifeste de nettoyage invalide')
    found=[]
    for item in data['files']:
        if not isinstance(item,dict):raise ValueError('Entrée de manifeste invalide')
        rel=item.get('path'); checksum=item.get('sha256');reason=item.get('reason')
        if not isinstance(rel,str) or not rel or '\\' in rel or rel.startswith('/') or ':' in rel or any(c in ('.','..','') for c in rel.split('/')):
            raise ValueError('Chemin dangereux dans manifeste')
        if not isinstance(checksum,str) or not HASH.fullmatch(checksum):
            raise ValueError('SHA-256 obligatoire et exact pour tout fichier ciblé')
        path=root.joinpath(*rel.split('/'))
        if path.is_symlink() or any(parent.is_symlink() for parent in list(path.parents) if parent!=root and root in parent.parents):
            status='blocked_symlink'
        elif not path.exists(): status='absent'
        elif not path.is_file(): status='not_a_regular_file'
        elif path.resolve().is_relative_to(root) is False: status='outside_root'
        elif hashlib.sha256(path.read_bytes()).hexdigest()!=checksum:status='modified_keep'
        else:status='eligible'
        found.append({'path':rel,'reason':str(reason or ''),'sha256':checksum,'status':status})
    return found

def delete_selected(root,manifest,selected):
    """Suppression dans le dépôt uniquement; revalidation stricte à l'instant du clic."""
    selected=set(selected)
    current={e['path']:e for e in candidates(root,manifest)}
    if selected-set(current):raise ValueError('Sélection absente du manifeste')
    if any(current[p]['status']!='eligible' for p in selected):
        raise ValueError('Au moins un fichier est absent, modifié ou dangereux')
    removed=[]
    for rel in sorted(selected):
        path=Path(root).resolve(strict=True).joinpath(*rel.split('/'))
        # Dernière vérification; arrêt en cas de changement entre aperçu et action.
        fresh={e['path']:e for e in candidates(root,manifest)}
        if fresh[rel]['status']!='eligible':raise ValueError('Fichier changé avant suppression: '+rel)
        path.unlink();removed.append(rel)
    return removed
