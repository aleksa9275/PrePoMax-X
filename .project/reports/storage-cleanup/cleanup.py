#!/usr/bin/env python3
"""Audit/replay this task's explicit task0041–0044 generated-payload cleanup.

This is a bounded maintenance record, not an automatic/general cache cleaner.
Plan is read-only. Apply refuses changed trees, tracked files, symlinked roots,
active payloads or mounted images. Small sibling provenance/job records survive.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ROOTS = ('X/Build/artifacts', 'X/Desktop/artifacts')
GENERATED = {'dist', 'dmg-payload', 'pyinstaller-cache', 'build', 'hosts'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True)


def qualified(parent):
    base = parent.parent.relative_to(ROOT).as_posix()
    if base == ROOTS[0]:
        return parent.name.startswith(tuple(f'task00{n}-' for n in (41, 42, 43, 44)))
    return base == ROOTS[1] and parent.name.startswith('package-macos-arm64')


def permitted(path):
    rel = path.relative_to(ROOT).as_posix()
    if not qualified(path.parent):
        raise ValueError('Outside the named historical output scope: ' + rel)
    if path.name not in GENERATED | {'Installed copy'}:
        raise ValueError('Not an approved generated child: ' + rel)
    marker = 'verification.json' if path.name == 'Installed copy' else None
    if marker:
        if not (path.parent / marker).is_file():
            raise ValueError('Missing verification provenance: ' + rel)
    elif not any((path.parent / name).is_file() for name in ('package.json', 'build.json')):
        raise ValueError('Missing build provenance: ' + rel)
    for ancestor in (path, *path.parents):
        if ancestor == ROOT:
            break
        if ancestor.is_symlink():
            raise ValueError('Symlinked cleanup root: ' + rel)
    if not path.is_dir():
        raise ValueError('Not a generated directory: ' + rel)
    if subprocess.run(['git', 'check-ignore', '--quiet', '--', rel], cwd=ROOT).returncode:
        raise ValueError('Not ignored by Git: ' + rel)
    tracked = git('ls-files', '-z', '--', rel).split('\0')
    if any(tracked):
        raise ValueError('Contains tracked files: ' + rel)
    return rel


def usage(path):
    digest = hashlib.sha256()
    allocated = logical = files = links = 0
    seen = set()
    stack = [path]
    while stack:
        item = stack.pop()
        info = item.lstat()
        rel = item.relative_to(path).as_posix()
        digest.update(json.dumps([rel, info.st_mode, info.st_size, info.st_mtime_ns,
                                  info.st_dev, info.st_ino], separators=(',', ':')).encode())
        if stat.S_ISLNK(info.st_mode):
            links += 1
            digest.update(os.readlink(item).encode())
        elif stat.S_ISDIR(info.st_mode):
            stack.extend(sorted(item.iterdir(), reverse=True))
        else:
            files += 1
            logical += info.st_size
        identity = (info.st_dev, info.st_ino)
        if identity not in seen:
            allocated += info.st_blocks * 512
            seen.add(identity)
    return {'allocatedBytes': allocated, 'logicalBytes': logical, 'regularFiles': files,
            'symlinks': links, 'treeStampSha256': digest.hexdigest()}


def protected():
    # Read process command lines only to protect this project's generated trees;
    # never retain unrelated process text or change application/system state.
    processes = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True).splitlines()
    mounted = plistlib.loads(subprocess.check_output(['hdiutil', 'info', '-plist']))
    images, mounts = [], []
    for entry in mounted.get('images', []):
        if entry.get('image-path'):
            images.append(entry['image-path'])
        mounts.extend(entity['mount-point'] for entity in entry.get('system-entities', []) if entity.get('mount-point'))
    return processes, images, mounts


def protection_reason(path, state):
    prefix = str(path) + '/'
    processes, images, mounts = state
    if any(prefix in command for command in processes):
        return 'An active process references this payload'
    if any(str(image).startswith(prefix) for image in images):
        return 'A disk image in this payload is mounted'
    if any(str(mount).startswith(prefix) for mount in mounts):
        return 'A mounted filesystem is inside this payload'
    return None


def available():
    value = os.statvfs(ROOT)
    return value.f_bavail * value.f_frsize


def plan():
    if (HERE / 'execution.json').exists():
        raise ValueError('Completed cleanup record exists; preserve its plan and use a new task for further cleanup')
    state = protected()
    rows, skips = [], []
    for base in ROOTS:
        for parent in sorted((ROOT / base).iterdir()):
            if not parent.is_dir() or parent.is_symlink() or not qualified(parent):
                continue
            for name in sorted(GENERATED | {'Installed copy'}):
                path = parent / name
                if not path.exists():
                    continue
                try:
                    rel = permitted(path)
                except ValueError as error:
                    skips.append({'path': path.relative_to(ROOT).as_posix(), 'reason': str(error)})
                    continue
                reason = protection_reason(path, state)
                if reason:
                    skips.append({'path': rel, 'reason': reason})
                    continue
                rows.append({'path': rel, **usage(path)})
    result = {'recordedAtUtc': datetime.now(timezone.utc).isoformat(), 'root': str(ROOT),
        'gitHead': git('rev-parse', 'HEAD').strip(), 'filesystemAvailableBeforeBytes': available(),
        'scope': 'Ignored task0041–0044 generated payloads only; preserve parent metadata, reports, jobs, source and build inputs',
        'entries': rows, 'skipped': skips,
        'allocatedBytesEstimate': sum(row['allocatedBytes'] for row in rows),
        'note': 'Allocated-byte sum can overcount APFS shared extents; actual free-space change is measured separately'}
    (HERE / 'plan.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'candidates': len(rows), 'estimatedGiB': result['allocatedBytesEstimate'] / 2**30,
                      'skipped': skips}))


def apply():
    value = json.loads((HERE / 'plan.json').read_text())
    if value['root'] != str(ROOT):
        raise ValueError('Plan belongs to a different checkout')
    if (HERE / 'execution.json').exists():
        raise ValueError('This reviewed cleanup already has a receipt; do not replay it blindly')
    state = protected()
    # Complete all guards before the first deletion. File timestamps/inodes also
    # detect newly generated/changed content after the inventory was prepared.
    for row in value['entries']:
        path = ROOT / row['path']
        permitted(path)
        reason = protection_reason(path, state)
        if reason:
            raise ValueError(row['path'] + ': ' + reason)
        if usage(path) != {key: row[key] for key in ('allocatedBytes', 'logicalBytes', 'regularFiles', 'symlinks', 'treeStampSha256')}:
            raise ValueError('Payload changed since planning: ' + row['path'])
    receipt = {'startedAtUtc': datetime.now(timezone.utc).isoformat(),
        'planSha256': hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest(),
        'filesystemAvailableBeforeBytes': available(), 'removed': [], 'success': False}
    try:
        for row in value['entries']:
            shutil.rmtree(ROOT / row['path'])
            receipt['removed'].append(row['path'])
        receipt['success'] = True
    except OSError as error:
        receipt['error'] = str(error)
        raise
    finally:
        receipt['filesystemAvailableAfterBytes'] = available()
        receipt['observedFreeSpaceIncreaseBytes'] = receipt['filesystemAvailableAfterBytes'] - receipt['filesystemAvailableBeforeBytes']
        receipt['finishedAtUtc'] = datetime.now(timezone.utc).isoformat()
        (HERE / 'execution.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'success': receipt['success'], 'removedDirectories': len(receipt['removed']),
                          'observedFreeSpaceIncreaseGiB': receipt['observedFreeSpaceIncreaseBytes'] / 2**30}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'apply'))
    args = parser.parse_args()
    plan() if args.action == 'plan' else apply()
