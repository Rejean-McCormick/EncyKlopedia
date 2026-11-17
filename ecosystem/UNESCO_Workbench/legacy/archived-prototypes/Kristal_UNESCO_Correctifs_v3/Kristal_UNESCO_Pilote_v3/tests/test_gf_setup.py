from pathlib import Path
import shutil
import sys
import zipfile
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gf_setup import discover_gf, import_official_zip, probe_gf, GFSetupError


def test_import_zip_into_private_directory_without_running_program(tmp_path):
    archive = tmp_path / 'gf-windows.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('gf-3.12/gf.exe', b'not an executable in this unit test')
        z.writestr('gf-3.12/README.txt', 'Official GF archive fixture')
    gf = import_official_zip(archive, tmp_path / 'appdata')
    assert gf.exists()
    assert gf.read_bytes() == b'not an executable in this unit test'
    assert (gf.parent / 'README.txt').is_file()
    assert import_official_zip(archive, tmp_path / 'appdata') == gf


def test_zip_traversal_rejected_and_no_file_placed_outside(tmp_path):
    archive = tmp_path / 'malicious.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('gf-3.12/gf.exe', b'x')
        z.writestr('../escape.txt', 'not here')
    with pytest.raises(GFSetupError, match='dangereux'):
        import_official_zip(archive, tmp_path / 'install')
    assert not (tmp_path / 'escape.txt').exists()


def test_no_fake_success_for_missing_compiler(tmp_path):
    gf, tried = discover_gf(str(tmp_path / 'does-not-exist.exe'))
    assert gf is None
    assert tried
    with pytest.raises(GFSetupError):
        probe_gf(tmp_path / 'does-not-exist.exe')
