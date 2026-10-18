"""Mechanical job/enum extraction; original net48 transport remains intact."""
from pathlib import Path
import hashlib, subprocess, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
BASELINE='de8f73032a72746e3d6d9afd53d9fbd289eb310a'

def original(revision,path):return subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT).decode('utf-8')
def render(revision=BASELINE):
 path='CaeJob/ExecutableJob.cs';text=original(revision,path);legacy=[]
 for start,end in [('        private void Run()','        private void _exe_ErrorDataReceived('),('        public void Kill(string message)','        private void AddDataToOutput(')]:
  a=text.index(start);b=text.index(end,a);legacy.append(text[a:b]);text=text[:a]+text[b:]
 text=text.replace('public class ExecutableJob','public partial class ExecutableJob',1).replace('using System.Management;\n','').replace('using System.ComponentModel;\n','')
 header=original(revision,path).split('namespace CaeJob')[0]
 result={path:text,'CaeJob/ExecutableJob.Legacy.cs':header+'namespace CaeJob\n{\n    public partial class ExecutableJob\n    {\n'+''.join(legacy)+'    }\n}\n'}
 path='CaeJob/AnalysisJob.cs';text=original(revision,path);a=text.index('    [Serializable]\n    public enum JobStatus');b=text.index('    //\n',a);enum=text[a:b]
 result[path]=text[:a]+text[b:]
 header=text[:text.index('using System;')]+'using System;\n\n'
 result['CaeJob/JobStatus.cs']=header+'namespace CaeJob\n{\n'+enum+'}\n'
 return {p:s.encode('utf-8')for p,s in result.items()}

def verify(revision=BASELINE):
 expected=render();assert render(revision)==expected,'Unreviewed upstream job boundary change'
 for name,data in expected.items():
  if (ROOT/name).read_bytes()!=data:raise ValueError('Job extraction changed: '+name)
 ns={'m':'http://schemas.microsoft.com/developer/msbuild/2003'}
 items=[c.attrib['Include'].replace('\\','/')for c in ET.parse(ROOT/'CaeJob/CaeJob.csproj').findall('.//m:Compile',ns)]
 for name in expected:
  if items.count(name.split('/',1)[1])!=1:raise ValueError('Original net48 owner/inclusion changed: '+name)
 if 'ExecutableJob.Portable.cs'in items:raise ValueError('Modern platform implementation must not replace legacy net48 transport')
 monitor='CaeJob/CalculixMonitorData.cs'
 data=original(BASELINE,monitor).encode('utf-8')
 if original(revision,monitor).encode('utf-8')!=data or (ROOT/monitor).read_bytes()!=data:raise ValueError('Original monitor parser changed')
 if items.count('CalculixMonitorData.cs')!=1:raise ValueError('Monitor parser must retain original owner')
 expected[monitor]=data
 return [{'path':name,'sha256':hashlib.sha256(data).hexdigest()}for name,data in sorted(expected.items())]
