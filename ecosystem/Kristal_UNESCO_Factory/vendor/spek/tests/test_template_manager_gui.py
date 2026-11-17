"""Headless tests for the .pyw launcher's local mutation layer."""
from __future__ import annotations
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from spek.core import ValidationError
from spek.template_manager import (
 TemplateConflict, create_category, create_family_template, create_layout,
 change_json, delete_template, digest, format_json, read_object,
 save_profile, source_root, template_inventory, validate_layout,
)

ROOT=Path(__file__).resolve().parents[1]

class TemplateManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'Spek'
        self.root.mkdir()
        (self.root/'spek').mkdir()
        (self.root/'spek/core.py').write_text('')
        shutil.copytree(ROOT/'layouts',self.root/'layouts')
        shutil.copytree(ROOT/'template_library',self.root/'template_library')

    def test_inventory_existing_categories_and_wiki(self):
        x=template_inventory(self.root)
        self.assertEqual(len(x['categories']),6)
        self.assertEqual(len(x['layouts']),27)
        self.assertEqual(len(x['profiles']),19)

    def test_reserved_category_and_draft(self):
        create_category(self.root,'poster','Affiches')
        f=create_family_template(self.root,'poster','first')
        self.assertEqual(read_object(f)['status'],'draft')
        clone=create_family_template(self.root,'poster','second',source='first')
        self.assertEqual(read_object(clone)['id'],'second')
        self.assertEqual(len(template_inventory(self.root)['templates']['poster']),2)
        backup=delete_template(self.root,'template_library/poster/templates/first.json',digest(f))
        self.assertFalse(f.exists());self.assertTrue(backup.is_file())

    def test_layout_new_edit_backup_and_conflict(self):
        p=create_layout(self.root,'new-card',source='concept-card')
        self.assertEqual(read_object(p)['id'],'new-card')
        before=digest(p);x=read_object(p);x['intent']='new-intent'
        backup=change_json(self.root,'layouts/new-card.json',x,before,kind='layout',item='new-card')
        self.assertTrue(backup.is_file())
        self.assertEqual(read_object(backup)['intent'],'define_and_contextualize')
        with self.assertRaises(TemplateConflict):
            change_json(self.root,'layouts/new-card.json',x,before,kind='layout',item='new-card')
        saved=delete_template(self.root,'layouts/new-card.json',digest(p))
        self.assertTrue(saved.exists())

    def test_used_layout_cannot_be_deleted(self):
        target=self.root/'layouts/concept-card.json'
        with self.assertRaises(ValidationError):
            delete_template(self.root,'layouts/concept-card.json',digest(target))
        self.assertTrue(target.exists())

    def test_profile_update_only_target(self):
        path=self.root/'template_library/wiki/archetype-profiles.json'
        original=read_object(path)
        slug='diagnostic-causal'
        prof=dict(original['archetypes'][slug]);prof['label']='Diagnostic — test'
        backup=save_profile(self.root,slug,prof,digest(path))
        now=read_object(path)
        self.assertEqual(now['archetypes'][slug]['label'],'Diagnostic — test')
        self.assertEqual(now['archetypes']['composition-hybride'],original['archetypes']['composition-hybride'])
        self.assertTrue(backup.is_file())

    def test_status_not_promoted_by_edit(self):
        path=self.root/'template_library/scientific/category.json'
        data=read_object(path);data['status']='implemented'
        with self.assertRaises(ValidationError):
            change_json(self.root,'template_library/scientific/category.json',data,digest(path),kind='category',item='scientific')

    def test_invalid_slug_and_slots(self):
        for slug in ('../bad','Bad','book/name'):
            with self.assertRaises(ValidationError):create_category(self.root,slug,'No')
        with self.assertRaises(ValidationError):
            validate_layout({'format':'kristal.editorial-layout/0.1','id':'bad','version':'1.0','slots':{'s':{'min':3,'max':1,'allowed_kinds':['statement']}}},'bad')

    def test_symlink_escape_rejected(self):
        try:(self.root/'layouts'/'unsafe.json').symlink_to(ROOT/'layouts'/'concept-card.json')
        except (OSError,NotImplementedError):self.skipTest('Symlinks unavailable')
        with self.assertRaises(ValidationError):template_inventory(self.root)

if __name__=='__main__':unittest.main()
