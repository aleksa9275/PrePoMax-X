#!/usr/bin/env python3
"""Inspect bounded PMX 3.0.0 result histories and compare raw series to DAT."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from runpy import run_path
import struct
import subprocess
import zlib

HERE = Path(__file__).resolve().parent
inspect_frames = run_path(str(HERE / 'inspect-result-chunks.py'))['inspect']
MAX_TRAILER = 8 * 1024 * 1024
MAX_ENTRY = 128 * 1024
MAX_SERIES = 4096
MAX_SAMPLES = 100_000
DERIVED_STRESS = {'MISES', 'TRESCA', 'SGN_MAX_ABS_PRI', 'PRINCIPAL_MAX',
                  'PRINCIPAL_MID', 'PRINCIPAL_MIN'}


class Reader:
    def __init__(self, data):
        self.stream = io.BytesIO(data)
        self.size = len(data)
        self.named_records = 0

    def read(self, size):
        if not 0 <= size <= self.size - self.stream.tell():
            raise ValueError('Truncated history or invalid length.')
        return self.stream.read(size)

    def integer(self):
        return struct.unpack('<i', self.read(4))[0]

    def count(self, maximum):
        count = self.integer()
        if not 0 <= count <= maximum:
            raise ValueError('History count exceeds the probe limit.')
        return count

    def flag(self, wide=True):
        flag = self.integer() if wide else self.read(1)[0]
        if flag not in (0, 1):
            raise ValueError('Invalid history presence or Boolean flag.')
        return bool(flag)

    def require(self):
        if not self.flag():
            raise ValueError('Missing expected history record.')

    def string(self, binary=False, optional=False):
        if binary:
            size = 0
            for shift in range(0, 35, 7):
                byte = self.read(1)[0]
                size |= (byte & 127) << shift
                if byte < 128:
                    break
            else:
                raise ValueError('Invalid history string length.')
        else:
            size = self.integer()
        if not 0 <= size <= 4096:
            raise ValueError('History string exceeds the probe limit.')
        value = self.read(size).decode('utf-8')
        if optional:
            return None if value == '@null#' else value
        if not value or value == '@null#':
            raise ValueError('Missing history identity.')
        return value

    def array(self, code):
        if not self.flag():
            return []
        count = self.count(MAX_SAMPLES)
        width = struct.calcsize(code)
        return list(struct.unpack(f'<{count}{code}', self.read(count * width)))

    def end(self):
        if self.stream.tell() != self.size:
            raise ValueError('Unexpected trailing history bytes.')


def entry(reader):
    reader.require()
    compressed = reader.read(reader.count(MAX_ENTRY))
    inflater = zlib.decompressobj(-15)
    raw = inflater.decompress(compressed, MAX_ENTRY + 1)
    if (len(raw) > MAX_ENTRY or not inflater.eof or inflater.unused_data
            or inflater.unconsumed_tail):
        raise ValueError('Invalid or oversized history entry Deflate frame.')
    payload = Reader(raw)
    payload.require()
    name = payload.string(binary=True)
    time = payload.array('d')
    values = payload.array('d')
    counts = payload.array('i')
    local = payload.flag(wide=False)
    unit = payload.string(binary=True, optional=True)
    payload.end()
    if (not values or (time and len(time) != len(values))
            or (counts and (len(counts) != len(values) or any(count < 1 for count in counts)))
            or not all(map(math.isfinite, time + values))):
        raise ValueError('Invalid history entry samples.')
    return name, {'time': time, 'values': values, 'counts': counts, 'local': local, 'unit': unit}


def records(reader, read_item, limit):
    if not reader.flag():
        return {}
    entries = {}
    for _ in range(reader.count(limit)):
        reader.named_records += 1
        if reader.named_records > MAX_SERIES:
            raise ValueError('History hierarchy exceeds the probe limit.')
        reader.require()
        name = reader.string()
        if name in entries:
            raise ValueError('Duplicate history identity.')
        entries[name] = read_item()
    return entries


def read_history(data):
    if len(data) > MAX_TRAILER:
        raise ValueError('History trailer exceeds the probe limit.')
    reader = Reader(data)
    present = reader.integer()
    if present == -1:
        reader.end()
        return {'name': None, 'sets': {}}
    if present != 1:
        raise ValueError('Invalid PMX history flag.')
    reader.require()
    name = reader.string()
    series_count = 0
    sample_count = 0

    def component():
        nonlocal series_count, sample_count
        unit = reader.string(optional=True)
        entries = {}
        first_time = None
        if reader.flag():
            for _ in range(reader.count(MAX_SERIES - series_count)):
                key, series = entry(reader)
                if key in entries:
                    raise ValueError('Duplicate history series identity.')
                if first_time is None:
                    first_time = series['time']
                if not series['time']:
                    series['time'] = first_time.copy()
                if len(series['time']) != len(series['values']):
                    raise ValueError('History time cannot be restored from the first series.')
                series_count += 1
                sample_count += len(series['values'])
                if sample_count > MAX_SAMPLES:
                    raise ValueError('History sample count exceeds the probe limit.')
                entries[key] = series
        return {'unit': unit, 'entries': entries}

    def result_set():
        harmonic = reader.flag(wide=False)
        fields = records(reader, lambda: records(reader, component, 128), 128)
        return {'harmonic': harmonic, 'fields': fields, 'baseSet': reader.string(optional=True)}

    sets = records(reader, result_set, 128)
    reader.end()
    return {'name': name, 'sets': sets}


def inspect(pmx):
    framing = inspect_frames(pmx)
    if framing['header'] != 'PrePoMax v3.0.0':
        raise ValueError('Expected PMX 3.0.0 result histories.')
    size = framing['opaqueHistoryTrailerBytes']
    if size > MAX_TRAILER:
        raise ValueError('History trailer exceeds the probe limit.')
    with pmx.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != framing['inputSha256']:
            raise ValueError('PMX changed before history inspection.')
        stream.seek(-size, 2)
        data = stream.read(size)
    if hashlib.sha256(data).hexdigest() != framing['opaqueHistoryTrailerSha256']:
        raise ValueError('PMX history differs from the inspected frame.')
    return {'pmxSha256': framing['inputSha256'], **read_history(data)}


def compare(history, dat):
    expected = {}
    for series in dat['histories']:
        entry_name = str(series['Id'])
        if series['IntegrationPoint'] is not None:
            entry_name += f'_{series["IntegrationPoint"]}'
        key = (series['SetName'], series['FieldName'], series['ComponentName'], entry_name)
        if key in expected:
            raise ValueError('DAT histories require distinct series across the compared steps.')
        expected[key] = series

    raw = derived = samples = 0
    stress_references = {key[:2] + key[3:]: series for key, series in expected.items()
                         if key[1] == 'STRESSES' and key[2] == 'S11'}
    for set_name, group in history['sets'].items():
        if group['harmonic']:
            raise ValueError('Harmonic history comparison is outside the static boundary.')
        for field, components in group['fields'].items():
            for name, component in components.items():
                for entry_name, series in component['entries'].items():
                    key = (set_name, field, name, entry_name)
                    reference = expected.pop(key, None)
                    if reference is None and field == 'STRESSES' and name in DERIVED_STRESS:
                        source = stress_references.get((set_name, field, entry_name))
                        if (source is None or series['time'] != source['time']
                                or group['baseSet'] != source['BaseSetName']
                                or series['local'] != source['Local']):
                            raise ValueError('Derived stress history has no matching raw series.')
                        derived += 1
                        continue
                    if (reference is None or group['baseSet'] != reference['BaseSetName']
                            or series['time'] != reference['time']
                            or series['values'] != reference['values']
                            or series['local'] != reference['Local']
                            or series['unit'] != reference['Unit']
                            or component['unit'] is not None
                            or series['counts'] != [1] * len(series['values'])):
                        raise ValueError(f'PMX history differs from DAT at {key}.')
                    raw += 1
                    samples += len(series['values'])
    if expected or raw == 0:
        raise ValueError('DAT raw history coverage is incomplete.')
    return {'datSha256': dat['SourceSha256'], 'matchedRawSeries': raw, 'matchedSamples': samples,
            'decodedDerivedStressSeries': derived}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pmx', type=Path)
    parser.add_argument('--dat', type=Path)
    parser.add_argument('--results-inspector', type=Path)
    args = parser.parse_args()
    if bool(args.dat) != bool(args.results_inspector):
        parser.error('--dat and --results-inspector are required together')
    try:
        history = inspect(args.pmx)
        if args.dat:
            command = ['dotnet', str(args.results_inspector.resolve()), 'inspect-dat', str(args.dat)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise ValueError((result.stderr or result.stdout).strip())
            history['comparison'] = compare(history, json.loads(result.stdout))
        print(json.dumps(history, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError, zlib.error) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
