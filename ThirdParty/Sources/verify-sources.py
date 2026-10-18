#!/usr/bin/env python3
"""Verify recovered third-party source bytes; no downloads or build side effects."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def verify():
 lock=json.loads((HERE/'source-lock.json').read_text());result=[]
 for component in lock['components']:
  path=HERE/component['manifest'];data=path.read_bytes()
  if hashlib.sha256(data).hexdigest()!=component['manifestSha256']:raise ValueError('Source manifest changed: '+str(path))
  manifest=json.loads(data);seen=set();total=0
  for row in manifest['files']:
   relative=Path(row['path'])
   if relative.is_absolute()or'..'in relative.parts or row['path']in seen:raise ValueError('Unsafe or duplicate source path')
   seen.add(row['path']);file=path.parent/relative
   if file.is_symlink()or not file.is_file():raise ValueError('Source must be a regular file: '+str(file))
   data=file.read_bytes()
   if len(data)!=row['bytes']or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Source bytes changed: '+str(file))
   total+=len(data)
  actual={p.relative_to(path.parent).as_posix()for p in (path.parent/'src').rglob('*')if p.is_file()}
  if actual!=seen:raise ValueError('Unexpected source additions/removals')
  result.append({'component':manifest['component'],'version':manifest['version'],'files':len(seen),'bytes':total,'archiveSha256':manifest['archiveSha256'],'releaseReady':manifest['releaseReady']})
 return result
if __name__=='__main__':print(json.dumps({'success':True,'components':verify()},indent=2))
