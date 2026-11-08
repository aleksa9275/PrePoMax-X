#!/usr/bin/env python3
"""Compile original C# projects as net48/C#7.3 using retained Windows DLL metadata.

Compile-only: no DLL is executed, no installed app is modified. This supplements
native Windows build/runtime acceptance. Reference metadata is supplied explicitly.
"""
import argparse,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape
root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference-directory',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
lib=args.reference_directory.resolve()
if not (lib/'Kitware.VTK.dll').is_file():parser.error('Original application lib directory is required')
names=['CaeGlobals','ThreeMF','vtkControl','CaeMesh','CaeResults','CaeModel','CaeJob','UserControls','APIs','PrePoMax','GmshCaller']
paths={'ThreeMF':'3MF/ThreeMF.csproj'}
results=[]
for name in names:
 original=root/paths.get(name,f'{name}/{name}.csproj');j=ET.parse(original).getroot();folder=out/name;folder.mkdir(exist_ok=True)
 code=[(original.parent/e.get('Include').replace('\\','/')).resolve() for e in j.iter() if e.tag.endswith('}Compile') and e.get('Include')]
 props='<TargetFramework>net48</TargetFramework><LangVersion>7.3</LangVersion><GenerateAssemblyInfo>false</GenerateAssemblyInfo><EnableDefaultCompileItems>false</EnableDefaultCompileItems><AllowUnsafeBlocks>true</AllowUnsafeBlocks><GenerateResourceUsePreserializedResources>true</GenerateResourceUsePreserializedResources><AssemblyName>'+name+'</AssemblyName>'
 lines=['<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'+props+'</PropertyGroup><ItemGroup>']
 lines += [f'<Compile Include="{escape(str(p))}" />' for p in code]
 lines += ['<PackageReference Include="Microsoft.NETFramework.ReferenceAssemblies" Version="[1.0.3]" />']
 for package in ['WindowsBase','System.Windows.Forms','System.Design','System.Drawing.Design','System.Management','System.Numerics','System.Runtime.Serialization','Microsoft.CSharp','System.Drawing','System.IO.Compression','System.IO.Compression.FileSystem','System.Web','System.ServiceModel','System.Runtime.Remoting','System.Net.Http']:
  lines += [f'<Reference Include="{package}" />']
 for dll in lib.glob('*.dll'):
  if dll.stem==name or dll.stem.startswith(('vtk','Kitware.VTK.')):continue
  candidate=out/dll.stem/'bin/Debug/net48'/dll.name
  if candidate.exists():dll=candidate
  lines += [f'<Reference Include="{dll.stem}"><HintPath>{escape(str(dll))}</HintPath><Private>false</Private></Reference>']
 for assembly in ['vtkControl','Kitware.VTK']:
  if assembly==name:continue
  dll=out/assembly/'bin/Debug/net48'/f'{assembly}.dll'
  if not dll.exists():dll=lib/f'{assembly}.dll'
  lines += [f'<Reference Include="{assembly}"><HintPath>{escape(str(dll))}</HintPath><Private>false</Private></Reference>']
 # Two original source dependencies are newer than the retained application package.
 if name=='CaeResults':lines += ['<PackageReference Include="OptimizedPriorityQueue" Version="[5.1.0]" />']
 if name=='CaeGlobals':
  for package,version in [('ExtendedNumerics.BigDecimal','2025.1001.2.129'),('Parlot','0.0.28')]:lines += [f'<PackageReference Include="{package}" Version="[{version}]" />']
 lines+=['</ItemGroup></Project>'];project=folder/f'{name}.csproj';project.write_text('\n'.join(lines))
 result=subprocess.run(['dotnet','build',str(project),'--disable-build-servers','-m:1','-p:UseSharedCompilation=false','-v:q'],capture_output=True,text=True)
 (folder/'build.log').write_text(result.stdout+result.stderr)
 errors=sorted(set(x.split(' [')[0] for x in result.stdout.splitlines() if ': error ' in x))
 results.append({'assembly':name,'passed':result.returncode==0,'errors':errors});print(name,result.returncode,*errors,sep='\n',flush=True)
(out/'result.json').write_text(json.dumps(results,indent=2)+'\n')

raise SystemExit(0 if all(r["passed"] for r in results) else 1)
