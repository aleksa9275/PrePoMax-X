#!/usr/bin/env python3
"""Verify controlled DAT histories, official command order and malformed inputs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from runpy import run_path
import struct
import subprocess
import sys
import zlib

HERE = Path(__file__).resolve().parent
history = run_path(str(HERE / 'inspect-history.py'))
commands = run_path(str(HERE / 'inspect-command-history.py'))


def check(condition, message):
    if not condition:
        raise ValueError(message)


def integer(number):
    return struct.pack('<i', number)


def name(value):
    encoded = value.encode()
    return integer(len(encoded)) + encoded


def entry(label, times, values, suffix=b''):
    raw = integer(1) + bytes([len(label)]) + label.encode()
    raw += integer(1) + integer(len(times)) + struct.pack(f'<{len(times)}d', *times)
    raw += integer(1) + integer(len(values)) + struct.pack(f'<{len(values)}d', *values)
    raw += integer(0) + b'\x00\x06@null#'
    compressed = zlib.compress(raw, wbits=-15) + suffix
    return integer(1) + integer(len(compressed)) + compressed


def synthetic(first, second):
    return (integer(1) * 2 + name('HistoryOutput')
            + integer(1) * 3 + name('Set') + b'\x00'
            + integer(1) * 3 + name('Field')
            + integer(1) * 3 + name('Component') + name('@null#')
            + integer(1) + integer(2) + first + second + name('Set'))


def main(fixtures, decoder, results_inspector):
    pmx = fixtures / 'definitions-with-results.pmx'
    dat_path = fixtures / 'cube-results.dat'
    dat = json.loads(subprocess.check_output(
        ['dotnet', str(results_inspector), 'inspect-dat', str(dat_path)], timeout=60))
    cube = history['inspect'](pmx)
    comparison = history['compare'](cube, dat)
    check(comparison['matchedRawSeries'] == 96 and comparison['matchedSamples'] == 96
          and comparison['decodedDerivedStressSeries'] == 48, 'Unexpected controlled history coverage')

    profile_path = fixtures / 'Profile.pmx'
    profile = history['inspect'](profile_path)
    profile_commands = commands['inspect'](profile_path, decoder)
    cube_commands = commands['inspect'](pmx, decoder)
    expected = ('CClear CSetNewModelProperties CImportFile CReplaceGeometryPartProperties '
                'CCreateMesh CAddMaterial CAddSection CAddStep CAddBC CAddLoad CReplaceFieldOutput '
                'CAddMeshSetupItem CCreateMesh CPrepareAndRunJob COpenResults CAddResultHistoryOutput '
                'CExportResultHistoryOutput CRunPythonScript CSaveToPmx').split()
    check([entry['type'].split('.')[-1] for entry in profile_commands['commands']] == expected
          and [entry['ordinal'] for entry in profile_commands['commands']] == list(range(19))
          and profile_commands['cursor'] == 18 and profile_commands['remainingRecordCount'] == 0,
          'Bundled project command order, identity or cursor changed')
    check(cube_commands['cursor'] == -1 and not cube_commands['commands'],
          'Unexpected scripted-capture command history')
    base = profile['sets']['From_Field-1']['fields']['STRESS']['MISES']
    doubled = profile['sets']['From_Field-1_STRESS_MISES_x2']['fields']['TABLE']['VALUE']
    check(base['unit'] == doubled['unit'] == 'MPa' and
          base['entries']['51']['time'] == doubled['entries']['51']['time'] == [1] and
          doubled['entries']['51']['values'] == [2 * base['entries']['51']['values'][0]],
          'Bundled field and table histories differ from the expected relationship')

    first = entry('1', [0.25, 1.0], [3, 4])
    second = entry('2', [], [5, 6])
    raw = synthetic(first, second)
    read = history['read_history']
    entries = read(raw)['sets']['Set']['fields']['Field']['Component']['entries']
    check(entries['1']['time'] == entries['2']['time'] == [0.25, 1.0]
          and entries['1']['time'] is not entries['2']['time'], 'Shared times were not copied')

    altered = deepcopy(cube)
    altered['sets']['NALL']['fields']['DISPLACEMENTS']['U1']['entries']['1']['values'][0] = 1
    controls = [
        ('truncated-trailer', lambda: read(raw[:-1])),
        ('trailing-bytes', lambda: read(raw + b'X')),
        ('duplicate-series', lambda: read(synthetic(first, first))),
        ('invalid-shared-time', lambda: read(synthetic(first, entry('2', [], [5])))),
        ('entry-trailing-deflate-data', lambda: read(synthetic(first, entry('2', [], [5, 6], b'X')))),
        ('nonfinite-sample', lambda: read(synthetic(first, entry('2', [], [float('nan'), 6])))),
        ('modified-dat-value', lambda: history['compare'](altered, dat)),
    ]
    rejected = []
    for label, run in controls:
        try:
            run()
        except (ValueError, zlib.error):
            rejected.append(label)
        else:
            raise ValueError(f'Accepted {label}')
    print(json.dumps({'controlledPmxSha256': cube['pmxSha256'],
                      'historyProjectionSha256': hashlib.sha256(json.dumps(
                          cube, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                      'comparison': comparison, 'profileResultHistories': profile,
                      'profileCommands': profile_commands, 'controlledCommands': cube_commands,
                      'sharedTimeSamplesRestored': 2, 'rejected': rejected}, indent=2))


if __name__ == '__main__':
    main(*(Path(argument).resolve() for argument in sys.argv[1:]))
