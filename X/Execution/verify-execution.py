#!/usr/bin/env python3
"""Verify native job transport and original monitor readers; no solver substitution."""
import argparse,hashlib,json,platform,shutil,subprocess,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
import definition_control
import cli_control
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--upstream-revision',choices=['3.0.0-rc2','post-rc2-2026-10-17']);p.add_argument('--output',required=True,type=Path);p.add_argument('--expect-os',choices=['Darwin','Linux','Windows']);p.add_argument('--expect-architecture',choices=['Arm64','X64']);a=p.parse_args()
 report={'success':False,'host':{'os':platform.system(),'architecture':platform.machine()},'recordedAtUtc':datetime.now(timezone.utc).isoformat(),'commands':[],'solverExecuted':False};temp=None
 def clean(value):return value.replace(str(ROOT),'<repository>').replace(temp or '<unused>','<temporary>')
 def run(command,expected=0):
  d=subprocess.run([str(x)for x in command],cwd=ROOT,text=True,capture_output=True,timeout=180)
  report['commands'].append({'arguments':[clean(str(x))for x in command],'exitCode':d.returncode,'stdout':clean(d.stdout),'stderr':clean(d.stderr)})
  if d.returncode!=expected:raise ValueError('Command failed; see retained logs')
  return d
 try:
  arch={'arm64':'Arm64','aarch64':'Arm64','x86_64':'X64','amd64':'X64'}.get(platform.machine().lower())
  if (a.expect_os and a.expect_os!=platform.system())or(a.expect_architecture and a.expect_architecture!=arch):raise ValueError('Unexpected native verification host')
  if a.upstream_revision:raise ValueError('Historical upstream slice replays were retired with the whole-library build (D062)')
  chk=subprocess.run([sys.executable,str(ROOT/'X/Domain/domain_sources.py'),'--check'],cwd=ROOT,capture_output=True,text=True)
  if chk.returncode:raise ValueError('Whole-library source lists are stale: '+chk.stdout.strip())
  report.update(upstreamRevision='current',sources={'mode':'whole original assemblies (X/Domain)','manifestSha256':sha(ROOT/'X/Domain/domain-sources.json')},repository={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT))})
  report['tools']={p.relative_to(HERE).as_posix():sha(p)for p in sorted(HERE.rglob('*'))if p.is_file()and not {'artifacts','bin','obj','__pycache__'}.intersection(p.relative_to(HERE).parts)}
  report['analysisTools']={p.relative_to(ROOT/'X/Analysis').as_posix():sha(p)for p in sorted((ROOT/'X/Analysis').rglob('*'))if p.is_file()and not {'artifacts','bin','obj','__pycache__'}.intersection(p.relative_to(ROOT/'X/Analysis').parts)}
  report['monitorFixtures']={str(p.relative_to(ROOT)):sha(p)for p in (ROOT/'.project/reports/windows-reference/solver').iterdir()if p.suffix in {'.sta','.cvg'}}
  report['thirdPartySources']=json.loads(run(['python3',ROOT/'ThirdParty/Sources/verify-sources.py']).stdout)
  with tempfile.TemporaryDirectory(prefix='prepomaxx-execution-')as temp:
   work=Path(temp)
   run(['dotnet','build',HERE/'PrePoMaxX.Execution.slnx','-c','Release','--disable-build-servers','-m:1','--artifacts-path',work/'build','-v:minimal'])
   report['tests']=json.loads(run(['dotnet',work/'build/bin/Tests/release/PrePoMaxX.ExecutionTests.dll']).stdout)
   if not report['tests']['success']or report['tests']['passed']!=49 or report['tests']['runtime']['architecture']!=arch:raise ValueError('Native transport/monitor/thread-plan checks incomplete or failed')
   cli=work/'build/bin/Solve/release/PrePoMaxX.Solve.dll'
   report['desktopDefinitionControl']=definition_control.verify(run,cli,ROOT,work)
   report['threadPlanning']={}
   for label,arguments in [('automatic',[]),('manual',['--threads','1','--jobs','1'])]:
    value=json.loads(run(['dotnet',cli,'thread-plan']+arguments).stdout);plan=value['plan'];available=plan['AvailableLogicalProcessors'];budget=plan['TotalThreadBudget']
    if not value['success']or any(value[k]for k in ['solverExecuted','settingsChanged','reservationEnforced','cpuUtilizationLimit']):raise ValueError('Thread planner changed execution state')
    if available<1 or budget!=(max(1,available*3//4)if label=='automatic'else 1)or plan['ThreadsPerJob']!=[budget]or plan['IsAutomatic']!=(label=='automatic'):raise ValueError('Host thread recommendation differs')
    report['threadPlanning'][label]=value
   report['availability']=json.loads(run(['dotnet',cli,'availability']).stdout)
   report['monitor']=json.loads(run(['dotnet',cli,'inspect-monitor',ROOT/'.project/reports/windows-reference/solver/uniaxial.sta',ROOT/'.project/reports/windows-reference/solver/uniaxial.cvg']).stdout)
   if report['monitor']['status']['Count']!=1 or report['monitor']['status']['TotalTimes']!=[1]or report['monitor']['convergence']['Count']!=0:raise ValueError('Recorded original monitor result differs')
   report['desktopPipeControl']=cli_control.verify(['dotnet',cli],ROOT,work,arch)
   report['cliControls']=[]
   controls=[('usage',['dotnet',cli],2),('unknown build',['dotnet',cli,'run-static','unknown',work,work/'mesh',work/'definition',work/'should-not-exist','30'],1),('unavailable or missing pinned build',['dotnet',cli,'run-static','windows-reference-2.22',work,work/'mesh',work/'definition',work/'should-not-exist','30'],1),('missing monitor',['dotnet',cli,'inspect-monitor',work/'missing.sta',work/'missing.cvg'],1)]
   for name,arguments in [('unknown option',['--unknown','1']),('missing value',['--threads']),('duplicate option',['--threads','auto','--threads','1']),('zero threads',['--threads','0']),('signed count',['--threads','+1']),('overflow count',['--threads','2147483648']),('excess concurrency',['--jobs','1025']),('zero jobs',['--jobs','0']),('overcommitted manual budget',['--threads','1','--jobs','2'])]:
    controls.append(('thread plan '+name,['dotnet',cli,'thread-plan']+arguments,1))
   for name,command,code in controls:
    done=run(command,code)
    if done.stdout or(work/'should-not-exist').exists():raise ValueError('Rejected CLI wrote output')
    if code==1 and json.loads(done.stderr)['solverExecuted']:raise ValueError('Rejected CLI ran a solver')
    report['cliControls'].append(name)
   report['success']=True
 except Exception as e:report['error']=clean(str(e))
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report.get(k)for k in ['success','upstreamRevision','error']}));return 0 if report['success']else 1
if __name__=='__main__':raise SystemExit(main())
