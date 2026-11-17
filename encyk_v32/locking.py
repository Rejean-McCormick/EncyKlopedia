"""One local writer per work database, including across UI/CLI processes.

OS locks are released on process death. The lock file must never be deleted.
Nested calls are allowed only for the same connection in the same thread.
"""
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
import os
import threading

_guard = threading.RLock()
_owners = {}


def database_path(db):
    return Path(next(r[2] for r in db.execute('PRAGMA database_list') if r[1] == 'main')).resolve()


@contextmanager
def writer_lock(path, owner):
    key = str(Path(path).resolve())
    token = (threading.get_ident(), owner)
    with _guard:
        existing = _owners.get(key)
        if existing:
            if existing[0] != token:
                raise RuntimeError('Un autre ordonnanceur utilise cette base; réessayer après sa fin.')
            _owners[key] = (token, existing[1] + 1)
            nested = True
        else:
            _owners[key] = (token, 1)
            nested = False
    handle = None
    acquired = False
    try:
        if not nested:
            lockpath = Path(key + '.writer.lock')
            lockpath.parent.mkdir(parents=True, exist_ok=True)
            handle = lockpath.open('a+b')
            if lockpath.stat().st_size == 0:
                handle.write(b'0'); handle.flush()
            handle.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError as exc:
                raise RuntimeError('Base occupée par un autre ordonnanceur local.') from exc
        yield
    finally:
        if handle:
            if acquired:
                handle.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
        with _guard:
            current = _owners[key]
            if current[1] == 1: del _owners[key]
            else: _owners[key] = (token, current[1] - 1)


def serialized(fn):
    @wraps(fn)
    def call(db, *args, **kwargs):
        with writer_lock(database_path(db), id(db)):
            return fn(db, *args, **kwargs)
    return call
