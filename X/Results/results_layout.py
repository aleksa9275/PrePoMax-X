"""Mechanically preserve original FRD/DAT decoding, history entries and net48 orchestration."""
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'X/Analysis'));import analysis_layout,static_layout
BASELINE=analysis_layout.BASELINE
FRD='CaeResults/FileInOut/Input/CalculiX/FrdFileReader.cs'
UNCHANGED=['CaeResults/FileInOut/Input/CalculiX/'+n+'.cs'for n in ['FrdStreamReader','FrdDataSet','FrdFeDescriptorId']]+['CaeResults/FieldOutput/'+n+'.cs'for n in ['FieldData','FieldComponent']]
ADAPTED={'CaeResults/FieldOutput/Field.cs':'using System.Diagnostics.Eventing.Reader;\n','CaeResults/FieldOutputNames.cs':'using Microsoft.SqlServer.Server;\n'}
def original(pin,path):return subprocess.check_output(['git','show',pin+':'+path],cwd=ROOT)
def render(pin=BASELINE):
 text=original(pin,FRD).decode();blocks=[]
 for start,end in [('        static public void ScaleAxisymmetricSegmentFields(', '        static public void ReadHeading('),('        static public FeResults Read(', '        static bool IsConstantWidth('),('        static private UnitSystem GetUnitSystem(', '        static private void GetMaterialIdsAndNames(')]:
  block,text=static_layout.span(text,start,end);blocks.append(block)
 text=text.replace('public static class FrdFileReader','public static partial class FrdFileReader',1)
 # Erased partial hooks leave the original net48 parser behavior intact.
 text=text.replace('                while ((line = reader.ReadLine()) != null)\n                {','                while ((line = reader.ReadLine()) != null)\n                {\n                    ValidatePortableHeader(line);',1)
 text=text.replace('            dataSet.Add(line);\n            //\n            int numOfStoredComponents', '            ValidatePortableComponents(numOfComponents);\n            dataSet.Add(line);\n            //\n            int numOfStoredComponents',1)
 text=text.replace('            return reader.ReadBytes(numOfValues * (sizeof(int) + numOfStoredComponents * GetBinaryValueSize(binaryFormat)));','            ValidatePortableAllocation((long)numOfValues * (sizeof(int) + numOfStoredComponents * GetBinaryValueSize(binaryFormat)));\n            return reader.ReadBytes(numOfValues * (sizeof(int) + numOfStoredComponents * GetBinaryValueSize(binaryFormat)));',1)
 text=text.replace('            return dataSets;', '            ValidatePortableTail(dataSet.ToArray());\n            return dataSets;',1)
 # Portable descriptor 12 is emitted by unchanged CalculiX for quadratic
 # 2D line output. Erased hooks preserve the original net48 decoder behavior.
 text=text.replace('        static private int GetNumberOfElementNodes(FrdFeDescriptorId feDescriptorId)\n        {', '        static private int GetNumberOfElementNodes(FrdFeDescriptorId feDescriptorId)\n        {\n            int portableCount=0; PortableElementNodeCount((int)feDescriptorId, ref portableCount);\n            if(portableCount!=0)return portableCount;',1)
 text=text.replace('        static private FeElement GetElement(int id, FrdFeDescriptorId feDescriptorId, int[] frdNodeIds)\n        {', '        static private FeElement GetElement(int id, FrdFeDescriptorId feDescriptorId, int[] frdNodeIds)\n        {\n            FeElement portableElement=null; PortableElement(id,(int)feDescriptorId,frdNodeIds,ref portableElement);\n            if(portableElement!=null)return portableElement;',1)
 pos=text.index('        static bool IsConstantWidth(')
 text=text[:pos]+'        static partial void ValidatePortableHeader(string line);\n        static partial void ValidatePortableComponents(int count);\n        static partial void ValidatePortableAllocation(long count);\n        static partial void ValidatePortableTail(string[] lines);\n        static partial void PortableElementNodeCount(int descriptor, ref int count);\n        static partial void PortableElement(int id, int descriptor, int[] nodes, ref FeElement element);\n'+text[pos:]
 legacy=static_layout.container(original(pin,FRD).decode(),'public static partial class FrdFileReader',''.join(blocks))
 return {FRD:text.encode(),FRD[:-3]+'.Legacy.cs':legacy.encode()}
DAT='CaeResults/FileInOut/Input/CalculiX/DatFileReader.cs'
ENTRIES='CaeResults/HistoryOutputs/HistoryResultEntries.cs'
DAT_UNCHANGED=['CaeResults/FileInOut/Input/CalculiX/DatDataSet.cs','CaeResults/HistoryOutputNames.cs','CaeMesh/Globals.cs','CaeMesh/CalculixNameShortener.cs']
def render_dat(pin=BASELINE):
 full=original(pin,DAT).decode();text=full;blocks=[]
 for start,end in [
  ('        private static readonly string[] _spaceSplitter', '        // CalculiX writes these totals'),
  ('        private static readonly Dictionary<string, string> nameKeyMap', '        // Methods'),
  ('        static private IEnumerable<string[]> SplitToDataSetLinesList(', '        static private void Repair('),
  ('        static private void Repair(', '        static private string GetFrequencyHistorySetName('),
  ('        static private DatDataSet GetDatDataSet(', '        static private HistoryResults GetHistoryOutput(')]:
  block,text=static_layout.span(text,start,end);blocks.append(block)
 shared=static_layout.container(full,'[Serializable]\n    public static partial class DatFileReader',''.join(blocks))
 for line in ['using Octree;\n','using System.Configuration;\n']:shared=shared.replace(line,'')
 text=text.replace('public static class DatFileReader','public static partial class DatFileReader',1).replace('    [Serializable]\n','',1)
 source=original(pin,ENTRIES).decode();entry_core=source
 body,entry_core=static_layout.span(entry_core,'        // Static methods','        // Methods')
 entry_core=entry_core.replace('public class HistoryResultEntries','public partial class HistoryResultEntries',1).replace('using static CaeGlobals.Geometry2;\n','')
 return {DAT:shared.encode(),DAT[:-3]+'.Legacy.cs':text.encode(),ENTRIES:entry_core.encode(),ENTRIES[:-3]+'.Legacy.cs':static_layout.container(source,'public partial class HistoryResultEntries',body).encode()}
def verify(pin=BASELINE):
 analysis=analysis_layout.source_rows(pin);expected=render();assert render(pin)==expected,'Upstream FRD boundary changed'
 dat=render_dat();assert render_dat(pin)==dat,'Upstream DAT boundary changed';expected.update(dat)
 for path,data in expected.items():assert(ROOT/path).read_bytes()==data,'FRD extraction changed: '+path
 for path in UNCHANGED+DAT_UNCHANGED+list(ADAPTED):
  data=original(BASELINE,path);assert original(pin,path)==data,'Unreviewed results source change: '+path
  if path in ADAPTED:
   line=ADAPTED[path].encode();assert data.count(line)==1;data=data.replace(line,b'')
  if path.endswith('/Field.cs'):data=data.replace(b'OrderedDictionary<',b'CaeGlobals.OrderedDictionary<')
  assert(ROOT/path).read_bytes()==data,'Results algorithm changed: '+path
  expected[path]=data
 expected['CaeGlobals/Tools.Results.cs']=(ROOT/'CaeGlobals/Tools.Results.cs').read_bytes()
 ns={'m':'http://schemas.microsoft.com/developer/msbuild/2003'}
 legacy=[c.attrib['Include'].replace('\\','/')for c in ET.parse(ROOT/'CaeResults/CaeResults.csproj').findall('.//m:Compile',ns)]
 for path in expected:
  if path.startswith('CaeResults/'):assert legacy.count(path.split('/',1)[1])==1,'Original result type ownership changed'
 for owner in ['CaeGlobals','CaeMesh']:
  base=ET.parse(ROOT/f'X/Analysis/{owner}/{owner}.csproj');project=ET.parse(ROOT/f'X/Results/{owner}/{owner}.csproj')
  native_only={'$(RepositoryRoot)'+p for p in analysis_layout.native_mesh_layout.ADDITIONS}|{'MeshSetupItem.Portable.cs'}
  original_items=[c.attrib['Include']for c in base.findall('.//Compile') if c.attrib['Include'] not in native_only];items=[c.attrib['Include']for c in project.findall('.//Compile')]
  extra=['$(RepositoryRoot)CaeGlobals/Tools.Results.cs']if owner=='CaeGlobals'else['$(RepositoryRoot)CaeMesh/Globals.cs','$(RepositoryRoot)CaeMesh/CalculixNameShortener.cs']
  assert sorted(items)==sorted(original_items+extra),'Results base closure differs'
 mesh_legacy=[c.attrib['Include'].replace('\\','/')for c in ET.parse(ROOT/'CaeMesh/CaeMesh.csproj').findall('.//m:Compile',ns)]
 for path in DAT_UNCHANGED:
  if path.startswith('CaeMesh/'):assert mesh_legacy.count(path.split('/',1)[1])==1,'Original mesh ownership changed'
 project=ET.parse(ROOT/'X/Results/CaeResults/CaeResults.csproj')
 included=[c.attrib['Include'].replace('$(RepositoryRoot)','')for c in project.findall('.//Compile')]
 required=['CaeResults/FieldOutput/Field.cs','CaeResults/FieldOutputNames.cs',FRD]+UNCHANGED+[DAT,ENTRIES]+[p for p in DAT_UNCHANGED if p.startswith('CaeResults/')]
 assert sorted(included)==sorted(required+['FrdSnapshot.Portable.cs','DatSnapshot.Portable.cs']),'Results assembly closure differs'
 rows={r['path']:r for r in analysis}
 rows.update({p:{'path':p,'sha256':hashlib.sha256(d).hexdigest()}for p,d in expected.items()})
 return sorted(rows.values(),key=lambda r:r['path'])
