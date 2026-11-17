"""Private CPython 3.13 bzip2 reader for existing EncyK Skope sidecars.

Does not scan/alter a full dump or modify an existing system Python. This module
runs within the main Factory interpreter and delegates only compressed random
reads to a private, version-compatible helper. All install operations are logged.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

PACKAGE = 'indexed_bzip2==1.7.0'

class ReaderSetupError(Exception):
    pass


def _python_in(venv: Path) -> Path:
    return venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def _check_reader(python: Path) -> bool:
    if not Path(python).is_file():
        return False
    try:
        p = subprocess.run([str(python), '-c', 'import sys,indexed_bzip2; assert sys.version_info[:2] in ((3,11),(3,12),(3,13)); print(sys.version)'],
                           capture_output=True, encoding='utf-8', errors='replace', timeout=15)
        return p.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _run(cmd, emit, cancel, timeout=360, env=None):
    if cancel(): raise InterruptedError('Interruption de la préparation du lecteur')
    cmd = [str(x) for x in cmd]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace', env=env,
                            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name == 'nt' else 0)
    try:
        output=[]
        start=time.monotonic()
        # communicate bounds elapsed time, unlike a blocking readline on a quiet installer.
        while True:
            if cancel():
                proc.terminate()
                raise InterruptedError('Lecteur interrompu')
            try:
                out, _ = proc.communicate(timeout=1)
                output.append(out or '')
                break
            except subprocess.TimeoutExpired:
                if time.monotonic() - start > timeout:
                    proc.kill()
                    raise ReaderSetupError('Commande de préparation expirée après '+str(timeout)+' s')
        result=''.join(output)
        if proc.returncode:
            emit('Lecteur : '+result[-2000:], 'WARN')
            raise ReaderSetupError('Préparation échouée (code '+str(proc.returncode)+') : '+result[-850:])
        if result.strip(): emit('Lecteur : '+result.strip()[-1000:])
        return result
    finally:
        if proc.poll() is None:
            proc.kill();proc.wait()
        if proc.stdout: proc.stdout.close()


def _find_python_313(emit):
    # The main GUI may use CPython 3.14 and must NOT load a cp313 binary module.
    options=[]
    if (3,11) <= sys.version_info[:2] <= (3,13):options.append(Path(sys.executable))
    if os.name == 'nt':
        for minor in (13,12,11):
            try:
                p=subprocess.run(['py',f'-3.{minor}','-c','import sys; print(sys.executable)'],
                                 capture_output=True,text=True,timeout=15)
                if p.returncode==0 and p.stdout.strip():options.append(Path(p.stdout.strip()))
            except (OSError,subprocess.TimeoutExpired):pass
    else:
        for minor in (13,12,11):
            command=shutil.which(f'python3.{minor}')
            if command:options.append(Path(command))
    for path in options:
        try:
            p=subprocess.run([str(path),'-c','import sys,platform; print(sys.version_info[:2], platform.architecture()[0])'],
                             capture_output=True,text=True,timeout=15)
            if p.returncode==0 and any(v in p.stdout for v in ('(3, 13)','(3, 12)','(3, 11)')):
                emit('Interpréteur compatible repéré : '+str(path))
                return path
        except (OSError, subprocess.TimeoutExpired):pass
    return None


def _get_uv(main_python: Path, emit, cancel):
    names=[]
    found=shutil.which('uv')
    if found:names.append(Path(found))
    names.append(main_python.with_name('uv.exe' if os.name=='nt' else 'uv'))
    for candidate in names:
        if candidate.is_file(): return candidate
    # Only install inside the existing *virtual environment*, never in Python system.
    if not (main_python.resolve().parent.parent/'pyvenv.cfg').is_file():
        raise ReaderSetupError('uv absent et Python principal non isolé : installation automatique refusée.')
    emit('Installation privée de uv (outil de téléchargement Python 3.13) ...')
    _run([main_python,'-m','pip','install','--disable-pip-version-check','--only-binary=:all:','uv>=0.8,<1'],emit,cancel,timeout=240)
    cli=main_python.with_name('uv.exe' if os.name=='nt' else 'uv')
    if not cli.is_file():raise ReaderSetupError('uv installé mais exécutable non trouvé : '+str(cli))
    return cli


def ensure_reader(main_python, base, emit, cancel=lambda:False):
    """Produce private interpreter with indexed_bzip2, no global installs.

    Uses an installed CPython 3.11-3.13 or lets uv download a managed 3.13
    into project-local private directories (network may be needed once).
    """
    main_python=Path(main_python).resolve()
    base=Path(base).resolve()
    target=base/'reader-cp313'
    executable=_python_in(target)
    if _check_reader(executable):
        emit('Lecteur BZIP2 privé réutilisé : '+str(executable))
        return executable
    if _check_reader(main_python):
        emit('Lecteur BZIP2 du Python principal disponible.')
        return main_python
    base.mkdir(parents=True,exist_ok=True)
    source_py=_find_python_313(emit)
    uv=None
    if source_py is not None:
        emit('Création du Python lecteur isolé : '+str(target))
        if not executable.is_file():
            _run([source_py,'-m','venv',target],emit,cancel,timeout=180)
        # A venv from CPython on Windows contains pip; fallback to uv if not.
        try:
            _run([executable,'-m','pip','install','--disable-pip-version-check',
                  '--only-binary=:all:',PACKAGE],emit,cancel,timeout=300)
        except ReaderSetupError as exc:
            emit('Installation pip impossible, tentative avec uv : '+str(exc),'WARN')
            uv=_get_uv(main_python,emit,cancel)
    else:
        emit('Python 3.11–3.13 absent. Installation privée et automatique de Python 3.13 via uv (téléchargement requis).')
        uv=_get_uv(main_python,emit,cancel)
        env=os.environ.copy()
        env['UV_CACHE_DIR']=str(base/'cache')
        env['UV_PYTHON_INSTALL_DIR']=str(base/'pythons')
        _run([uv,'venv','--python','3.13','--managed-python',target],
             emit,cancel,timeout=600,env=env)
    if uv is not None:
        env=os.environ.copy()
        env['UV_CACHE_DIR']=str(base/'cache')
        env['UV_PYTHON_INSTALL_DIR']=str(base/'pythons')
        _run([uv,'pip','install','--python',executable,PACKAGE],emit,cancel,timeout=300,env=env)
    if not _check_reader(executable):
        raise ReaderSetupError('Validation du lecteur impossible : Python 3.11–3.13 et indexed_bzip2 non opérationnels.')
    emit('Lecteur BZIP2 validé : '+str(executable))
    return executable


def write_reader_request(wanted, out):
    valid=sorted({x for x in wanted if isinstance(x,str) and x.startswith('Q') and x[1:].isdigit()},key=lambda q:int(q[1:]))
    if not valid:raise ReaderSetupError('Aucun QID unique à extraire')
    if len(valid)>100_000:raise ReaderSetupError('Trop de QID pour une extraction ciblée (limite 100 000).')
    target=Path(out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({'qids':valid},ensure_ascii=False),encoding='utf-8')
    return target
