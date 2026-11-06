import ast
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class OverlayContract(unittest.TestCase):
    def test_ui_present_and_parsable(self):
        source=(ROOT/'Concilier_Dictionnaires_diK_UI.pyw').read_text(encoding='utf-8')
        ast.parse(source)
        self.assertIn('Explorer les candidats',source)
        self.assertIn('Lancer / reprendre',source)
        self.assertIn('Vérifier les exports',source)

    def test_source_server_not_in_staging(self):
        self.assertTrue((ROOT/'tools/dictionary-harvester/dik_reconciliation.py').exists())
        src=(ROOT/'tools/dictionary-harvester/dik_reconciliation.py').read_text()
        self.assertIn('readonly_connection',src)
        self.assertIn('mode=ro',src)
        self.assertIn('manual_review_required',src)

    def test_docs_block_canonical_integration(self):
        docs=(ROOT/'docs/CONCILIATION_DIK_LEX1_V05.md').read_text(encoding='utf-8')
        self.assertIn('aucune publication',docs)
        self.assertIn('KQ/KP',docs)

if __name__=='__main__':unittest.main()
