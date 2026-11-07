using System.Formats.Nrbf;
using System.Globalization;

internal static partial class StaticGraph
{
    // Original enum values from CaeMesh/Elements/FeElementType.cs, guarded by
    // family tests against source. Unsupported choices are explicit failures.
    private static Dictionary<int,string> Choices(params (int Value,string Name)[] values)=>values.ToDictionary(x=>x.Value,x=>x.Name);
    private static readonly (int Vtk,string Field,string Enum,Dictionary<int,string> Names)[] FamilyTypes={
        (3,"_linearBeamType","FeElementTypeLinearBeam",Choices((10,"T3D2"),(11,"B31"),(12,"B31R"),(20,"T2D2"),(21,"B21"))),
        (21,"_parabolicBeamType","FeElementTypeParabolicBeam",Choices((10,"T2D3"),(11,"B32"),(12,"B32R"))),
        (5,"_linearTriaType","FeElementTypeLinearTria",Choices((10,"S3"),(11,"M3D3"),(20,"CPS3"),(30,"CPE3"),(40,"CAX3"))),
        (22,"_parabolicTriaType","FeElementTypeParabolicTria",Choices((10,"S6"),(11,"M3D6"),(20,"CPS6"),(30,"CPE6"),(40,"CAX6"))),
        (9,"_linearQuadType","FeElementTypeLinearQuad",Choices((10,"S4"),(11,"S4R"),(12,"M3D4"),(13,"M3D4R"),(20,"CPS4"),(21,"CPS4R"),(30,"CPE4"),(31,"CPE4R"),(40,"CAX4"),(41,"CAX4R"))),
        (23,"_parabolicQuadType","FeElementTypeParabolicQuad",Choices((10,"S8"),(11,"S8R"),(12,"M3D8"),(13,"M3D8R"),(20,"CPS8"),(21,"CPS8R"),(30,"CPE8"),(31,"CPE8R"),(40,"CAX8"),(41,"CAX8R"))),
        (10,"_linearTetraType","FeElementTypeLinearTetra",Choices((10,"C3D4"))),
        (24,"_parabolicTetraType","FeElementTypeParabolicTetra",Choices((10,"C3D10"),(11,"C3D10T"))),
        (14,"_linearPyramidType","FeElementTypeLinearPyramid",Choices((10,"C3D5"))),
        (27,"_parabolicPyramidType","FeElementTypeParabolicPyramid",Choices((10,"C3D13"))),
        (13,"_linearWedgeType","FeElementTypeLinearWedge",Choices((10,"C3D6"))),
        (26,"_parabolicWedgeType","FeElementTypeParabolicWedge",Choices((10,"C3D15"))),
        (12,"_linearHexaType","FeElementTypeLinearHexa",Choices((10,"C3D8"),(11,"C3D8R"),(12,"C3D8I"))),
        (25,"_parabolicHexaType","FeElementTypeParabolicHexa",Choices((10,"C3D20"),(11,"C3D20R")))
    };
    internal static object ReadFamilies(SerializationRecord root)
    {
        var controller=Controller(root);var model=Record(controller.GetRawValue("_model"),"CaeModel.FeModel");
        var properties=Record(model.GetRawValue("_properties"),"CaeModel.ModelProperties");
        int space=EnumValue(properties,"ModelSpace","CaeModel.ModelSpaceEnum");
        string modelSpace=space switch {1=>"ThreeD",2=>"PlaneStress",3=>"PlaneStrain",4=>"Axisymmetric",_=>throw new NotSupportedException("Explicit original model space required.")};
        if(EnumValue(properties,"ModelType","CaeModel.ModelType")!=0 || properties.GetString("GlobalResultsFileName")!=null)throw new NotSupportedException("General model without linked results required.");
        var units=Record(model.GetRawValue("_unitSystem"),"CaeGlobals.UnitSystem");
        if(EnumValue(units,"_unitSystemType","CaeGlobals.UnitSystemType")!=2)throw new NotSupportedException("Family projection currently requires MM_TON_S_C units.");
        EmptyDictionaries(model,"_amplitudes","_constraints","_contactPairs","_distributions","_initialConditions","_surfaceInteractions","_userViews");
        if(model.HasMember("_materialOrientations"))EmptyDictionaries(model,"_materialOrientations");
        foreach(var f in new[]{"_calculixKeywordOverrides","_calculixUserKeywords"}) {
            var raw=model.GetRawValue(f);if(raw==null)continue;
            var value=Record(raw);int size=f=="_calculixUserKeywords"?Record(value.GetRawValue("_list")).GetInt32("_size"):value.GetInt32("_size");
            if(size!=0)throw new NotSupportedException("Family PMX projection refuses custom keyword content.");
        }
        EmptyDictionaries(Record(model.GetRawValue("_parameters"),"CaeModel.EquationParameterCollection"),"_parameters","_overriddenParameters");
        var mesh=Record(model.GetRawValue("_mesh"),"CaeMesh.FeMesh");
        EmptyDictionaries(mesh,"_coordinateSystems","_referencePoints","_surfaces","_meshSetupItems");
        var collection=Record(model.GetRawValue("_stepCollection"),"CaeModel.StepCollection");
        if(collection.GetBoolean("_onlyCheckModel"))throw new NotSupportedException("Model-check-only PMX cannot be submitted as a solve.");
        var steps=List(collection.GetRawValue("_steps"));
        if(steps.Length!=1)throw new NotSupportedException("Family PMX projection currently requires one static step.");
        var step=Record(steps[0],"CaeModel.StaticStep");Active(step);
        if(EnumValue(step,"_incrementationType","CaeModel.IncrementationTypeEnum")!=1 || !step.GetBoolean("_runAnalysis") || step.GetBoolean("_perturbation") || step.GetBoolean("_direct") || EnumValue(step,"_solverType","CaeModel.SolverTypeEnum")!=0 || List(Record(step.GetRawValue("_stepControls")).GetRawValue("_parameters")).Length!=0)throw new NotSupportedException("Ordinary running automatic static controls required.");
        EmptyDictionaries(step,"_definedFields");
        var materials=Entries(model,"_materials").Select(pair=> {
            var material=Named(pair,"CaeModel.Material");Active(material);
            if(material.GetBoolean("_temperatureDependent"))throw new NotSupportedException("Constant elastic family materials required.");
            var props=List(material.GetRawValue("_properties")).Select(RecordOnly).ToArray();
            if(props.Length<1 || props.Length>2 || props.Select(p=>p.TypeName.FullName).Distinct().Count()!=props.Length || props.Any(p=>p.TypeName.FullName is not ("CaeModel.Elastic" or "CaeModel.Density")))throw new NotSupportedException("Elasticity and optional density required.");
            var elastic=props.Single(p=>p.TypeName.FullName=="CaeModel.Elastic");var er=EquationRows(elastic.GetRawValue("_youngsPoissonsTemp"));
            if(er.Length!=1 || er[0].Length!=3 || !new[]{"0","0 °C"}.Contains(er[0][2]))throw new NotSupportedException("Single constant elastic row required.");
            var result=new Dictionary<string,object?>{{"name",pair.Key},{"youngsModulus",er[0][0]},{"poissonsRatio",er[0][1]}};
            var density=props.FirstOrDefault(p=>p.TypeName.FullName=="CaeModel.Density");
            if(density!=null){var dr=EquationRows(density.GetRawValue("_densityTemp"));if(dr.Length!=1 || dr[0].Length!=2)throw new NotSupportedException("Single density row required.");result["density"]=dr[0][0];}
            return result;
        }).ToArray();
        var sections=Entries(model,"_sections").Select(pair=> {
            var s=Named(pair,pair.Value.TypeName.FullName);Active(s);
            string kind=s.TypeName.FullName switch {"CaeModel.SolidSection"=>"solid","CaeModel.ShellSection"=>"shell","CaeModel.MembraneSection"=>"membrane",_=>throw new NotSupportedException("Solid/shell/membrane section required.")};
            if(EnumValue(s,"_regionType","CaeGlobals.RegionTypeEnum")!=4 || s.GetBoolean("_twoD")!=(space!=1))throw new NotSupportedException("Named section assignments matching model space required.");
            var result=new Dictionary<string,object?>{{"name",pair.Key},{"material",s.GetString("_materialName")},{"elementSet",s.GetString("_regionName")},{"kind",kind}};
            if(space!=1 || kind!="solid")result["thickness"]=Equation(s.GetRawValue("_thickness"));
            if(kind!="solid")result["offset"]=Equation(s.GetRawValue("_offset"));return result;
        }).ToArray();
        var constraints=Entries(step,"_boundaryConditions").Select(pair=> {
            var bc=Named(pair,"CaeModel.DisplacementRotation");FamilyAssignment(bc,space,2);
            string? Free(string? value)=>value=="Unconstrained"?null:value;
            var rotations=Equations(bc,"_ur1","_ur2","_ur3").Select(Free).ToArray();
            return new {name=pair.Key,nodeSet=bc.GetString("_regionName"),displacements=Equations(bc,"_u1","_u2","_u3").Select(Free).ToArray(),rotations=space==1?rotations:null};
        }).ToArray();
        var loads=Entries(step,"_loads").Select(pair=> {
            var load=Named(pair,"CaeModel.CLoad");FamilyAssignment(load,space,2);
            return new{name=pair.Key,nodeSet=load.GetString("_regionName"),forcePerNode=Equations(load,"_f1","_f2","_f3")};
        }).ToArray();
        var histories=Entries(step,"_historyOutputs").Select(pair=> {
            var h=Named(pair,pair.Value.TypeName.FullName);Active(h);bool nodal=h.TypeName.FullName=="CaeModel.NodalHistoryOutput";
            if(!nodal && h.TypeName.FullName!="CaeModel.ElementHistoryOutput")throw new NotSupportedException("Nodal/element history output required.");
            if(EnumValue(h,"_regionType","CaeGlobals.RegionTypeEnum")!=(nodal?2:4))throw new NotSupportedException("Named history region required.");
            int vars=EnumValue(h,"_variables",nodal?"CaeModel.NodalHistoryVariable":"CaeModel.ElementHistoryVariable");
            if(vars!=(nodal?3:1))throw new NotSupportedException("Original U/RF nodal or stress element histories required.");
            if(!h.GetBoolean("_global") || EnumValue(h,"_totals","CaeModel.TotalsTypeEnum")!=2 || h.GetRawValue("_creationData")!=null || h.GetRawValue("_creationIds") is ArrayRecord hi && hi.Lengths[0]!=0)throw new NotSupportedException("Ordinary global histories required.");
            return new{name=pair.Key,kind=nodal?"node":"element",region=h.GetString("_regionName"),variables=vars};
        }).ToArray();
        var fields=Entries(step,"_fieldOutputs").Select(pair=> {
            var f=Named(pair,pair.Value.TypeName.FullName);Active(f);
            bool node=f.TypeName.FullName=="CaeModel.NodalFieldOutput";
            if(!node && f.TypeName.FullName!="CaeModel.ElementFieldOutput")throw new NotSupportedException("Nodal/element field output required.");
            if(f.GetBoolean("_lastIterations") || f.GetBoolean("_contactElements") || !f.GetBoolean("_global"))throw new NotSupportedException("Ordinary global fields required.");
            return new {name=pair.Key,kind=node?"node":"element",variables=EnumValue(f,"_variables",node?"CaeModel.NodalFieldVariable":"CaeModel.ElementFieldVariable"),dimension=node?0:EnumValue(f,"_output","CaeModel.ElementFieldOutputOutputEnum")};
        }).ToArray();
        var dims=fields.Where(f=>f.kind=="element").Select(f=>f.dimension).Distinct().ToArray();
        if(dims.Length>1 || dims.Any(d=>d<0||d>2))throw new NotSupportedException("One original result output dimension required.");
        var analysis=new {schemaVersion=1,unitSystem="mm-N-s-C",modelSpace,materials,sections,step=new {
            name=step.GetString("_name"),timePeriod=step.GetDouble("_timePeriod"),initialTimeIncrement=step.GetDouble("_initialTimeIncrement"),minimumTimeIncrement=step.GetDouble("_minTimeIncrement"),maximumTimeIncrement=step.GetDouble("_maxTimeIncrement"),maximumIncrements=step.GetInt32("_maxIncrements"),outputFrequency=step.GetInt32("_outputFrequency"),nonlinearGeometry=step.GetBoolean("_nlgeom"),constraints,loads,nodalHistorySets=Array.Empty<string>(),elementHistorySets=Array.Empty<string>(),historyOutputs=histories,fieldOutputs=fields.Select(f=>new{f.name,f.kind,f.variables}).ToArray(),elementOutput=dims.Length==0?"Default":dims[0] switch {0=>"Default",1=>"TwoD",2=>"ThreeD",_=>throw new NotSupportedException()}}};
        return new {analysis,nodeSets=Sets(mesh,"_nodeSets","CaeMesh.FeNodeSet"),elementSets=Sets(mesh,"_elementSets","CaeMesh.FeElementSet"),parts=Entries(mesh,"_parts").Select(pair=> {
            var part=Named(pair,"CaeMesh.MeshPart");Active(part);
            var types=new Dictionary<int,string>();foreach(var spec in FamilyTypes) {
                int value=EnumValue(part,spec.Field,"CaeMesh."+spec.Enum);
                if(value==0)continue;if(!spec.Names.TryGetValue(value,out string? name))throw new NotSupportedException("Unknown original family formulation enum value.");types[spec.Vtk]=name;
            }
            return new {name=pair.Key,id=part.GetInt32("_partId"),nodes=Labels(part,"_nodeLabels"),elements=Labels(part,"_labels"),formulations=types};
        }).ToArray(),history=ReadCommandHistory(root),preservesOriginalBytes=true,newNativeSessionPersistence=false};
    }
    private static ClassRecord RecordOnly(object? value)=>Record(value);
    private static void FamilyAssignment(ClassRecord r,int space,int region)
    {
        Active(r);
        if(r.HasMember("_distributionName") && r.GetString("_distributionName")!="Constant")throw new NotSupportedException("Constant global assignments required.");
        if(r.HasMember("_phaseDeg") && !new[]{"0","0 °","0 rad"}.Contains(Equation(r.GetRawValue("_phaseDeg"))))throw new NotSupportedException("Zero-phase real assignments required.");
        if(r.GetBoolean("_twoD")!=(space!=1) || r.GetRawValue("_creationData")!=null || r.GetRawValue("_creationIds") is ArrayRecord ids && ids.Lengths[0]!=0 || EnumValue(r,"_regionType","CaeGlobals.RegionTypeEnum")!=region || r.GetBoolean("_complex") || (r.GetString("_amplitudeName")??"Default")!="Default" || (r.GetString("_coordinateSystemName")??"Global")!="Global")throw new NotSupportedException("Real global named assignments matching model dimensionality required.");
    }
}
