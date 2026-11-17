"""Regression tests for direct .pyw execution with wrong Python environment."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime_bootstrap as boot


class RuntimeBootstrapTests(unittest.TestCase):
    def test_current_worker_has_dependencies(self):
        self.assertTrue(boot.valid_runtime(boot.worker_executable()))

    def test_pythonw_selects_python_companion_for_child_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            gui = base / 'pythonw.exe'
            worker = base / 'python.exe'
            gui.touch(); worker.touch()
            self.assertEqual(boot.worker_executable(gui), worker)

    def test_wrong_interpreter_relaunches_using_valid_runtime(self):
        # Does not launch a real GUI: validates the re-exec path and exit code.
        chosen = Path('/test/venv/bin/python')
        with patch.object(boot, 'runtime_candidates', return_value=iter([chosen])), \
             patch.object(boot, 'valid_runtime', return_value=True), \
             patch.object(boot, 'worker_executable', return_value=Path('/wrong/python')), \
             patch.object(boot.subprocess, 'Popen') as popen:
            with self.assertRaises(SystemExit) as raised:
                boot.bootstrap()
            self.assertEqual(raised.exception.code, 0)
            self.assertEqual(str(popen.call_args.args[0][0]), str(chosen))
            self.assertEqual(str(popen.call_args.args[0][1]), str(boot.BASE / 'Fabrique_UNESCO.pyw'))

    def test_installed_runtime_does_not_spawn_second_gui(self):
        current = boot.worker_executable()
        with patch.object(boot, 'runtime_candidates', return_value=iter([current])), \
             patch.object(boot, 'valid_runtime', return_value=True), \
             patch.object(boot.subprocess, 'Popen') as popen:
            self.assertEqual(boot.bootstrap(), current)
            popen.assert_not_called()


if __name__ == '__main__':
    unittest.main()
