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


if __name__ == '__main__':
    unittest.main()
