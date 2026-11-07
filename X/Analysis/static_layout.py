"""Mechanical partial extraction for original static-deck data and writers.

These functions verify checked-in source. They do not generate code at build time.
Coupled members remain in the original net48 projects, with their bodies intact.
"""
import subprocess

BASELINE = 'de8f73032a72746e3d6d9afd53d9fbd289eb310a'
REMOVED = {
 'CaeGlobals/Selection/Selection.cs':['using System.Runtime.InteropServices.WindowsRuntime;\n'],
 'CaeMesh/CoordinateSystem.cs':['using System.Net.Configuration;\n'],
 'CaeModel/Steps/Loads/CLoad.cs':['using System.Drawing.Design;\n'],
}


def original(root, revision, path):
    return subprocess.check_output(['git','show',revision+':'+path],cwd=root).decode('utf-8')


def header(text): return text[:text.index('namespace ')]


def container(text, declaration, body):
    namespace = text[text.index('namespace ')+10:text.index('\n{',text.index('namespace '))]
    return header(text)+'namespace '+namespace+'\n{\n    '+declaration+'\n    {\n'+body+'    }\n}\n'


def span(text,start,end):
    a=text.index(start);b=text.index(end,a)
    return text[a:b],text[:a]+text[b:]


def render_extensions(text):
    blocks=[]
    for start,end in [('        public static string ToCalculiX16String(', '        // String[]'),
                      ('        public static string GetNextNumberedKey(this HashSet<string>', '        public static string GetNextNumberedKey(this List<string>'),
                      ('        public static bool IsGeometryBased(', '        // Double'),
                      ('        public static string GetDisplayedName<', '        // NamedClass[]')]:
        body,text=span(text,start,end);blocks.append(body)
    legacy=text.replace('public static class ExtensionMethods','public static partial class ExtensionMethods',1)
    imports=header(text)[:header(text).index('using System;')]+'using System;\nusing System.Collections.Generic;\nusing System.Reflection;\n\n'
    core=imports+'namespace CaeGlobals\n{\n    public static partial class ExtensionMethods\n    {\n'+''.join(blocks)+'    }\n}\n'
    return {'CaeGlobals/Extensions.cs':legacy,'CaeGlobals/Extensions.Calculix.cs':core}


def render(root,revision=BASELINE):
    result={}
    def read(path):return original(root,revision,path)
    def split(path,declaration,start,end,legacy_decl=None):
        text=read(path);body,core=span(text,start,end)
        core=core.replace(declaration,declaration.replace('class ','partial class '),1)
        decl=legacy_decl or declaration.replace('class ','partial class ')
        # Legacy declarations carry no repeated base class or attributes.
        if legacy_decl is None:decl=decl.split(' : ')[0]
        result[path]=core
        result[path[:-3]+'.Legacy.cs']=container(text,decl,body)
    split('CaeGlobals/Selection/Selection.cs','public class Selection : ISerializable',
          '        public Selection(Selection selection, bool copyNodes, bool copyNodeHashes)',
          '        public Selection(SerializationInfo info, StreamingContext context)')
    path='CaeGlobals/Selection/Selection.cs'
    body,core=span(result[path],'        public Selection DeepCopy(', '        public void DeepClone()')
    result[path]=core
    legacy=result[path[:-3]+'.Legacy.cs'];result[path[:-3]+'.Legacy.cs']=legacy.replace('    }\n}',body+'    }\n}',1)
    split('CaeModel/Steps/Step.cs','public abstract class Step : NamedClass, ISerializable',
          '        public abstract bool IsBoundaryConditionSupported(', '        public int GetNumberOfStepControls()')
    split('CaeModel/Steps/StaticStep.cs','public class StaticStep : Step, ISerializable',
          '        public override bool IsBoundaryConditionSupported(', '        // ISerialization')
    for kind in ('FrequencyStep','BuckleStep'):
        split('CaeModel/Steps/'+kind+'.cs','public class '+kind+' : Step, ISerializable',
              '        public override bool IsBoundaryConditionSupported(', '        // ISerialization')
    path='CaeModel/Steps/BoundaryConditions/DisplacementRotation.cs';text=read(path)
    body,core=span(text,'        public bool IsDistributionTypeSupported(', '        // IContainsEquations')
    full='public class DisplacementRotation : BoundaryCondition, IDistribution, IPreviewable, ISerializable'
    core=core.replace(full,'public partial class DisplacementRotation : BoundaryCondition, ISerializable',1)
    result[path]=core
    result[path[:-3]+'.Legacy.cs']=container(text,'public partial class DisplacementRotation : IDistribution, IPreviewable',body)
    result['CaeModel/Steps/Step.cs']=result['CaeModel/Steps/Step.cs'].replace('OrderedDictionary<','CaeGlobals.OrderedDictionary<')
    split('CaeModel/Distributions/Distribution.cs','public abstract class Distribution : NamedClass, ISerializable',
          '        public abstract void GetMagnitudesAndDistancesForPoints(', '        // ISerialization')
    # Original BC constructor initialization is shared by a new mesh-independent
    # overload; the existing FeModel overload retains its optional model behavior.
    path='CaeModel/FileInOut/Output/Calculix/Keywords/Step/BC/CalDisplacementRotation.cs';text=read(path)
    a=text.index('        public CalDisplacementRotation(DisplacementRotation displacementRotation,')
    b=text.index('\n\n\n        // Methods',a);ctor=text[a:b]
    init=ctor[ctor.index('        {\n')+10:ctor.index('            if (model != null)')]
    core_ctor='''        public CalDisplacementRotation(DisplacementRotation displacementRotation,
                                       Dictionary<string, CalReferencePoint> referencePoints,
                                       string nodeSetNameOfSurface, ComplexLoadTypeEnum complexLoadType)
        {
'''+init+'        }'
    legacy_ctor=ctor[:ctor.index('        {\n')] + '''            : this(displacementRotation, referencePoints, nodeSetNameOfSurface, complexLoadType)
        {
'''+ctor[ctor.index('            if (model != null)'):]
    result[path]=(text[:a]+core_ctor+text[b:]).replace('internal class CalDisplacementRotation','internal partial class CalDisplacementRotation',1)
    result[path[:-3]+'.Legacy.cs']=container(text,'internal partial class CalDisplacementRotation',legacy_ctor+'\n')
    path='CaeModel/FileInOut/Output/Calculix/Keywords/Step/Load/CalCLoad.cs';text=read(path)
    field='        private FeMesh _mesh;\n'
    a=text.index('        public CalCLoad(FeMesh mesh,');b=text.index('\n\n\n        // Methods',a);ctor=text[a:b]
    legacy_ctor=ctor[:ctor.index('        {\n')]+'''            : this(load, referencePoints, complexLoadType)
        {
            _mesh = mesh;
        }
'''
    new_ctor='''        public CalCLoad(CLoad load, Dictionary<string, CalReferencePoint> referencePoints,
                        ComplexLoadTypeEnum complexLoadType)
        {
'''+ctor[ctor.index('        {\n')+10:].replace('            _mesh = mesh;\n','')
    core=text[:a]+new_ctor+text[b:];core=core.replace(field,'',1)
    a=core.index('        public override string GetDataString()')
    b=core.index('        // A *Transform',a);method=core[a:b]
    c=method.index('            StringBuilder sb = new StringBuilder();')
    prefix=method[method.index('        {\n')+10:c]
    helper='        internal string GetGlobalDataString()\n        {\n'+method[c:]
    wrapper='        public override string GetDataString()\n        {\n'+prefix+'            return GetGlobalDataString();\n        }\n'
    tail,core_after=span(core[b:],'        private string GetDataStringInGlobalDirections(', '    }\n}')
    core_dispatch="""        partial void ResolveCoordinateSystem(ref string result, ref bool hasContext);
        public override string GetDataString()
        {
            string result = null;
            bool hasContext = false;
            ResolveCoordinateSystem(ref result, ref hasContext);
            if (result != null) return result;
            if (!hasContext && _load.CoordinateSystemName != CoordinateSystem.DefaultCoordinateSystemName)
                throw new NotSupportedException("Local concentrated-load coordinates require the full mesh context.");
            return GetGlobalDataString();
        }
"""
    hook="""        partial void ResolveCoordinateSystem(ref string result, ref bool hasContext)
        {
            hasContext = true;
"""+prefix.replace('return GetDataStringInGlobalDirections(coordinateSystem);','result = GetDataStringInGlobalDirections(coordinateSystem);')+'        }\n'
    core=core[:a]+core_dispatch+helper+core_after
    core=core.replace('internal class CalCLoad','internal partial class CalCLoad',1)
    result[path]=core
    result[path[:-3]+'.Legacy.cs']=container(text,'internal partial class CalCLoad',field+legacy_ctor+hook+tail)
    split('CaeModel/FileInOut/Output/Calculix/Keywords/Step/HistoryOutput/CalNodePrint.cs','internal class CalNodePrint : CalculixKeyword',
          '        public CalNodePrint(FeModel model,', '        public CalNodePrint(NodalHistoryOutput nodalHistoryOutput, string regionName, int outputFrequency)')
    # Move pure phase normalization out of the legacy serializer-heavy Tools file.
    path='CaeGlobals/Tools.cs';text=read(path);body,legacy=span(text,'        public static double GetPhase360(', '        public static float GetComplexMagnitude(')
    legacy=legacy.replace('    [Serializable]\n    public static class Tools','    public static partial class Tools',1)
    result[path]=legacy
    result['CaeGlobals/Tools.Equations.cs']=text[:text.index('using System;')]+'using System;\n\nnamespace CaeGlobals\n{\n    [Serializable]\n    public static partial class Tools\n    {\n'+body+'    }\n}\n'
    # Original IO helpers and field-invariant math stay in one implementation.
    # Results builds include this partial; the existing analysis slice need not.
    legacy=result[path];blocks=[]
    for start,end in [('        private static readonly float _oneThird', '        //\n'),
                      ('        public static bool IsFileLocked(', '        public static string[] ReadAllLines('),
                      ('        public static string GetRandomString(', '        public static float Sin(')]:
        block,legacy=span(legacy,start,end);blocks.append(block)
    result[path]=legacy
    result['CaeGlobals/Tools.Results.cs']=text[:text.index('using System;')]+'using System;\nusing System.IO;\n\nnamespace CaeGlobals\n{\n    public static partial class Tools\n    {\n'+''.join(blocks)+'    }\n}\n'
    # Original pressure preview/model evaluation stays in the legacy owner;
    # transport data, equations and serialization remain in the shared original type.
    path='CaeModel/Steps/Loads/VariablePressure.cs';text=read(path)
    body,core=span(text,'        public abstract double GetPressureForPoint(', '        // ISerialization')
    result[path]=core.replace('public abstract class VariablePressure','public abstract partial class VariablePressure',1)
    result[path[:-3]+'.Legacy.cs']=container(text,'public abstract partial class VariablePressure',body)
    path='CaeModel/Steps/Loads/DLoad.cs';text=read(path)
    body,core=span(text,'        public FeResults GetPreview(', '        public new void GetObjectData(')
    full='public class DLoad : VariablePressure, IDistribution, IPreviewable, ISerializable'
    result[path]=core.replace(full,'public partial class DLoad : VariablePressure, ISerializable',1)
    result[path[:-3]+'.Legacy.cs']=container(text,'public partial class DLoad : IDistribution, IPreviewable',body)
    split('CaeMesh/FeSurface.cs','public class FeSurface : NamedClass',
          '        public FeSurface(FeSurface surface)', '        // Methods')
    result.update(render_extensions(read('CaeGlobals/Extensions.cs')))
    for path,lines in REMOVED.items():
        text=result.get(path,read(path))
        for line in lines:
            if text.count(line)!=1:raise ValueError('Unused import anchor changed: '+path)
            text=text.replace(line,'')
        result[path]=text
    return {path:text.encode('utf-8') for path,text in result.items()}
