"""Les réglages UI et Wizard sont compatibles avec le moteur, sans collecte automatique."""
import unittest
from pathlib import Path
from skope.scope import validate_recipe,PREVIEW_NODE_BUDGET

STATIC=Path(__file__).resolve().parents[1]/'skope/static'

class WorldwideBotanyDefaults(unittest.TestCase):
    def test_backend_accepts_entire_ui_range_and_preview_budget(self):
        recipe={'root':'Q192154','default_depth':8,'branches':{'P171:in':8},
                'direction':'in','allowed_properties':['P171'],'max_entities':10000,
                'convergence':{'threshold_percent':14.6,'min_support':8,'extra_depth':0,'include':[]}}
        result=validate_recipe(recipe)
        self.assertEqual(result['default_depth'],8)
        self.assertEqual(result['max_entities'],PREVIEW_NODE_BUDGET)
        self.assertEqual(validate_recipe(dict(recipe,max_entities=0))['max_entities'],0)
        self.assertEqual(validate_recipe(dict(recipe,max_entities=1000000))['max_entities'],1000000)
        for value in (9,-1):
            with self.assertRaises(ValueError):validate_recipe(dict(recipe,default_depth=value))
        with self.assertRaises(ValueError):validate_recipe(dict(recipe,max_entities=-1))
    def test_depth_and_botany_defaults_are_aligned(self):
        page=(STATIC/'index.html').read_text()
        app=(STATIC/'app.js').read_text()
        wizard=(STATIC/'wizard.js').read_text()
        self.assertIn('max="8" value="6" id="depth"',page)
        self.assertIn('for(let i=0;i<=8;i++',app)
        for item in ["el('depth').value='6'","el('budget').value='0'",
                     "el('props').value='P171'","el('minsupport').value='8'",
                     "root=n.id;selectedCandidates.clear();branchOverrides={}"]:
            self.assertIn(item,app)
        self.assertIn("values:{direction:'in',props:'P171',depth:6,budget:0,threshold:14.6,minsupport:8,extra:0}",wizard)
        self.assertIn('profileRecipe().max_entities===0?1500',wizard)
        self.assertIn('previewBusy=true',app)
        self.assertIn("+el('budget').value===0",app)
        self.assertIn('Batch QID inventory',page)
    def test_no_canonical_mutation_new_paths(self):
        for filename in ('app.js','wizard.js'):
            src=(STATIC/filename).read_text()
            self.assertNotIn('canon/',src)
        self.assertIn("if route=='/api/preview'",(STATIC.parent/'api.py').read_text())

if __name__=='__main__':unittest.main()
