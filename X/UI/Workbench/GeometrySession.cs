using CaeGlobals;
using CaeMesh;
using FileInOut.Output;
using PrePoMax;
using PrePoMax.Forms;
using PrePoMaxX.UI.OriginalForms;

namespace PrePoMaxX.UI;

public sealed class GeometrySession(Controller controller)
{
    public static string[] GeometryEditors=>["Split solid","Split shell","Offset faces","Repair geometry","Split periodic faces","FlipNormal","Defeature","DeleteCadFaces","DeleteStlFaces","FuseFaces"];
    public static string[] MeshEditors=>["Boundary layer","Remesh elements","Thicken shell mesh","Split mesh using surface","Merge coincident nodes","Element quality"];
    public static string[] Transforms=>["Translate","Rotate","Mirror","Scale"];
    public GeometryFormRule Edit(string family,string name=null,string[] parts=null)=>family switch {
        "Mesh setup"=>new FrmMeshSetupItemRule(controller,name),
        "Parts" or "Geometry parts"=>new FrmPartPropertiesRule(controller,name),
        "Translate"=>new FrmTranslateRule(controller,parts:parts),
        "Rotate"=>new FrmRotateRule(controller,parts:parts),
        "Mirror"=>new FrmMirrorRule(controller,parts:parts),
        "Scale"=>new FrmScaleRule(controller,parts:parts),
        "Split solid" or "Split shell"=>new FrmSplitSolidRule(controller,family),
        "Offset faces"=>new FrmOffsetFaceRule(controller),
        "Repair geometry"=>new FrmRepairGeometryRule(controller),
        "Split periodic faces"=>new FrmSplitPeriodicFacesRule(controller),
        "FlipNormal" or "Defeature" or "DeleteCadFaces" or "DeleteStlFaces" or "FuseFaces"=>new FrmSurfaceOperationRule(controller,family),
        "Boundary layer"=>new FrmBoundaryLayerRule(controller),
        "Remesh elements"=>new FrmRemeshingParametersRule(controller),
        "Thicken shell mesh"=>new FrmThickenShellMeshRule(controller),
        "Split mesh using surface"=>new FrmSplitPartMeshUsingSurfaceRule(controller),
        "Merge coincident nodes"=>new FrmMergeCoincidentNodesRule(controller),
        "Element quality"=>new FrmElementQualityRule(controller,parts:parts),
        _=>throw new NotSupportedException("Unknown original geometry/mesh editor: "+family)
    };
    public ModelTreeEntry[] Tree=>[
        new(){Family="Geometry parts",Name="Geometry",Group=true,Children=GeometryParts()},
        new(){Family="Mesh setup",Name="Mesh setup",Group=true,Children=Entries("Mesh setup",controller.Model.Geometry?.MeshSetupItems.Values.Cast<NamedClass>()??[])}
    ];
    ModelTreeEntry[] Entries(string family,IEnumerable<NamedClass> items)=>items.Where(i=>!i.Internal).Select(i=>OriginalModelTree.Annotate(new ModelTreeEntry {Family=family,Name=i.Name,Type=i.GetType().Name},i,OriginalModelTree.Geometry,controller)).ToArray();
    /// <summary>ModelTree.AddObjectsToNode/AddOrderedDictionaryLayoutNodes for geometry parts: folders, and the
    /// cells of a compound gathered under the part they were cut from.</summary>
    ModelTreeEntry[] GeometryParts()
    {
        var parts=controller.Model.Geometry?.Parts;
        if(parts==null)return [];
        var subParts=new HashSet<string>(parts.Values.OfType<CompoundGeometryPart>().SelectMany(p=>p.SubPartNames),StringComparer.OrdinalIgnoreCase);
        ModelTreeEntry Part(BasePart part,bool subPart=false)
        {
            if(part is not CompoundGeometryPart compound)return OriginalModelTree.Annotate(new ModelTreeEntry{Family="Geometry parts",Name=part.Name,Type=part.GetType().Name},part,OriginalModelTree.Geometry,controller,subPart);
            string single=compound.GetSingleSplitSubPartName();
            var order=new List<int>();
            foreach(string split in compound.GetSplitSubPartNames())
                for(int i=0;i<compound.SubPartNames.Length;i++)if(compound.CellSubPartNames[i]==split)order.Add(i);
            for(int i=0;i<compound.SubPartNames.Length;i++)if(compound.CellSubPartNames?[i]==null)order.Add(i);
            var children=new List<ModelTreeEntry>();var groups=new Dictionary<string,List<ModelTreeEntry>>();
            foreach(int i in order)
            {
                if(!parts.TryGetValue(compound.SubPartNames[i],out var cell)||cell.Internal)continue;
                var node=Part(cell,true);
                string split=compound.CellSubPartNames?[i];
                if(split!=null&&single==null&&compound.GetCellNames(split).Length>1)
                {
                    if(!groups.TryGetValue(split,out var list)){list=[];groups[split]=list;children.Add(new ModelTreeEntry{Family="Split sub parts",Step=compound.Name,Name=split,Group=true});}
                    list.Add(node);
                }
                else children.Add(node);
            }
            var resolved=children.Select(c=>c.Family=="Split sub parts"?new ModelTreeEntry{Family=c.Family,Step=c.Step,Name=c.Name,Group=true,Children=groups[c.Name].ToArray()}:c).ToArray();
            foreach(var split in resolved.Where(c=>c.Family=="Split sub parts"))OriginalModelTree.SplitSubPartStatus(split,controller);
            var entry=new ModelTreeEntry{Family="Geometry parts",Name=part.Name,Type=part.GetType().Name,Children=resolved,Text=single};
            return OriginalModelTree.Annotate(entry,part,OriginalModelTree.Geometry,controller,subPart);
        }
        if(parts is IOrderedDictionaryItemLayout<string> layout)
        {
            ModelTreeEntry[] Build(IEnumerable<OrderedDictionaryItemNode<string>> nodes)=>nodes.SelectMany(n=>n.IsGroup
                ?new[]{new ModelTreeEntry{Family="Geometry parts",Name=n.Name,Group=true,FolderId=n.Id.ToString(),Children=Build(n.Children),Icon="Folder.ico"}}
                :!subParts.Contains(n.Key)&&parts.TryGetValue(n.Key,out var part)&&!part.Internal?new[]{Part(part)}:Array.Empty<ModelTreeEntry>()).ToArray();
            return Build(layout.GetItemLayoutSnapshot().Nodes);
        }
        return parts.Values.Where(p=>!p.Internal&&!subParts.Contains(p.Name)).Select(p=>Part(p)).ToArray();
    }
    public Task Import(string path)=>Task.Run(()=>controller.ImportFileCommand(Path.GetFullPath(path),false));
    public Task Execute(string operation,string[] names)=>Task.Run(()=>ExecuteNow(operation,names));
    public void ExecuteNow(string operation,string[] names)
    {
        if(names==null || names.Length==0)throw new CaeException("Select at least one part or mesh setup item first.");
        bool geometry=controller.CurrentView==ViewGeometryModelResults.Geometry;
        switch(operation)
        {
            case "Create mesh":if(!controller.CreateMeshesCommand(names))throw new CaeException("Mesh creation failed. See the original mesher output.");break;
            case "Preview edge mesh":foreach(var name in names)if(!controller.PreviewEdgeMesh(name,null))throw new CaeException("Edge mesh preview failed.");break;
            case "Duplicate mesh setup":controller.DuplicateMeshSetupItemsCommand(names);break;
            case "Remove mesh setup":controller.RemoveMeshSetupItemsCommand(names);break;
            case "Create compound":controller.CreateAndImportCompoundPartCommand(names);break;
            case "Regenerate compound":controller.RegenerateCompoundPartsCommand(names);break;
            case "Swap geometries":if(names.Length!=2)throw new CaeException("Select two geometry parts.");controller.SwapPartGeometriesCommand(names[0],names[1]);break;
            case "Shell to solid":controller.ConvertShellToSolidCommand(names);break;
            case "Solid to shell":controller.ConvertSolidToShellCommand(names);break;
            case "Flip STL normals":controller.FlipStlPartSurfacesNormalCommand(names);break;
            case "Merge mesh parts":controller.MergeModelPartsCommand(names);break;
            case "Hide":if(geometry)controller.HideGeometryPartsCommand(names);else controller.HideModelPartsCommand(names);break;
            case "Show":if(geometry)controller.ShowGeometryPartsCommand(names);else controller.ShowModelPartsCommand(names);break;
            case "Remove":if(geometry)controller.RemoveGeometryPartsCommand(names);else controller.RemoveModelPartsCommand(names);break;
            default:throw new NotSupportedException("Unknown geometry/mesh command: "+operation);
        }
    }
    public void SetActive(string[] names,bool active)=>controller.ActivateDeactivateMultipleCommand(names.Select(n=>(NamedClass)controller.GetMeshSetupItem(n)).ToArray(),active,names.Select(_=>(string)null).ToArray());
    public Task FindEdges(string[] names,double angle)=>Task.Run(()=> {if(controller.CurrentView==ViewGeometryModelResults.Geometry)controller.FindEdgesByAngleForGeometryPartsCommand(names,angle);else controller.FindEdgesByAngleForModelPartsCommand(names,angle);});
    public Task Export(string[] names,string path,string format)=>Task.Run(()=> {
        if(controller.CurrentView==ViewGeometryModelResults.Geometry)controller.ExportGeometryPartsCommand(names,path,Enum.Parse<GeometryExportFormatEnum>(format));
        else controller.ExportMeshPartsCommand(names,path,Enum.Parse<MeshExportFormatEnum>(format));
    });
    public string[] ExportFormats=>controller.CurrentView==ViewGeometryModelResults.Geometry?Enum.GetNames<GeometryExportFormatEnum>():Enum.GetNames<MeshExportFormatEnum>();
    public Task Renumber(bool nodes,int start)=>Task.Run(()=>{if(nodes)controller.RenumberNodesCommand(start);else controller.RenumberElementsCommand(start);});
    public Task UpdateCoordinates(string path)=>Task.Run(()=>controller.UpdateNodalCoordinatesFromFileCommand(path));
    public bool HasGeometryHistory=>controller.Model.Geometry?.Parts.Count>0 ||
        controller.GetCommands().OfType<PrePoMax.Commands.IImportFileCommand>().Any(command=>
            new[]{".brep",".step",".stp",".iges",".igs",".stl"}.Contains(Path.GetExtension(command.FileName).ToLowerInvariant()));
    public GeometryAnalysisSession Analyze(string[] names)=>new(controller,names);
    public string[] CompoundNames=>controller.Model.Geometry.Parts.Values.OfType<CompoundGeometryPart>().Select(p=>p.Name).ToArray();
    public string[] Bodies(string compound)=>controller.GetSubParts(compound).Select(p=>p.Name).ToArray();
    public string[] SubParts(string compound)=>((CompoundGeometryPart)controller.GetGeometryPart(compound)).CellSubPartNames?.Distinct().ToArray()??[];
    public Task GroupCells(string compound,string[] names,string target)=>Task.Run(()=>controller.GroupSplitCellsCommand(compound,names,target));
    public Task FuseBodies(string compound,string[] names)=>Task.Run(()=>controller.FuseBodiesCommand(compound,names));
    public Task RenameSubPart(string compound,string name,string replacement)=>Task.Run(()=>controller.RenameSplitSubPartCommand(compound,name,replacement));
    public Task Undo()=>Task.Run(()=>controller.UndoHistory(PrePoMax.Commands.RegenerateTypeEnum.All));
    public Task Redo()=>Task.Run(controller.RedoHistory);
    public void Cancel()=>controller.StopExecutableJob();
}

// FrmAnalyzeGeometry presents these original Controller measurements and display
// filters. This adapter contains its default threshold formatting, no geometry math.
public sealed class GeometryAnalysisSession(Controller controller,string[] names)
{
    public double ShortestEdge {get;private set;}
    public double ClosestEdges {get;private set;}
    public double SmallestFace {get;private set;}
    public double EdgeLimit {get;set;}
    public double DistanceLimit {get;set;}
    public double FaceLimit {get;set;}
    public double Angle {get;set;}=175;
    public bool ShowEdges {get;set;}=true;
    public bool ShowCloseEdges {get;set;}=true;
    public bool ShowFaces {get;set;}=true;
    public bool ShowVertices {get;set;}
    public string LengthUnit=>controller.Model.UnitSystem.LengthUnitAbbreviation;
    public string AreaUnit=>controller.Model.UnitSystem.AreaUnitAbbreviation;
    public Task Measure()=>Task.Run(()=> {
        if(names==null || names.Length==0)throw new CaeException("No parts were selected for analysis.");
        ShortestEdge=controller.GetShortestEdgeLen(names);
        ClosestEdges=controller.GetClosestUnConnectedEdgesDistance(names);
        SmallestFace=controller.GetSmallestFace(names);
        // Same control defaults as FrmAnalyzeGeometry_VisibleChanged.
        EdgeLimit=DefaultLimit(ShortestEdge);DistanceLimit=DefaultLimit(ClosestEdges);FaceLimit=DefaultLimit(SmallestFace);
    });
    static double DefaultLimit(double value)=>value>0?Math.Pow(10,Math.Ceiling(Math.Log10(value))):0;
    public Task Show()=>Task.Run(()=> {
        controller.ClearAllSelection();
        if(ShowEdges)controller.ShowShortEdges(EdgeLimit,names);
        if(ShowFaces)controller.ShowSmallFaces(FaceLimit,names);
        if(ShowCloseEdges)controller.ShowCloseUnConnectedEdges(DistanceLimit,names);
        if(ShowVertices)controller.ShowVerticesWithLargeAngle(names,Angle);
    });
}
