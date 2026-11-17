"""Root library category layout: one directory for every family."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from spek.core import ValidationError
from spek.template_library import list_template_categories
from spek.wiki import load_profiles

ROOT=Path(__file__).resolve().parents[1]

class LibraryCategoryTests(unittest.TestCase):
    def test_all_families_registered_at_one_root(self):
        categories={c['id']:c['status'] for c in list_template_categories()}
        self.assertEqual(categories,{
            'wiki':'implemented','educational':'reserved','scientific':'reserved',
            'report':'reserved','book':'reserved','rhetorical':'implemented'})
        profiles=load_profiles(ROOT/'template_library/wiki/archetype-profiles.json')
        self.assertEqual(len(profiles),19)

    def test_unknown_category_without_descriptor_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'wiki').mkdir()
            with self.assertRaisesRegex(ValidationError,'declaration missing'):
                list_template_categories(root)

    def test_category_with_wrong_identity_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cat=root/'wiki';cat.mkdir()
            (cat/'category.json').write_text(json.dumps({
                'format':'spek.template-category/1.0','id':'book','status':'reserved'}))
            with self.assertRaisesRegex(ValidationError,'identity'):
                list_template_categories(root)

if __name__=='__main__':unittest.main()
