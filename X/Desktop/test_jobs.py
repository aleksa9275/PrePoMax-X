"""Real Qt process + original C# boundary tests; no VTK/window is needed."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from PyQt6 import QtCore
from jobs import DesktopJob, ROOT


class DesktopJobBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])
        cls.host = Path(os.environ.get('DESKTOP_TEST_SOLVE_HOST', ROOT / 'X/Build/artifacts/task0042-mac-hosts/hosts/solve/PrePoMaxX.Solve'))
        if not cls.host.is_file():
            raise RuntimeError('Build current shared hosts or set DESKTOP_TEST_SOLVE_HOST')

    def wait(self, predicate, seconds=15):
        until = time.monotonic() + seconds
        while not predicate() and time.monotonic() < until:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertTrue(predicate(), 'Timed out waiting for process outcome')

    def command(self, root, script):
        solver = root / 'fixture-solver'
        solver.write_text(script)
        solver.chmod(0o755)
        registry = root / 'fixture-registry.json'
        registry.write_text(json.dumps({'schemaVersion': 1, 'builds': [{
            'id': 'test-only', 'os': 'Darwin' if os.uname().sysname == 'Darwin' else 'Linux',
            'architecture': 'Arm64' if os.uname().machine in ('arm64', 'aarch64') else 'X64',
            'executable': solver.name, 'version': '2.22',
            'files': {solver.name: hashlib.sha256(solver.read_bytes()).hexdigest()}}]}))
        return [str(self.host), '--registry', str(registry), 'run-static', 'test-only', str(root)]

    def test_cancel_reaches_original_host_and_stops_solver(self):
        with tempfile.TemporaryDirectory(prefix='desktop job ') as directory:
            root = Path(directory)
            command = self.command(root, '#!/bin/sh\necho "CalculiX Version 2.22"\necho $$ > solver.pid\nexec /bin/sleep 60\n')
            job = DesktopJob()
            job.start(ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp', ROOT / 'X/Analysis/StaticDeck/cube-analysis.json', root / 'jobs', command)
            self.wait(lambda: (job.directory / 'solver.pid').exists())
            pid = int((job.directory / 'solver.pid').read_text())
            with self.assertRaisesRegex(ValueError, 'already running'):
                job.start(ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp', ROOT / 'X/Analysis/StaticDeck/cube-analysis.json', root / 'jobs', command)
            job.cancel()
            self.wait(lambda: job.result is not None)
            self.assertEqual(job.state, 'Cancelled')
            self.assertTrue(job.result['outcome']['solverExecuted'])
            self.assertFalse(job.result['success'])
            self.assertFalse(job.active)
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
            self.assertTrue((job.directory / 'run.json').is_file())

    def test_original_preflight_failure_keeps_diagnostics(self):
        with tempfile.TemporaryDirectory(prefix='desktop preflight ') as directory:
            root = Path(directory)
            command = self.command(root, '#!/bin/sh\nexit 99\n')
            bad = root / 'bad analysis.json'
            bad.write_text('{invalid')
            job = DesktopJob()
            job.start(ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp', bad, root / 'jobs', command)
            self.wait(lambda: job.result is not None)
            self.assertEqual(job.state, 'Failed')
            self.assertFalse(job.result['success'])
            self.assertIn('error', job.result['outcome'])
            self.assertTrue((job.directory / 'desktop.stderr').read_bytes())
            self.assertFalse((job.directory / 'solver.pid').exists())

    def test_zero_exit_solver_error_cannot_pass_with_nonempty_output_headers(self):
        with tempfile.TemporaryDirectory(prefix='desktop reported error ') as directory:
            root = Path(directory)
            command = self.command(root, '#!/bin/sh\necho "CalculiX Version 2.22"\necho " *ERROR in arpack: too many eigenvalues requested"\nfor file in analysis.frd analysis.dat analysis.sta; do echo header > "$file"; done\nexit 0\n')
            job = DesktopJob()
            job.start(ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp', ROOT / 'X/Analysis/StaticDeck/cube-analysis.json', root / 'jobs', command)
            self.wait(lambda: job.result is not None)
            self.assertEqual(job.state, 'Failed')
            self.assertTrue(job.result['outcome']['solverReportedErrors'])
            self.assertEqual(job.result['outcome']['exitCode'], 0)
            self.assertTrue(job.result['outcome']['outputsPresent'])
            self.assertFalse(job.result['success'])

    def test_changed_native_solver_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory(prefix='desktop changed ') as directory:
            root = Path(directory)
            command = self.command(root, '#!/bin/sh\nexit 99\n')
            (root / 'fixture-solver').write_text('#!/bin/sh\necho tampered\n')
            job = DesktopJob()
            job.start(ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp', ROOT / 'X/Analysis/StaticDeck/cube-analysis.json', root / 'jobs', command)
            self.wait(lambda: job.result is not None)
            self.assertEqual(job.state, 'Failed')
            self.assertIn('missing or changed', job.result['outcome']['error'])
            self.assertFalse(job.result['success'])

    def test_editor_run_freezes_mesh_and_definition_before_execution(self):
        with tempfile.TemporaryDirectory(prefix='desktop edited model ') as directory:
            root = Path(directory)
            command = self.command(root, '#!/bin/sh\necho "CalculiX Version 2.22"\necho $$ > solver.pid\nexec /bin/sleep 60\n')
            mesh = root / 'original mesh.inp'
            initial_mesh = (ROOT / 'X/Analysis/StaticDeck/cube-mesh.inp').read_bytes()
            mesh.write_bytes(initial_mesh)
            definition = json.loads((ROOT / 'X/Analysis/StaticDeck/cube-analysis.json').read_text())
            job = DesktopJob()
            job.start(mesh, None, root / 'jobs', command, definition=definition)
            definition['materials'][0]['youngsModulus'] = '999 GPa'
            mesh.write_text('Changed after submission')
            self.wait(lambda: (job.directory / 'solver.pid').exists())
            self.assertEqual((job.input_directory / 'mesh.inp').read_bytes(), initial_mesh)
            frozen = json.loads((job.input_directory / 'analysis.json').read_text())
            self.assertEqual(frozen['materials'][0]['youngsModulus'], '210 GPa')
            self.assertIn('210000, 0.3', (job.directory / 'analysis.inp').read_text())
            self.assertEqual(job.input_directory.parent, job.directory.parent)
            job.cancel()
            self.wait(lambda: job.result is not None)
            self.assertEqual(job.state, 'Cancelled')
            self.assertEqual(Path(job.result['inputDirectory']), job.input_directory)


if __name__ == '__main__':
    unittest.main()
