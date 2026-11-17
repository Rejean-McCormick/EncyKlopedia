"""Private, noncanonical Spek vNext discourse plans and source-literal previews.

Does not select argumentative relations, invent facts or claim GF realization.
The preview is a demonstration with explicitly sourced UNESCO vocabulary literals.
For real prose, SemantiK CommunicationRequest/Result pairs must be supplied and verified.
"""
from __future__ import annotations
import hashlib
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parent
SPEK_ROOT = ROOT / 'vendor' / 'spek'
if str(SPEK_ROOT) not in sys.path:
    sys.path.insert(0, str(SPEK_ROOT))
from spek.composition.engine import Library, resolve, dialogue_plan, materialize, render_html, render_markdown
from spek.composition.discourse import discourse_audit
from spek.core import ValidationError

LANGUAGES = ('fr','en')


def dump(path: Path, val: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(val, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')


def source_label(concept: dict, language: str) -> str:
    labels = concept.get('preferred_labels') or {}
    a = labels.get(language) or []
    return str(a[0]) if a else concept['unesco_id']


def source_definition(concept: dict, language: str) -> str | None:
    # Only actual SKOS definition literals: do not relabel scope notes as definitions.
    definitions = concept.get('definitions') or {}
    values = definitions.get(language) or []
    return str(values[0]) if values and str(values[0]).strip() else None


def slot(name: str, cid: str, lang: str, kind: str) -> dict:
    key = f'{cid}.{lang}.{name}'
    return {'node_type':'text_slot','kind':kind,'realization_key':key,
            # Planned request reference; actual authorized CommunicationRequest
            # does NOT exist until supplied by the SemantiK source process.
            'communication_request_ref':f'requests/{key}.json'}


def instance_for(concept: dict, lang: str, actual_definition: bool) -> dict:
    cid = concept['unesco_id']
    if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9._-]{0,64}', cid):
        raise ValueError('Unsupported UNESCO concept identifier')
    if actual_definition:
        ref = 'rhetorical.definition@1.0.0'
        bindings = {'term':slot('term',cid,lang,'concept'),
                    'definition':slot('definition',cid,lang,'definition')}
    else:
        ref = 'rhetorical.assertion@1.0.0'
        bindings = {'statement':slot('statement',cid,lang,'claim'),
                    'scope':slot('scope',cid,lang,'scope')}
    return {'format':'spek.composition-instance/1.0',
            'authority':'editorial_bindings_explicit_not_approved',
            'instance_id':f'unesco-{cid}-{lang}', 'template_ref':ref,
            'bindings':bindings,
            'presentation':{'layout_variant':'flow','show_template_labels':False,'join_mode':'block'}}


def source_fixture(concept: dict, language: str, definition: str | None,
                   *, description: str | None=None, micro_label: str | None=None) -> dict:
    cid=concept['unesco_id'];label=source_label(concept,language)
    # Only externally reported source facts + transparent editorial framing.
    # NEVER SemantiK output; never scientific truth without independent review.
    if definition:
        texts={f'{cid}.{language}.term':label, f'{cid}.{language}.definition':definition}
    else:
        if description:
            statement=(f'Wikidata décrit le candidat associé à « {label} » comme « {description} ».' if language=='fr' else
                       f'Wikidata describes the candidate associated with “{label}” as “{description}”.')
        else:
            statement=(f'Le Thésaurus UNESCO répertorie « {label} ».' if language=='fr' else
                       f'The UNESCO Thesaurus lists “{label}”.')
        micro=micro_label or '—'
        scope=(f'Ce concept est classé dans le microthésaurus « {micro} ».' if language=='fr' else
               f'This concept is classified under the “{micro}” microthesaurus.')
        texts={f'{cid}.{language}.statement':statement,f'{cid}.{language}.scope':scope}
    return {'format':'kristal.layout-realizations/0.1',
            'note':'SOURCE LITERAL / EDITORIAL DISPLAY FIXTURE; NOT SEMANTIK/GF',
            'entries':{key:{language:{'text':value,'status':'fixture',
                      'provider':'unesco_source_literal_editorial_preview_not_gf'}} for key,value in texts.items()}}


def build(concepts:dict, groups:list, directory:Path,
          *, descriptions:dict|None=None, mapping:dict|None=None, callback:Callable[[str],None]|None=None,
          cancelled:Callable[[],None]|None=None) -> dict:
    """Render a fully validated discourse-plan inventory; private HTML/MD previews only.

    No P3916 identity promotion or semantic relation inference. Existing Spek
    classical site remains separate. Fails fast when template schema changes.
    """
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    lib=Library(SPEK_ROOT/'template_library')
    rhetorical = [r for r in lib.definitions if r.startswith('rhetorical.')]
    if len(rhetorical)<62:
        raise ValidationError('Catalogue rhétorique Spek incomplet (<62)')
    if callback:callback(f'Bibliothèque Spek vNext : {len(rhetorical)} templates rhétoriques chargés.')
    descriptions=descriptions or {}
    mapping=mapping or {}
    group_by_id={g['id']:g for g in groups if g.get('type')=='microthesaurus'}
    index=defaultdict(lambda:defaultdict(list))
    statuses=Counter()
    audits=Counter()
    summaries=[]
    # All refs and text sources are explicit, including the *absence* of GF requests.
    with (directory/'source_bindings.jsonl').open('w',encoding='utf-8') as provenance:
        for n,concept in enumerate(sorted(concepts.values(),key=lambda x:x['unesco_id']),1):
            if cancelled and n%50==0:cancelled()
            cid=concept['unesco_id']
            mids=concept.get('microthesaurus_ids') or []
            if len(mids)!=1:
                raise ValueError(f'Expected one microthesaurus for concept {cid}')
            mid=mids[0]
            if not re.fullmatch(r'[A-Za-z0-9._-]+',mid):raise ValueError('Unsafe microthesaurus ID')
            provenance.write(json.dumps({'concept_id':cid,'source_uri':concept.get('source_uri',''),
                              'microthesaurus_id':mid,'source_status':'UNESCO_SKOS_NOT_SEMANTICALLY_REVIEWED',
                              'wikidata_mapping_status':mapping.get(cid,{}).get('status','UNAVAILABLE'),
                              'wikidata_candidate_qid':mapping.get(cid,{}).get('wikidata_qid_candidate'),
                              'wikidata_descriptions_unreviewed':cid in descriptions,
                              'GF_qualified':False,'canonical_assertions_selected':False},ensure_ascii=False)+'\n')
            for lang in LANGUAGES:
                text=source_definition(concept,lang)
                has_definition=bool(text)
                inst=instance_for(concept,lang,has_definition)
                path=directory/'instances'/lang/f'{cid}.json'
                dump(path,inst)
                result=resolve(inst,lib)
                plan=dialogue_plan(result,lang)
                dump(directory/'dialogue'/lang/f'{cid}.json',plan)
                audit=discourse_audit(result)
                audits['templates_with_discourse_model']+=audit['templates_with_discourse_model']
                audits['declared_relations_unverified']+=audit['declared_relations_unverified']
                # Source literal preview must never masquerade as GF output.
                raw_desc=(descriptions.get(cid,{}).get('description_'+lang) or '').strip()
                # Source literal, not a source-asserted truth or a SemantiK utterance.
                if len(raw_desc)>700:raw_desc=raw_desc[:700]+'…'
                micro_label=group_by_id[mid].get('label_'+lang) or mid
                preview=source_fixture(concept,lang,text,description=raw_desc or None,micro_label=micro_label)
                if raw_desc:statuses['wikidata_literal_previews']+=1
                values=materialize(result,preview,lang)
                page=render_html(result,values,title=source_label(concept,lang),language=lang)
                # Extract only the reader-safe body generated by *native Spek*.
                marker='<article>'
                if marker not in page or '</article>' not in page:
                    raise ValidationError('Spek preview structure unknown')
                fragment=page.split(marker,1)[1].split('</article>',1)[0]
                idx_label=source_label(concept,lang)
                index[mid][lang].append((cid,idx_label,fragment,has_definition))
                statuses['instances_validated']+=1
                statuses['source_literal_previews']+=1
                statuses['skos_definitions_available' if has_definition else 'concepts_without_definition_in_language']+=1
            if n%500==0 and callback:callback(f'Plans discursifs vérifiés : {n}/{len(concepts)} concepts (FR/EN).')
    if statuses['instances_validated'] != 2*len(concepts):
        raise ValueError('Discourse plan coverage mismatch')
    table=[]
    for group in groups:
        if group.get('type')!='microthesaurus':continue
        mid=group['id'];slug='unesco-'+mid.replace('.','-')
        for lang in LANGUAGES:
            records=index[mid][lang]
            if not records:raise ValueError(f'No discourse records for group {mid} and language {lang}')
            prefix='Aperçus de notices SKOS — source littérale, PAS GF, non publiables' if lang=='fr' else 'SKOS entry previews — source literals, NOT GF, not publishable'
            title=group.get('label_'+lang) or mid
            cards=[]
            for cid,label,fragment,has_definition in records:
                status='Définition UNESCO' if has_definition and lang=='fr' else 'UNESCO definition' if has_definition else 'Libellé seulement' if lang=='fr' else 'Label only'
                cards.append('<section id="'+html.escape(cid,quote=True)+'"><h2>'+html.escape(label)+'</h2>'+
                             '<div class="kind">'+html.escape(status)+'</div>'+fragment+'</section>')
            html_doc='''<!doctype html><html lang="'''+lang+'''"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+html.escape(title)+'''</title>
<style>body{font-family:system-ui,Segoe UI,sans-serif;background:#f4f8f7;color:#18312f;max-width:980px;margin:0 auto;padding:22px;line-height:1.6}a{color:#08647c}h1{font-size:2rem}h2{font-size:1.23rem;margin:0}.note{background:#fff4d6;border-left:4px solid #ba8b2e;padding:14px}section{background:white;border:1px solid #dce8e5;padding:18px;margin:14px 0;border-radius:10px}section p{margin:9px 0}.kind{font-size:12px;color:#526c65}input{padding:12px;width:93%;font-size:16px;border-radius:6px;border:1px solid #c8d6d2}section[hidden]{display:none}</style>
<body><p><a href="../index.html">Catalogue discursif</a></p><h1>'''+html.escape(title)+'''</h1><p class="note">'''+prefix+'''<br>Les phrases de transition et les relations causales ne sont pas inférées. Le moteur Spek a vérifié les instances et organisé les textes disponibles.</p><input id="q" type="search" placeholder="Rechercher…"><div id="items">'''+''.join(cards)+'''</div><script>const q=document.querySelector('#q'),l=[...document.querySelectorAll('section')];q.addEventListener('input',()=>{const v=q.value.toLowerCase();for(const e of l)e.hidden=!e.textContent.toLowerCase().includes(v)});</script></body></html>'''
            page=directory/'previews'/lang/f'{slug}.html';page.parent.mkdir(parents=True,exist_ok=True)
            page.write_text(html_doc,encoding='utf-8')
            summaries.append({'id':mid,'language':lang,'count':len(records),'page':str(page)})
    table_html=[]
    for group in groups:
        if group.get('type')!='microthesaurus':continue
        mid=group['id'];slug='unesco-'+mid.replace('.','-')
        table_html.append('<tr><td>'+html.escape(group.get('label_fr') or mid)+'</td><td>'+str(len(index[mid]['fr']))+'</td><td><a href="previews/fr/'+slug+'.html">FR</a></td><td><a href="previews/en/'+slug+'.html">EN</a></td></tr>')
    index_html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Spek — grammaire discursive UNESCO</title><style>body{font-family:system-ui;background:#f4f8f7;color:#173631;margin:25px auto;max-width:1000px;padding:16px}h1{font-size:28px}p{line-height:1.55}.notice{padding:16px;background:#fff3d8;border-left:4px solid #ad863b}table{width:100%;border-collapse:collapse;background:white}td,th{border-bottom:1px solid #dce9e7;padding:10px;text-align:left}a{color:#006780}input{padding:10px;border:1px solid #ccd;width:90%;border-radius:6px}</style>
<h1>Spek — grammaire discursive UNESCO</h1><p class="notice">Aperçus privés fondés sur des libellés et définitions déjà présents dans l’UNESCO. <b>Ce ne sont pas des paragraphes générés ou qualifiés par SemantiK/GF.</b> Aucun raisonnement causal, aucune preuve nouvelle, aucun lien rhétorique non autorisé. Les instances et les plans de dialogue sont dans les dossiers internes.</p>
<p><input id="q" placeholder="Rechercher un microthésaurus…" type="search"></p><table><thead><tr><th>Microthésaurus</th><th>Concepts</th><th>Aperçu FR</th><th>Aperçu EN</th></tr></thead><tbody>'''+''.join(table_html)+'''</tbody></table><script>const q=document.querySelector('#q');q.addEventListener('input',()=>{for(const x of document.querySelectorAll('tbody tr'))x.hidden=!x.textContent.toLowerCase().includes(q.value.toLowerCase())});</script></html>'''
    (directory/'index.html').write_text(index_html,encoding='utf-8')
    report={'format':'kristal.unesco-factory-discourse/1.0','status':'PRIVATE_SOURCE_LITERAL_PREVIEWS_NOT_GF',
            'count_concepts':len(concepts),'languages':list(LANGUAGES),
            'template_inventory_rhetorical':len(rhetorical),
            'instance_count':statuses['instances_validated'],
            'source_literal_previews':statuses['source_literal_previews'],
            'source_definitions_by_language':statuses['skos_definitions_available'],
            'without_definition_by_language':statuses['concepts_without_definition_in_language'],
            'wikidata_literal_previews':statuses['wikidata_literal_previews'],
            'microthesaurus_preview_pages':len(summaries),
            'discourse_audit':dict(audits),
            'real_semantik_requests_supplied':0,'GF_PGF_realizations_validated':0,
            'semantic_relations_approved':0,'publication_authorized':False,
            'candidates_status':'not_canonical_not_approved',
            'no_promotion':True}
    dump(directory/'manifest_discourse.json',report)
    if callback:callback(f'Discours Spek vNext : {report["instance_count"]} instances vérifiées, {len(summaries)} aperçus microthésaurus, GF=0.')
    return report
