"""Regression scenarios for user-centered Spek Studio and explicit IA recipes."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from spek.core import ValidationError
from spek.composition_registry import read_registry, assignment_for_identity
from spek.studio_workflow import inspect_kristal, execute_preview, project_pair, command_for_preview
from spek.template_manager import change_json, delete_template, digest, read_object

ROOT = Path(__file__).resolve().parents[1]


class SpekStudioWorkflowTests(unittest.TestCase):
    def test_catalogue_is_authored_and_no_assignments_are_inferred(self):
        data = read_registry(ROOT)
        self.assertEqual(len(data['compositions']), 19)
        self.assertFalse(data['assignments'])
        self.assertIsNone(assignment_for_identity(data, 'Kristal-AI'))
        doc = data['compositions']['arketype-diagnostic-causal']
        self.assertEqual([x['layout_id'] for x in doc['sections_in_order']],
                         ['observation-inference','argument-map','result-card'])

    def test_inspect_kristal_does_not_guess_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)/'Kristal-Sample';folder.mkdir()
            (folder/'kristal.workspace.json').write_text(json.dumps({
                'format':'kristal.local-workspace/3.2.0','slug':'real-identity-only',
                'title':'Fiction','state_ref':'urn:example','native_model':{'kind':'graphe'}}))
            item=inspect_kristal(folder, ROOT)
            self.assertEqual(item['identity'], 'real-identity-only')
            self.assertIsNone(item['assignment'])
            self.assertIsNone(item['composition'])

    def test_refuse_unknown_kristal_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValidationError):inspect_kristal(Path(tmp),ROOT)

    def test_project_pair_does_not_follow_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            article=root/'article.json';real=root/'realizations.json'
            article.write_text('{}');real.write_text('{}')
            self.assertEqual(project_pair(article, real),(article,real))
            link=root/'alias.json'
            try:link.symlink_to(article)
            except (OSError,NotImplementedError):self.skipTest('symlink cannot be created')
            with self.assertRaises(ValidationError):project_pair(link,real)

    def test_html_preview_with_real_compiler_and_fixtures(self):
        article=ROOT/'examples/article.json'
        real=ROOT/'examples/realizations.json'
        with tempfile.TemporaryDirectory() as tmp:
            cmd=command_for_preview(ROOT,article,real,'fr',Path(tmp))
            self.assertIn('build',cmd)
            self.assertIn('--formats',cmd)
        val=execute_preview(ROOT,article,real,'fr',build=False)
        self.assertEqual(val['status'],'checked_only_not_published')
        rendered=execute_preview(ROOT,article,real,'fr',build=True)
        self.assertEqual(rendered['status'],'built_private_not_published')
        self.assertTrue(Path(rendered['page']).is_file())
        shutil.rmtree(rendered['directory'])

    def test_incompatible_language_rejected(self):
        with self.assertRaises(ValidationError):command_for_preview(ROOT,ROOT/'examples/article.json',ROOT/'examples/realizations.json','de',ROOT/'dist')

    def test_delete_or_break_layout_used_by_composition_is_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'Spek';target.mkdir()
            (target/'spek').mkdir();(target/'spek/core.py').touch()
            shutil.copytree(ROOT/'layouts',target/'layouts')
            shutil.copytree(ROOT/'template_library',target/'template_library')
            p=target/'layouts'/'argument-map.json'
            with self.assertRaisesRegex(ValidationError,'composition|Composition'):
                delete_template(target,'layouts/argument-map.json',digest(p))
            obj=read_object(p);obj['version']='99.0.0'
            with self.assertRaisesRegex(ValidationError,'Composition IA'):
                change_json(target,'layouts/argument-map.json',obj,digest(p),kind='layout',item='argument-map')
            self.assertNotEqual(read_object(p)['version'],'99.0.0')


if __name__ == '__main__':
    unittest.main()
