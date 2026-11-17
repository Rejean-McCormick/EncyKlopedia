"""Offline, conflict-safe editing for Spek template_library and shared layouts.

No semantic inference, language generation or publication is implemented here.
All category files retain their explicit declared status.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import ValidationError
from .template_library import list_template_categories
from .wiki import load_profiles

SLUG = re.compile(r"[a-z][a-z0-9-]{0,49}\Z")
LAYOUT_SLUG = re.compile(r"[a-z][a-z0-9-]{0,75}\Z")
SLOT_SLUG = re.compile(r"[a-z][a-z0-9_-]{0,75}\Z")
CATEGORY_FORMAT = "spek.template-category/1.0"
LAYOUT_FORMAT = "kristal.editorial-layout/0.1"
FAMILY_TEMPLATE_FORMAT = "spek.category-template/1.0"


class TemplateConflict(ValidationError):
    """The editor's source has changed on disk since loading it."""


def source_root(root: str | Path) -> Path:
    path = Path(root).expanduser().absolute()
    if path.is_symlink() or not path.is_dir():
        raise ValidationError("Dossier Spek absent ou lien symbolique interdit")
    if not (path / 'spek' / 'core.py').is_file():
        raise ValidationError("Racine Spek incorrecte (spek/core.py absent)")
    if not (path / 'template_library').is_dir() or (path / 'template_library').is_symlink():
        raise ValidationError("template_library/ absent ou lien symbolique interdit")
    if not (path / 'layouts').is_dir() or (path / 'layouts').is_symlink():
        raise ValidationError("layouts/ absent ou lien symbolique interdit")
    return path


def safe_slug(name: str) -> str:
    if not isinstance(name, str) or not SLUG.fullmatch(name):
        raise ValidationError("Identifiant requis : lettres minuscules, chiffres et tirets; commence par une lettre")
    return name


def safe_file(root: Path, relative: str) -> Path:
    base = source_root(root)
    rel = Path(relative)
    if rel.is_absolute() or not rel.parts or any(part in {'..', '.', ''} for part in rel.parts):
        raise ValidationError("Chemin de template non autorisé")
    target = base / rel
    if not target.resolve(strict=False).is_relative_to(base.resolve()):
        raise ValidationError("Chemin hors de Spek")
    walk = base
    for item in rel.parts:
        walk = walk / item
        if walk.is_symlink():
            raise ValidationError("Lien symbolique interdit dans template_library/layouts")
    return target


def read_object(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValidationError("Lien symbolique interdit: " + str(path))
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise ValidationError(f"JSON invalide ou illisible : {path.name} — {e}") from e
    if not isinstance(data, dict):
        raise ValidationError("Objet JSON attendu : " + path.name)
    return data


def format_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def digest(path: Path) -> str | None:
    if not path.exists():
        return None
    if not path.is_file() or path.is_symlink():
        raise ValidationError('Fichier incompatible : ' + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def template_inventory(root: Path) -> dict[str, Any]:
    base = source_root(root)
    cats = list_template_categories(base / 'template_library')
    layouts = []
    for f in sorted((base / 'layouts').iterdir()):
        if f.is_symlink():
            raise ValidationError('Layout symbolique interdit: ' + f.name)
        if f.is_file() and f.suffix == '.json':
            obj = read_object(f)
            validate_layout(obj, f.stem)
            layouts.append(f.stem)
    templates = {}
    for c in cats:
        folder = base / 'template_library' / c['id']
        directory = folder / 'templates'
        if directory.is_symlink():
            raise ValidationError('Dossier templates symbolique interdit')
        items = []
        if directory.exists():
            if not directory.is_dir():
                raise ValidationError('templates/ doit être un dossier')
            for f in sorted(directory.glob('*.json')):
                if f.is_symlink():
                    raise ValidationError('Template symbolique interdit')
                obj = read_object(f)
                if obj.get('format') == 'spek.template-graph/1.0':
                    # vNext definitions are read-only here: edited only by their
                    # own strict versioned contract, not the draft JSON editor.
                    continue
                validate_family_template(obj, c['id'], f.stem)
                items.append(f.stem)
        templates[c['id']] = items
    profiles = load_profiles(base / 'template_library' / 'wiki' / 'archetype-profiles.json') if any(c['id']=='wiki' and c['status']=='implemented' for c in cats) else {}
    for slug, prof in profiles.items():
        for name in prof['allowed_layouts']:
            if name not in layouts:
                raise ValidationError(f"Archétype {slug}: layout inconnu {name}")
    return {'categories':cats,'layouts':layouts,'profiles':profiles,'templates':templates}


def validate_layout(data: dict[str, Any], name: str) -> None:
    if data.get('format') != LAYOUT_FORMAT or data.get('id') != name or not LAYOUT_SLUG.fullmatch(name):
        raise ValidationError('Layout : contrat format/id incorrect')
    if not isinstance(data.get('version'), str) or not data['version'].strip():
        raise ValidationError('Layout : version requise')
    slots = data.get('slots')
    if not isinstance(slots,dict) or not slots:
        raise ValidationError('Layout : slots non vides requis')
    for key, entry in slots.items():
        if not isinstance(key,str) or not SLOT_SLUG.fullmatch(key) or not isinstance(entry,dict):
            raise ValidationError('Slot invalide: '+str(key))
        kinds=entry.get('allowed_kinds')
        lo,hi=entry.get('min'),entry.get('max')
        if (not isinstance(kinds,list) or not kinds or not all(isinstance(k,str) and k for k in kinds)
            or not isinstance(lo,int) or isinstance(lo,bool) or not isinstance(hi,int) or isinstance(hi,bool)
            or lo < 0 or hi < lo):
            raise ValidationError('Contrat slot invalide: '+key)


def validate_family_template(obj: dict, category: str, slug: str) -> None:
    if (obj.get('format') != FAMILY_TEMPLATE_FORMAT or obj.get('id') != slug
        or obj.get('category') != category):
        raise ValidationError('Template de catégorie invalide : format/id/category')
    if not isinstance(obj.get('description'),str):
        raise ValidationError('Description de template requise')
    if obj.get('status') != 'draft':
        raise ValidationError('Ce type de template demeure un brouillon non exécutable')


def validate_category(obj: dict, name: str, *, previous: dict | None = None) -> None:
    if obj.get('format') != CATEGORY_FORMAT or obj.get('id') != name:
        raise ValidationError('Catégorie : identité format/id incorrecte')
    if obj.get('status') not in {'reserved','implemented'}:
        raise ValidationError('Catégorie : status attendu reserved/implemented')
    if not isinstance(obj.get('description'),str):
        raise ValidationError('Catégorie : description manquante')
    if previous and obj['status']!=previous.get('status'):
        raise ValidationError('Changer le statut nécessite une implémentation moteur explicite, non un simple JSON')


def validate_profile(obj: dict, slug: str, all_layouts: list[str]) -> None:
    if not LAYOUT_SLUG.fullmatch(slug):
        raise ValidationError('Identifiant archétype invalide')
    allowed=obj.get('allowed_layouts')
    if not isinstance(allowed,list) or not allowed or not all(isinstance(x,str) for x in allowed) or len(set(allowed))!=len(allowed) or not all(x in all_layouts for x in allowed):
        raise ValidationError('Archétype : allowed_layouts inconnus, répétés ou vides')
    if obj.get('preferred_layout') not in allowed:
        raise ValidationError('Archétype : preferred_layout doit être admis')
    if not isinstance(obj.get('arketype_id'),str) or not obj['arketype_id']:
        raise ValidationError('Archétype : arketype_id nécessaire')
    if not isinstance(obj.get('label'),str) or not obj['label'].strip():
        raise ValidationError('Archétype : label nécessaire')


def backup_file(root: Path, relative: str) -> Path | None:
    path=safe_file(root, relative)
    if not path.exists():return None
    base=Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.spek') / 'Spek' / 'template-manager-backups'
    now=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    stamp=now+'-'+uuid.uuid4().hex[:8]
    out=base/stamp/relative
    out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,out,follow_symlinks=False)
    return out


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile('wb',dir=path.parent,prefix='.spek-tmp-',delete=False) as f:
            tmp=Path(f.name)
            f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if tmp is not None and tmp.exists():tmp.unlink()


def change_json(root: Path, relative: str, obj: dict, expected_hash: str | None, *, kind: str, item: str = '') -> Path | None:
    base=source_root(root);path=safe_file(base,relative)
    old_hash=digest(path)
    if old_hash!=expected_hash:
        raise TemplateConflict('Fichier modifié depuis son ouverture. Recharge avant de sauvegarder.')
    previous=read_object(path) if old_hash else None
    inv=template_inventory(base)
    if kind=='layout':
        if relative!=f'layouts/{item}.json':raise ValidationError('Chemin layout incohérent')
        validate_layout(obj,item)
        if old_hash and composition_layout_references(base,item):
            from .composition_registry import read_registry
            for cid,doc in read_registry(base)['compositions'].items():
                for section in doc['sections_in_order']:
                    if section['layout_id'] != item:
                        continue
                    if obj['version'] != section['layout_version']:
                        raise ValidationError('Composition IA '+cid+' requiert la version '+section['layout_version'])
                    for slot,needed in section['required_slots'].items():
                        spec = obj.get('slots',{}).get(slot)
                        if not spec or not spec['min'] <= needed <= spec['max']:
                            raise ValidationError('Composition IA '+cid+' requiert le slot '+slot)
    elif kind=='category':
        if relative!=f'template_library/{item}/category.json':raise ValidationError('Chemin catégorie incohérent')
        validate_category(obj,item,previous=previous)
    elif kind=='profile':
        if relative!='template_library/wiki/archetype-profiles.json':raise ValidationError('Chemin profil incohérent')
        if previous is None:raise ValidationError('Registre Wiki absent')
        if obj.get('format')!=previous.get('format') or set(obj.get('archetypes',{}))!=set(previous.get('archetypes',{})):
            raise ValidationError('Modification du catalogue des archétypes interdite dans l’éditeur')
        for slug, prof in obj['archetypes'].items():validate_profile(prof,slug,inv['layouts'])
        load_profiles_sanity(obj)
    elif kind=='family':
        bits=Path(relative).parts
        if len(bits)!=4 or bits[0]!='template_library' or bits[2]!='templates' or bits[3]!=item+'.json':
            raise ValidationError('Chemin de catégorie incohérent')
        validate_family_template(obj,bits[1],item)
    else:raise ValidationError('Type de fichier inconnu')
    copied=backup_file(base,relative)
    atomic_write(path,format_json(obj).encode('utf-8'))
    return copied


def load_profiles_sanity(obj: dict) -> None:
    if obj.get('format')!='spek.wiki-archetype-templates/1.0':
        raise ValidationError('Format du registre Wiki incorrect')
    a=obj.get('archetypes')
    if not isinstance(a,dict) or not a:raise ValidationError('Profils absents')
    for slug,row in a.items():
        if row.get('preferred_layout') not in row.get('allowed_layouts',[]):
            raise ValidationError('Profil invalide: '+slug)


def save_profile(root: Path, slug: str, obj: dict, expected_hash: str) -> Path | None:
    base=source_root(root)
    rel='template_library/wiki/archetype-profiles.json'
    path=safe_file(base,rel)
    if digest(path)!=expected_hash:
        raise TemplateConflict('Registre des archétypes modifié entre-temps. Recharge.')
    record=read_object(path)
    if slug not in record.get('archetypes',{}):raise ValidationError('Archétype inconnu: '+slug)
    inv=template_inventory(base)
    validate_profile(obj,slug,inv['layouts'])
    record['archetypes'][slug]=obj
    return change_json(base,rel,record,expected_hash,kind='profile')


def create_category(root: Path, name: str, description: str) -> Path:
    base=source_root(root);name=safe_slug(name)
    folder=safe_file(base,f'template_library/{name}')
    if folder.exists():raise ValidationError('Catégorie déjà présente')
    folder.mkdir()
    try:
        atomic_write(folder/'category.json',format_json({'format':CATEGORY_FORMAT,'id':name,'status':'reserved','description':description}).encode('utf-8'))
        (folder/'README.md').write_text(f'# {name}\n\nCatégorie réservée. Aucun moteur de rendu déclaré.\n',encoding='utf-8')
    except Exception:
        shutil.rmtree(folder)
        raise
    return folder


def create_layout(root: Path, slug: str, *, source: str | None = None) -> Path:
    base=source_root(root);slug=safe_slug(slug)
    path=safe_file(base,f'layouts/{slug}.json')
    if path.exists():raise ValidationError('Layout déjà existant')
    if source:
        source=safe_slug(source)
        data=read_object(safe_file(base,f'layouts/{source}.json'))
        data['id']=slug
    else:
        data={'format':LAYOUT_FORMAT,'id':slug,'version':'0.1.0','intent':'to_define',
              'audience':'to_define','slots':{'content':{'allowed_kinds':['statement'],'min':1,'max':1}}}
    validate_layout(data,slug)
    atomic_write(path,format_json(data).encode('utf-8'))
    return path


def create_family_template(root: Path, category: str, slug: str, *, source: str | None = None) -> Path:
    base=source_root(root);category=safe_slug(category);slug=safe_slug(slug)
    inv=template_inventory(base)
    cat=next((c for c in inv['categories'] if c['id']==category),None)
    if cat is None:raise ValidationError('Catégorie inexistante')
    if cat['status']!='reserved':
        raise ValidationError('Cette catégorie possède son propre contrat; modifie son registre existant')
    path=safe_file(base,f'template_library/{category}/templates/{slug}.json')
    if path.exists():raise ValidationError('Template déjà présent')
    if source:
        src=safe_slug(source)
        data=read_object(safe_file(base,f'template_library/{category}/templates/{src}.json'))
        data['id']=slug
    else:
        data={'format':FAMILY_TEMPLATE_FORMAT,'id':slug,'category':category,'status':'draft',
              'description':'Nouveau brouillon de gabarit. Aucun moteur de génération associé.',
              'sections':[]}
    validate_family_template(data,category,slug)
    atomic_write(path,format_json(data).encode('utf-8'))
    return path


def composition_layout_references(root: Path, layout_name: str) -> list[str]:
    registry = root / 'template_library' / 'wiki' / 'composition-registry.json'
    if not registry.exists():
        return []
    from .composition_registry import read_registry
    compositions = read_registry(root)['compositions']
    return [key for key, doc in compositions.items()
            if any(row['layout_id'] == layout_name for row in doc['sections_in_order'])]


def delete_template(root: Path, relative: str, expected_hash: str) -> Path:
    base=source_root(root);p=Path(relative)
    pieces=p.parts
    allowed=(len(pieces)==2 and pieces[0]=='layouts' and pieces[1].endswith('.json')) or (
        len(pieces)==4 and pieces[0]=='template_library' and pieces[2]=='templates' and pieces[3].endswith('.json'))
    if not allowed:raise ValidationError('Suppression autorisée uniquement pour les layouts et brouillons de catégorie')
    target=safe_file(base,relative)
    if digest(target)!=expected_hash:raise TemplateConflict('Fichier modifié depuis son ouverture. Recharge.')
    if pieces[0]=='layouts':
        refs = composition_layout_references(base, p.stem)
        if refs:
            raise ValidationError('Layout utilisé par les compositions IA : '+', '.join(refs[:3]))
        inv=template_inventory(base)
        for slug,prof in inv['profiles'].items():
            if p.stem in prof['allowed_layouts']:
                raise ValidationError(f'Layout utilisé par l’archétype {slug} : retirer sa référence avant de le supprimer')
    saved=backup_file(base,relative)
    target.unlink()
    assert saved is not None
    return saved
