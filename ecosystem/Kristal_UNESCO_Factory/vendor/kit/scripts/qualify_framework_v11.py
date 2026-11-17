#!/usr/bin/env python3
"""Read-only qualification of a v11 Authoring workspace against PINNED Framework draft.4.

Optional dependency: jsonschema (also required by the Framework reference tools).
No downloads; no changes to source, workspace, or published commitments.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / 'contracts/v11-framework-pin.json'


class QualificationError(ValueError):
    pass


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_pin(framework):
    # Keep the EXACT shared pin with Integration Pack; no lookups by label.
    spec = json.loads(PIN.read_text(encoding='utf-8'))
    if spec.get('profile') != 'kristal-integration-framework-pin/v11.0-draft.4':
        raise QualificationError('unsupported pin format')
    if not framework.is_dir() or not (framework/'VERSION').is_file():
        raise QualificationError('Framework path missing')
    if (framework/'VERSION').read_text().strip() != spec['version']:
        raise QualificationError('Framework v11 version mismatch')
    for name, expected in spec['files'].items():
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts or '\\' in name:
            raise QualificationError('unsafe pinned path')
        source = (framework / rel).resolve()
        if not source.is_relative_to(framework) or not source.is_file() or sha(source) != expected:
            raise QualificationError('Framework pin drift: ' + name)
    return spec


def _load_framework(framework):
    tools = framework / 'tools' / 'v11'
    if str(tools) not in sys.path:
        sys.path.insert(0,str(tools))
    import validate_v11
    import dictionaries
    import dik_coverage
    return validate_v11, dictionaries, dik_coverage


def qualify(workspace, framework, integration=None, locales=None):
    workspace=Path(workspace).resolve()
    framework=Path(framework).resolve()
    pin=verify_pin(framework)
    # Framework validator scripts run ONLY after pin verification.
    official, dictionary, official_coverage = _load_framework(framework)
    sys.path.insert(0,str(ROOT/'tools'))
    import kristal_v11_core as kit
    active=kit.validate(workspace)
    files=active['files']
    registration=kit.read(files['registry']);graph=kit.read(files['graph'])
    crosswalk=kit.read(files['crosswalk']);catalog=kit.read(files['catalog'])
    official.check_fixtures()  # verify Framework's shipped schema/TCK fixture mirror
    official.validate_documents(registry=registration,graph=graph,crosswalk=crosswalk,lexicons=[])
    dictionary.audit(files['catalog'],files['crosswalk'],files['registry'])
    requested=list(locales) if locales is not None else None
    # Compare independently implemented Kit and Framework reports exactly.
    kit_report=kit.coverage(workspace,locales=requested)
    reference=official_coverage.make_report(
        graph_path=files['graph'], registry_path=files['registry'],
        crosswalk_path=files['crosswalk'], catalog_path=files['catalog'], locales=requested)
    if kit_report != reference:
        raise QualificationError('Kit coverage differs from the official Framework v11 reference report')
    integration_info=None
    if integration is not None:
        integration=Path(integration).resolve()
        pack_pin=integration/'contracts/v11-framework-pin.json'
        if not pack_pin.is_file() or json.loads(pack_pin.read_text()) != pin:
            raise QualificationError('Integration Pack uses a different Framework v11 pin')
        common=['--framework',str(framework),'--registry',str(files['registry']),
                '--graph',str(files['graph']),'--crosswalk',str(files['crosswalk']),
                '--catalog',str(files['catalog'])]
        bridge=integration/'tools/v11_integration.py'
        if not bridge.is_file():
            raise QualificationError('Integration Pack v11 bridge missing')
        for command, extra in [('check',[]),('coverage',['--locales',','.join(requested or active['languages'])])]:
            proc=subprocess.run([sys.executable,str(bridge),command,*common,*extra],text=True,capture_output=True)
            if proc.returncode:
                raise QualificationError('Integration Pack '+command+' failed: '+(proc.stderr or proc.stdout)[:500])
            payload=json.loads(proc.stdout)
            if command=='coverage' and payload!=reference:
                raise QualificationError('Integration Pack coverage differs from Framework')
            if command=='check' and (not payload.get('valid') or payload.get('graph_id')!=active['graph_id']):
                raise QualificationError('Integration Pack rejected graph identity')
        integration_info='coverage-and-check-matched'
    return {'profile':'kristal.authoring-framework-qualification/11.0-draft.4',
            'valid':True,'read_only':True,'framework_version':pin['version'],
            'namespace_id':active['namespace_id'],'graph_id':active['graph_id'],
            'graph_sha256':kit.digest(files['graph']),'catalog_sha256':kit.digest(files['catalog']),
            'languages_tested':requested if requested is not None else list(active['languages']),
            'reference_coverage_match':True,'integration_pack':integration_info}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--framework',type=Path,required=True)
    p.add_argument('--integration-pack',type=Path)
    p.add_argument('--locales',help='Comma-separated declared locale tags')
    args=p.parse_args(argv)
    locales=args.locales.split(',') if args.locales is not None else None
    if locales is not None and (not all(locales) or len(set(locales))!=len(locales)):
        raise QualificationError('invalid locale selection')
    result=qualify(args.project,args.framework,args.integration_pack,locales)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))


if __name__=='__main__':
    try:main()
    except (QualificationError,ValueError,KeyError,TypeError,OSError,ImportError) as exc:
        raise SystemExit('Framework v11 qualification: FAIL: '+str(exc))
