"""Tests hors ligne sans prétendre compiler GF. Aucune rédaction simulée."""
from pathlib import Path
import json
import shutil
import sys
import os
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pilot import lookup_concept, make_request, create_candidate, create_lock, run_pilot, PilotError

SPEK_SNAPSHOT=Path(os.environ.get('SPEK_TEST_ROOT', r'C:\mycode\Kristal\Kristal_UNESCO_Factory\vendor\spek'))
SA_SNAPSHOT=Path(os.environ.get('SEMANTIK_TEST_ROOT', r'C:\mycode\SemantiK_Architect\SemantiK_Architect'))
RUN_SAMPLE=ROOT/'tests'/'fixtures'

@pytest.fixture
def project(tmp_path):
    factory=tmp_path/'Kristal_UNESCO_Factory'; (factory/'vendor').mkdir(parents=True)
    if not SPEK_SNAPSHOT.is_dir() or not SA_SNAPSHOT.is_dir():
        pytest.skip('Code source Spek/SemantiK non disponible')
    try:
        (factory/'vendor'/'spek').symlink_to(SPEK_SNAPSHOT, target_is_directory=True)
    except OSError:
        shutil.copytree(SPEK_SNAPSHOT, factory/'vendor'/'spek')
    run=tmp_path/'RUN-test'
    inv=run/'01_INVENTAIRE'; inv.mkdir(parents=True)
    concept={'unesco_id':'concept10','status':'source_only_not_canonical',
        'source_uri':'http://vocabularies.unesco.org/thesaurus/concept10',
        'preferred_labels':{'fr':['Éducation'], 'en':['Education']},
        'microthesaurus_ids':['mt1.10'], 'definitions':{}}
    (inv/'concepts.jsonl').write_text(json.dumps(concept,ensure_ascii=False)+'\n',encoding='utf8')
    (inv/'groupes.csv').write_text('type,id,uri,label_fr,label_en,parent_domain_ids,members_count\n'
      'microthesaurus,mt1.10,http://vocabularies.unesco.org/thesaurus/mt1.10,Politique éducative,Educational policy,,41\n',encoding='utf8')
    for lang in ('fr','en'):
        sample=RUN_SAMPLE/f'concept10.{lang}.json'
        target=run/'07_DISCOURS'/'instances'/lang/'concept10.json'
        target.parent.mkdir(parents=True)
        shutil.copyfile(sample,target)
    return run,factory,SA_SNAPSHOT

def test_requests_are_sourced_and_safe(project,tmp_path):
    run,factory,sa=project
    zip_path=run_pilot(run,factory,sa,tmp_path/'out', gf_executable='missing-gf-command')
    assert zip_path.is_file()
    stage=zip_path.with_suffix('')
    report=json.loads((stage/'report.json').read_text(encoding='utf-8'))
    assert report['status']=='BLOCKED_OR_PARTIAL'
    assert report['languages']['fr']['status']=='BLOCKED_GF_COMPILER_MISSING'
    for lang in ('fr','en'):
      for slot in ('statement','scope'):
        p=stage/'requests'/lang/f'concept10.{lang}.{slot}.json'
        raw=json.loads(p.read_text(encoding='utf8'))
        assert raw['semantic_graph']['statements'][0]['source_refs']
        assert raw['obligations'][0]['semantic_refs']==['s1']
      assert not (stage/'wiki_prive'/f'concept10.{lang}.md').exists()

def test_candidate_real_semantik_plan_without_simulated_gf(project,tmp_path):
    run,factory,sa=project
    archive=run_pilot(run,factory,sa,tmp_path/'out', gf_executable='missing-gf-command')
    stage=archive.with_suffix('')
    sys.path.insert(0,str(sa/'src'))
    from semantik_architect.conformance.candidate import CandidateConformance
    for lang in ('fr','en'):
      candidate=stage/'candidates'/lang
      (candidate/'grammar.pgf').write_bytes(b'NOT_A_REAL_GRAMMAR_PLAN_ONLY')
      create_lock(candidate,lang)
      app=CandidateConformance(candidate,f'unesco-pilot-{lang}-1')
      for slot in ('statement','scope'):
        raw=json.loads((stage/'requests'/lang/f'concept10.{lang}.{slot}.json').read_text(encoding='utf8'))
        plan=app.plan(raw)
        assert [u.operation_id for u in plan.units]==['clause.transitive_event']
      # On ne simule jamais la vraie réalisation GF.

def test_source_missing_refuses_to_continue(project,tmp_path):
    run,factory,sa=project
    (run/'01_INVENTAIRE'/'concepts.jsonl').unlink()
    archive=run_pilot(run,factory,sa,tmp_path/'out')
    report=json.loads((archive.with_suffix('')/'report.json').read_text(encoding='utf8'))
    assert report['status']=='ERROR'
    assert not list((archive.with_suffix('')).glob('wiki_prive/*'))

def test_spek_semantik_contract_offline_with_test_double_only(project,tmp_path):
    """Couverture du contrat Spek/SA sans prétendre à une exécution GF."""
    run,factory,sa=project
    archive=run_pilot(run,factory,sa,tmp_path/'out', gf_executable='missing-gf-command')
    stage=archive.with_suffix('')
    sys.path.insert(0,str(sa/'src'))
    sys.path.insert(0,str(SPEK_SNAPSHOT))
    from semantik_architect.conformance.candidate import CandidateConformance
    from semantik_architect.application.ports.realizer import RealizationResult,RealizedUnit
    from spek.composition.engine import Library, resolve, materialize
    from spek.composition.semantik_adapter import import_results

    class TestDoubleRealizer:
        def realize(self, plan, bindings, runtime):
            # This is a *test double*, never used by pilot.py in production.
            return RealizationResult(tuple(RealizedUnit(u.unit_id,'TEST-DOUBLE ONLY') for u in plan.units))

    lang='fr'
    candidate=stage/'candidates'/lang
    (candidate/'grammar.pgf').write_bytes(b'TEST-DOUBLE ONLY')
    create_lock(candidate,lang)
    app=CandidateConformance(candidate,'unesco-pilot-fr-1',realizer=TestDoubleRealizer())
    resdir=stage/'results'/lang
    resdir.mkdir(parents=True,exist_ok=True)
    for slot in ('statement','scope'):
        fname=f'concept10.fr.{slot}.json'
        req=json.loads((stage/'requests'/lang/fname).read_text(encoding='utf-8'))
        result=app.render(req)
        (resdir/fname).write_text(json.dumps(result,ensure_ascii=False),encoding='utf8')
    instance=json.loads((stage/'instances'/lang/'concept10.json').read_text(encoding='utf8'))
    resolved=resolve(instance,Library(SPEK_SNAPSHOT/'template_library'))
    bundle=import_results(resolved,stage/'requests'/lang,resdir,lang)
    assert bundle['entries']['concept10.fr.statement']['fr']['text']=='TEST-DOUBLE ONLY'
    assert len(materialize(resolved,bundle,lang))==2
