"""Self-healing, stdlib-only Python runtime bootstrap for the Windows GUI.

The GUI may be opened directly through the Windows .pyw association, pointing
at a Python installation different from the one used to install rdflib.
Prefer the Kristal venv, otherwise prepare an app-private venv. Never pip
install into the operating-system Python interpreter.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

BASE = Path(__file__).absolute().parent
ROOT = Path(os.environ.get('KRISTAL_ROOT') or BASE.parent)
BOOT_LOG = BASE / 'BOOTSTRAP_RUNTIME.log'


def worker_executable(executable=None):
    """Use python.exe even when this GUI was launched with pythonw.exe."""
    p = Path(executable or sys.executable)
    if p.name.lower() == 'pythonw.exe':
        console = p.with_name('python.exe')
        if console.is_file():
            return console
    return p


def same_executable(left, right):
    return os.path.normcase(os.path.abspath(str(left))).lower() == os.path.normcase(os.path.abspath(str(right))).lower()


def log(msg):
    line = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(msg)
    try:
        BOOT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with BOOT_LOG.open('a', encoding='utf-8') as stream:
            stream.write(line + '\n')
    except OSError:
        pass


def _run(command, timeout=90):
    opts = {}
    if os.name == 'nt':
        opts['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    return subprocess.run([str(c) for c in command], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                          errors='replace', timeout=timeout, **opts)


def valid_runtime(executable):
    py = Path(executable)
    if not py.is_file():
        return False
    try:
        result = _run([py, '-c', 'import sys, rdflib, tkinter; print(sys.version.split()[0], rdflib.__version__)'], 25)
        log(f'Vérification {py}: {result.returncode} {result.stdout.strip()[:240]}')
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired) as err:
        log(f'Vérification {py}: {err}')
        return False


def runtime_candidates():
    override = os.environ.get('KRISTAL_FACTORY_PYTHON', '').strip()
    paths = []
    if override:
        paths.append(Path(override))
    if os.name == 'nt':
        paths.extend([ROOT / '.venv-unesco' / 'Scripts' / 'python.exe',
                      BASE / '.venv' / 'Scripts' / 'python.exe'])
    else:
        paths.extend([ROOT / '.venv-unesco' / 'bin' / 'python',
                      BASE / '.venv' / 'bin' / 'python'])
    paths.append(worker_executable())
    found = set()
    for path in paths:
        key = str(path).lower()
        if key not in found:
            found.add(key)
            yield path


def _status_window():
    """Small visible progress window when dependency installation is needed."""
    try:
        import tkinter as tk
        win = tk.Tk()
        win.title('Kristal UNESCO Factory — environnement Python')
        win.geometry('575x155')
        win.resizable(False, False)
        label = tk.Label(win, text='Préparation automatique de Python...', padx=18, pady=22,
                         justify='left', wraplength=540, font=('Segoe UI', 11))
        label.pack(fill='both', expand=True)
        win.update()
        return win, label
    except Exception:
        return None, None


def _show_failure(message):
    log('ERREUR: ' + message)
    try:
        from tkinter import Tk, messagebox
        root = Tk()
        root.withdraw()
        messagebox.showerror('Kristal UNESCO Factory — environnement Python',
                             message + '\n\nJournal : ' + str(BOOT_LOG), parent=root)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


def create_private_runtime():
    target = BASE / '.venv'
    py = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    host = worker_executable()
    win, label = _status_window()
    try:
        if not py.is_file():
            log('Création de l’environnement privé: ' + str(target))
            if label:
                label.configure(text='Création de l’environnement privé Python…\n' + str(target))
                win.update()
            result = _run([host, '-m', 'venv', target], 180)
            log('venv : ' + result.stdout[-3000:])
            if result.returncode:
                raise RuntimeError('Création du venv impossible : ' + result.stdout[-700:])
        if label:
            label.configure(text='Installation de rdflib dans l’environnement privé…\nLes sources UNESCO ne sont pas modifiées.')
            win.update()
        log('Installation de rdflib>=7,<9 dans ' + str(py))
        result = _run([py, '-m', 'pip', 'install', 'rdflib>=7,<9'], 300)
        log('pip : ' + result.stdout[-4000:])
        if result.returncode:
            raise RuntimeError('Installation de rdflib impossible : ' + result.stdout[-1000:])
        if not valid_runtime(py):
            raise RuntimeError('Validation Python/rdflib/tkinter échouée après installation.')
        return py
    finally:
        if win:
            try:
                win.destroy()
            except Exception:
                pass


def bootstrap():
    """Execute before importing the GUI/pipeline; re-exec the right Python if needed."""
    log('Démarrage par ' + str(sys.executable))
    selected = None
    for candidate in runtime_candidates():
        if valid_runtime(candidate):
            selected = candidate
            break
    if selected is None:
        try:
            selected = create_private_runtime()
        except Exception as error:
            _show_failure(str(error))
            raise SystemExit(1)
    current = worker_executable()
    if same_executable(selected, current):
        log('Environnement prêt dans le processus actuel : ' + str(selected))
        return selected
    target = selected.with_name('pythonw.exe') if os.name == 'nt' and selected.with_name('pythonw.exe').exists() else selected
    command = [target, BASE / 'Fabrique_UNESCO.pyw', *sys.argv[1:]]
    env = os.environ.copy()
    env['KRISTAL_ROOT'] = str(ROOT)
    env['KRISTAL_FACTORY_BOOTSTRAPPED'] = '1'
    log('Relance GUI avec : ' + str(target))
    try:
        kwargs = {'cwd': str(BASE), 'env': env, 'close_fds': True}
        if os.name == 'nt':
            kwargs['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        subprocess.Popen([str(p) for p in command], **kwargs)
    except Exception as error:
        _show_failure('Relance de l’application impossible : ' + str(error))
        raise SystemExit(1)
    raise SystemExit(0)
