using System.ComponentModel;
using CaeGlobals;
using CaeMesh;
using PrePoMax;

namespace PrePoMaxX.UI.OriginalForms;

// Toolkit-neutral draft shell. Engineering behavior is in the generated original
// members and original descriptors/Controller. Each commit is one original flow.
public abstract class GeometryFormRule(Controller controller,string name):FormRule(controller,null,name)
{
    protected bool Enabled {get;set;}=true;
    protected virtual Task ApplyAsync(bool addNew)=>throw new NotSupportedException();
    public Task CommitInBackground()=>Task.Run(Commit);
    public Task PreviewInBackground()=>Task.Run(Preview);
    public override PropertySheet Properties=>new(SelectedObject,changedProperty:PropertyChanged);
    protected virtual void PropertyChanged(string property)=>Changed();
    public virtual bool CanPreview=>GetType().GetMethod(nameof(Preview)).DeclaringType!=typeof(GeometryFormRule);
    public virtual void Preview()=>throw new NotSupportedException("This operation has no preview.");
    public virtual void Reset()=>throw new NotSupportedException("This operation has no reset.");
    public virtual bool CanReset=>GetType().GetMethod(nameof(Reset)).DeclaringType!=typeof(GeometryFormRule);
    public vtkSelectItem SelectionKind(string prefix="")=>Item switch {
        LocalMeshSize=>vtkSelectItem.Geometry,
        SweepMesh sweep when sweep.SourceType!=SweepSourceTypeEnum.Automatic=>vtkSelectItem.GeometrySurface,
        RemeshingParameters=>vtkSelectItem.Element,
        MeshSetupItem=>vtkSelectItem.Part,
        GeometryFeature feature=>prefix.Length>0?vtkSelectItem.Geometry:feature.SplitType==SplitTypeEnum.Solid?vtkSelectItem.Part:vtkSelectItem.GeometrySurface,
        FaceOffset or GeometrySelection=>vtkSelectItem.GeometrySurface,
        GeometryRepair or PeriodicFaceSplit=>vtkSelectItem.Part,
        MergeCoincidentNodes=>vtkSelectItem.Node,
        SplitPartMeshData=>prefix=="Base part"?vtkSelectItem.Part:vtkSelectItem.Surface,
        PrePoMax.Forms.ViewBoundaryLayer=>vtkSelectItem.Geometry,
        _=>throw new CaeException("This editor does not use a region selection.")
    };
    protected void ValidateSelection(Selection source,string prefix="")
    {
        if(source==null || source.CurrentView!=(int)_controller.CurrentView || source.SelectItem!=SelectionKind(prefix))
            throw new CaeException("Pick the region with this editor's Pick control before assigning it.");
    }
    public void PrepareSelection(string prefix="")
    {
        _controller.ClearAllSelection();
        _controller.SelectItem=SelectionKind(prefix);
        if(Item is GeometryFeature feature)
        {
            _controller.GeometryFeaturePointPicking=prefix=="Splitter"?Controller.GetSplitGeometryPointPicking(feature):GeometryFeaturePointPickingEnum.None;
            _controller.PickCompoundSubPartsSeparately=prefix.Length==0 && feature.SplitType==SplitTypeEnum.Solid;
        }
    }
    public void Close()
    {
        _controller.GeometryFeaturePointPicking=GeometryFeaturePointPickingEnum.None;
        _controller.PickCompoundSubPartsSeparately=false;
        _controller.Selection.LimitSelectionToFirstPart=false;
        _controller.Selection.LimitSelectionToFirstMesherType=false;
        _controller.Clear3DSelection();
    }
    protected Selection CopySelection(Selection source)=>source?.DeepCopy(true,false)??throw new CaeException("Pick a selection before assigning the region.");
    protected void SetCreation(object item,int[] ids,Selection source)
    {
        var type=item.GetType();
        (type.GetProperty("CreationIds")??type.GetProperty("GeometryIds")??throw new NotSupportedException("This operation needs its region-specific picker.")).SetValue(item,ids);
        type.GetProperty("CreationData")?.SetValue(item,CopySelection(source));
    }
    public override void SetSelection(int[] ids,Selection source=null,string prefix="")
    {
        ValidateSelection(source,prefix);
        SetCreation(Item,ids,source);
        var region=Item.GetType().GetProperty("RegionType");
        if(region?.CanWrite==true)region.SetValue(Item,RegionTypeEnum.Selection);
        Changed();
    }
    public override void SetPoint(string property,int[] nodeIds)
    {
        if(nodeIds==null || nodeIds.Length!=1)throw new CaeException("Pick exactly one node first.");
        var node=_controller.DisplayedMesh.Nodes[nodeIds[0]];
        string prefix=property.Replace("ItemSet","");
        if(prefix=="ScaleCenter")prefix="Center";
        string suffix=prefix=="StartPoint"?"1":prefix=="EndPoint"?"2":"";
        foreach(var coordinate in new[]{("X",node.X),("Y",node.Y),("Z",node.Z)})
        {
            var descriptor=TypeDescriptor.GetProperties(View)[suffix.Length>0?coordinate.Item1+suffix:prefix+coordinate.Item1];
            if(descriptor==null)throw new CaeException("Use this operation's splitter selection or coordinate fields.");
            descriptor.SetValue(View,coordinate.Item2);
        }
        Changed();
    }
}
