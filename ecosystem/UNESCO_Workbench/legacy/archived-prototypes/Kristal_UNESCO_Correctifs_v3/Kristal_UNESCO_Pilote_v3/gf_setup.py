# -*- coding: utf-8 -*-
"""GF Windows discovery and explicit, local, safe archive import.

No network access, no PATH editing, and no modifications to the project.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile
import zipfile

DOWNLOAD_PAGE = 'https://www.grammaticalframework.org/download/index.html'
WINDOWS_GUIDE = 'https://www.grammaticalframework.org/~inari/gf-windows.html'
MAX_ARCHIVE_FILES = 2500
MAX_UNCOMPRESSED = 500 * 1024 * 1024
MAX_MEMBER = 180 * 1024 * 1024

class GFSetupError(RuntimeError):
    pass


def private_tool_root() -> Path:
    """User-owned application data, never the source checkout."""
    if os.name == 'nt':
        root = os.environ.get('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Local')
        return Path(root) / 'KristalUNESCO' / 'GF'
    return Path.home() / '.local' / 'share' / 'KristalUNESCO' / 'GF'


def _valid_file(path: str | Path | None) -> Path | None:
    if not path:
        return None
    p = Path(str(path).strip().strip('"')).expanduser()
    if p.is_file() and p.name.lower() in ('gf.exe', 'gf'):
        return p.resolve()
    return None


def _limited_gf_search(root: Path, *, max_depth: int = 4, max_dirs: int = 450) -> Path | None:
    """Non-recursive bounded walk: avoids one-hour scans and symlink loops."""
    if not root.is_dir():
        return None
    queue = [(root, 0)]
    scanned = 0
    while queue and scanned < max_dirs:
        path, depth = queue.pop(0)
        scanned += 1
        for filename in (('gf.exe', 'gf') if os.name == 'nt' else ('gf', 'gf.exe')):
            exe = path / filename
            if exe.is_file():
                return exe.resolve()
        if depth >= max_depth:
            continue
        try:
            children = sorted((p for p in path.iterdir() if p.is_dir() and not p.is_symlink()), key=lambda p: p.name.lower())
            for child in children[:100]:
                queue.append((child, depth + 1))
        except (OSError, PermissionError):
            pass
    return None


def discover_gf(explicit: str = '', semantik_root: str | Path = '') -> tuple[str | None, list[str]]:
    """Find an existing gf.exe by exact path, PATH or a few bounded locations."""
    examined: list[str] = []
    if explicit and explicit.strip():
        p = _valid_file(explicit)
        examined.append('Chemin utilisateur : ' + explicit)
        return (str(p) if p else None), examined
    for source, value in [('SEMANTIK_GF_EXECUTABLE', os.environ.get('SEMANTIK_GF_EXECUTABLE', '')),
                          ('PATH', shutil.which('gf.exe') or shutil.which('gf') or '')]:
        if not value:
            continue
        examined.append(source + ' : ' + str(value))
        p = _valid_file(value)
        if p:
            return str(p), examined
    bases = [private_tool_root(), Path.home() / 'Downloads', Path.home() / 'Documents']
    if semantik_root:
        from project_paths import runtime_paths
        root = runtime_paths(semantik_root)
        bases = [Path(root['gf_wordbench']), Path(root['semantik_project']) / 'bin',
                 Path(root['semantik_project']).parent / 'SemantiK_Runtime_Orchestrator' / 'GF_Wordbench', *bases]
    if os.name == 'nt':
        bases.extend([
            Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'GF',
            Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'Grammatical Framework',
            Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'GF',
            Path('C:/GF'), Path('C:/gf-3.12'), Path('C:/msys64/mingw64/bin'),
        ])
    for base in bases:
        examined.append('Recherche bornée : ' + str(base))
        # Search only likely GF folders in very broad directories.
        if base.name.lower() in ('downloads', 'documents') and base.is_dir():
            try:
                children = sorted((p for p in base.iterdir() if p.is_dir() and
                                   p.name.lower().startswith(('gf', 'grammatical')) and not p.is_symlink()),
                                  key=lambda p: p.name.lower())
            except OSError:
                children = []
            for child in children[:30]:
                p = _limited_gf_search(child, max_depth=3)
                if p:
                    return str(p), examined
        else:
            p = _limited_gf_search(base, max_depth=4)
            if p:
                return str(p), examined
    return None, examined


def probe_gf(gf: str | Path, *, timeout: int = 8) -> dict:
    """Explicit user action: invoke only selected/detected GF with a timeout."""
    exe = _valid_file(gf)
    if not exe:
        raise GFSetupError('gf.exe absent ou chemin incorrect : ' + str(gf))
    try:
        cp = subprocess.run([str(exe), '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=timeout, shell=False, check=False)
    except subprocess.TimeoutExpired as exc:
        raise GFSetupError(f'GF ne répond pas après {timeout} secondes.') from exc
    except OSError as exc:
        raise GFSetupError('Impossible de lancer gf.exe : ' + str(exc)) from exc
    output = (cp.stdout or b'').decode('utf-8', errors='replace').strip()
    return {'executable': str(exe), 'exit_code': cp.returncode, 'output': output[:2000],
            'usable': cp.returncode == 0 or ('Grammatical Framework' in output)}


def import_official_zip(archive: str | Path, dest_base: Path | None = None) -> Path:
    """Extract a user-provided GF ZIP into private tool dir; no execution or PATH editing.

    Archive format, entry size and paths are validated. This does not authenticate
    a third-party download: the user must obtain it from the official GF site.
    """
    archive = Path(archive).expanduser().resolve()
    if not archive.is_file() or archive.suffix.lower() != '.zip':
        raise GFSetupError('Choisir une archive .zip GF Windows valide.')
    if archive.stat().st_size > MAX_UNCOMPRESSED:
        raise GFSetupError('Archive trop volumineuse pour cet import (>500 Mo).')
    dest_base = (dest_base or private_tool_root()).expanduser()
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries) > MAX_ARCHIVE_FILES:
            raise GFSetupError('Archive avec trop de fichiers.')
        total = 0
        gf_candidates = []
        for item in entries:
            name = item.filename.replace('\\', '/')
            parts = PurePosixPath(name).parts
            mode = (item.external_attr >> 16) & 0xFFFF
            is_link = stat.S_ISLNK(mode)
            if (name.startswith('/') or not parts or any(p in ('.', '..') for p in parts)
                or ':' in parts[0] or is_link or '\x00' in name):
                raise GFSetupError('Chemin dangereux détecté dans le ZIP GF : ' + name)
            if item.file_size > MAX_MEMBER:
                raise GFSetupError('Un fichier dépasse la limite de 180 Mo : ' + name)
            total += item.file_size
            if total > MAX_UNCOMPRESSED:
                raise GFSetupError('Contenu extrait dépasse 500 Mo.')
            if not item.is_dir() and parts[-1].lower() == 'gf.exe':
                gf_candidates.append(item)
        if len(gf_candidates) != 1:
            raise GFSetupError('Le ZIP doit contenir un seul gf.exe (trouvés : '+str(len(gf_candidates))+').')
        dest_base.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()[:12]
        target = dest_base / ('GF-' + digest)
        existing = _limited_gf_search(target)
        if existing:
            return existing
        if target.exists():
            raise GFSetupError('Installation privée partielle existante : '+str(target))
        with tempfile.TemporaryDirectory(prefix='gf-import-', dir=dest_base) as temporary:
            staging = Path(temporary)
            for info in entries:
                sub = PurePosixPath(info.filename.replace('\\', '/'))
                output = staging.joinpath(*sub.parts)
                # Force paths to remain inside staging; avoid archive traversal.
                if not output.resolve().is_relative_to(staging.resolve()):
                    raise GFSetupError('Chemin hors du dossier d’extraction : '+info.filename)
                if info.is_dir():
                    output.mkdir(parents=True, exist_ok=True)
                else:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(info) as r, output.open('wb') as w:
                        shutil.copyfileobj(r, w)
            extracted = _limited_gf_search(staging, max_depth=7)
            if not extracted:
                raise GFSetupError('Extraction terminée mais gf.exe introuvable.')
            relative = extracted.relative_to(staging)
            staging.rename(target)
            return target / relative


def probe_existing_pgf(python: str | Path, artifact: str | Path, timeout: int = 10) -> dict:
    """Test SemantiK's preferred python-pgf backend on a *pre-existing* PGF.

    This does NOT compile the UNESCO candidate and cannot qualify its pages.
    The interpreter and a small, fixed inline probe have a strict timeout.
    """
    python = Path(str(python).strip().strip('"')).expanduser()
    artifact = Path(str(artifact).strip().strip('"')).expanduser()
    result = {'python': str(python), 'pgf_path': str(artifact),
              'backend': 'python_pgf', 'loaded': False,
              'concrete_languages': [], 'scope': 'existing_konstellation_runtime_only'}
    if not python.is_file():
        result['error'] = 'Interpréteur Python introuvable'
        return result
    if not artifact.is_file():
        result['error'] = 'Fichier PGF précompilé introuvable'
        return result
    if artifact.stat().st_size < 100:
        result['error'] = 'Fichier PGF suspect (moins de 100 octets)'
        return result
    code = (
        'import json,sys,pgf\n'
        'g=pgf.readPGF(sys.argv[1])\n'
        'print(json.dumps({"loaded": True, "concrete_languages":'
        'sorted(g.languages.keys())}))\n'
    )
    try:
        cp = subprocess.run([str(python), '-P', '-c', code, str(artifact)],
                            capture_output=True, text=True, encoding='utf-8',
                            errors='replace', timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        result['error'] = f'Test python-pgf interrompu après {timeout} secondes'
        return result
    except OSError as exc:
        result['error'] = f'Python non lançable : {exc}'
        return result
    if cp.returncode:
        result['error'] = ('Impossible de charger le PGF avec le module Python pgf : ' +
                           (cp.stderr or cp.stdout or 'échec inconnu').strip()[-1200:])
        return result
    try:
        payload = __import__('json').loads(cp.stdout.strip())
        if not payload.get('loaded') or not isinstance(payload.get('concrete_languages'), list):
            raise ValueError('Réponse incorrecte')
        result.update(payload)
    except (ValueError, TypeError) as exc:
        result['error'] = f'Réponse python-pgf invalide : {exc}'
    return result
