#!/usr/bin/env python3
"""Offline read-only comparison of official solver and PrePoMax release ZIPs."""
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
def pe(data):
 offset=struct.unpack_from('<I',data,0x3c)[0]
 if data[offset:offset+4]!=b'PE\0\0':raise ValueError('Not a PE binary')
 machine,sections,stamp,_,_,opt_size,_=struct.unpack_from('<HHIIIHH',data,offset+4);optional=offset+24
 magic=struct.unpack_from('<H',data,optional)[0]
 if magic!=0x20b:raise ValueError('Expected PE32+ executable')
 directory=optional+112;section_table=optional+opt_size
 entries=[]
 for i in range(sections):
  o=section_table+40*i;virtual_size,virtual_address,raw_size,raw_offset=struct.unpack_from('<IIII',data,o+8);entries.append((virtual_address,max(virtual_size,raw_size),raw_offset))
 def at(rva):
  for address,size,raw in entries:
   if address<=rva<address+size:return raw+rva-address
  raise ValueError('PE RVA not mapped')
 import_rva,_=struct.unpack_from('<II',data,directory+8);imports=[]
 if import_rva:
  o=at(import_rva)
  while any(data[o:o+20]):
   name_rva=struct.unpack_from('<I',data,o+12)[0];n=at(name_rva);imports.append(data[n:data.index(b'\0',n)].decode());o+=20
 versions=[];marker=b'\xbd\x04\xef\xfe';i=0
 while (i:=data.find(marker,i))>=0:
  if len(data)>=i+52 and struct.unpack_from('<I',data,i+4)[0]==0x10000:
   a,b=struct.unpack_from('<II',data,i+8);versions.append([a>>16,a&65535,b>>16,b&65535])
  i+=4
 return{'machineHex':hex(machine),'architecture':'x64'if machine==0x8664 else'unknown','imports':imports,'fileVersionResources':versions}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--official-zip',type=Path,required=True);p.add_argument('--prepomax-zip',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
 expected=json.loads((ROOT/'X/Execution/solver-builds.json').read_text())['builds'][0]['files'];report={'success':False,'toolSha256':sha(Path(__file__).read_bytes()),'archives':{},'comparisons':{}}
 for key,file in [('official',a.official_zip),('prepomaxRC2',a.prepomax_zip)]:
  row={'bytes':file.stat().st_size,'sha256':sha(file.read_bytes()),'solverMembers':[]}
  with zipfile.ZipFile(file)as z:
   for entry in z.infolist():
    basename=Path(entry.filename).name
    if entry.is_dir()or not(basename in expected or basename in ['README_Install','http.txt']):continue
    if key=='prepomaxRC2'and'/solver/'not in entry.filename.lower():continue
    data=z.read(entry);member={'path':entry.filename,'bytes':len(data),'sha256':sha(data),'crc32':hex(entry.CRC)}
    if basename.lower().endswith(('.exe','.dll')):member['pe']=pe(data)
    else:(a.output_dir/(key+'-'+basename+'.txt')).write_bytes(data)
    row['solverMembers'].append(member)
    if basename=='ccx_dynamic.exe':
     strings=[s.decode('ascii')for s in re.findall(rb'[ -~]{8,}',data)]
     patterns={'hwloc':'hwloc-2.11.1','arpack':'arpack-ng-3.9.1','gfortran':'gcc-14.1.0/libgfortran','openblas':'OpenBLAS','scotch':'SCOTCH_','spoolesMT':'FrontMtx_MT_factorInpMtx','eigensolver':'dsaupd_','pastix':'PASTIX_','MKL':'mkl_rt.2.dll'}
     member['markers']={name:next((s for s in strings if value in s),None)for name,value in patterns.items()}
     member['compilerStrings']=list(dict.fromkeys(s for s in strings if s.startswith('GCC:')))
     member['defaultBackendBannerReference']='PaStiX 6.0.1 observed in retained execution; symbol strings alone do not establish every build flag/revision'
  report['archives'][key]=row
 official={Path(r['path']).name:r for r in report['archives']['official']['solverMembers']};rc2={Path(r['path']).name:r for r in report['archives']['prepomaxRC2']['solverMembers']}
 report['comparisons']['executableMatchesOfficial']=rc2['ccx_dynamic.exe']['sha256']==official['ccx_dynamic.exe']['sha256']
 report['comparisons']['allSixExecutableRuntimeFilesMatchRecordedNativeWindows']={name:rc2[name]['sha256']==checksum for name,checksum in expected.items()}
 report['comparisons']['bundledInstallReadmeMatchesOfficial']=rc2['README_Install']['sha256']==official['README_Install']['sha256']
 report['success']=report['comparisons']['executableMatchesOfficial']and all(report['comparisons']['allSixExecutableRuntimeFilesMatchRecordedNativeWindows'].values())and report['comparisons']['bundledInstallReadmeMatchesOfficial']
 report['limits']=['Byte identity establishes distributed Windows program/runtime identity, not native ARM availability','No source patch set, PaStiX/Scotch commit, all ABI flags or full cross-platform numerical equivalence inferred from strings','No binary executed by this inspector']
 (a.output_dir/'archive-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['comparisons'],indent=2));return 0 if report['success']else 1
if __name__=='__main__':raise SystemExit(main())
