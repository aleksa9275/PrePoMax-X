#!/usr/bin/env python3
"""Removes the build machine's absolute RUNPATH/RPATH entries from the ELF files below the given folders (Linux
packages, run in the build container: patchelf). Relative entries ($ORIGIN...) stay; a file without an absolute
entry is not touched (fingerprinted third-party files are not passed at all). Prints each change.

  python3 X/Build/Linux/strip_rpaths.py <folder> [<folder> ...]
"""
import subprocess
import sys
from pathlib import Path


def runpath(path):
    out = subprocess.run(['patchelf', '--print-rpath', str(path)], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def main():
    changed = 0
    for path in sorted(p for folder in sys.argv[1:] for p in Path(folder).rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        with open(path, 'rb') as f:
            if f.read(4) != b'\x7fELF':
                continue
        current = runpath(path)
        if not current:
            continue
        entries = current.split(':')
        if not any(p.startswith('/') for p in entries):
            continue
        kept = [p for p in entries if p and not p.startswith('/')]
        subprocess.run(['patchelf', '--set-rpath', ':'.join(kept), str(path)], check=True)
        print(f'{path}: {current} -> {":".join(kept)}')
        changed += 1
    print(f'{changed} files changed')


if __name__ == '__main__':
    main()
