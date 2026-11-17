"""Test the offline, opt-in cleanup logic without opening its Tk window."""
import hashlib
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader, module_from_spec
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_pywindow():
    loader = SourceFileLoader('kit_cleanup', str(ROOT / 'Nettoyer_Anciens_Fichiers.pyw'))
    spec = spec_from_loader('kit_cleanup', loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


class CleanupTests(unittest.TestCase):
    def test_only_matching_snapshot_indexes_can_be_removed(self):
        module = load_pywindow()
        with tempfile.TemporaryDirectory() as tmp:
            module.ROOT = Path(tmp)
            allowed = next(iter(module.OLD_FILES))
            # Use exact old snapshot bytes (loaded from ZIP? not needed for this
            # invariant; temporarily replace expected hash for synthetic text).
            content = b'old synthetic index\n'
            module.OLD_FILES = {allowed: hashlib.sha256(content).hexdigest(), 'SNAPSHOT_INDEX.txt': '0' * 64}
            source = module.ROOT / allowed
            source.write_bytes(content)
            changed = module.ROOT / 'SNAPSHOT_INDEX.txt'
            changed.write_text('modified manually')
            canon = module.ROOT / 'canon.json'
            canon.write_text('{"keep": true}')
            self.assertIn('supprimable', module.status(allowed))
            self.assertIn('protégé', module.status('SNAPSHOT_INDEX.txt'))
            removed, refused = module.delete_matching([allowed, 'SNAPSHOT_INDEX.txt', 'canon.json'])
            self.assertEqual(removed, [allowed])
            self.assertEqual(set(refused), {'SNAPSHOT_INDEX.txt', 'canon.json'})
            self.assertFalse(source.exists())
            self.assertTrue(changed.exists())
            self.assertTrue(canon.exists())

    def test_outside_path_and_symlink_cannot_be_removed(self):
        module = load_pywindow()
        with tempfile.TemporaryDirectory() as tmp:
            module.ROOT = Path(tmp)
            name = 'SMARTDUMP_INDEX.txt'
            data = b'a\n'
            module.OLD_FILES = {name: hashlib.sha256(data).hexdigest()}
            outside = Path(tmp).parent / (Path(tmp).name + '_outside')
            outside.write_bytes(data)
            try:
                (Path(tmp) / name).symlink_to(outside)
            except (OSError, NotImplementedError):
                outside.unlink()
                self.skipTest('Symlinks unavailable')
            deleted, refused = module.delete_matching([name, '../' + outside.name])
            self.assertFalse(deleted)
            self.assertEqual(len(refused), 2)
            self.assertTrue(outside.exists())
            outside.unlink()


if __name__ == '__main__':
    unittest.main()
