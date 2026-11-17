"""Find mismatch between pip import, fastio cached module and verified locator."""
import importlib
import sys
from pathlib import Path
from ._encyk_common import data_root,project_root,add,bounded_json

def collect(cfg):
    repo=project_root(cfg);root=data_root(cfg)
    scripts=repo/'00_system/tools/scope-builder/scripts'
    if not scripts.is_dir():raise FileNotFoundError('Scope Builder scripts missing')
    if str(scripts) not in sys.path:sys.path.insert(0,str(scripts))
    imported=importlib.import_module('scope_common')
    # Ensure the actual source is loaded (protect against an unrelated scope_common).
    if Path(imported.__file__).resolve().parent!=scripts.resolve():
        raise RuntimeError('scope_common imported from unexpected location')
    fastio=imported.fastio
    result={'python':sys.executable,'scope_common':imported.__file__,
            'fastio':getattr(fastio,'__file__',None),
            'cached_indexed_bzip2':getattr(fastio,'_INDEXED_BZIP2',None) is not None}
    try:
        mod=importlib.import_module('indexed_bzip2')
        result['imported_reader']=True
        result['reader_file']=getattr(mod,'__file__',None)
        result['reader_version']=getattr(mod,'__version__',None)
    except Exception as ex:
        result['imported_reader']=False
        result['reader_error']=type(ex).__name__+': '+str(ex)[:300]
    dump_dir=root/'10_sources/wikidata/dumps/current'
    dumps=sorted(dump_dir.glob('*.json.bz2')) if dump_dir.is_dir() else []
    dump=dumps[0] if len(dumps)==1 else None
    result['dump_candidates']=len(dumps)
    result['dump_exists']=dump is not None and dump.is_file()
    if result['dump_exists']:
        ok,info=imported.fast_access_status(root,dump)
        result.update(locator_exists=ok,random_access_ready=info.get('random_access_ready'),
                      backend=(info.get('runtime_backend') or {}).get('backend'),
                      locator_path=info.get('locator_path'),compression_index_path=info.get('compression_index_path'),
                      locator_file_exists=Path(info.get('locator_path')).is_file() if info.get('locator_path') else False,
                      compression_file_exists=Path(info.get('compression_index_path')).is_file() if info.get('compression_index_path') else False)
    return result

def run(cfg,report):
    try:out=collect(cfg)
    except Exception as exc:
        add(report,'encyk.reader.diagnostic_import','ERROR','Reader check itself failed.',{'error':type(exc).__name__+': '+str(exc)[:260]});return
    status='PASS' if out['imported_reader'] else ('FAIL' if out['dump_exists'] else 'BLOCKED')
    add(report,'encyk.reader.module.import',status,'Optional indexed_bzip2 import checked in this Python.',
        {k:out.get(k) for k in ('python','imported_reader','reader_file','reader_version','reader_error')},
        None if status=='PASS' else 'Check this exact Python executable; do not rebuild Wikidata.')
    cache='PASS' if out['cached_indexed_bzip2'] else 'FAIL' if out['imported_reader'] else 'BLOCKED'
    add(report,'encyk.reader.fastio.cache',cache,'Reader import and fastio backend cache compared.',
        {'cached':out['cached_indexed_bzip2'],'imported':out['imported_reader'],'fastio':out['fastio']},
        'Investigate early import and reload order if imported=True but cached=False.' if cache=='FAIL' else None)
    if not out['dump_exists']:
        add(report,'encyk.reader.random_access','BLOCKED','Source dump unavailable, reader index cannot be checked.');return
    status='PASS' if out.get('random_access_ready') else 'WARN'
    add(report,'encyk.reader.random_access',status,'Metadata-based random access capability check (no dump scan).',
        {k:out.get(k) for k in ('backend','random_access_ready','locator_file_exists','compression_file_exists','locator_path','compression_index_path')},
        'Review EncyK reader and existing sidecar metadata; no dump scan or index rebuild.' if status=='FAIL' else None)
    report.metrics.update({'reader_python':out['python'],'reader_backend':out.get('backend'),'reader_ready':out.get('random_access_ready')})
