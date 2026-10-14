import unittest
from pathlib import Path


class InlineGeographyTests(unittest.TestCase):
    def test_geographic_controls_exposed_alongside_existing_wizard(self):
        static=Path(__file__).resolve().parents[1]/'skope/static'
        html=(static/'index.html').read_text(encoding='utf8')
        for identifier in ['geo-primary-ui', 'geo-secondary-ui','geo-mode-ui','geo-apply-ui','wizard-open','geostate']:
            self.assertIn('id="'+identifier+'"',html)
        self.assertIn('Secondary area',html)
        self.assertIn('North America = Q49',html)
        self.assertIn('Canada = Q16',html)
    def test_geographic_controls_share_wizard_state_and_are_exported(self):
        static=Path(__file__).resolve().parents[1]/'skope/static'
        app=(static/'app.js').read_text(encoding='utf8')
        self.assertIn("setGeography: (spec) => setGeoSpecification(spec)",app)
        self.assertIn("el('geo-apply-ui').addEventListener('click',applyGeoFromSidebar)",app)
        self.assertIn('function syncGeoUi()',app)
        self.assertIn('geography:{...geography}',app)
        self.assertIn('function invalidateGeoPreview()',app)
        self.assertIn('geoLabel',app)
