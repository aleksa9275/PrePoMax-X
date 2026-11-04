"""Desktop adapter for the checked, result-free PMX 3.0.0 static workflow."""
import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess
import sys
import tempfile

from PyQt6 import QtCore, QtWidgets

from jobs import ROOT, resources

HOSTS = (
    ('pmx-mesh', 'PmxMesh', 'X/Feasibility/PmxMesh'),
    ('pmx-graph', 'PrePoMaxX.NrbfInventory', 'X/Feasibility/Pmx'),
    ('pmx-deck', 'PmxDeck', 'X/Feasibility/PmxDeck'),
)
MAX_PROJECT_BYTES = 32 * 1024 * 1024


def tool_paths():
    if getattr(sys, 'frozen', False):
        base = resources()
        return base / 'pmx-tools', tuple(base / 'hosts' / host / executable for host, executable, _ in HOSTS)
    return ROOT / 'X/Feasibility/Pmx', tuple(
        ROOT / directory / 'bin/Release/net10.0' / (executable + '.dll') for _, executable, directory in HOSTS)


def available():
    tools, hosts = tool_paths()
    return (tools / 'write-controlled-edit.py').is_file() and all(path.is_file() for path in hosts)


class PmxSession:
    def __init__(self, path, *, tools=None, hosts=None):
        self.path = Path(path).resolve()
        if tools is None:
            tools, hosts = tool_paths()
        if not all(path.is_file() for path in hosts):
            raise ValueError('The checked PMX tools are missing from this build.')
        self.mesh_host, self.graph_host, self.deck_host = hosts
        self.writer = run_path(str(tools / 'write-controlled-edit.py'))
        decks = self.writer['decks']
        with self.path.open('rb') as stream:
            self.contents = stream.read(MAX_PROJECT_BYTES + 1)
        if len(self.contents) > MAX_PROJECT_BYTES:
            raise ValueError('This PMX editor accepts project files up to 32 MiB.')

        with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-open-') as directory:
            copy = Path(directory) / 'project.pmx'
            copy.write_bytes(self.contents)
            reader = self.writer['reader']
            self.project = reader['inspect'](copy, self.mesh_host, self.graph_host)
            with copy.open('rb') as stream:
                framing, graph, _ = reader['read_frames'](stream)
            targets = decks['validate_shape'](self.project, framing, graph, self.graph_host)
            self.mesh_bytes = decks['mesh_input'](self.project).encode('utf-8')
            self.definition = decks['project_definition'](self.project['graph'])
            deck = Path(directory) / 'check.inp'
            decks['build_deck'](self.mesh_bytes, self.definition, self.deck_host, deck)
            self.deck_sha256 = hashlib.sha256(deck.read_bytes()).hexdigest()
        values = {target['Role']: target['Value'] for target in targets}
        if not values['modulus'].endswith(' MPa') or not values['force'].endswith(' N'):
            raise ValueError('The PMX editor requires stored MPa and N equation values.')
        self.modulus = self.writer['positive_decimal'](values['modulus'].removesuffix(' MPa'))
        self.force = self.writer['positive_decimal'](values['force'].removesuffix(' N'))

    def save_as(self, destination, modulus, force):
        destination = Path(destination)
        if destination.suffix.lower() != '.pmx':
            raise ValueError('Choose a .pmx destination.')
        if destination.resolve() == self.path or destination.exists() or destination.is_symlink():
            raise FileExistsError('Choose a new PMX filename.')
        with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-save-') as directory:
            source = Path(directory) / 'original.pmx'
            source.write_bytes(self.contents)
            return self.writer['write_edit'](
                source, destination, self.mesh_host, self.graph_host, deck_builder=self.deck_host,
                modulus_mpa=modulus, force_n=force)


class PmxDialog(QtWidgets.QDialog):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle('Static PMX project')
        form = QtWidgets.QFormLayout(self)
        mesh = session.project['mesh']
        graph = session.project['graph']
        fields = (
            ('Project', session.path.name),
            ('Mesh', f"{len(mesh['nodes'])} nodes · {len(mesh['elements'])} elements"),
            ('Units', graph['unitSystem']),
            ('Material', graph['materials'][0]['name']),
            ('Load region', graph['steps'][0]['loads'][0]['region']),
        )
        for name, value in fields:
            label = QtWidgets.QLabel(value)
            label.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            form.addRow(name, label)
        self.modulus = QtWidgets.QLineEdit(session.modulus)
        self.force = QtWidgets.QLineEdit(session.force)
        form.addRow('Young’s modulus (MPa)', self.modulus)
        form.addRow('Axial force per node (N)', self.force)
        self.message = QtWidgets.QLabel()
        self.message.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.message.setWordWrap(True)
        form.addRow(self.message)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Save |
                                             QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setText('Save As…')
        buttons.accepted.connect(self.choose_destination)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def choose_destination(self):
        name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save static PMX copy', str(self.session.path.with_name(self.session.path.stem + '-edited.pmx')),
            'PrePoMax project (*.pmx)', options=QtWidgets.QFileDialog.Option.DontConfirmOverwrite)
        if name:
            path = Path(name)
            self.save(path if path.suffix else path.with_suffix('.pmx'))

    def save(self, path):
        try:
            receipt = self.session.save_as(path, self.modulus.text().strip(), self.force.text().strip())
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            self.message.setText(str(error))
            return None
        self.message.setText('Saved ' + Path(path).name)
        return receipt


def run_probe(app, window, source, output):
    """Exercise the PMX dialog, model viewport and native job."""
    try:
        output.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        print(json.dumps({'success': False, 'error': str(error)}), flush=True)
        window.close()
        app.exit(1)
        return
    report = {'success': False, 'viewport': window.transport, 'checks': []}
    target = output / 'edited.pmx'
    node_ids = [13, 23, 33, 43, 53, 63, 73, 83]
    errors = []
    timeout = QtCore.QTimer(window)
    timeout.setSingleShot(True)
    timeout.timeout.connect(window.job.cancel)

    def check(name, condition):
        report['checks'].append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise ValueError(name)

    def in_dialog(action):
        def interact():
            dialog = app.activeModalWidget()
            try:
                check('Opened the static PMX dialog', isinstance(dialog, PmxDialog))
                action(dialog)
            except Exception as error:
                errors.append(error)
            finally:
                if isinstance(dialog, QtWidgets.QDialog):
                    dialog.reject()
        QtCore.QTimer.singleShot(0, interact)
        window.edit_pmx_action.trigger()
        if errors:
            raise errors[0]

    def edit(dialog):
        check('Opened baseline material and load', dialog.modulus.text() == '210000' and
              dialog.force.text() == '25')
        dialog.modulus.setText('0')
        check('Invalid modulus leaves no file', dialog.save(target) is None and not target.exists())
        dialog.modulus.setText('84500.5')
        dialog.force.setText('42.25')
        receipt = dialog.save(target)
        check('Save As publishes a verified PMX', bool(receipt and receipt['portableReadbackPassed']))
        report['write'] = receipt
        before = hashlib.sha256(target.read_bytes()).hexdigest()
        check('Save As refuses an existing file', dialog.save(target) is None and
              hashlib.sha256(target.read_bytes()).hexdigest() == before)

    def reopened(dialog):
        check('Fresh reopen shows saved equations', dialog.modulus.text() == '84500.5' and
              dialog.force.text() == '42.25')

    def finish(error=None):
        if error is not None:
            report['error'] = str(error)
        report['success'] = error is None
        (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report), flush=True)
        window.close()
        app.exit(0 if report['success'] else 1)

    def completed(result):
        timeout.stop()
        try:
            check('Native solver completed the PMX job', result['success'] and result['outcome']['solverExecuted'])
            inputs = Path(result['inputDirectory'])
            identity = json.loads((inputs / 'input-identity.json').read_text())
            check('Frozen inputs identify the reopened PMX and validated definition',
                  identity['sourcePmxSha256'] == report['write']['outputSha256']
                  and (inputs / 'mesh.inp').read_bytes() == pmx.mesh_bytes
                  and json.loads((inputs / 'analysis.json').read_text()) == pmx.definition)
            deck_sha256 = result['outcome']['outputs']['analysis.inp']
            check('Executed deck matches the original C# validation', deck_sha256 == pmx.deck_sha256)
            check('Result fields loaded in the viewport with the PMX model retained',
                  window.current_path == Path(result['directory']) / 'analysis.frd'
                  and window.model_path == target and window.mapper.GetScalarVisibility()
                  and {'DISP', 'STRESS', 'FORC'} <= {field['name'] for field in window.scene['fields']})
            check('Both project files are unchanged after solve',
                  hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
                  and hashlib.sha256(target.read_bytes()).hexdigest() == identity['sourcePmxSha256'])
            report['job'] = {'deckSha256': deck_sha256, 'inputs': identity,
                             'frdSha256': result['outcome']['outputs']['analysis.frd'],
                             'requiredOutputs': result['outcome']['requiredOutputs']}
        except Exception as error:
            finish(error)
        else:
            finish()

    try:
        original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        check('PMX action is available', window.pmx_action.isVisible())
        window.open_pmx(source)
        check('Baseline project opened in the model tree and viewport',
              window.model_path == source and window.current_path == source and window.edit_pmx_action.isVisible())
        in_dialog(edit)
        window.open_pmx(target)
        pmx = window.pmx_session
        in_dialog(reopened)
        grid_nodes = window.grid.GetPointData().GetGlobalIds()
        grid_elements = window.grid.GetCellData().GetGlobalIds()
        check('Fresh reopen renders the original mesh IDs',
              [grid_nodes.GetValue(i) for i in range(grid_nodes.GetNumberOfValues())] == node_ids
              and [grid_elements.GetValue(i) for i in range(grid_elements.GetNumberOfValues())] == [7001])
        unsupported = output / 'old.pmx'
        unsupported.write_bytes(pmx.contents.replace(b'PrePoMax v3.0.0', b'PrePoMax v2.6.0', 1))
        try:
            window.open_pmx(unsupported)
        except ValueError:
            check('Unsupported PMX preserves the active model', window.pmx_session is pmx and window.current_path == target)
        else:
            raise ValueError('Unsupported PMX was accepted.')
        window.jobs_root = output / 'jobs'
        window.job.completed.connect(completed)
        timeout.start(120000)
        window.run_action.trigger()
        check('Run analysis launched the PMX job', window.job.active)
    except Exception as error:
        finish(error)
