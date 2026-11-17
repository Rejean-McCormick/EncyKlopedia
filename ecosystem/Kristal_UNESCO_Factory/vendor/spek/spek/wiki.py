"""Private GitHub Wiki drafts from preselected Spek/SemantiK editorial material.

Arketype chooses an editorial *shape*; it does NOT select claims. The Spek
compiler checks typed slot bindings. SemantiK realizations are supplied by the
caller; this module neither generates language nor authenticates a RuntimeSet.
No Git, network, or publication operation occurs here.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from .core import ValidationError, compile_inputs, read_json
from .document import SpekDocument, project_document
from .locale import UI

FORMAT = 'spek.wiki-draft/1.0'
SLUG = re.compile(r'[a-z0-9](?:[a-z0-9-]{0,75}[a-z0-9])?\Z')
LABELS = {
 'fr': {'claim':'Énoncé','conditions':'Conditions et portée','evidence':'Preuves','uncertainty':'Incertitudes',
        'implications':'Implications','thesis':'Thèse','premises':'Prémisses','inference':'Inférence',
        'objection':'Objections','conclusion':'Conclusion','topic':'Sujet','criterion':'Critères',
        'approach_a':'Approche A','approach_b':'Approche B','synthesis':'Synthèse','limitations':'Limites',
        'definition':'Définition','examples':'Exemples','counterexamples':'Contre-exemples','context':'Contexte',
        'limits':'Limites','objective':'Objectif','prerequisites':'Prérequis','steps':'Étapes',
        'reflection':'Réflexion','question':'Question','source_a':'Source A','source_b':'Source B',
        'perspective_a':'Perspective A','perspective_b':'Perspective B','observations':'Observations',
        'interpretation':'Interprétation','verification':'Vérification','events':'Événements'},
 'en': {'claim':'Claim','conditions':'Scope and conditions','evidence':'Evidence','uncertainty':'Uncertainty',
        'implications':'Implications','thesis':'Thesis','premises':'Premises','inference':'Inference',
        'objection':'Objections','conclusion':'Conclusion','topic':'Topic','criterion':'Criteria',
        'approach_a':'Approach A','approach_b':'Approach B','synthesis':'Synthesis','limitations':'Limitations',
        'definition':'Definition','examples':'Examples','counterexamples':'Counterexamples','context':'Context',
        'limits':'Limits','objective':'Objective','prerequisites':'Prerequisites','steps':'Steps',
        'reflection':'Reflection','question':'Question','source_a':'Source A','source_b':'Source B',
        'perspective_a':'Perspective A','perspective_b':'Perspective B','observations':'Observations',
        'interpretation':'Interpretation','verification':'Verification','events':'Events'},
 'it': {'claim':'Affermazione','conditions':'Condizioni e ambito','evidence':'Prove','uncertainty':'Incertezze',
        'implications':'Implicazioni','thesis':'Tesi','premises':'Premesse','inference':'Inferenza',
        'objection':'Obiezioni','conclusion':'Conclusione','topic':'Tema','criterion':'Criteri',
        'approach_a':'Approccio A','approach_b':'Approccio B','synthesis':'Sintesi','limitations':'Limiti',
        'definition':'Definizione','examples':'Esempi','counterexamples':'Controesempi','context':'Contesto',
        'limits':'Limiti','objective':'Obiettivo','prerequisites':'Prerequisiti','steps':'Passaggi',
        'reflection':'Riflessione','question':'Domanda','source_a':'Fonte A','source_b':'Fonte B',
        'perspective_a':'Prospettiva A','perspective_b':'Prospettiva B','observations':'Osservazioni',
        'interpretation':'Interpretazione','verification':'Verifica','events':'Eventi'}
}
CAPTIONS = {
 'fr': {'home':'Catalogue Kristal','back':'Retour au catalogue','demo':'DÉMONSTRATION — NON PUBLIABLE',
        'draft':'Brouillon privé, non autorisé à la publication','profile':'Archétype','source':'Référence de l’état',
        'warning':'Ce document est une projection dérivée. Il ne remplace pas l’état canonique.'},
 'en': {'home':'Kristal catalog','back':'Back to catalog','demo':'DEMONSTRATION — NOT PUBLISHABLE',
        'draft':'Private draft, not authorized for publication','profile':'Archetype','source':'State reference',
        'warning':'This is a derived projection, not a canonical state.'},
 'it': {'home':'Catalogo Kristal','back':'Torna al catalogo','demo':'DIMOSTRAZIONE — NON PUBBLICABILE',
        'draft':'Bozza privata, pubblicazione non autorizzata','profile':'Archetipo','source':'Riferimento stato',
        'warning':'Questa è una proiezione derivata, non lo stato canonico.'}
}

# The Markdown Wiki consumes the same explicitly realized typed slots as HTML/TeX.
for _lang in LABELS:
    for _slot in ('entities','relations','stages','links','axes','entries','period_context',
                  'accounts','reconciliations','scope','concepts','specializations',
                  'constraints','sources','attributions'):
        LABELS[_lang][_slot] = UI[_lang][_slot]

def safe_md(value: str) -> str:
    """Escape supplied realizations as plain Markdown text, never raw HTML/links."""
    value = ' '.join(str(value).split())
    # HTML is never passed through. Escape special Markdown tokens and table pipes.
    return re.sub(r'([\\`*_{}\[\]()<>#+!|])',r'\\\1',value)

def load_profiles(path: Path) -> dict:
    raw = read_json(path)
    if raw.get('format')!='spek.wiki-archetype-templates/1.0':
        raise ValidationError('Unknown wiki archetype templates contract')
    items=raw.get('archetypes')
    if not isinstance(items,dict) or not items:raise ValidationError('No archetype profiles')
    for slug,spec in items.items():
        if not SLUG.fullmatch(slug):raise ValidationError('Unsafe archetype slug')
        allowed=spec.get('allowed_layouts')
        if not isinstance(allowed,list) or not allowed or len(set(allowed))!=len(allowed):
            raise ValidationError('Invalid layout list: '+slug)
        if spec.get('preferred_layout') not in allowed:
            raise ValidationError('Missing preferred layout: '+slug)
    return items

def validate_profile(document: SpekDocument, profile: str, templates: dict) -> dict:
    if profile not in templates:
        raise ValidationError('Unknown Arketype profile: '+profile)
    selected=templates[profile]
    allowed=set(selected['allowed_layouts'])
    if not document.sections:
        raise ValidationError('No sections to render')
    for section in document.sections:
        if section.layout not in allowed:
            raise ValidationError('Layout '+section.layout+' is not admitted for archetype '+profile)
    return selected

def require_semantik(model, lang: str) -> dict:
    """Require explicit SemantiK provenance on EVERY realized key, not a claim of attestation.

    The producer must separately verify signed RuntimeSets and the upstream
    authorization. A status=qualified field by itself is not cryptographic proof.
    """
    keys={model.source['article'][f'{p}_key'] for p in ('title','subtitle','abstract')}
    for section in model.sections:
        keys.add(section['heading_key'])
        for refs in section.get('slots',{}).values():
            refs=[refs] if isinstance(refs,str) else refs
            for ref in refs:
                src=model.units.get(ref) or model.evidence.get(ref)
                keys.add(src['realization_key'])
    ids={}
    for key in sorted(keys):
        item=model.realizations['entries'][key][lang]
        if item.get('channel')!='semantik_architect' or item.get('status')!='qualified':
            raise ValidationError(f'SemantiK qualified realization required for {key}/{lang}')
        if not item.get('request_id') or not item.get('runtime_set_id'):
            raise ValidationError(f'Missing SemantiK request / RuntimeSet: {key}/{lang}')
        ids[key]={'request_id':item['request_id'],'runtime_set_id':item['runtime_set_id']}
    return ids

def _lines_for_items(items, style, label):
    # Keep each admitted unit exactly once and in source order; never rewrite words.
    if not items:return []
    header='### '+label
    if style=='numbered':
        return [header,'']+[f'{i}. {safe_md(v.text)}' for i,v in enumerate(items,1)]+['']
    return [header,'']+[f'- {safe_md(v.text)}' for v in items]+['']

def render_document(document:SpekDocument, *,slug:str,archetype:str,profile:dict,demo:bool) -> dict[str,str]:
    if not SLUG.fullmatch(slug):raise ValidationError('Unsafe Wiki page slug')
    lang=document.language; cap=CAPTIONS[lang]; labels=LABELS[lang]
    title=safe_md(document.title)
    lines=[f'# {title}','',f'**{cap["demo"] if demo else cap["draft"]}**','',
        safe_md(document.subtitle),'',safe_md(document.abstract),'',
        f'- **{cap["profile"]} :** `{archetype}` (`{profile["arketype_id"]}`)',
        f'- **Spek :** `spek.wiki-draft/1.0`',
        f'- **{cap["source"]} :** `{safe_md(document.source_state_ref) or "not_published"}`','',
        '> '+safe_md(cap['warning']),'']
    for section in document.sections:
        lines.extend(['## '+safe_md(section.heading),''])
        for slot,items in section.slots.items():
            if not items:continue
            ordered=slot in {'premises','steps','events','prerequisites'}
            lines.extend(_lines_for_items(items,'numbered' if ordered else 'bullets',labels.get(slot,slot)))
        lines.extend([''])
    lines.extend(['---','',f'[{cap["back"]}](Home)',''])
    page='Kristal-'+slug+'.md'
    home='\n'.join(['# '+cap['home'],'',f'**{cap["demo"] if demo else cap["draft"]}**','',
                   '- ['+title+']('+page[:-3]+')',''])
    sidebar='\n'.join(['# '+cap['home'],'','[Home](Home)',
                    '- ['+title+']('+page[:-3]+')',''])
    return {page:'\n'.join(lines), 'Home.md':home, '_Sidebar.md':sidebar}

def _sha(data: bytes) -> str:return hashlib.sha256(data).hexdigest()

def build_wiki(*,source:Path,realizations:Path,layouts:Path,templates:Path,
               archetype:str,language:str,slug:str,out:Path,
               demonstration:bool=False,state_snapshot:Path|None=None)->dict:
    if language not in CAPTIONS:raise ValidationError('Unsupported wiki language')
    if not SLUG.fullmatch(slug):raise ValidationError('Unsafe wiki slug')
    template_profiles=load_profiles(templates)
    layoutdefs=[read_json(p) for p in sorted(Path(layouts).glob('*.json'))]
    if not layoutdefs:raise ValidationError('Missing Spek typed layouts')
    snapshot=read_json(Path(state_snapshot)) if state_snapshot else None
    model=compile_inputs(read_json(Path(source)),read_json(Path(realizations)),layoutdefs,
           languages=(language,),state_snapshot=snapshot,production=False)
    doc=project_document(model,language)
    prof=validate_profile(doc,archetype,template_profiles)
    if not demonstration:
        if model.demo:raise ValidationError('Unqualified SemantiK realizations or unverified source')
        require_semantik(model,language)
        if not model.source_verified:
            raise ValidationError('Pinned source reference not verified')
        if model.source['source'].get('disclosure')!='approved':
            raise ValidationError('Disclosure approval required')
        if model.source['source'].get('scientific_review')!='approved':
            raise ValidationError('Scientific review required')
        if model.source['source'].get('language_review',{}).get(language)!='approved':
            raise ValidationError('Language review required')
    pages=render_document(doc,slug=slug,archetype=archetype,profile=prof,demo=demonstration)
    out=Path(out).expanduser()
    if out.exists() or out.is_symlink():raise ValidationError('Wiki output must be a NEW directory')
    resolved=out.resolve()
    for path in [source,realizations,layouts,templates]+([state_snapshot] if state_snapshot else []):
        if resolved.is_relative_to(Path(path).resolve()):
            raise ValidationError('Wiki destination must be outside source inputs')
    if any(p.is_symlink() for p in list(out.parents) if p.exists()):
        raise ValidationError('Output must not traverse symlinks')
    if any((p/'.git').exists() for p in out.parents):
        raise ValidationError('Wiki private draft must be outside ALL Git repositories')
    if not out.parent.is_dir():raise ValidationError('Output parent must already exist')
    stage=Path(tempfile.mkdtemp(prefix='.'+out.name+'-spek-stage-',dir=out.parent))
    try:
        hashes={}
        for name,body in sorted(pages.items()):
            b=body.encode('utf8');(stage/name).write_bytes(b);hashes[name]=_sha(b)
        manifest={'format':FORMAT,'status':'PRIVATE_CANDIDATE_NOT_PUBLISHED',
                  'authorization':'EXTERNAL_C1_C2_REQUIRED',
                  'semantik_runtime_authentication':'EXTERNAL_REQUIRED',
                  'archetype':archetype,'arketype_id':prof['arketype_id'],
                  'preferred_layout':prof['preferred_layout'],
                  'used_layouts':[s.layout for s in doc.sections],
                  'language':language,'article_id':doc.article_id,
                  'source_sha256':doc.source_sha256,'realizations_sha256':doc.realizations_sha256,
                  'layouts_sha256':doc.layouts_sha256,'source_verified':doc.source_verified,
                  'demonstration':bool(demonstration),'files':hashes}
        (stage/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
        verify_wiki(stage)
        os.rename(stage,out) # NO replacing existing paths
    finally:
        if stage.exists():shutil.rmtree(stage)
    return manifest

def verify_wiki(path:Path)->dict:
    root=Path(path)
    if not root.is_dir() or root.is_symlink():raise ValidationError('Unsafe Wiki directory')
    manifest=read_json(root/'manifest.json')
    if manifest.get('format')!=FORMAT:raise ValidationError('Not a Spek Wiki draft')
    files=manifest.get('files')
    if not isinstance(files,dict) or not files:raise ValidationError('Missing wiki file inventory')
    if not {'Home.md','_Sidebar.md'}<=set(files):raise ValidationError('Missing wiki navigation')
    actual={p.name for p in root.iterdir() if p.is_file() and p.name!='manifest.json'}
    if set(files)!=actual:raise ValidationError('Missing or undeclared Wiki files')
    for name, expected in files.items():
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.md',name) or not re.fullmatch(r'[a-f0-9]{64}',str(expected)):
            raise ValidationError('Invalid wiki path or digest')
        p=root/name
        if p.is_symlink() or not p.is_file() or _sha(p.read_bytes())!=expected:
            raise ValidationError('Modified Wiki file: '+name)
    return manifest
