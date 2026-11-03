"""Two Unix process regressions for the desktop stdin cancellation protocol."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time


def verify(command, root, work, architecture):
    if os.name == 'nt':
        return {'status': 'pending native Windows pipe fixture; no Unix script substitution'}
    fixture = work / 'pipe-control'
    fixture.mkdir()
    solver = fixture / 'solver'
    solver.write_text('#!/bin/sh\necho "CalculiX Version 2.22"\nif [ -f "../wait" ]; then echo $$ > solver.pid; exec /bin/sleep 60; fi\n'
        'if [ -f "../fields" ]; then echo fixture > analysis.frd; echo fixture > analysis.sta; : > analysis.dat; fi\n')
    solver.chmod(0o755)
    registry = fixture / 'registry.json'
    registry.write_text(json.dumps({'schemaVersion': 1, 'builds': [{'id': 'pipe-fixture',
        'os': platform.system(), 'architecture': architecture, 'version': '2.22',
        'executable': solver.name, 'files': {solver.name: hashlib.sha256(solver.read_bytes()).hexdigest()}}]}))
    def arguments(name, analysis=None):
        return [*map(str, command), '--registry', str(registry), 'run-static', 'pipe-fixture', str(fixture),
                str(root / 'X/Analysis/StaticDeck/cube-mesh.inp'), str(analysis or root / 'X/Analysis/StaticDeck/cube-analysis.json'),
                str(fixture / name), '10']
    eof = subprocess.run(arguments('eof'), input='', capture_output=True, text=True, timeout=15)
    value = json.loads(eof.stdout)
    if eof.returncode != 1 or not value['solverExecuted'] or value['status'] != 'OK' or value['outputsPresent']:
        raise ValueError('EOF must allow solver exit, without fabricating output success')
    (fixture / 'fields').touch()
    requested = subprocess.run(arguments('requested-history'), input='', capture_output=True, text=True, timeout=15)
    value = json.loads(requested.stdout)
    if requested.returncode != 1 or value['success'] or value['outputsPresent'] or '.dat' not in value['requiredOutputs']:
        raise ValueError('Requested histories must still require nonempty DAT')
    spec = json.loads((root / 'X/Analysis/StaticDeck/cube-analysis.json').read_text())
    spec['step']['nodalHistorySets'], spec['step']['elementHistorySets'] = [], []
    definition = fixture / 'no-history.json'
    definition.write_text(json.dumps(spec))
    field_only = subprocess.run(arguments('field-only', definition), input='', capture_output=True, text=True, timeout=15)
    value = json.loads(field_only.stdout)
    if field_only.returncode or not value['success'] or not value['solverExecuted'] or value['requiredOutputs'] != ['.frd', '.sta']:
        raise ValueError('Field-only transport incorrectly requires unrequested DAT')
    (fixture / 'fields').unlink()
    missing = subprocess.run(arguments('missing-fields', definition), input='', capture_output=True, text=True, timeout=15)
    value = json.loads(missing.stdout)
    if missing.returncode != 1 or value['success'] or value['outputsPresent']:
        raise ValueError('Field-only transport must still require FRD/STA')
    (fixture / 'wait').touch()
    process = subprocess.Popen(arguments('cancel'), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 8
    marker = fixture / 'cancel/solver.pid'
    while not marker.is_file() and process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.01)
    stdout, stderr = process.communicate('cancel\n', timeout=15)
    value = json.loads(stdout)
    if not marker.is_file() or process.returncode != 1 or value['success'] or value['status'] != 'Killed' or not value['solverExecuted']:
        raise ValueError('Stdin cancellation failed to stop actual fixture solver: ' + stderr)
    try:
        os.kill(int(marker.read_text()), 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError('Fixture solver survived cancellation')
    return {'status': 'passed', 'eofDoesNotCancel': True, 'cancelStopsSolver': True,
            'requestedHistoryRequiresDat': True, 'fieldOnlyAllowsEmptyDat': True, 'missingFieldsRejected': True,
            'cancelWritesNormalOutcome': (fixture / 'cancel/run.json').is_file(), 'fixtureOnly': True}
