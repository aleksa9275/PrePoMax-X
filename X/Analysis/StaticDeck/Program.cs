using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using CaeGlobals;
using CaeModel;
using PrePoMaxX.MeshDeck;

namespace PrePoMaxX.StaticDeck;

public sealed record MaterialSpec(string Name,string? YoungsModulus=null,string? PoissonsRatio=null,
    string? Density=null,string[][]? PlasticCurve=null,string Hardening="Isotropic",string? Conductivity=null,string? SpecificHeat=null,string[][]? ConductivityTable=null,string[][]? SpecificHeatTable=null,string[][]? DensityTable=null,
    string? Expansion=null,string? ExpansionZeroTemperature=null);
public sealed record LayerSpec(string Material,string Thickness);
public sealed record SectionSpec(string Name,string Material,string ElementSet,string? Thickness=null,string Kind="solid",string? Offset=null,string Shape="RECT",string[]? Dimensions=null,double[]? Direction=null,LayerSpec[]? Layers=null,string? Mass=null,string? Stiffness=null,int Dof=0,int SecondDof=0,string? Clearance=null,string? TensileForce=null);
public sealed record ConstraintSpec(string Name,string NodeSet,string[] Displacements,string? Amplitude=null,string[]? Rotations=null);
public sealed record ForceSpec(string Name,string NodeSet,string[] ForcePerNode,string? Amplitude=null);
public sealed record MomentSpec(string Name,string NodeSet,string[] MomentPerNode,string? Amplitude=null);
public sealed record PressureSpec(string Name,string Magnitude,string? NodeSet=null,string? ElementSet=null,int? Face=null,string? Amplitude=null);
public sealed record GravitySpec(string Name,string ElementSet,string[] Acceleration,string? Amplitude=null);
public sealed record TemperatureSpec(string Name,string NodeSet,string Temperature,string? Amplitude=null);
public sealed record HeatLoadSpec(string Name,string Kind,string Region,string Magnitude,string? SinkTemperature=null,string? Amplitude=null,string? CoefficientAmplitude=null);
public sealed record ThermalSpec(bool SteadyState=true,string? InitialTemperature=null,double? MaximumTemperatureChange=null,bool Direct=false,double? AbsoluteZero=null,double? StefanBoltzmann=null);
public sealed record AmplitudeSpec(string Name,double[][] Points,string TimeSpan="StepTime",double ShiftX=0,double ShiftY=0);
public sealed record DynamicsSpec(double Alpha=-0.05,bool Direct=false,string Damping="Off",double MassDamping=0,double StiffnessDamping=0,int BasisModes=1,double ModalDampingRatio=0,string BasisName="Frequency-basis");
public sealed record FieldOutputSpec(string Name,string Kind,int Variables);
public sealed record HistoryOutputSpec(string Name,string Kind,string Region,int Variables);
public sealed record StepSpec(string Name,double TimePeriod,double InitialTimeIncrement,double MinimumTimeIncrement,
    double MaximumTimeIncrement,int MaximumIncrements,int OutputFrequency,ConstraintSpec[] Constraints,ForceSpec[] Loads,
    string[] NodalHistorySets,string[] ElementHistorySets,bool NonlinearGeometry=false,
    PressureSpec[]? Pressures=null,GravitySpec[]? GravityLoads=null,
    string Kind="static",int Modes=10,double? LowerFrequency=null,double? UpperFrequency=null,double BucklingAccuracy=0.0001, ThermalSpec? Thermal=null,TemperatureSpec[]? Temperatures=null,HeatLoadSpec[]? HeatLoads=null,TemperatureSpec[]? TemperatureFields=null,string? InitialTemperature=null,DynamicsSpec? Dynamics=null,MomentSpec[]? Moments=null,string ElementOutput="Default",FieldOutputSpec[]? FieldOutputs=null,HistoryOutputSpec[]? HistoryOutputs=null);
public sealed record AnalysisSpec(int SchemaVersion,string UnitSystem,MaterialSpec[] Materials,SectionSpec[] Sections,StepSpec Step,
    string? PyramidConversion = null,AmplitudeSpec[]? Amplitudes=null,string ModelSpace="ThreeD");

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
    public static (Material[] Materials,Section[] Sections,Step Step) Create(AnalysisSpec spec)
    {
        if(spec==null || spec.SchemaVersion!=1 || spec.Step==null || spec.Materials==null || spec.Sections==null)
            throw new InvalidDataException("Complete schema version 1 analysis tool definition required.");
        if(spec.UnitSystem is not ("mm-N-s-C" or "m-N-s-C"))throw new InvalidDataException("Explicit mm-N-s-C or m-N-s-C units required.");
        if(spec.ModelSpace is not ("ThreeD" or "PlaneStress" or "PlaneStrain" or "Axisymmetric"))throw new InvalidDataException("Choose ThreeD, PlaneStress, PlaneStrain or Axisymmetric model space.");
        bool twoD=spec.ModelSpace!="ThreeD";

        string length=spec.UnitSystem=="mm-N-s-C"?"mm":"m";
        StringPressureConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"MPa":"Pa";
        StringAreaConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"mm²":"m²";
        StringLengthConverter.SetUnit=length;StringLengthDOFConverter.SetUnit=length;StringForceConverter.SetUnit="N";
        StringMassConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"t":"kg";StringForcePerLengthConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"N/mm":"N/m";
        StringMomentConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"N·mm":"N·m";
        StringTemperatureConverter.SetUnit="°C";StringAngleDOFConverter.SetUnit="rad";
        StringDensityConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"t/mm³":"kg/m³";
        StringAccelerationConverter.SetUnit=spec.UnitSystem=="mm-N-s-C"?"mm/s²":"m/s²";
        if(spec.Materials.Length>1000 || spec.Sections.Length==0 || spec.Sections.Length>1000)
            throw new InvalidDataException("Bounded nonempty material/section arrays required.");
        string Equation(string text)
        { if(text==null || text.Length==0 || text.Length>4096)throw new InvalidDataException("Missing or oversized equation.");return text; }
        void InPlane(string text, Type converter)
        {
            if(!twoD)return;
            var component=new EquationContainer(converter,0);component.SetEquation(Equation(text));
            if(component.Value!=0)throw new InvalidDataException("2D force/gravity third component must be zero; components are never silently discarded.");
        }
        bool thermal=spec.Step.Kind=="heat-transfer";
        string power=spec.UnitSystem=="mm-N-s-C"?"mW":"W";
        StringThermalConductivityConverter.SetPowerUnit=power;StringThermalConductivityConverter.SetLengthUnit=length;StringThermalConductivityConverter.SetTemperatureDeltaUnit="∆°C";
        StringSpecificHeatConverter.SetEnergyUnit=spec.UnitSystem=="mm-N-s-C"?"mJ":"J";StringSpecificHeatConverter.SetMassUnit=spec.UnitSystem=="mm-N-s-C"?"t":"kg";StringSpecificHeatConverter.SetTemperatureDeltaUnit="∆°C";
        StringPowerConverter.SetUnit=power;
        StringPowerPerAreaConverter.SetPowerUnit=power;StringPowerPerAreaConverter.SetAreaUnit=spec.UnitSystem=="mm-N-s-C"?"mm²":"m²";
        StringPowerPerVolumeConverter.SetPowerUnit=power;StringPowerPerVolumeConverter.SetVolumeUnit=spec.UnitSystem=="mm-N-s-C"?"mm³":"m³";
        StringHeatTransferCoefficientConverter.SetPowerUnit=power;StringHeatTransferCoefficientConverter.SetAreaUnit=spec.UnitSystem=="mm-N-s-C"?"mm²":"m²";StringHeatTransferCoefficientConverter.SetTemperatureDeltaUnit="∆°C";
        StringThermalExpansionConverter.SetUnit="1/°C";
        void Table(string[][]? input,EquationContainer[][] target) {
            if(input==null)return;
            if(input.Length<1 || input.Length>1000 || input.Any(r=>r==null || r.Length!=2))throw new InvalidDataException("Thermal table rows require value and temperature.");
            for(int i=0;i<input.Length;i++)for(int j=0;j<2;j++)target[i][j].SetEquation(Equation(input[i][j]));
        }
        var materials=spec.Materials.Select(value=>
        {
            if(value==null)throw new InvalidDataException("Null material.");
            var material=new Material(value.Name);
            bool tables=value.ConductivityTable!=null || value.SpecificHeatTable!=null || value.DensityTable!=null;
            if(tables && !thermal)throw new InvalidDataException("Thermal property tables require heat-transfer analysis.");
            material.TemperatureDependent=tables;
            if(thermal) {
                if(value.YoungsModulus!=null || value.PoissonsRatio!=null || value.PlasticCurve!=null || value.Expansion!=null || value.ExpansionZeroTemperature!=null)throw new InvalidDataException("Thermal analysis uses thermal materials; remove mechanical properties.");
                if(value.ConductivityTable!=null && value.Conductivity!=null)throw new InvalidDataException("Choose scalar conductivity or a conductivity table.");
                var conductivity=new ThermalConductivity((value.ConductivityTable??new[]{new[]{"1","0"}}).Select(_=>new[]{1d,0d}).ToArray());
                if(value.ConductivityTable!=null)Table(value.ConductivityTable,conductivity.ThermalConductivityTemp);
                else conductivity.ThermalConductivityTemp[0][0].SetEquation(Equation(value.Conductivity));material.AddProperty(conductivity);
                if(value.SpecificHeatTable!=null && value.SpecificHeat!=null)throw new InvalidDataException("Choose scalar specific heat or a table.");
                if(value.SpecificHeat!=null || value.SpecificHeatTable!=null){var heat=new SpecificHeat((value.SpecificHeatTable??new[]{new[]{"1","0"}}).Select(_=>new[]{1d,0d}).ToArray());
                    if(value.SpecificHeatTable!=null)Table(value.SpecificHeatTable,heat.SpecificHeatTemp);else heat.SpecificHeatTemp[0][0].SetEquation(Equation(value.SpecificHeat));material.AddProperty(heat);}
            } else {
            if(value.Conductivity!=null || value.SpecificHeat!=null)throw new InvalidDataException("Thermal properties require heat-transfer analysis.");
            var elastic=new Elastic(new[]{new[]{1d,.3,0}});
            elastic.YoungsPoissonsTemp[0][0].SetEquation(Equation(value.YoungsModulus));
            elastic.YoungsPoissonsTemp[0][1].SetEquation(Equation(value.PoissonsRatio));material.AddProperty(elastic);
            }
            if(value.Expansion!=null) {
                if(value.ExpansionZeroTemperature==null)throw new InvalidDataException("Explicit thermal expansion reference temperature required.");
                var expansion=new ThermalExpansion(new[]{new[]{0d,0d}});expansion.ThermalExpansionTemp[0][0].SetEquation(Equation(value.Expansion));expansion.ZeroTemperature.SetEquation(Equation(value.ExpansionZeroTemperature));material.AddProperty(expansion);
            } else if(value.ExpansionZeroTemperature!=null)throw new InvalidDataException("Expansion reference temperature requires an expansion coefficient.");
            if(value.DensityTable!=null) {
                if(value.Density!=null)throw new InvalidDataException("Choose scalar density or a table.");
                var density=new Density(value.DensityTable.Select(_=>new[]{1d,0d}).ToArray());Table(value.DensityTable,density.DensityTemp);material.AddProperty(density);
            }
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
        if(thermal && spec.Sections.Any(s=>s?.Kind!="solid"))throw new InvalidDataException("Heat transfer requires solid sections in this workflow.");
        var sections=spec.Sections.Select(value=> {
            if(value==null)throw new InvalidDataException("Null section.");
            if(!twoD && value.Kind=="solid" && value.Thickness!=null)throw new InvalidDataException("Thickness applies to a 2D solid section.");
            if(twoD && spec.ModelSpace!="Axisymmetric" && value.Thickness==null)throw new InvalidDataException("Explicit plane section thickness required.");
            if(value.Kind is not ("solid" or "shell" or "membrane" or "beam" or "truss" or "composite" or "mass" or "spring" or "gap"))throw new InvalidDataException("Unknown section kind.");
            if(twoD && value.Kind!="solid")throw new InvalidDataException("Plane and axisymmetric elements require solid sections.");
            if(value.Kind is "shell" or "membrane" && value.Thickness==null)throw new InvalidDataException("Explicit shell/membrane thickness required.");
            if(value.Kind is "beam" or "truss" or "composite" && value.Thickness!=null)throw new InvalidDataException("Line/composite sections use dimensions/area/layers, not scalar thickness.");
            if(value.Kind=="truss" && value.Shape!="RECT")throw new InvalidDataException("Truss sections use area, without a beam shape selection.");
            if(value.Kind is not ("shell" or "membrane" or "composite") && value.Offset!=null)throw new InvalidDataException("Offset applies to shell/membrane sections.");
            if(value.Kind is not ("beam" or "truss" or "gap") && (value.Dimensions!=null || value.Direction!=null || value.Shape!="RECT"))throw new InvalidDataException("Line section controls require a beam/truss section.");
            if(value.Kind!="composite" && value.Layers!=null)throw new InvalidDataException("Layers require a composite section.");
            bool discrete=value.Kind is "mass" or "spring" or "gap";
            if(discrete && (value.Material!="" || value.Thickness!=null || value.Offset!=null || value.Dimensions!=null || value.Layers!=null))throw new InvalidDataException("Discrete sections have no material, thickness, offset or layer assignment.");
            if(!discrete && (value.Mass!=null || value.Stiffness!=null || value.Clearance!=null || value.TensileForce!=null || value.Dof!=0 || value.SecondDof!=0))throw new InvalidDataException("Discrete controls require a discrete section.");
            Section section=value.Kind=="solid" ? new SolidSection(value.Name,value.Material,value.ElementSet,RegionTypeEnum.ElementSetName,1,twoD) :
                value.Kind is "shell" or "composite" ? new ShellSection(value.Name,value.Material,value.ElementSet,RegionTypeEnum.ElementSetName,1,false) :
                value.Kind=="membrane" ? new MembraneSection(value.Name,value.Material,value.ElementSet,RegionTypeEnum.ElementSetName,1,false) :
                new SolidSection(value.Name,value.Material,value.ElementSet,RegionTypeEnum.ElementSetName,1,false);
            if(value.Offset!=null) {
                if(section is ShellSection shell)shell.Offset.SetEquation(Equation(value.Offset));
                if(section is MembraneSection membrane)membrane.Offset.SetEquation(Equation(value.Offset));
            }
            if(value.Thickness!=null)section.Thickness.SetEquation(Equation(value.Thickness));
            return section;
        }).ToArray();
        var definition=spec.Step;
        double[] times={definition.TimePeriod,definition.InitialTimeIncrement,definition.MinimumTimeIncrement,definition.MaximumTimeIncrement};
        if(times.Any(t=>!double.IsFinite(t)||t<=0) || definition.InitialTimeIncrement>definition.TimePeriod ||
            definition.InitialTimeIncrement>definition.MaximumTimeIncrement || definition.MinimumTimeIncrement>definition.InitialTimeIncrement ||
            definition.MinimumTimeIncrement>definition.MaximumTimeIncrement || definition.MaximumIncrements<1 || definition.OutputFrequency<1)
            throw new InvalidDataException("Invalid static incrementation/output values; clamping is not applied to tool input.");
        if(definition.Constraints==null || definition.Loads==null || definition.NodalHistorySets==null || definition.ElementHistorySets==null ||
            (!thermal && definition.Constraints.Length==0) || definition.Constraints.Length>1000 || definition.Loads.Length>1000 ||
            definition.NodalHistorySets.Length>100 || definition.ElementHistorySets.Length>100)
            throw new InvalidDataException("Complete bounded step arrays required.");
        Step step;
        if(thermal) {
            if(definition.Thermal==null || definition.Temperatures?.Length>1000 || definition.HeatLoads?.Length>1000 ||
                definition.Thermal.InitialTemperature?.Length>4096 || definition.NonlinearGeometry || definition.Constraints.Length!=0 || definition.Loads.Length!=0 ||
                definition.Pressures?.Length>0 || definition.GravityLoads?.Length>0 || (definition.Thermal.MaximumTemperatureChange.HasValue &&
                (!double.IsFinite(definition.Thermal.MaximumTemperatureChange.Value) || definition.Thermal.MaximumTemperatureChange<=0)))
                throw new InvalidDataException("Explicit thermal controls required; remove mechanical supports and loads.");
            step=new HeatTransferStep(definition.Name){SteadyState=definition.Thermal.SteadyState,
                Deltmx=definition.Thermal.MaximumTemperatureChange??double.PositiveInfinity,
                IncrementationType=definition.Thermal.Direct?IncrementationTypeEnum.Direct:IncrementationTypeEnum.Automatic,
                TimePeriod=definition.TimePeriod,InitialTimeIncrement=definition.InitialTimeIncrement,MinTimeIncrement=definition.MinimumTimeIncrement,
                MaxTimeIncrement=definition.MaximumTimeIncrement,MaxIncrements=definition.MaximumIncrements,OutputFrequency=definition.OutputFrequency};
            foreach(var t in definition.Temperatures??Array.Empty<TemperatureSpec>()) {
                if(t==null)throw new InvalidDataException("Null temperature boundary condition.");
                var bc=new TemperatureBC(t.Name,t.NodeSet,RegionTypeEnum.NodeSetName,0,false);bc.Temperature.SetEquation(Equation(t.Temperature));bc.AmplitudeName=t.Amplitude??Amplitude.DefaultAmplitudeName;step.BoundaryConditions.Add(bc.Name,bc);
            }
            foreach(var h in definition.HeatLoads??Array.Empty<HeatLoadSpec>()) {
                if(h==null)throw new InvalidDataException("Null heat load.");
                Load load;
                if(h.Kind=="nodal") {var v=new CFlux(h.Name,h.Region,RegionTypeEnum.NodeSetName,0,false);v.Magnitude.SetEquation(Equation(h.Magnitude));load=v;}
                else if(h.Kind=="body") {var v=new BodyFlux(h.Name,h.Region,RegionTypeEnum.ElementSetName,0,false);v.Magnitude.SetEquation(Equation(h.Magnitude));load=v;}
                else if(h.Kind=="surface") {var v=new DFlux(h.Name,h.Region,RegionTypeEnum.NodeSetName,0,false);v.Magnitude.SetEquation(Equation(h.Magnitude));load=v;}
                else if(h.Kind=="film") {var v=new FilmHeatTransfer(h.Name,h.Region,RegionTypeEnum.NodeSetName,0,1,false);v.FilmCoefficient.SetEquation(Equation(h.Magnitude));v.SinkTemperature.SetEquation(Equation(h.SinkTemperature));load=v;}
                else if(h.Kind=="radiation") {var v=new RadiationHeatTransfer(h.Name,h.Region,RegionTypeEnum.NodeSetName,0,0,false);
                    // Original emissivity setter clamps. Tool input is checked before that setter, preserving its original behavior.
                    var rawEmissivity=new EquationContainer(typeof(StringDoubleConverter),0);rawEmissivity.SetEquation(Equation(h.Magnitude));double emissivity=rawEmissivity.Value;
                    if(!double.IsFinite(emissivity) || emissivity<0 || emissivity>1)throw new InvalidDataException("Radiation emissivity must be in [0,1].");
                    v.Emissivity.SetEquation(Equation(h.Magnitude));v.SinkTemperature.SetEquation(Equation(h.SinkTemperature));load=v;}
                else throw new InvalidDataException("Choose nodal, body, surface, film or radiation heat load.");
                if(h.Kind is not ("film" or "radiation") && h.SinkTemperature!=null)throw new InvalidDataException("Sink temperature applies only to film convection.");
                load.AmplitudeName=h.Amplitude??Amplitude.DefaultAmplitudeName;
                if(load is FilmHeatTransfer film)film.CoefficientAmplitudeName=h.CoefficientAmplitude??Amplitude.DefaultAmplitudeName;
                else if(load is RadiationHeatTransfer radiation)radiation.EmissivityAmplitudeName=h.CoefficientAmplitude??Amplitude.DefaultAmplitudeName;
                else if(h.CoefficientAmplitude!=null)throw new InvalidDataException("Coefficient amplitude applies to film/radiation only.");
                step.Loads.Add(load.Name,load);
            }
        }
        else if(definition.Thermal!=null || definition.Temperatures?.Length>0 || definition.HeatLoads?.Length>0)throw new InvalidDataException("Thermal controls require heat-transfer analysis.");
        else if(definition.Kind is "dynamic" or "modal-dynamics") {
            var d=definition.Dynamics??throw new InvalidDataException("Explicit dynamics controls required.");
            if(!double.IsFinite(d.Alpha) || d.Alpha>0 || d.Alpha< -1d/3 || !double.IsFinite(d.MassDamping) || d.MassDamping<0 ||
                !double.IsFinite(d.StiffnessDamping) || d.StiffnessDamping<0 || !double.IsFinite(d.ModalDampingRatio) || d.ModalDampingRatio<0 || d.ModalDampingRatio>=1 ||
                d.BasisModes<1 || d.BasisModes>1000 || definition.NonlinearGeometry || definition.InitialTemperature!=null || definition.TemperatureFields?.Length>0)
                throw new InvalidDataException("Valid linear solid dynamics controls, nonnegative damping and no prescribed temperature fields required.");
            if(definition.Kind=="dynamic") {
                if(d.Damping is not ("Off" or "Rayleigh"))throw new InvalidDataException("Implicit dynamics supports original Off or Rayleigh damping.");
                step=new DynamicStep(definition.Name){Alpha=d.Alpha,IncrementationType=d.Direct?IncrementationTypeEnum.Direct:IncrementationTypeEnum.Automatic,
                    TimePeriod=definition.TimePeriod,InitialTimeIncrement=definition.InitialTimeIncrement,MinTimeIncrement=definition.MinimumTimeIncrement,
                    MaxTimeIncrement=definition.MaximumTimeIncrement,MaxIncrements=definition.MaximumIncrements,OutputFrequency=definition.OutputFrequency,
                    Damping=new Damping(){DampingType=d.Damping=="Off"?DampingTypeEnum.Off:DampingTypeEnum.Rayleigh,Alpha=d.MassDamping,Beta=d.StiffnessDamping}};
            } else {
                if(d.Damping is not ("Off" or "Rayleigh" or "Constant"))throw new InvalidDataException("Modal dynamics supports original Off, Constant or Rayleigh damping.");
                step=new ModalDynamicsStep(definition.Name){TimePeriod=definition.TimePeriod,InitialTimeIncrement=definition.InitialTimeIncrement,
                    MinTimeIncrement=definition.MinimumTimeIncrement,MaxTimeIncrement=definition.MaximumTimeIncrement,
                    MaxIncrements=definition.MaximumIncrements,OutputFrequency=definition.OutputFrequency,
                    ModalDamping=new ModalDamping(){DampingType=d.Damping=="Off"?ModalDampingTypeEnum.Off:d.Damping=="Constant"?ModalDampingTypeEnum.Constant:ModalDampingTypeEnum.Rayleigh,
                        Alpha=d.MassDamping,Beta=d.StiffnessDamping,ViscousDampingRatio=d.ModalDampingRatio}};
                foreach(var output in step.FieldOutputs.Values.OfType<NodalFieldOutput>())output.Variables|=NodalFieldVariable.V;
            }
        }
        else if(definition.Dynamics!=null)throw new InvalidDataException("Dynamics controls require a dynamics analysis.");
        else if(definition.Kind=="static") step=new StaticStep(definition.Name){IncrementationType=IncrementationTypeEnum.Automatic,
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
        if(definition.FieldOutputs!=null) {
            if(definition.FieldOutputs.Length<1 || definition.FieldOutputs.Length>100)throw new InvalidDataException("Bounded nonempty original field outputs required.");
            step.FieldOutputs.Clear();
            foreach(var output in definition.FieldOutputs) {
                if(output==null || output.Kind is not ("node" or "element"))throw new InvalidDataException("Choose node or element field output.");
                FieldOutput field=output.Kind=="node" ? new NodalFieldOutput(output.Name,(NodalFieldVariable)output.Variables) : new ElementFieldOutput(output.Name,(ElementFieldVariable)output.Variables);
                step.AddFieldOutput(field);
            }
        }
        if(!Enum.TryParse<ElementFieldOutputOutputEnum>(definition.ElementOutput,out var elementOutput) || !Enum.IsDefined(elementOutput))throw new InvalidDataException("Known original element field output dimension required.");
        foreach(var output in step.FieldOutputs.Values.OfType<ElementFieldOutput>())output.Output=elementOutput;
        foreach(var value in definition.Constraints)
        {
            if(value==null || value.Displacements==null || value.Displacements.Length!=3)throw new InvalidDataException("Three displacement components required; null means free.");
            if(twoD && value.Displacements[2]!=null)throw new InvalidDataException("2D supports use U1/U2; leave U3 free.");
            var bc=new DisplacementRotation(value.Name,value.NodeSet,RegionTypeEnum.NodeSetName,twoD,false,0);
            if(value.Rotations!=null) {
                if(twoD || value.Rotations.Length!=3)throw new InvalidDataException("Three rotations require a spatial structural model.");
                var rotations=new[]{bc.UR1,bc.UR2,bc.UR3};
                for(int i=0;i<3;i++)if(value.Rotations[i]!=null)rotations[i].SetEquation(Equation(value.Rotations[i]));
            }
            var components=new[]{bc.U1,bc.U2,bc.U3};
            for(int i=0;i<3;i++)if(value.Displacements[i]!=null)components[i].SetEquation(Equation(value.Displacements[i]));
            if(step.BoundaryConditions.ContainsKey(bc.Name))throw new InvalidDataException("Duplicate boundary condition name.");
            bc.AmplitudeName=value.Amplitude??Amplitude.DefaultAmplitudeName;
            if(definition.Kind!="modal-dynamics")step.BoundaryConditions.Add(bc.Name,bc);
        }
        foreach(var value in definition.Loads)
        {
            if(value==null || value.ForcePerNode==null || value.ForcePerNode.Length!=3)throw new InvalidDataException("Three force-per-node components required.");
            InPlane(value.ForcePerNode[2],typeof(StringForceConverter));
            var load=new CLoad(value.Name,value.NodeSet,RegionTypeEnum.NodeSetName,0,0,0,twoD,false,0);
            load.F1.SetEquation(Equation(value.ForcePerNode[0]),true);load.F2.SetEquation(Equation(value.ForcePerNode[1]),true);load.F3.SetEquation(Equation(value.ForcePerNode[2]),true);
            if(step.Loads.ContainsKey(load.Name))throw new InvalidDataException("Duplicate load name.");
            load.AmplitudeName=value.Amplitude??Amplitude.DefaultAmplitudeName;step.Loads.Add(load.Name,load);
        }
        foreach(var value in definition.Moments??Array.Empty<MomentSpec>()) {
            if(twoD || value==null || value.MomentPerNode==null || value.MomentPerNode.Length!=3)throw new InvalidDataException("Three moment components on a spatial structural model required.");
            var load=new MomentLoad(value.Name,value.NodeSet,RegionTypeEnum.NodeSetName,0,0,0,false,false,0){AmplitudeName=value.Amplitude??Amplitude.DefaultAmplitudeName};
            load.M1.SetEquation(Equation(value.MomentPerNode[0]),true);load.M2.SetEquation(Equation(value.MomentPerNode[1]),true);load.M3.SetEquation(Equation(value.MomentPerNode[2]),true);
            if(step.Loads.ContainsKey(load.Name))throw new InvalidDataException("Duplicate mechanical load name.");step.Loads.Add(load.Name,load);
        }
        int index=0;
        foreach(var value in definition.Pressures??Array.Empty<PressureSpec>()) {
            if(value==null || (string.IsNullOrEmpty(value.NodeSet)==string.IsNullOrEmpty(value.ElementSet)) ||
                (value.NodeSet!=null && value.Face!=null) || (value.ElementSet!=null && (value.Face is <1 or >6 || value.Face==null)))
                throw new InvalidDataException("Pressure requires a boundary node set or an element set with an explicit face 1–6.");
            var load=new DLoad(value.Name,value.NodeSet??value.ElementSet,value.NodeSet!=null?RegionTypeEnum.NodeSetName:RegionTypeEnum.ElementSetName,0,twoD,false,0);
            load.ElementFaceName=value.Face.HasValue?(CaeMesh.FeFaceName)value.Face.Value:CaeMesh.FeFaceName.Empty;
            load.Magnitude.SetEquation(Equation(value.Magnitude));
            if(step.Loads.ContainsKey(load.Name))throw new InvalidDataException("Duplicate mechanical load name.");load.AmplitudeName=value.Amplitude??Amplitude.DefaultAmplitudeName;step.Loads.Add(load.Name,load);
        }
        foreach(var value in definition.GravityLoads??Array.Empty<GravitySpec>()) {
            if(value==null || value.Acceleration==null || value.Acceleration.Length!=3)throw new InvalidDataException("Gravity requires three acceleration components.");
            InPlane(value.Acceleration[2],typeof(StringAccelerationConverter));
            var load=new GravityLoad(value.Name,value.ElementSet,RegionTypeEnum.ElementSetName,twoD,false,0);
            load.F1.SetEquation(Equation(value.Acceleration[0]),true);load.F2.SetEquation(Equation(value.Acceleration[1]),true);load.F3.SetEquation(Equation(value.Acceleration[2]),true);
            if(step.Loads.ContainsKey(load.Name))throw new InvalidDataException("Duplicate mechanical load name.");load.AmplitudeName=value.Amplitude??Amplitude.DefaultAmplitudeName;step.Loads.Add(load.Name,load);
        }
        if(definition.TemperatureFields?.Length>0) {
            if(thermal || definition.Kind!="static" || definition.TemperatureFields.Length>1000)throw new InvalidDataException("Temperature-driven fields require static mechanical analysis.");
            foreach(var t in definition.TemperatureFields) {
                if(t==null)throw new InvalidDataException("Null temperature field.");
                var field=new DefinedTemperature(t.Name,t.NodeSet,RegionTypeEnum.NodeSetName,0){AmplitudeName=t.Amplitude??Amplitude.DefaultAmplitudeName};
                field.Temperature.SetEquation(Equation(t.Temperature));step.DefinedFields.Add(field.Name,field);
            }
        }
        if(definition.InitialTemperature!=null && (thermal || definition.Kind!="static" || definition.InitialTemperature.Length>4096))throw new InvalidDataException("Mechanical initial temperature requires a static step.");
        if(materials.Any(m=>m.Properties.Any(p=>p is Plastic)))
            foreach(var field in step.FieldOutputs.Values.OfType<ElementFieldOutput>())field.Variables|=ElementFieldVariable.PEEQ;
        foreach(string set in definition.NodalHistorySets)step.AddHistoryOutput(new NodalHistoryOutput("NodeHistory-"+(++index),thermal?NodalHistoryVariable.NT|NodalHistoryVariable.RFL:definition.Kind is "dynamic" or "modal-dynamics"?NodalHistoryVariable.U|NodalHistoryVariable.RF|NodalHistoryVariable.V:NodalHistoryVariable.U|NodalHistoryVariable.RF,set,RegionTypeEnum.NodeSetName));
        foreach(string set in definition.ElementHistorySets)step.AddHistoryOutput(new ElementHistoryOutput("ElementHistory-"+(++index),thermal?ElementHistoryVariable.HFL:ElementHistoryVariable.S,set,RegionTypeEnum.ElementSetName));
        if(definition.HistoryOutputs!=null) {
            if(definition.HistoryOutputs.Length>100 || definition.NodalHistorySets.Length!=0 || definition.ElementHistorySets.Length!=0)throw new InvalidDataException("Choose explicit original histories or shorthand history sets.");
            step.HistoryOutputs.Clear();
            foreach(var output in definition.HistoryOutputs) {
                if(output==null || output.Kind is not ("node" or "element"))throw new InvalidDataException("Choose node or element history output.");
                HistoryOutput history=output.Kind=="node" ? new NodalHistoryOutput(output.Name,(NodalHistoryVariable)output.Variables,output.Region,RegionTypeEnum.NodeSetName) : new ElementHistoryOutput(output.Name,(ElementHistoryVariable)output.Variables,output.Region,RegionTypeEnum.ElementSetName);
                step.AddHistoryOutput(history);
            }
        }
        return(materials,sections,step);
    }

    public static string Build(CaeModel.InpMeshData mesh,AnalysisSpec spec)
    {
        // Deck admission is owned by StaticAnalysisDeckWriter. The optional
        // PrePoMax measurement command is not the CalculiX element formulation.
        var values=Create(spec);
        if(spec.Amplitudes?.Length>100)throw new InvalidDataException("At most 100 amplitudes supported.");
        var amplitudes=(spec.Amplitudes??Array.Empty<AmplitudeSpec>()).Select(a=> {
            if(a==null || !Enum.TryParse<AmplitudeTimeSpanEnum>(a.TimeSpan,out var span) || !Enum.IsDefined(span))throw new InvalidDataException("Known original amplitude time span required.");
            return new AmplitudeTabular(a.Name,a.Points){TimeSpan=span,ShiftX=a.ShiftX,ShiftY=a.ShiftY};
        }).ToArray();
        if(values.Step is HeatTransferStep heat) {
            if(spec.PyramidConversion!=null)throw new InvalidDataException("Thermal pyramid conversions remain pending.");
            return ThermalAnalysisDeckWriter.Write(mesh,values.Materials,values.Sections.Cast<SolidSection>().ToArray(),heat,spec.Step.Thermal.InitialTemperature,amplitudes,spec.Step.Thermal.AbsoluteZero,spec.Step.Thermal.StefanBoltzmann);
        }
        FrequencyStep? basis=null;
        if(values.Step is ModalDynamicsStep) {
            var d=spec.Step.Dynamics;
            var bs=spec with {Amplitudes=null,Step=spec.Step with {Kind="frequency",Name=d.BasisName,Dynamics=null,Modes=d.BasisModes,
                Loads=Array.Empty<ForceSpec>(),Moments=null,Pressures=null,GravityLoads=null,HistoryOutputs=null,NodalHistorySets=Array.Empty<string>(),ElementHistorySets=Array.Empty<string>()}};
            basis=(FrequencyStep)Create(bs).Step;basis.Storage=true;
            if(basis.Name==values.Step.Name)throw new InvalidDataException("Frequency basis and modal step names must differ.");
        }
        return StaticAnalysisDeckWriter.Write(mesh,values.Materials,values.Sections,values.Step,PyramidConversion(spec),amplitudes,spec.Step.InitialTemperature,basis,spec.ModelSpace,SectionKeywords(spec));
    }
    private static Dictionary<string,StructuralSectionData> SectionKeywords(AnalysisSpec spec)
    {
        var result=new Dictionary<string,StructuralSectionData>();
        double Quantity(string text,Type converter) { if(string.IsNullOrEmpty(text)||text.Length>4096)throw new InvalidDataException("Bounded section quantity required.");var v=new EquationContainer(converter,0);v.SetEquation(text);return v.Value; }
        foreach(var section in spec.Sections.Where(s=>s.Kind is "beam" or "truss" or "composite" or "mass" or "spring" or "gap")) {
            if(section.Layers!=null && section.Layers.Any(l=>l==null))throw new InvalidDataException("Null composite layer.");
            var data=new StructuralSectionData {Kind=section.Kind,Shape=section.Shape,Direction=section.Direction,
                Dimensions=section.Dimensions?.Select(v=>Quantity(v,section.Kind=="truss"?typeof(StringAreaConverter):typeof(StringLengthConverter))).ToArray(),
                Mass=section.Mass==null?null:Quantity(section.Mass,typeof(StringMassConverter)),
                Stiffness=section.Stiffness==null?null:Quantity(section.Stiffness,typeof(StringForcePerLengthConverter)),Dof=section.Dof,SecondDof=section.SecondDof,
                Clearance=section.Clearance==null?null:Quantity(section.Clearance,typeof(StringLengthConverter)),
                TensileForce=section.TensileForce==null?null:Quantity(section.TensileForce,typeof(StringForceConverter)),
                Offset=section.Offset==null?0:Quantity(section.Offset,typeof(StringDoubleConverter)),
                LayerMaterials=section.Layers?.Select(l=>l.Material).ToArray(),LayerThicknesses=section.Layers?.Select(l=>Quantity(l.Thickness,typeof(StringLengthConverter))).ToArray()};
            if(!result.TryAdd(section.Name,data))throw new InvalidDataException("Duplicate section name.");
        }
        return result;
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
