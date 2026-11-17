# -*- coding: utf-8 -*-
"""Pilote prive UNESCO -> Kristal/SpeK -> SemantiK candidat -> vraie GF.
Aucune publication, aucun changement dans les depots; aucun texte GF simule.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from typing import Callable
import zipfile

PROFILE = 'unesco-pilot-1'
LANGS = {'fr': ('UnescoPilotFre', 'Le Thésaurus UNESCO', 'répertorie', 'Le concept', 'appartient au', 'microthésaurus'),
         'en': ('UnescoPilotEng', 'The UNESCO Thesaurus', 'lists', 'The concept', 'belongs to the', 'microthesaurus')}
SAFE_CONCEPT = re.compile(r'^concept[0-9]+$')
MAX_SOURCE = 20_000_000

class PilotError(Exception):
    pass

class Cancelled(PilotError):
    pass

def sha(path: Path) -> str:
    d = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            d.update(block)
    return d.hexdigest()

def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def read_json(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_SOURCE:
        raise PilotError('Fichier JSON absent ou trop grand: ' + str(path))
    return json.loads(path.read_text(encoding='utf-8-sig'))

def find_latest_run(root: Path) -> Path:
    bases = [root / 'Kristalizer' / 'SORTIE' / 'UNESCO' / 'FABRIQUE',
             root / 'Kristal_UNESCO_Factory' / 'SORTIE' / 'UNESCO' / 'FABRIQUE',
             root / 'SORTIE' / 'UNESCO' / 'FABRIQUE']
    runs = [p for base in bases if base.is_dir() for p in base.glob('RUN-*') if p.is_dir()]
    if not runs:
        raise PilotError('Aucun RUN trouvé. Fournir le dossier RUN explicitement.')
    return sorted(runs, key=lambda p: p.stat().st_mtime)[-1]

def lookup_concept(run: Path, cid: str) -> dict:
    path = run / '01_INVENTAIRE' / 'concepts.jsonl'
    if not path.is_file():
        raise PilotError('Source d’autorité manquante: ' + str(path))
    if not SAFE_CONCEPT.fullmatch(cid):
        raise PilotError('Identifiant concept invalide: ' + cid)
    if path.stat().st_size > 40_000_000:
        raise PilotError('Fichier source anormalement volumineux')
    with path.open(encoding='utf-8') as f:
        found = None
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            if row.get('unesco_id') == cid:
                if found is not None: raise PilotError('Concept dupliqué dans l’inventaire')
                found = row
    if not found:
        raise PilotError('Concept absent de concepts.jsonl: ' + cid)
    if found.get('status') != 'source_only_not_canonical':
        raise PilotError('Statut du concept différent du contrat source attendu')
    if not str(found.get('source_uri', '')).startswith('http'):
        raise PilotError('URI source UNESCO absente')
    ids = found.get('microthesaurus_ids')
    if not isinstance(ids, list) or len(ids) != 1:
        raise PilotError('Le pilote exige un seul microthésaurus explicite')
    return found

def lookup_micro(run: Path, mid: str) -> dict:
    path = run / '01_INVENTAIRE' / 'groupes.csv'
    if not path.is_file(): raise PilotError('Groupes UNESCO manquants: ' + str(path))
    with path.open(encoding='utf-8-sig', newline='') as f:
        found = [r for r in csv.DictReader(f) if r.get('type') == 'microthesaurus' and r.get('id') == mid]
    if len(found) != 1:
        raise PilotError('Microthésaurus unique introuvable: ' + mid)
    if not str(found[0].get('uri', '')).startswith('http'):
        raise PilotError('URI source du microthésaurus absente')
    return found[0]

def _label(row: dict, lang: str) -> str:
    values = row.get('preferred_labels', {}).get(lang, [])
    if not isinstance(values, list) or not values or not isinstance(values[0], str) or not values[0].strip():
        raise PilotError('Étiquette UNESCO ' + lang + ' absente: impossible de réaliser fidèlement')
    return values[0].strip()

def _clean_label(value: str) -> str:
    if not value or len(value) > 300 or any(ord(c) < 32 for c in value):
        raise PilotError('Étiquette conceptuelle non sûre ou vide')
    return value

def make_request(concept: dict, micro: dict, lang: str, leaf) -> dict:
    if lang not in LANGS: raise PilotError('Langue non prise en charge')
    cid = concept['unesco_id']
    label = _clean_label(_label(concept, lang))
    mlabel = _clean_label((micro.get('label_' + lang) or '').strip())
    if not mlabel: raise PilotError('Étiquette microthésaurus absente en ' + lang)
    _, thes, _lists, cn, _belongs, mn = LANGS[lang]
    if leaf.kind == 'claim' and leaf.key == f'{cid}.{lang}.statement':
        agent, patient = thes, '« ' + label + ' »' if lang == 'fr' else '“' + label + '”'
        predicate = 'unesco:lists-concept'
        source_refs = [concept['source_uri']]
        force = 'ASSERT'
    elif leaf.kind == 'scope' and leaf.key == f'{cid}.{lang}.scope':
        agent = cn + (' « ' + label + ' »' if lang == 'fr' else ' “' + label + '”')
        patient = mn + (' « ' + mlabel + ' »' if lang == 'fr' else ' “' + mlabel + '”')
        predicate = 'unesco:member-of'
        source_refs = [concept['source_uri'], micro['uri']]
        force = 'PRESENT'
    else:
        raise PilotError('Slot Spek non pris en charge: ' + leaf.key + ' / ' + leaf.kind +
                         '. Aucune définition ni fait n’est inventé.')
    rid = 'sha256:' + hashlib.sha256((cid + '|' + lang + '|' + leaf.key + '|' +
            json.dumps([agent, patient, source_refs], ensure_ascii=False)).encode('utf-8')).hexdigest()
    graph = {'graph_id': rid,
             'nodes': [{'id': 'n1', 'kind': 'entity_ref', 'external_ref': 'unesco-pilot:source-actor',
                        'labels': {lang: agent}},
                       {'id': 'n2', 'kind': 'entity_ref', 'external_ref': concept['source_uri'] if leaf.kind == 'claim' else micro['uri'],
                        'labels': {lang: patient}}],
             'statements': [{'id': 's1', 'predicate_ref': predicate,
                             'arguments': [{'role_ref': 'unesco-role:agent', 'value_id': 'n1'},
                                           {'role_ref': 'unesco-role:patient', 'value_id': 'n2'}],
                             'polarity': 'positive', 'source_refs': source_refs}]}
    return {'schema_version': '1.0', 'request_id': rid,
            'semantic_graph': graph,
            'obligations': [{'obligation_id': 'o1', 'semantic_refs': ['s1'], 'force': force,
                             'ordering': 'FIXED', 'source_refs': []}],
            'context': {'target_language': lang, 'target_locale': 'fr-FR' if lang == 'fr' else 'en-GB',
                        'register': 'encyclopedic', 'channel': 'wiki_private'},
            'constraints': {'allowed_block_kinds': ['utterance'], 'opening_policy': 'forbidden',
                            'closing_policy': 'forbidden', 'list_policy': 'forbidden',
                            'output_format': 'structured', 'max_length': 1100},
            'capability_profile': PROFILE,
            'runtime_selector': {'runtime_set_id': f'unesco-pilot-{lang}-1'}}

def create_candidate(stage: Path, lang: str, requests: dict) -> Path:
    candidate = stage / 'candidates' / lang
    candidate.mkdir(parents=True, exist_ok=True)
    grammar = Path(__file__).resolve().parent / 'grammar'
    for filename in ['UnescoPilot.gf', 'UnescoPilotFre.gf', 'UnescoPilotEng.gf']:
        shutil.copy2(grammar / filename, candidate / filename)
    concrete, _t, listed, _c, belongs, _m = LANGS[lang]
    write_json(candidate / 'lexicon.json', {
        'schema_version': '1.1', 'lexicon_id': f'unesco-pilot-{lang}-1',
        'source_kind': 'project', 'entries': [
            {'semantic_ref': 'unesco:lists-concept', 'language': lang, 'lexical_ref': listed, 'binding_kind': 'literal'},
            {'semantic_ref': 'unesco:member-of', 'language': lang, 'lexical_ref': belongs, 'binding_kind': 'literal'}]})
    write_json(candidate / 'bridge.json', {'schema_version': '1.0', 'contract_version': '1.0',
        'operations': {'clause.transitive_event': {
            'requires': ['agent', 'predicate', 'patient'],
            'expression': 'RealizeTransitive {agent} {predicate} {patient}',
            'consumes_features': ['polarity', 'register']}}})
    write_json(candidate / 'profile.json', {'schema_version': '1.0', 'profile_id': 'unesco-pilot',
        'profile_version': 1, 'required_operations': ['clause.transitive_event'],
        'required_features': [], 'required_block_kinds': ['utterance'],
        'test_suite_ref': f'suite:unesco-pilot-{lang}-1'})
    suite = {'schema_version': '1.0', 'suite_id': f'suite:unesco-pilot-{lang}-1',
             'language': lang, 'capability_profile': PROFILE,
             'runtime_set_id': f'unesco-pilot-{lang}-1',
             'cases': [{'case_id': leaf_key.split('.')[-1], 'request': req,
                        'expected': {'coverage_complete': True}}
                       for leaf_key, req in sorted(requests.items())]}
    write_json(candidate / 'conformance.suite.json', suite)
    return candidate

def create_lock(candidate: Path, lang: str) -> None:
    names = ['grammar.pgf', 'bridge.json', 'lexicon.json', 'profile.json', 'conformance.suite.json']
    concrete = LANGS[lang][0]
    write_json(candidate / 'pipeline.lock.json', {
        'runtime_set_id': f'unesco-pilot-{lang}-1', 'profile_id': PROFILE,
        'language': lang, 'concrete': concrete, 'sa_gf_contract_version': '1.0',
        'inputs': {name: sha(candidate / name) for name in names},
        'extension_capabilities': [],
    })

DEFAULT_WORDBENCH = Path(r'C:\mycode\Grammatical-Framework\GF_Wordbench')
DEFAULT_GF = Path(r'C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe')
DEFAULT_RGL = Path(r'C:\mycode\Grammatical-Framework\gf-rgl')
DEFAULT_ORCHESTRATOR = Path(r'C:\mycode\SemantiK_Architect\SemantiK_Runtime_Orchestrator')


def find_gf(explicit: str = '', semantik_root: str | Path = '') -> str | None:
    """Only documented GF paths; a .pgf is never a compiler."""
    candidates = [Path(explicit)] if explicit else [DEFAULT_GF]
    found = shutil.which('gf')
    if found:
        candidates.append(Path(found))
    for path in candidates:
        if path.is_file() and path.name.lower() in {'gf.exe', 'gf'}:
            return str(path.resolve())
    return None


def compile_grammar(candidate: Path, lang: str, gf: str, *,
                    wordbench: Path = DEFAULT_WORDBENCH, seconds: int = 90) -> None:
    """Invoke the *owning* Wordbench runner, not a competing GF shell runner."""
    runner = wordbench / 'tools' / 'unesco_gf_build.py'
    if not runner.is_file():
        raise PilotError('Overlay GF_Wordbench requis, outil absent: ' + str(runner))
    command = [sys.executable, str(runner), '--candidate', str(candidate),
               '--lang', lang, '--gf-exe', str(gf), '--timeout', str(seconds)]
    try:
        cp = subprocess.run(command, cwd=str(candidate), capture_output=True,
                            text=True, encoding='utf-8', errors='replace',
                            timeout=seconds+25, shell=False)
    except subprocess.TimeoutExpired as exc:
        raise PilotError('Wordbench n a pas termine dans le budget de temps') from exc
    (candidate / 'wordbench-driver.log').write_text(
        (cp.stdout or '') + '\n' + (cp.stderr or ''), encoding='utf-8')
    report = candidate / 'wordbench-build.json'
    if cp.returncode != 0 or not (candidate / 'grammar.pgf').is_file():
        raise PilotError('Wordbench a refuse le PGF candidat : consulter wordbench-build.json et les logs')
    if not report.is_file() or json.loads(report.read_text(encoding='utf-8')).get('status') != 'PGF_BUILT_CANDIDATE_ONLY':
        raise PilotError('Wordbench ne prouve pas la compilation du PGF')


def run_pilot(run: Path, factory: Path, semantik: Path, out_base: Path,
              *, cid: str = 'concept10', langs: tuple = ('fr', 'en'), gf_executable: str = '',
              existing_pgf: str = '', pgf_python: str = '', wordbench: Path = DEFAULT_WORDBENCH,
              orchestrator: Path = DEFAULT_ORCHESTRATOR,
              callback: Callable[[str], None] | None = None,
              is_cancelled: Callable[[], bool] | None = None) -> Path:
    """Return ZIP, always emitted even for a fail-closed partial result."""
    callback = callback or (lambda msg: None)
    is_cancelled = is_cancelled or (lambda: False)
    out_base.mkdir(parents=True, exist_ok=True)
    stage = out_base / ('Kristal_UNESCO_Pilote_' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    stage.mkdir(parents=True, exist_ok=False)
    state = {'format':'unesco-gf-pilot/1.0', 'source_run':str(run), 'concept_id':cid,
             'languages':{}, 'publication_authorized':False, 'qualified_released_runtime':False,
             'status':'STARTED', 'errors': [], 'pipeline_interpreter':sys.executable}
    messages = []
    def log(s):
        messages.append(datetime.now().isoformat(timespec='seconds')+' '+s)
        callback(s)
    def check():
        if is_cancelled(): raise Cancelled('Annulation demandée par l’utilisateur')
    try:
        log('Validation des sources UNESCO et Spek...')
        if not run.is_dir(): raise PilotError('Dossier RUN introuvable: ' + str(run))
        concept = lookup_concept(run,cid)
        micro = lookup_micro(run,concept['microthesaurus_ids'][0])
        write_json(stage / 'source-provenance.json', {'concept_id':cid,'source_uri':concept['source_uri'],
            'microthesaurus_uri':micro['uri'],'concept_label_fr':concept.get('preferred_labels',{}).get('fr'),
            'concept_label_en':concept.get('preferred_labels',{}).get('en'),
            'status':'source_only_not_canonical'})
        spek_root = factory / 'vendor' / 'spek'
        if not (spek_root / 'spek' / 'composition' / 'semantik_adapter.py').is_file():
            raise PilotError('Spek embarqué absent dans ' + str(spek_root))
        if str(spek_root) not in sys.path: sys.path.insert(0,str(spek_root))
        from spek.composition.engine import Library, resolve, materialize, render_markdown, render_html
        from spek.composition.semantik_adapter import import_results
        from spek.slot_dialogue import KIND_POLICY, compose_request
        lib = Library(spek_root / 'template_library')
        src = semantik / 'src'
        if not (src / 'semantik_architect').is_dir():
            raise PilotError('SemantiK Architect/src absent: '+str(src))
        if str(src) not in sys.path: sys.path.insert(0,str(src))
        from semantik_architect.application.validation.request_validation import RequestValidator
        from semantik_architect.domain.communication.request import CommunicationRequest
        if existing_pgf:
            log('PGF Konstellation détecté séparément : ne se substitue pas au candidat UNESCO.')
        gf = find_gf(gf_executable, semantik)
        log('GF compilateur: '+(gf or 'ABSENT; candidate préparé, aucune réalisation GF revendiquée'))
        state['gf_executable'] = gf or None
        for lang in langs:
            check()
            log('Préparation '+lang+'...')
            state['languages'][lang]={'status':'PREPARATION'}
            instance_file = run / '07_DISCOURS' / 'instances' / lang / (cid+'.json')
            if not instance_file.is_file(): raise PilotError('Instance Spek manquante: '+str(instance_file))
            inst = read_json(instance_file)
            resolved = resolve(inst,lib)
            leaves = tuple(resolved.leaves)
            if sorted(l.kind for l in leaves) != ['claim','scope']:
                raise PilotError('Le pilote couvre seulement assertion + portée (concept sans définition)')
            requests = {}
            req_dir = stage / 'requests' / lang
            res_dir = stage / 'results' / lang
            req_dir.mkdir(parents=True)
            res_dir.mkdir(parents=True)
            for leaf in leaves:
                raw = make_request(concept,micro,lang,leaf)
                _,force,kinds,limit=KIND_POLICY[leaf.kind]
                constrained = compose_request(raw,{'force':force,'block_kinds':kinds,'max_length':limit},language=lang)
                RequestValidator().validate(CommunicationRequest.from_dict(constrained))
                requests[leaf.key] = constrained
                write_json(req_dir / Path(leaf.request_ref).name, constrained)
            write_json(stage / 'instances' / lang / (cid+'.json'),inst)
            candidate = create_candidate(stage,lang,requests)
            state['languages'][lang]['candidate_dir'] = str(candidate)
            state['languages'][lang]['request_count'] = len(leaves)
            if not gf:
                state['languages'][lang]['status']='BLOCKED_GF_COMPILER_MISSING'
                log(lang+': requêtes conformes construites; compilation GF impossible, pas de résultat inventé')
                continue
            check()
            log(lang+': compilation de la grammaire GF (délai max 45 s)')
            try:
                compile_grammar(candidate,lang,gf,wordbench=wordbench)
                create_lock(candidate,lang)
                # SemantiK owns conformance and GF realization, in its own process.
                sa_tool = semantik / 'tools' / 'unesco_candidate_probe.py'
                if not sa_tool.is_file():
                    raise PilotError('Overlay SemantiK_Architect manquant: ' + str(sa_tool))
                cmd = [sys.executable,str(sa_tool),'--candidate',str(candidate),
                       '--requests-dir',str(req_dir),'--results-dir',str(res_dir),
                       '--gf-exe',str(gf)]
                cp = subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',
                                    errors='replace',timeout=180,shell=False)
                (candidate/'semantik-run.log').write_text(
                    (cp.stdout or '')+'\n'+(cp.stderr or ''),encoding='utf-8')
                if cp.returncode != 0:
                    raise PilotError('Conformité SemantiK réelle refusée: voir semantik-run.log')
                # The orchestrator only inspects proof. It cannot approve a release.
                or_tool = orchestrator/'tools'/'unesco_candidate_preflight.py'
                if not or_tool.is_file():
                    raise PilotError('Overlay Orchestrator manquant: '+str(or_tool))
                cp = subprocess.run([sys.executable,str(or_tool),'--candidate',str(candidate),
                                      '--output',str(candidate/'orchestrator-preflight.json')],
                                    capture_output=True,text=True,encoding='utf-8',
                                    errors='replace',timeout=20,shell=False)
                (candidate/'orchestrator-run.log').write_text(
                    (cp.stdout or '')+'\n'+(cp.stderr or ''),encoding='utf-8')
                if cp.returncode != 0:
                    raise PilotError('Preflight Orchestrator refusé: voir orchestrator-run.log')
                bundle=import_results(resolved,req_dir,res_dir,lang)
                values=materialize(resolved,bundle,lang)
                title=_label(concept,lang)
                markdown=render_markdown(resolved,values,title=title)
                html=render_html(resolved,values,title=title,language=lang)
                dest=stage / 'wiki_prive'
                dest.mkdir(exist_ok=True)
                (dest / f'{cid}.{lang}.md').write_text(markdown,encoding='utf-8')
                (dest / f'{cid}.{lang}.html').write_text(html,encoding='utf-8')
                write_json(stage / 'verified' / lang / (cid+'.json'),bundle)
                state['languages'][lang]['status']='CANDIDATE_GF_SEMANTIK_SPEK_VERIFIED_NOT_RELEASED'
                state['languages'][lang]['gf_sha256']=sha(candidate/'grammar.pgf')
                state['languages'][lang]['verified_slots']=len(values)
                log(lang+': GF réel + SemantiK candidat + Spek vérifiés; aperçu privé créé')
            except Exception as exc:
                state['languages'][lang]['status']='BLOCKED_FAIL_CLOSED'
                state['languages'][lang]['error']=f'{type(exc).__name__}: {exc}'
                log(lang+': ÉCHEC (sans prose de remplacement) : '+str(exc))
        statuses = [row['status'] for row in state['languages'].values()]
        if statuses and all(x == 'CANDIDATE_GF_SEMANTIK_SPEK_VERIFIED_NOT_RELEASED' for x in statuses):
            state['status']='CANDIDATE_VERIFIED_PRIVATE_NOT_RELEASED'
        else:
            state['status']='BLOCKED_OR_PARTIAL'
    except Cancelled as exc:
        state['status']='CANCELLED'
        state['errors'].append(str(exc))
        log(str(exc))
    except Exception as exc:
        state['status']='ERROR'
        state['errors'].append(f'{type(exc).__name__}: {exc}')
        log('ERREUR : '+repr(exc))
    finally:
        write_json(stage / 'report.json',state)
        (stage / 'journal.log').write_text('\n'.join(messages)+'\n',encoding='utf-8')
        (stage / 'README_STATUT.txt').write_text(
          'PILOTE NON PUBLIABLE.\n'
          'La conformité candidate ne constitue ni activation ni approbation éditoriale.\n'
          'Aucun RuntimeSet n’est modifié/activé, aucune source n’est réécrite.\n'
          'Seuls les fichiers dans ce dossier de sortie sont créés.\n'
          'Étiquettes et chemins du projet peuvent être privés : inspecter avant partage.\n',encoding='utf-8')
        archive=stage.with_suffix('.zip')
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for file in stage.rglob('*'):
                if file.is_file(): z.write(file,file.relative_to(stage))
        callback('Archive prête : '+str(archive))
    return archive

def main():
    ap=argparse.ArgumentParser(description='Pilote UNESCO Spek SemantiK GF, sortie privée et fail-closed')
    ap.add_argument('--kristal', default=r'C:\mycode\Kristal')
    ap.add_argument('--semantik', default=r'C:\mycode\SemantiK_Architect\SemantiK_Architect')
    ap.add_argument('--run',default='')
    ap.add_argument('--concept',default='concept10')
    ap.add_argument('--languages',default='fr,en')
    ap.add_argument('--gf',default=str(DEFAULT_GF))
    ap.add_argument('--wordbench',default=str(DEFAULT_WORDBENCH))
    ap.add_argument('--orchestrator',default=str(DEFAULT_ORCHESTRATOR))
    ap.add_argument('--pgf-python',default='')
    ap.add_argument('--existing-pgf',default='')
    ap.add_argument('--output',default=str(Path.home()/'Downloads'))
    a=ap.parse_args()
    try:
        root=Path(a.kristal)
        run=Path(a.run) if a.run else find_latest_run(root)
        archive=run_pilot(run,root/'Kristal_UNESCO_Factory',Path(a.semantik),Path(a.output),
                          cid=a.concept,langs=tuple(x.strip() for x in a.languages.split(',') if x.strip()),
                          gf_executable=a.gf,existing_pgf=a.existing_pgf,pgf_python=a.pgf_python,
                          wordbench=Path(a.wordbench),orchestrator=Path(a.orchestrator),
                          callback=lambda s: print(s,flush=True))
        print('ZIP:',archive)
        data=read_json(archive.with_suffix('')/'report.json')
        return 0 if data['status']=='CANDIDATE_VERIFIED_PRIVATE_NOT_RELEASED' else 2
    except Exception as exc:
        print('ERREUR:',exc,file=sys.stderr)
        return 3
if __name__=='__main__': raise SystemExit(main())
