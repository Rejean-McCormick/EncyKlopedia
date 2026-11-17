import tempfile
import unittest
from pathlib import Path
from unesco_paths import default_factory_paths

class PathSafety(unittest.TestCase):
    def test_moved_factory_uses_new_data_and_run_paths(self):
        root=Path(r'C:\mycode\EncyKlopedia\Kristal_UNESCO_Factory')
        paths=default_factory_paths(root,{})
        self.assertTrue(str(paths['output']).endswith('90_runtime\\unesco\\factory') or str(paths['output']).endswith('90_runtime/unesco/factory'))
        self.assertIn('10_sources',str(paths['ttl']))
        self.assertNotIn('LinkedDataHub',str(paths['ttl']))
    def test_prefer_explicit_existing_2026_source(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            f=home/'10_sources/unesco/unesco-thesaurus.ttl'
            f.parent.mkdir(parents=True)
            f.write_text('local test only')
            paths=default_factory_paths(home/'code/Factory', {'ENCYKLOPEDIA_DATA_HOME':str(home)})
            self.assertEqual(paths['ttl'],f)

if __name__=='__main__':unittest.main()
