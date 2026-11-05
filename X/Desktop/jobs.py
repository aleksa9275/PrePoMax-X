"""Desktop process adapter. Original C# owns deck validation and solver lifecycle."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid
from PyQt6 import QtCore

ROOT = Path(__file__).resolve().parents[2]


def resources():
    return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else ROOT


def solver_command(*, pmx=False):
    if getattr(sys, 'frozen', False):
        base = resources()
        registry = base / 'native-solver/build-registry.json'
        if not registry.is_file():
            registry = base.parent / 'Resources/native-solver/build-registry.json'
        profile = json.loads(registry.read_text())['builds'][0]
        return [str(base / 'hosts/solve/PrePoMaxX.Solve'), '--registry', str(registry),
                'run-static-pmx' if pmx else 'run-static', profile['id'], str(registry.parent / 'bin')]
    raise ValueError('Use a packaged solver preview for desktop jobs; no development solver is selected implicitly.')


def examples():
    return resources() / 'examples' if getattr(sys, 'frozen', False) else ROOT / 'X/Analysis/StaticDeck'


def validation_command():
    if getattr(sys, 'frozen', False):
        return [str(resources() / 'hosts/solve/PrePoMaxX.Solve'), 'validate-static']
    return ['dotnet', str(ROOT / 'X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve.dll'), 'validate-static']


class DesktopJob(QtCore.QObject):
    changed = QtCore.pyqtSignal(str)
    completed = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.directory = None
        self.result = None
        self.state = 'Ready'
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.command = None
        self.requested_cancel = False
        self.input_directory = None
        self.workspace = None

    @property
    def active(self):
        return self.process is not None and self.process.state() != QtCore.QProcess.ProcessState.NotRunning

    def start(self, mesh, analysis, parent_directory, command=None, timeout=3600, *,
              definition=None, mesh_bytes=None, pmx_sha256=None, cad_mesh=None, pmx_bytes=None):
        if self.active:
            raise ValueError('A job is already running.')
        mesh = Path(mesh).resolve()
        analysis = Path(analysis).resolve() if analysis is not None else None
        if definition is None and (not mesh.is_file() or analysis is None or not analysis.is_file()):
            raise ValueError('Select an existing INP mesh and analysis JSON.')
        # Serialize now; subsequent edits cannot alter the submitted definition.
        if definition is not None:
            definition_bytes = (json.dumps(definition, indent=2, allow_nan=False) + '\n').encode('utf-8')
            mesh_bytes = mesh.read_bytes() if mesh_bytes is None else mesh_bytes
        if pmx_bytes is not None and (pmx_sha256 is None or hashlib.sha256(pmx_bytes).hexdigest() != pmx_sha256):
            raise ValueError('PMX snapshot differs from its validated source hash.')
        command = list(command if command is not None else solver_command(pmx=pmx_sha256 is not None))
        parent_directory = Path(parent_directory).resolve()
        parent_directory.mkdir(parents=True, exist_ok=True)
        # The original host reserves/creates this new directory atomically.
        self.directory = parent_directory / (datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:12])
        self.workspace = self.directory
        self.input_directory = None
        if definition is not None:
            self.workspace.mkdir()
            self.input_directory = self.workspace / 'inputs'
            self.input_directory.mkdir()
            self.directory = self.workspace / 'solve'
            mesh, analysis = self.input_directory / 'mesh.inp', self.input_directory / 'analysis.json'
            with mesh.open('xb') as stream:
                stream.write(mesh_bytes)
            with analysis.open('xb') as stream:
                stream.write(definition_bytes)
            identity = {
                'meshSha256': hashlib.sha256(mesh_bytes).hexdigest(),
                'analysisSha256': hashlib.sha256(definition_bytes).hexdigest(),
                'scope': 'Immutable submitted job input; not project persistence'}
            if pmx_sha256 is not None:
                identity['sourcePmxSha256'] = pmx_sha256
                if pmx_bytes is not None:
                    with (self.input_directory / 'source.pmx').open('xb') as stream:
                        stream.write(pmx_bytes)
            if cad_mesh is not None:
                cad = cad_mesh.freeze(self.input_directory / 'cad')
                identity['sourceCadSha256'] = cad['sourceSha256']
                identity['baseCadMeshSha256'] = cad['baseMeshSha256']
            (self.input_directory / 'input-identity.json').write_text(json.dumps(identity, indent=2) + '\n')
        self.stdout, self.stderr = bytearray(), bytearray()
        self.result, self.requested_cancel = None, False
        self.command = command + [str(mesh), str(analysis), str(self.directory), str(timeout)]
        self.process = QtCore.QProcess(self)
        self.process.setProgram(self.command[0])
        self.process.setArguments(self.command[1:])
        self.process.setWorkingDirectory(str(parent_directory))
        env = QtCore.QProcessEnvironment.systemEnvironment()
        # The GUI's frozen Python environment must not redirect native loader paths.
        for name in ('PYTHONHOME', 'PYTHONPATH', 'DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH'):
            env.remove(name)
        self.process.setProcessEnvironment(env)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_output)
        self.process.started.connect(lambda: self.set_state('Running'))
        self.process.errorOccurred.connect(self.process_error)
        self.process.finished.connect(self.finished)
        self.set_state('Starting')
        self.process.start()

    def set_state(self, value):
        self.state = value
        self.changed.emit(value)

    def read_output(self):
        self.stdout.extend(bytes(self.process.readAllStandardOutput()))
        self.stderr.extend(bytes(self.process.readAllStandardError()))

    def cancel(self):
        if self.active and not self.requested_cancel:
            self.requested_cancel = True
            # Explicit cross-platform control channel; C# cancels and kills its
            # own solver tree, then writes the normal job outcome.
            self.process.write(b'cancel\n')
            self.set_state('Cancelling')

    def process_error(self, error):
        if error == QtCore.QProcess.ProcessError.FailedToStart:
            self.read_output()
            self.finish_result(False, 'Failed to start', {'error': self.process.errorString()})

    def finished(self, exit_code, exit_status):
        self.read_output()
        try:
            value = json.loads(self.stdout.decode('utf-8'))
        except (ValueError, UnicodeError):
            value = {'error': self.stderr.decode('utf-8', errors='replace') or 'Job host did not return a complete outcome.'}
        success = (exit_code == 0 and exit_status == QtCore.QProcess.ExitStatus.NormalExit
                   and value.get('success') is True and value.get('solverExecuted') is True)
        state = 'Completed' if success else 'Cancelled' if value.get('status') == 'Killed' else 'Failed'
        self.finish_result(success, state, value)

    def finish_result(self, success, state, value):
        if self.result is not None:
            return
        # Preflight failures may happen before the original host creates a folder.
        self.directory.mkdir(exist_ok=True)
        (self.directory / 'desktop.stdout').write_bytes(self.stdout)
        (self.directory / 'desktop.stderr').write_bytes(self.stderr)
        self.result = {'success': success, 'state': state, 'command': self.command,
                       'directory': str(self.directory), 'cancelRequested': self.requested_cancel,
                       'inputDirectory': str(self.input_directory) if self.input_directory else None,
                       'workspace': str(self.workspace),
                       'outcome': value}
        (self.directory / 'desktop-job.json').write_text(json.dumps(self.result, indent=2) + '\n')
        self.set_state(state)
        self.completed.emit(self.result)
