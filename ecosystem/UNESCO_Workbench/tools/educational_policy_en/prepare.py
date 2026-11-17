"""English-only UNESCO branch scope handoff. Pure copy, no canonical promotion."""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, shutil, subprocess, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r'C:\mycode\EncyKlopedia')
SOURCE = ROOT / 'UNESCO_Kristals/branches/unesco-mt1-10'
OUTPUT = ROOT / 'UNESCO_Workbench/candidates/educational-policy/en'
KRISTALIZER = Path(r'C:\mycode\Kristal\Kristalizer\kristalizer.py')
INDEX = Path(r'D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite')
SCOPE = HERE / 'scope/SCOPE_EDUCATIONAL_POLICY_EN.json'
PARAMS = HERE / 'scope/OPTIMAL_PARAMETERS_EN.json'
OMIT = {'.git', '.venv', 'node_modules', '__pycache__', 'build', 'runtime', 'release', 'materializations'}


def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,obj):
    p=Path(p);p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()


def validate(source):
    obj=load(source/'canon/domain/unesco-source.json')
    ws=load(source/'kristal.workspace.json')
    scope,params=load(SCOPE),load(PARAMS)
    cc=obj.get('concepts')
    if (obj.get('format')!='kristal.unesco-import-snapshot/1.0'
        or obj.get('unesco_microthesaurus',{}).get('id')!='mt1.10'
        or ws.get('slug')!='unesco-mt1-10'):
        raise ValueError('Unexpected UNESCO branch, expected mt1.10')
    if not isinstance(cc,list) or len(cc)!=41 or scope['subject']['expected_seed_count']!=41:
        raise ValueError('41-concept baseline missing or changed')
    ids=[c.get('unesco_id') for c in cc]
    if len(set(ids))!=41 or 'concept10' not in ids or any('mt1.10' not in c.get('microthesaurus_ids',[]) for c in cc):
        raise ValueError('Missing, duplicate or out-of-branch UNESCO concept')
    if any(not c.get('preferred_labels',{}).get('en') for c in cc):
        raise ValueError('Missing English labels')
    return cc,scope,params


def plans(source,concepts,params):
    path=source/'derived/wikidata-p3916-candidates.json'
    qid_pattern=re.compile(r'Q[1-9][0-9]*\Z')
    approved_ids={c['unesco_id'] for c in concepts}
    valid=[];seen=set()
    if path.is_file():
        for r in load(path).get('mappings',[]):
            q=r.get('qid_candidate');k=r.get('unesco_id')
            if (k in approved_ids and r.get('status')=='SINGLE_P3916_CANDIDATE'
                and r.get('local_index_status')=='FOUND_IN_LOCAL_INDEX' and isinstance(q,str)
                and qid_pattern.fullmatch(q) and q not in seen):
                seen.add(q);valid.append({'unesco_id':k,'qid_candidate':q})
    valid.sort(key=lambda r:int(r['unesco_id'][7:]))
    first=[r for r in valid if r['unesco_id']=='concept10']
    rest=[r for r in valid if r['unesco_id']!='concept10']
    max_roots=int(params['skope']['max_roots']);count=max(0,max_roots-len(first))
    if count and len(rest)>count:
        rest=[rest[round(i*(len(rest)-1)/max(1,count-1))] for i in range(count)]
    roots=(first+rest[:count])[:max_roots]
    recipes=[]
    for r in roots:
        for direction,key in [('out','outbound'),('in','inbound_optional_review_only')]:
            spec=params['skope'][key]
            recipes.append({'unesco_id':r['unesco_id'],'root':r['qid_candidate'],
                'direction':direction,'default_depth':spec['default_depth'],'branches':spec['branches'],
                'max_entities':spec['max_entities'],'convergence':params['skope']['convergence'],
                'geography':params['skope']['geography'],'status':'UNEXECUTED_REVIEW_PROPOSAL'})
    return roots, recipes


def produce(source=SOURCE,output=OUTPUT,kristalizer=KRISTALIZER,index=INDEX,zip_dir=None,scan=True,now=None,log=print):
    source=Path(source).resolve();output=Path(output).resolve();kristalizer=Path(kristalizer);index=Path(index)
    if source==output or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('Candidate output must be separated from the original workspace')
    if not source.is_dir() or source.is_symlink():
        raise FileNotFoundError('Migrated source Kristal not found or a symbolic link: '+str(source))
    concepts,scope,params=validate(source)
    tag=now or datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+os.urandom(3).hex()
    if not re.fullmatch(r'[A-Za-z0-9-]{6,60}',tag):raise ValueError('Invalid run tag')
    target=output/('SCOPE-'+tag)
    target.mkdir(parents=True,exist_ok=False)
    def msg(s):
        log(s)
        with (target/'RUN.log').open('a',encoding='utf8') as f:f.write(s+'\n')
    msg('English encyclopedia scope candidate: 41 UNESCO anchor concepts')
    dest=target/'01_CANDIDATE_WORKSPACE/unesco-mt1-10'
    def ignore(folder, names):return {n for n in names if n in OMIT or (Path(folder)/n).is_symlink()}
    shutil.copytree(source,dest,ignore=ignore)
    for tpl in (HERE/'scope/templates').glob('*.md'):
        p=dest/'docs'/tpl.name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(tpl,p)
    original_sha=sha(source/'canon/domain/unesco-source.json')
    if original_sha != sha(dest/'canon/domain/unesco-source.json'):
        raise RuntimeError('Canonical source copy does not match SHA-256')
    save(dest/'derived/encyclopedia_scope.en.json',{**scope,'status':'editorial_proposal_not_canonical',
         'source_sha256':original_sha})
    ws=load(dest/'kristal.workspace.json')
    ws['state_scope']={'domain':'education_policy','working_language':'en',
        'unesco_microthesaurus_id':'mt1.10','source_sha256':original_sha,
        'purpose':'encyclopedia_candidate','review_status':'proposal_only'}
    ws['semantic_ownership']={'owns':scope['owned_subjects'],'does_not_own':scope['excluded_subjects']}
    ws.setdefault('epistemic_model',{})['ai_output_policy']='proposal_only'
    save(dest/'kristal.workspace.json',ws)
    mappings_path=dest/'derived/wikidata-p3916-candidates.json'
    mappings={r['unesco_id']:r.get('qid_candidate','') for r in load(mappings_path).get('mappings',[])} if mappings_path.is_file() else {}
    review=target/'02_EDITORIAL_REVIEW/concepts.en.csv';review.parent.mkdir(parents=True)
    with review.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f)
        writer.writerow(['unesco_id','label_en','source_uri','scope_note_en','qid_candidate_unreviewed',
                         'proposed_facets','identity_review','claim_review','priority'])
        for c in sorted(concepts,key=lambda x:int(x['unesco_id'][7:])):
            label=c['preferred_labels']['en'][0]
            term=' '.join([label,*c.get('alternate_labels',{}).get('en',[])]).lower()
            facet=[x['id'] for x in scope['facet_taxonomy'] if any(k.lower() in term for k in x['keywords'])]
            writer.writerow([c['unesco_id'],label,c.get('source_uri',''),
                ' | '.join(c.get('scope_notes',{}).get('en',[])),mappings.get(c['unesco_id'],''),
                ';'.join(facet),'pending','not_started','pilot' if c['unesco_id']=='concept10' else 'normal'])
    roots,recipes=plans(source,concepts,params)
    save(target/'03_RESEARCH_PLAN/recipes.en.json',{'status':'NOT_EXECUTED',
        'roots':roots,'skope_recipes':recipes,'maxwd_proposed_parameters':params['maxwd'],
        'kristalizer_parameters':params['kristalizer']})
    msg(f'Scope copied. {len(roots)} QID research roots selected; no expansion executed')
    status={'status':'SKIPPED' if not scan else 'BLOCKED_KRISTALIZER_MISSING'}
    if scan and kristalizer.is_file():
        cmd=[sys.executable,str(kristalizer),'scan','--source',str(dest),
             '--output',str(target/'04_KRISTALIZER'), '--max-results',str(params['kristalizer']['max_results_per_label'])]
        if index.is_file():cmd.extend(['--index',str(index)])
        try:
            p=subprocess.run(cmd,text=True,capture_output=True,encoding='utf8',errors='replace',timeout=180)
            (target/'04_KRISTALIZER_stdout.txt').write_text(p.stdout,encoding='utf8')
            (target/'04_KRISTALIZER_stderr.txt').write_text(p.stderr,encoding='utf8')
            status={'status':'EXECUTED' if p.returncode==0 else 'FAILED',
                    'exit_code':p.returncode,'index_connected':index.is_file(),
                    'report':'04_KRISTALIZER/ANALYSE/RAPPORT.json'}
            scan_report=target/'04_KRISTALIZER/ANALYSE/RAPPORT.json'
            if p.returncode==0 and scan_report.is_file():
                observed=load(scan_report)
                status['candidate_count']=observed.get('candidates',0)
                status['v11_migration_required']=observed.get('migration_required',0)
                if observed.get('migration_required',0):
                    status['status']='V11_MIGRATION_REQUIRED'
        except subprocess.TimeoutExpired:
            status={'status':'TIMEOUT_180S'}
        msg('Kristalizer scan: '+status['status'])
    report={'format':'encyklopedia.unesco.scope-handoff/3.0','source_workspace':str(source),
        'branch':'unesco-mt1-10','language':'en','concept_count':41,
        'source_sha256':original_sha,'scope_sha256':sha(SCOPE),'parameters_sha256':sha(PARAMS),
        'kristalizer':status,'canonical_assertions_added':0,'maxwd_executed':False,
        'skope_executed':False,'publication_enabled':False,'source_modified':False}
    save(target/'05_REPORT.json',report)
    (target/'README_RESULT.txt').write_text('PRIVATE CANDIDATE ONLY. Original UNESCO workspace unchanged.\n'
         'Review concept10 / Right to education first. Send this ZIP for evidence-grounded enrichment.\n',encoding='utf8')
    zip_dir=Path(zip_dir or Path.home()/'Downloads').resolve();zip_dir.mkdir(parents=True,exist_ok=True)
    archive=zip_dir/('UNESCO-Educational-Policy-Scope-EN-'+tag+'.zip')
    if archive.exists():raise FileExistsError(archive)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(target.rglob('*')):
            if p.is_file() and not p.is_symlink():z.write(p,p.relative_to(target).as_posix())
    msg('Created ZIP: '+str(archive))
    return archive,report


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',default=str(SOURCE));ap.add_argument('--output',default=str(OUTPUT))
    ap.add_argument('--kristalizer',default=str(KRISTALIZER));ap.add_argument('--index',default=str(INDEX))
    ap.add_argument('--zip-dir',default=str(Path.home()/'Downloads'))
    ap.add_argument('--check-only',action='store_true');ap.add_argument('--no-scan',action='store_true')
    args=ap.parse_args(argv)
    try:
        if args.check_only:
            c,scope,params=validate(Path(args.source))
            print(json.dumps({'concepts':len(c),'scope':scope['subject']['title'],
                 'max_results':params['kristalizer']['max_results_per_label']},indent=2))
        else:
            archive,report=produce(Path(args.source),Path(args.output),Path(args.kristalizer),
                 Path(args.index),Path(args.zip_dir),not args.no_scan)
            print(json.dumps({'archive':str(archive),'scan':report['kristalizer']},ensure_ascii=False,indent=2))
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
