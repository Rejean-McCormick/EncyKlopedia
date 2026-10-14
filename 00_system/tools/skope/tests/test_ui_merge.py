"""Release regression checks: density graph and batch result actions coexist."""
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]/'skope/static'

class Parser(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.scripts=[];self.tags={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            self.ids.append(a['id']);self.tags[a['id']]=tag
        if tag=='script':self.scripts.append(a.get('src'))

class ConsolidatedUI(unittest.TestCase):
    def test_all_controls_exist_and_no_id_conflicts(self):
        tree=Parser();tree.feed((ROOT/'index.html').read_text(encoding='utf8'))
        self.assertEqual(len(tree.ids),len(set(tree.ids)))
        self.assertEqual(tree.tags['graph'],'canvas')
        self.assertEqual(tree.tags['large-job-modal'],'dialog')
        self.assertEqual(tree.tags['convergence-help'],'dialog')
        for element in ('density-controls','density-legend','density-pick','density-detail','density-lens',
                        'large-results','large-dialog-download','large-dialog-open','large-dialog-copy',
                        'convergence-help-open','wizard-open','geo-secondary-ui',
                        'extract-profile','extract-preflight','extract-start','extract-modal','extract-progress','extract-open'):
            self.assertIn(element,tree.ids)
        script_names=[x for x in tree.scripts if x]
        self.assertEqual(script_names,['/density.js','/app.js','/wizard.js','/results.js','/extraction.js'])
    def test_app_uses_density_and_resumes_job_by_state_not_translated_button(self):
        js=(ROOT/'app.js').read_text(encoding='utf8')
        self.assertIn('window.SkopeDensity.render(report,root)',js)
        self.assertIn('window.SkopeDensity.clear()',js)
        self.assertIn("['paused','failed','interrupted','limit_reached','running'].includes(window.SkopeLastLargeStatus.state)",js)
        self.assertNotIn("textContent.includes('Reprendre')",js)
        self.assertIn('window.SkopeJobModal?.show()',js)
        self.assertIn("$('large-results').addEventListener('click',show)",(ROOT/'results.js').read_text())
    def test_results_export_and_open_still_exist(self):
        from skope import massive
        from skope.api import App
        self.assertTrue(hasattr(massive,'prepare_result_zip'))
        src=(ROOT/'results.js').read_text()
        self.assertIn('/api/large/result.zip?job=',src)
        self.assertIn('/api/large/open',src)
        self.assertIn('/api/large/copy',src)

if __name__=='__main__': unittest.main()
