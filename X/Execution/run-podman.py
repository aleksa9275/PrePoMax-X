#!/usr/bin/env python3
"""Run native process/monitor checks in a cached native ARM64 image, offline/read-only."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--image', default='localhost/prepomaxx-research:linux-arm64')
    args = parser.parse_args()
    info = json.loads(subprocess.check_output(['podman','info','--format','json']))
    image = json.loads(subprocess.check_output(['podman','image','inspect',args.image]))[0]
    if info['host']['arch'] != 'arm64' or image['Architecture'] != 'arm64' or image['Os'] != 'linux':
        raise ValueError('Native Linux ARM64 server/image required')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    container = {'engine':'podman','serverArchitecture':info['host']['arch'],'serverVersion':info['version']['Version'],
        'imageId':image['Id'],'imageDigest':image.get('Digest'),'network':'none','repositoryMount':'read-only','initReaper':True,
        'execution':'native Linux ARM64 container in macOS VM; not native x64 acceptance',
        'recordedAtUtc':datetime.now(timezone.utc).isoformat()}
    reports=[]
    for label, revision in [('current',None),('rc2','3.0.0-rc2'),('post-rc2','post-rc2-2026-10-17')]:
        command=['python3','X/Execution/verify-execution.py','--expect-os','Linux','--expect-architecture','Arm64','--output','/tmp/analysis.json']
        if revision:command+=['--upstream-revision',revision]
        program='import pathlib,subprocess,sys; code=subprocess.run('+repr(command)+',stdout=sys.stderr).returncode; sys.stdout.write(pathlib.Path("/tmp/analysis.json").read_text()); sys.exit(code)'
        run=['podman','run','--rm','--init','--pull=never','--platform','linux/arm64','--network=none','--read-only','--tmpfs','/tmp:rw,size=2g',
            '--mount','type=bind,source='+str(ROOT)+',destination=/workspace,ro=true','--entrypoint','python3',image['Id'],'-c',program]
        done=subprocess.run(run,cwd=ROOT,text=True,capture_output=True,timeout=240)
        if not done.stdout:
            raise RuntimeError('Container produced no report: '+done.stderr)
        report=json.loads(done.stdout);report['container']=container
        (args.output_dir/(label+'-linux-arm64.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'mode':label,'success':report['success'],'tests':report.get('tests',{}).get('passed'),'error':report.get('error')}),flush=True)
        if done.returncode or not report['success']:return 1
        reports.append(report)
    return 0


if __name__=='__main__': raise SystemExit(main())
