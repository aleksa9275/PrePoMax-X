#!/usr/bin/env python3
"""Report PMX command types, order, record identity and cursor without replay."""
import argparse
import json
from pathlib import Path
from runpy import run_path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
helpers = run_path(str(HERE / 'inspect-static-project.py'))


def inspect(pmx, decoder):
    with pmx.open('rb') as stream:
        framing, graph, _ = helpers['read_frames'](stream)
    if framing['header'] != 'PrePoMax v3.0.0':
        raise ValueError('Expected PMX 3.0.0 command history.')
    with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-command-') as directory:
        path = Path(directory) / 'graph.nrbf'
        path.write_bytes(graph)
        summary = helpers['decode'](decoder, ['--command-history', path])
    return {'pmxSha256': framing['inputSha256'], **summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pmx', type=Path)
    parser.add_argument('decoder', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.pmx, args.decoder), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
