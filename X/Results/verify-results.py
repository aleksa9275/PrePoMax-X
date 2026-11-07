#!/usr/bin/env python3
"""Verify original-owned static FRD mesh/fields using pinned source and offline packages."""
import argparse,hashlib,json,platform,shutil,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
import results_layout as layout
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--upstream-revision',choices=['3.0.0-rc2','post-rc2-2026-10-17']);p.add_argument('--output',type=Path,required=True);p.add_argument('--expect-os');p.add_argument('--expect-architecture');a=p.parse_args()
 report={'success':False,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),'commands':[],'solverExecuted':False};temp=None
 def clean(text):return text.replace(str(ROOT),'<repository>').replace(temp or '<unused>','<temporary>')
 def run(command,expected=0):
  r=subprocess.run([str(c)for c in command],cwd=ROOT,capture_output=True,text=True,timeout=180)
  report['commands'].append({'arguments':[clean(str(c))for c in command],'exitCode':r.returncode,'stdout':clean(r.stdout),'stderr':clean(r.stderr)})
  if r.returncode!=expected:raise ValueError('Command failed; see retained logs')
  return r
 try:
  arch={'arm64':'Arm64','aarch64':'Arm64','x86_64':'X64','amd64':'X64'}.get(platform.machine().lower());host=platform.system()
  report['host']={'os':host,'architecture':arch}
  if(a.expect_os and host!=a.expect_os)or(a.expect_architecture and arch!=a.expect_architecture):raise ValueError('Unexpected native host')
  pin=layout.BASELINE
  if a.upstream_revision:pin=next(r['commit']for r in json.loads((ROOT/'X/Core/upstream-replays.json').read_text())['revisions']if r['name']==a.upstream_revision)
  report.update(upstreamRevision=a.upstream_revision or'current',sources=layout.verify(pin),repository={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT))})
  report['tools']={f.relative_to(HERE).as_posix():sha(f)for f in sorted(HERE.rglob('*'))if f.is_file()and not {'artifacts','bin','obj','__pycache__'}.intersection(f.relative_to(HERE).parts)}
  report['analysisTools']={n:sha(ROOT/'X/Analysis'/n)for n in ['analysis_layout.py','static_layout.py']}
  fixture=ROOT/'.project/reports/windows-reference/solver/uniaxial.frd';report['fixtureSha256']=sha(fixture)
  dat_fixture=fixture.with_suffix('.dat');report['datFixtureSha256']=sha(dat_fixture)
  with tempfile.TemporaryDirectory(prefix='prepomaxx-results-')as temp:
   work=Path(temp);source=work/'source'
   for row in report['sources']:
    name=row['path'];data=layout.original(pin,name)if row.get('upstreamVariant')else(ROOT/name).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'],name
    path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
   feed=work/'feed';feed.mkdir();pins=json.loads((ROOT/'X/Analysis/dependency-artifacts.json').read_text())['packages'];report['packageArchives']={}
   for name,version in layout.analysis_layout.PACKAGES.items():
    path=ROOT/'X/Analysis/artifacts/packages'/name.lower()/version/(name.lower()+'.'+version+'.nupkg');expected=next(r['packageSha256']for r in pins if r['id'].lower()==name.lower());assert sha(path)==expected;shutil.copyfile(path,feed/path.name);report['packageArchives'][name]=expected
   run(['dotnet','build',HERE/'PrePoMaxX.Results.slnx','-c','Release','--disable-build-servers','-m:1','--artifacts-path',work/'build','-p:RepositoryRoot='+str(source)+'/','-p:RestorePackagesPath='+str(work/'packages'),'--source',feed,'-v:minimal'])
   report['tests']=json.loads(run(['dotnet',work/'build/bin/Tests/release/PrePoMaxX.ResultsTests.dll']).stdout)
   if not report['tests']['success']or report['tests']['passed']!=84 or report['tests']['runtime']['architecture']!=arch:raise ValueError('Native results checks failed/incomplete')
   cli=work/'build/bin/Inspect/release/PrePoMaxX.InspectResults.dll'
   report['inspection']=json.loads(run(['dotnet',cli,'inspect-frd',fixture]).stdout)
   value=report['inspection']
   if not value['success']or value['SourceSha256']!=report['fixtureSha256']or len(value['nodes'])!=8 or len(value['elements'])!=1 or len(value['fields'])!=4 or value['solverExecuted']:raise ValueError('Inspection output differs')
   report['datInspection']=json.loads(run(['dotnet',cli,'inspect-dat',dat_fixture]).stdout)
   dat=report['datInspection']
   if not dat['success']or dat['SourceSha256']!=report['datFixtureSha256']or dat['DataSetCount']!=3 or len(dat['histories'])!=96 or dat['completionEstablished']or dat['solverExecuted']:raise ValueError('DAT inspection differs')
   report['cliControls']=[]
   for name,args,code in [('usage',[],2),('unknown command',['read',fixture],2),('missing file',['inspect-frd',work/'missing.frd'],1),('truncated',['inspect-frd',work/'truncated.frd'],1),('empty',['inspect-frd',work/'empty.frd'],1),('missing DAT',['inspect-dat',work/'missing.dat'],1),('malformed DAT',['inspect-dat',work/'bad.dat'],1),('empty DAT',['inspect-dat',work/'empty.dat'],1),('unsupported DAT',['inspect-dat',work/'unsupported.dat'],1)]:
    (work/'bad.dat').write_text('S T E P 1\n\nINCREMENT 1\n\ndisplacements (vx,vy,vz) for set NALL and time 1\n\n1 2 3\n');(work/'empty.dat').write_bytes(b'');(work/'unsupported.dat').write_text('unsupported result\n')
    (work/'truncated.frd').write_text('    1C\n');(work/'empty.frd').write_bytes(b'')
    done=run(['dotnet',cli]+args,code)
    if done.stdout:raise ValueError('Rejected CLI wrote successful output')
    if code==1 and(json.loads(done.stderr)['success']or json.loads(done.stderr)['solverExecuted']):raise ValueError('Rejected inspection marked success')
    report['cliControls'].append(name)
   report['success']=True
 except Exception as e:report['error']=clean(str(e))
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'success':report['success'],'upstreamRevision':a.upstream_revision or'current','error':report.get('error')}));return 0 if report['success']else 1
if __name__=='__main__':raise SystemExit(main())
