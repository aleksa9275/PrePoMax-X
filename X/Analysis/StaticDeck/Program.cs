using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using CaeGlobals;
using CaeModel;
using PrePoMaxX.MeshDeck;

namespace PrePoMaxX.StaticDeck;

public sealed record MaterialSpec(string Name,string YoungsModulus,string PoissonsRatio,
    string? Density=null,string[][]? PlasticCurve=null,string Hardening="Isotropic");
public sealed record SectionSpec(string Name,string Material,string ElementSet);
public sealed record ConstraintSpec(string Name,string NodeSet,string[] Displacements);
public sealed record ForceSpec(string Name,string NodeSet,string[] ForcePerNode);
public sealed record PressureSpec(string Name,string Magnitude,string? NodeSet=null,string? ElementSet=null,int? Face=null);
public sealed record GravitySpec(string Name,string ElementSet,string[] Acceleration);
public sealed record StepSpec(string Name,double TimePeriod,double InitialTimeIncrement,double MinimumTimeIncrement,
    double MaximumTimeIncrement,int MaximumIncrements,int OutputFrequency,ConstraintSpec[] Constraints,ForceSpec[] Loads,
    string[] NodalHistorySets,string[] ElementHistorySets,bool NonlinearGeometry=false,
    PressureSpec[]? Pressures=null,GravitySpec[]? GravityLoads=null,
    string Kind="static",int Modes=10,double? LowerFrequency=null,double? UpperFrequency=null,double BucklingAccuracy=0.0001);
public sealed record AnalysisSpec(int SchemaVersion,string UnitSystem,MaterialSpec[] Materials,SectionSpec[] Sections,StepSpec Step,
    string? PyramidConversion = null);

public static class AnalysisFiles
{
    public static CaeMesh.ConvertPyramidsToEnum? PyramidConversion(AnalysisSpec spec) => spec.PyramidConversion switch {
        null => null, "wedges" => CaeMesh.ConvertPyramidsToEnum.Wedges,
        "hexahedrons" => CaeMesh.ConvertPyramidsToEnum.Hexahedrons,
        _ => throw new InvalidDataException("Choose explicit pyramid conversion: wedges or hexahedrons.") };
    public const int MaximumDefinitionBytes=2*1024*1024;
    public static AnalysisSpec Read(string path)
    {
        using var stream=File.OpenRead(path);
        if(stream.Length>MaximumDefinitionBytes)throw new InvalidDataException("Analysis tool definition exceeds 2 MiB.");
        using var document=JsonDocument.Parse(stream,new JsonDocumentOptions{MaxDepth=32});
        void Unique(JsonElement element)
        {
            if(element.ValueKind==JsonValueKind.Object)
            {
                var names=new HashSet<string>(StringComparer.Ordinal);
                foreach(var property in element.EnumerateObject())
                { if(!names.Add(property.Name))throw new InvalidDataException("Duplicate JSON property: "+property.Name); Unique(property.Value); }
            }
            else if(element.ValueKind==JsonValueKind.Array)foreach(var item in element.EnumerateArray())Unique(item);
        }
        Unique(document.RootElement);
        var options=new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase,
            UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow,RespectRequiredConstructorParameters=true,MaxDepth=32};
        return document.RootElement.Deserialize<AnalysisSpec>(options)??throw new InvalidDataException("Null analysis tool definition.");
    }

    // This is tool configuration that constructs original engineering objects,
    // not a replacement FeModel or a selected application persistence format.
    public static (Material[] Materials,SolidSection[] Sections,Step Step) Create(AnalysisSpec spec)
    {
        if(spec==null || spec.SchemaVersion!=1 || spec.Step==null || spec.Materials==null || spec.Sections==null)
            throw new InvalidDataException("Complete schema version 1 analysis tool definition required.");
        if(spec.UnitSystem is not ("mm-N-s-C" or "m-N-s-C"))throw new InvalidDataException("Explicit mm-N-s-C or m-N-s-C units required.");
        string length=spec.UnitSystem=="mm-N-s-C"?"mm":"m";
        StringPressureConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"MPa":"Pa";
        StringLengthConverter.SetUnit=length;StringLengthDOFConverter.SetUnit=length;StringForceConverter.SetUnit="N";
        StringTemperatureConverter.SetUnit="°C";StringAngleDOFConverter.SetUnit="rad";
        StringDensityConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"t/mm³":"kg/m³";
        StringAccelerationConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"mm/s²":"m/s²";
        if(spec.Materials.Length==0 || spec.Materials.Length>1000 || spec.Sections.Length==0 || spec.Sections.Length>1000)
            throw new InvalidDataException("Bounded nonempty material/section arrays required.");
        string Equation(string text)
        { if(text==null || text.Length==0 || text.Length>4096)throw new InvalidDataException("Missing or oversized equation.");return text; }
        var materials=spec.Materials.Select(value=>
        {
            if(value==null)throw new InvalidDataException("Null material.");
            var material=new Material(value.Name);var elastic=new Elastic(new[]{new[]{1d,.3,0}});
            elastic.YoungsPoissonsTemp[0][0].SetEquation(Equation(value.YoungsModulus));
            elastic.YoungsPoissonsTemp[0][1].SetEquation(Equation(value.PoissonsRatio));material.AddProperty(elastic);
            if(value.Density!=null){var density=new Density(new[]{new[]{1d,0d}});density.DensityTemp[0][0].SetEquation(Equation(value.Density));material.AddProperty(density);}
            if(value.PlasticCurve!=null){
                if(value.PlasticCurve.Length<1 || value.PlasticCurve.Length>10000 || value.PlasticCurve.Any(r=>r==null || r.Length!=2)) throw new InvalidDataException("Plastic curve rows require stress and plastic strain.");
                if(!Enum.TryParse<PlasticHardening>(value.Hardening,out var hardening) || !Enum.IsDefined(hardening)) throw new InvalidDataException("Unknown original plastic hardening model.");
                var plastic=new Plastic(value.PlasticCurve.Select(r=>new[]{1d,0d,0d}).ToArray()){Hardening=hardening};
                for(int i=0;i<value.PlasticCurve.Length;i++)for(int j=0;j<2;j++)plastic.StressStrainTemp[i][j].SetEquation(Equation(value.PlasticCurve[i][j]));
                material.AddProperty(plastic);
            }
            return material;
        }).ToArray();
        var sections=spec.Sections.Select(value=>value==null?throw new InvalidDataException("Null section."):
            new SolidSection(value.Name,value.Material,value.ElementSet,RegionTypeEnum.ElementSetName,1,false)).ToArray();
        var definition=spec.Step;
        double[] times={definition.TimePeriod,definition.InitialTimeIncrement,definition.MinimumTimeIncrement,definition.MaximumTimeIncrement};
        if(times.Any(t=>!double.IsFinite(t)||t<=0) || definition.InitialTimeIncrement>definition.TimePeriod ||
            definition.InitialTimeIncrement>definition.MaximumTimeIncrement || definition.MinimumTimeIncrement>definition.InitialTimeIncrement ||
            definition.MinimumTimeIncrement>definition.MaximumTimeIncrement || definition.MaximumIncrements<1 || definition.OutputFrequency<1)
            throw new InvalidDataException("Invalid static incrementation/output values; clamping is not applied to tool input.");
        if(definition.Constraints==null || definition.Loads==null || definition.NodalHistorySets==null || definition.ElementHistorySets==null ||
            definition.Constraints.Length==0 || definition.Constraints.Length>1000 || definition.Loads.Length>1000 ||
            definition.NodalHistorySets.Length>100 || definition.ElementHistorySets.Length>100)
            throw new InvalidDataException("Complete bounded step arrays required.");
        Step step;
        if(definition.Kind=="static") step=new StaticStep(definition.Name){IncrementationType=IncrementationTypeEnum.Automatic,
            TimePeriod=definition.TimePeriod,InitialTimeIncrement=definition.InitialTimeIncrement,
            MinTimeIncrement=definition.MinimumTimeIncrement,MaxTimeIncrement=definition.MaximumTimeIncrement,
            MaxIncrements=definition.MaximumIncrements,OutputFrequency=definition.OutputFrequency,Nlgeom=definition.NonlinearGeometry};
        else if(definition.Kind is "frequency" or "buckling") {
            if(definition.NonlinearGeometry || definition.Modes<1 || definition.Modes>1000 ||
                definition.LowerFrequency.HasValue && (!double.IsFinite(definition.LowerFrequency.Value) || definition.LowerFrequency<0) ||
                definition.UpperFrequency.HasValue && (!double.IsFinite(definition.UpperFrequency.Value) || definition.UpperFrequency<=0) ||
                definition.LowerFrequency.HasValue && definition.UpperFrequency.HasValue && definition.LowerFrequency>=definition.UpperFrequency ||
                !double.IsFinite(definition.BucklingAccuracy) || definition.BucklingAccuracy<=0)
                throw new InvalidDataException("Valid original eigenmode controls and linear geometry are required.");
            step=definition.Kind=="frequency"
                ? new FrequencyStep(definition.Name){NumOfFrequencies=definition.Modes,LowerFrequency=definition.LowerFrequency??double.NaN,UpperFrequency=definition.UpperFrequency??double.NaN}
                : new BuckleStep(definition.Name){NumOfBucklingFactors=definition.Modes,Accuracy=definition.BucklingAccuracy};
            step.OutputFrequency=definition.OutputFrequency;
        } else throw new InvalidDataException("Choose static, frequency or buckling analysis.");
        foreach(var value in definition.Constraints)
        {
            if(value==null || value.Displacements==null || value.Displacements.Length!=3)throw new InvalidDataException("Three displacement components required; null means free.");
            var bc=new DisplacementRotation(value.Name,value.NodeSet,RegionTypeEnum.NodeSetName,false,false,0);
            var components=new[]{bc.U1,bc.U2,bc.U3};
            for(int i=0;i<3;i++)if(value.Displacements[i]!=null)components[i].SetEquation(Equation(value.Displacements[i]));
            if(step.BoundaryConditions.ContainsKey(bc.Name))throw new InvalidDataException("Duplicate boundary condition name.");
            step.BoundaryConditions.Add(bc.Name,bc);
        }
        foreach(var value in definition.Loads)
        {
            if(value==null || value.ForcePerNode==null || value.ForcePerNode.Length!=3)throw new InvalidDataException("Three force-per-node components required.");
            var load=new CLoad(value.Name,value.NodeSet,RegionTypeEnum.NodeSetName,0,0,0,false,false,0);
            load.F1.SetEquation(Equation(value.ForcePerNode[0]),true);load.F2.SetEquation(Equation(value.ForcePerNode[1]),true);load.F3.SetEquation(Equation(value.ForcePerNode[2]),true);
            if(step.Loads.ContainsKey(load.Name))throw new InvalidDataException("Duplicate load name.");
            step.Loads.Add(load.Name,load);
        }
        int index=0;
        foreach(var value in definition.Pressures??Array.Empty<PressureSpec>()) {
            if(value==null || (string.IsNullOrEmpty(value.NodeSet)==string.IsNullOrEmpty(value.ElementSet)) ||
                (value.NodeSet!=null && value.Face!=null) || (value.ElementSet!=null && (value.Face is <1 or >6 || value.Face==null)))
                throw new InvalidDataException("Pressure requires a boundary node set or an element set with an explicit face 1–6.");
            var load=new DLoad(value.Name,value.NodeSet??value.ElementSet,value.NodeSet!=null?RegionTypeEnum.NodeSetName:RegionTypeEnum.ElementSetName,0,false,false,0);
            load.ElementFaceName=value.Face.HasValue?(CaeMesh.FeFaceName)value.Face.Value:CaeMesh.FeFaceName.Empty;
            load.Magnitude.SetEquation(Equation(value.Magnitude));
            if(step.Loads.ContainsKey(load.Name))throw new InvalidDataException("Duplicate mechanical load name.");step.Loads.Add(load.Name,load);
        }
        foreach(var value in definition.GravityLoads??Array.Empty<GravitySpec>()) {
            if(value==null || value.Acceleration==null || value.Acceleration.Length!=3)throw new InvalidDataException("Gravity requires three acceleration components.");
            var load=new GravityLoad(value.Name,value.ElementSet,RegionTypeEnum.ElementSetName,false,false,0);
            load.F1.SetEquation(Equation(value.Acceleration[0]),true);load.F2.SetEquation(Equation(value.Acceleration[1]),true);load.F3.SetEquation(Equation(value.Acceleration[2]),true);
            if(step.Loads.ContainsKey(load.Name))throw new InvalidDataException("Duplicate mechanical load name.");step.Loads.Add(load.Name,load);
        }
        if(materials.Any(m=>m.Properties.Any(p=>p is Plastic)))
            foreach(var field in step.FieldOutputs.Values.OfType<ElementFieldOutput>())field.Variables|=ElementFieldVariable.PEEQ;
        foreach(string set in definition.NodalHistorySets)step.AddHistoryOutput(new NodalHistoryOutput("NodeHistory-"+(++index),NodalHistoryVariable.U|NodalHistoryVariable.RF,set,RegionTypeEnum.NodeSetName));
        foreach(string set in definition.ElementHistorySets)step.AddHistoryOutput(new ElementHistoryOutput("ElementHistory-"+(++index),ElementHistoryVariable.S,set,RegionTypeEnum.ElementSetName));
        return(materials,sections,step);
    }

    public static string Build(CaeModel.InpMeshData mesh,AnalysisSpec spec)
    {
        // Deck admission is owned by StaticAnalysisDeckWriter. The optional
        // PrePoMax measurement command is not the CalculiX element formulation.
        var values=Create(spec);
        return StaticAnalysisDeckWriter.Write(mesh,values.Materials,values.Sections,values.Step,PyramidConversion(spec));
    }
    public static void WriteNew(string path,string text)
    {
        using var stream=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None);
        using var writer=new StreamWriter(stream,new UTF8Encoding(false));writer.Write(text);
    }
}

internal static class Program
{
    private static int Main(string[] args)
    {
        CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;CultureInfo.CurrentUICulture=CultureInfo.InvariantCulture;
        if(args.Length!=4 || args[0]!="build-static")
        { Console.Error.WriteLine("Usage: PrePoMaxX.StaticDeck build-static <mesh.inp> <analysis.json> <new-output.inp>");return 2; }
        try
        {
            var mesh=MeshFiles.Read(args[1]);var spec=AnalysisFiles.Read(args[2]);string deck=AnalysisFiles.Build(mesh,spec);
            AnalysisFiles.WriteNew(args[3],deck);
            Console.WriteLine(JsonSerializer.Serialize(new{success=true,analysisDeck=true,unitSystem=spec.UnitSystem,
                nodes=mesh.Nodes.Count,elements=mesh.Elements.Count,materials=spec.Materials.Length,sections=spec.Sections.Length,
                constraints=spec.Step.Constraints.Length,loads=spec.Step.Loads.Length,outputWritten=true,solverExecuted=false}));return 0;
        }
        catch(Exception error)when(error is IOException or InvalidDataException or UnauthorizedAccessException or ArgumentException or JsonException or
            CaeException or FormatException or OverflowException or NotSupportedException)
        {Console.Error.WriteLine(JsonSerializer.Serialize(new{success=false,error=error.Message}));return 1;}
    }
}
