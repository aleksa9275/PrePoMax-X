#!/usr/bin/env python3
"""Compare a PMX 3.0.0 embedded static result with its source FRD."""
import argparse
import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
inspect = run_path(str(HERE / 'inspect-result-chunks.py'))['inspect']
FRAME_LIMIT = 16 * 1024 * 1024


def read_payload(stream, row):
    if max(row['compressedBytes'], row['inflatedBytes']) > FRAME_LIMIT:
        raise ValueError('Result frame exceeds comparison limit.')
    stream.seek(row['offset'])
    decoder = zlib.decompressobj(-15)
    data = decoder.decompress(stream.read(row['compressedBytes']), FRAME_LIMIT + 1)
    if (len(data) != row['inflatedBytes'] or not decoder.eof or decoder.unused_data
            or decoder.unconsumed_tail or hashlib.sha256(data).hexdigest() != row['inflatedSha256']):
        raise ValueError('Result frame differs from inspected data.')
    return data


def compare(pmx, frd, probe):
    result = inspect(pmx)
    if result['header'] != 'PrePoMax v3.0.0' or not 1 <= result['fieldFrameCount'] <= 64:
        raise ValueError('Expected PMX 3.0.0 with 1–64 embedded fields.')
    with tempfile.TemporaryDirectory(prefix='prepomaxx-pmx-results-') as directory:
        frames = []
        with pmx.open('rb') as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != result['inputSha256']:
                raise ValueError('PMX changed before field comparison.')
            for row in result['chunks']:
                frame = Path(directory) / row['kind']
                frame.write_bytes(read_payload(source, row))
                frames.append(str(frame))
            source.seek(0)
            if hashlib.file_digest(source, 'sha256').hexdigest() != result['inputSha256']:
                raise ValueError('PMX changed during field comparison.')
        command = ['dotnet', str(probe.resolve()), '--compare-results', str(frd.resolve()), *frames]
        output = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if output.returncode:
            raise ValueError(output.stderr.strip())
        return {'pmxSha256': result['inputSha256'], **json.loads(output.stdout),
                'opaqueHistoryTrailerBytes': result['opaqueHistoryTrailerBytes']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('pmx', 'frd', 'probe'):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(compare(args.pmx, args.frd, args.probe), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError, zlib.error) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
