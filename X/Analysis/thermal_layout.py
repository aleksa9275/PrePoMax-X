"""Reproduce thermal partial extraction; guard original methods and serialization."""
import subprocess

BASELINE='de8f73032a72746e3d6d9afd53d9fbd289eb310a'

def render(root,revision=BASELINE):
    result={}
    def extract(path,first,last,cls,namespace,replace=None):
        s=subprocess.check_output(['git','show',revision+':'+path],cwd=root).decode('utf-8')
        a=s.index(first);b=s.index(last,a);part=s[a:b];s=s[:a]+s[b:];s=s.replace('class '+cls+' :','partial class '+cls+' :')
        if replace:s=s.replace(*replace)
        header=s[:s.index('namespace ')];legacy=path[:-3]+'.Legacy.cs'
        result[path]=s
        result[legacy]=header+'namespace '+namespace+'\n{\n    '+('internal' if cls.startswith('Cal') else 'public')+' partial class '+cls+'\n    {\n'+part+'    }\n}\n'
    extract('CaeModel/Steps/HeatTransferStep.cs','        public override bool IsBoundaryConditionSupported','        // ISerialization','HeatTransferStep','CaeModel')
    for path,cls in [('CaeModel/Steps/BoundaryConditions/TemperatureBC.cs','TemperatureBC'),('CaeModel/InitialConditions/InitialTemperature.cs','InitialTemperature'),('CaeModel/Steps/DefinedFields/DefinedTemperature.cs','DefinedTemperature')]:
        extract(path,'        public FeResults GetPreview','        // ISerialization',cls,'CaeModel',('IDistribution, IPreviewable, ISerializable','IDistribution, ISerializable'))
        legacy=path[:-3]+'.Legacy.cs';result[legacy]=result[legacy].replace('partial class '+cls+'\n','partial class '+cls+' : IPreviewable\n')
    for path,cls,constructor in [
        ('CaeModel/FileInOut/Output/Calculix/Keywords/Step/BC/CalTemperatureBC.cs','CalTemperatureBC', '''        // Constant named-region snapshot; legacy FeModel expansion stays in its partial.
        public CalTemperatureBC(TemperatureBC temperatureBC, string nodeSetNameOfSurface)
        {
            if (temperatureBC.DistributionName != Distribution.DefaultDistributionName) throw new NotSupportedException();
            _temperatureBC = temperatureBC;
            _nodeSetNameOfSurface = nodeSetNameOfSurface;
        }

'''),
        ('CaeModel/FileInOut/Output/Calculix/Keywords/ModelDefinition/InitialConditions/CalInitialTemperature.cs','CalInitialTemperature', '''        public CalInitialTemperature(InitialTemperature initialTemperature)
        {
            if ((initialTemperature.RegionType != RegionTypeEnum.NodeSetName && initialTemperature.RegionType != RegionTypeEnum.NodeId) ||
                initialTemperature.DistributionName != Distribution.DefaultDistributionName) throw new NotSupportedException();
            _initialTemperature = initialTemperature;
            _regionName = initialTemperature.RegionName;
            _initialTemperatures = initialTemperature.RegionType == RegionTypeEnum.NodeId ? new[] { initialTemperature } : null;
        }

''')]:
        extract(path,'        public '+cls+'(FeModel','        // Methods',cls,'FileInOut.Output.Calculix')
        result[path]=result[path].replace('internal class '+cls,'internal partial class '+cls).replace('        // Methods',constructor+'        // Methods')
    path='CaeModel/FileInOut/Output/Calculix/Keywords/Step/DefinedField/CalDefinedTemperature.cs'
    extract(path,'        public CalDefinedTemperature(FeModel','        // Methods','CalDefinedTemperature','FileInOut.Output.Calculix')
    constructor="""        public CalDefinedTemperature(DefinedTemperature temperature)
        {
            if (temperature.Type != DefinedTemperatureTypeEnum.ByValue || temperature.RegionType != RegionTypeEnum.NodeSetName ||
                temperature.DistributionName != Distribution.DefaultDistributionName) throw new NotSupportedException();
            _definedTemperature = temperature;
            _regionName = temperature.RegionName;
            _opType = OpTypeEnum.None;
        }

        partial void ResolveFileData(ref string data);

"""
    result[path]=result[path].replace('        // Methods',constructor+'        // Methods')
    a=result[path].index('                string stepData =');b=result[path].index('            }\n            else',a)
    block=result[path][a:b]
    replacement="""                string resolved = null;
                ResolveFileData(ref resolved);
                if (resolved == null) throw new NotSupportedException("File temperatures require the full model context.");
                fileData = resolved;
"""
    result[path]=result[path][:a]+replacement+result[path][b:]
    legacy=path[:-3]+'.Legacy.cs'
    hook='        partial void ResolveFileData(ref string data)\n        {\n'+block.replace('fileData =','data =')+'        }\n'
    result[legacy]=result[legacy].replace('    }\n}',hook+'    }\n}',1)
    path='CaeModel/ModelProperties.cs'
    text=subprocess.check_output(['git','show',revision+':'+path],cwd=root).decode('utf-8')
    a=text.index('    public static class ExtensionMethods');b=text.index('    //\n    [Serializable]\n    public class ModelProperties',a)
    result[path]=text[:a]+text[b:]
    result[path[:-3]+'.Legacy.cs']=text[:text.index('namespace ')]+'namespace CaeModel\n{\n'+text[a:b]+'}\n'
    return {p:s.encode('utf-8') for p,s in result.items()}
