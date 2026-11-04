#!/usr/bin/env python3
"""Read the supported PMX analysis-mesh prefix without opening a project."""
import argparse
import json
from pathlib import Path
from runpy import run_path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
read_frames = run_path(str(HERE / 'inspect-pmx.py'))['read_frames']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('decoder', type=Path, help='Built PmxMesh.dll')
    args = parser.parse_args()
    try:
        with args.input.open('rb') as stream:
            framing, _, model = read_frames(stream)
        if framing['header'] != 'PrePoMax v3.0.0':
            raise ValueError('The mesh-prefix probe requires the PrePoMax v3.0.0 header.')
        with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-mesh-') as folder:
            block = Path(folder) / 'model.bin'
            block.write_bytes(model)
            result = subprocess.run(
                ['dotnet', str(args.decoder.resolve()), str(block)],
                capture_output=True, text=True, timeout=30, check=False)
        if result.returncode:
            raise ValueError(result.stderr.strip())
        print(json.dumps({'inputSha256': framing['inputSha256'], **json.loads(result.stdout)}))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
