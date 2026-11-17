"""Repository integrity checks: English wiki, safe publication defaults, fixed layout contracts."""
import re
import tempfile
import unittest
from pathlib import Path

from spek.cli import verify_site
from spek.core import ValidationError, read_json
from spek.render import landing_html

from spek.core import compile_inputs

def fixtures():
    return (read_json(ROOT/"examples/article.json"),read_json(ROOT/"examples/realizations.json"),
            [read_json(p) for p in sorted((ROOT/"layouts").glob("*.json"))])

ROOT = Path(__file__).resolve().parent.parent

class RepositoryIntegrity(unittest.TestCase):
    def test_english_landing_and_trilingual_navigation(self):
        model = compile_inputs(*fixtures())
        html = landing_html(model)
        self.assertIn('<html lang="en">', html)
        self.assertIn('SPEK · 0.5', html)
        for language in ('fr', 'en', 'it'):
            self.assertIn(f'{language}/index.html', html)

    def test_wiki_has_links_and_all_pages(self):
        wiki = ROOT / 'wiki'
        pages = {p.stem for p in wiki.glob('*.md')}
        self.assertGreaterEqual(len(pages), 16)
        self.assertIn('Home', pages)
        self.assertIn('_Sidebar', pages)
        for p in wiki.glob('*.md'):
            text = p.read_text(encoding='utf-8')
            for name in re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', text):
                target = name.replace(' ', '-')
                self.assertIn(target, pages, f'{p.name}: [[{name}]] missing')

    def test_layout_spec_cardinality_is_explicit(self):
        for path in (ROOT / 'layouts').glob('*.json'):
            contract = read_json(path)
            self.assertEqual(contract['format'], 'kristal.editorial-layout/0.1')
            self.assertTrue(contract['version'])
            for rule in contract['slots'].values():
                self.assertGreaterEqual(rule['min'], 0)
                self.assertGreaterEqual(rule['max'], rule['min'])
                self.assertTrue(rule['allowed_kinds'])

    def test_manifest_symlink_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'real').mkdir()
            (root/'real'/'manifest.json').write_text('{}', encoding='utf-8')
            (root/'fake').symlink_to(root/'real', target_is_directory=True)
            with self.assertRaisesRegex(ValidationError, 'Site root must not be a symlink'):
                verify_site(root/'fake')
