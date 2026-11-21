#!/usr/bin/env python3
"""Compares two bounds dumps (Dump.cs): the original's and X/App's, form by form and control by control.

Usage: compare.py <original.json> <x.json> [--output report.json] [--markdown report.md]
A control matches when its path (names under the form) is on both sides; its bounds differ when any of x, y, width,
height differs by more than --tolerance pixels (default 0). The report lists every difference; it judges nothing.
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def load(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    return data['platform'], {form['type']: form for form in data['forms']}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('original')
    p.add_argument('x')
    p.add_argument('--tolerance', type=int, default=0)
    p.add_argument('--output', type=Path)
    p.add_argument('--markdown', type=Path)
    a = p.parse_args()
    original_platform, original = load(a.original)
    x_platform, x = load(a.x)
    report = {'original': original_platform, 'x': x_platform, 'tolerance': a.tolerance,
              'onlyOriginal': sorted(set(original) - set(x)), 'onlyX': sorted(set(x) - set(original)),
              'notConstructed': {}, 'forms': {}}
    totals = Counter()
    for name in sorted(set(original) & set(x)):
        o, n = original[name], x[name]
        if 'error' in o or 'error' in n:
            report['notConstructed'][name] = {'original': o.get('error'), 'x': n.get('error')}
            totals['notConstructed'] += 1
            continue
        oc = {c['path']: c for c in o['controls']}
        xc = {c['path']: c for c in n['controls']}
        differences = []
        for path in sorted(set(oc) & set(xc)):
            ob, xb = oc[path]['bounds'], xc[path]['bounds']
            if any(abs(i - j) > a.tolerance for i, j in zip(ob, xb)):
                differences.append({'path': path, 'type': oc[path]['type'], 'original': ob, 'x': xb})
        entry = {'controls': len(oc), 'matched': len(set(oc) & set(xc)), 'different': len(differences),
                 'client': {'original': o['client'], 'x': n['client']}, 'autoScale': {'original': o['autoScale'], 'x': n['autoScale']},
                 'onlyOriginal': sorted(set(oc) - set(xc)), 'onlyX': sorted(set(xc) - set(oc)), 'differences': differences}
        report['forms'][name] = entry
        totals['forms'] += 1
        totals['controls'] += entry['matched']
        totals['different'] += entry['different']
        totals['formsIdentical'] += 1 if not differences and o['client'] == n['client'] and not entry['onlyOriginal'] and not entry['onlyX'] else 0
        totals['clientDifferent'] += 0 if o['client'] == n['client'] else 1
    report['totals'] = dict(totals)
    if a.output: a.output.write_text(json.dumps(report, indent=1) + '\n')
    if a.markdown:
        lines = [f"# Bounds comparison", "", f"- Original: {original_platform}", f"- X: {x_platform}",
                 f"- Tolerance: {a.tolerance} px", f"- Totals: {dict(totals)}", "",
                 "| Form | Controls | Different | Client (original / X) |", "|---|---|---|---|"]
        for name, e in report['forms'].items():
            lines.append(f"| {name.split('.')[-1]} | {e['matched']} | {e['different']} | {e['client']['original']} / {e['client']['x']} |")
        a.markdown.write_text('\n'.join(lines) + '\n')
    print(json.dumps(report['totals']), 'onlyOriginal', report['onlyOriginal'], 'onlyX', report['onlyX'])


if __name__ == '__main__':
    main()
