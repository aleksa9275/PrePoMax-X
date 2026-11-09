using System.Collections;
using System.ComponentModel;
using System.Reflection;
using CaeGlobals;
using CaeMesh;
using CaeModel;
using PrePoMax;

namespace PrePoMaxX.UI.OriginalForms;

// Data consumed by Qt, not replacement WinForms controls. Generated members
// retain the original form's full factory, validation and command bodies.
public sealed class EditorChoice(string text)
{
    public string Text {get;}=text;
    public object Tag {get;set;}
}
public abstract class FormRule
{
    protected readonly Controller _controller;
    protected readonly string _stepName;
    protected bool _propertyItemChanged;
    protected readonly List<EditorChoice> choices=[];
    protected object SelectedObject;
    public string OriginalName {get;}
    public object View=>SelectedObject;
    public abstract object Item {get;}
    public EditorChoice[] Choices=>choices.ToArray();
    protected FormRule(Controller controller,string step,string name) {_controller=controller;_stepName=step;OriginalName=name;}
    protected static void CheckName(string oldName,string name,ICollection<string> names,string label)=>UserControls.PropertyNameValidation.CheckName(oldName,name,names,label);
    protected abstract void OnApply(bool addNew);
    protected abstract void OnSelect(object view);
    public void Select(int index)
    {
        if(OriginalName!=null)throw new InvalidOperationException("An existing item's type cannot be changed.");
        SelectedObject=choices[index].Tag;
        OnSelect(SelectedObject);
        _propertyItemChanged=true;
    }
    public virtual PropertySheet Properties=>new(SelectedObject,changed:Changed);
    public virtual void Changed()
    {
        _propertyItemChanged=true;
        // The original setters update most visibility. Steps and BCs also have
        // a property-grid change callback which calls their UpdateVisibility.
        SelectedObject?.GetType().GetMethod("UpdateVisibility",Type.EmptyTypes)?.Invoke(SelectedObject,null);
    }
    public virtual void SetPoint(string property,int[] nodeIds)
    {
        if(nodeIds==null || nodeIds.Length!=1)throw new CaeException("Pick exactly one mesh node first.");
        var node=_controller.Model.Mesh.Nodes[nodeIds[0]];
        string suffix=property=="FirstPointItemSet"?"1":property=="SecondPointItemSet"?"2":property=="ThirdPointItemSet"?"3":"";
        foreach(var coordinate in new[]{("X",node.X),("Y",node.Y),("Z",node.Z)})
        {
            var descriptor=TypeDescriptor.GetProperties(SelectedObject)[coordinate.Item1+suffix]??throw new CaeException("This point uses its original region selection controls.");
            descriptor.SetValue(SelectedObject,new EquationString(coordinate.Item2.ToString(System.Globalization.CultureInfo.InvariantCulture)));
        }
        Changed();
    }
    public string[] CollectionNames=>Properties.CollectionNames;
    public CollectionSheet Collection(string name)=>Properties.Collection(name);
    public virtual string[] SelectionPrefixes
    {
        get
        {
            if(Item==null)return Array.Empty<string>();
            if(Item is FeNodeSet || Item is FeElementSet || Item is FeSurface)return new[]{""};
            return new[]{"","Master","Slave","Center","PointX","PointXY"}.Where(prefix=>Item.GetType().GetProperty(prefix+"CreationData")!=null).ToArray();
        }
    }
    public void Commit() {OnApply(false);}
    protected virtual string[] Names(string key)=>key switch
    {
        "materialNames"=>_controller.GetMaterialNames(),
        "partNames"=>_controller.GetModelPartNames(),
        "nodeSetNames"=>_controller.GetUserNodeSetNames(),
        "elementSetNames"=>_controller.GetUserElementSetNames(),
        "surfaceNames"=>_controller.GetUserSurfaceNames(),
        "cyclicSurfaceNames"=>_controller.GetUserSurfaceNames(FeSurfaceType.Element),
        "referencePointNames"=>_controller.GetModelReferencePointNames(),
        "coordinateSystemNames"=>_controller.GetModelCoordinateSystemNames(),
        "amplitudeNames"=>_controller.GetAmplitudeNames(),
        "distributionNames"=>_controller.GetDistributionNamesIncludingDefault(),
        "surfaceInteractionNames"=>_controller.GetSurfaceInteractionNames(),
        "contactPairNames"=>_controller.GetContactPairNames(),
        _=>throw new NotSupportedException("Original dropdown requires a provider: "+key)
    }??[];
    protected virtual void Configure(object view)
    {
        foreach(var method in view.GetType().GetMethods().Where(m=>(m.Name=="PopulateDropDownLists" || m.Name=="PopulateDropDownList") && m.GetParameters().All(p=>p.ParameterType==typeof(string[]))))
        {
            var args=method.GetParameters().Select(p=>(object)Names(p.Name)).ToArray();
            // Preserve the original section form's allowed region families.
            if(view is ViewSection)
            {
                var section=((ViewSection)view).GetBase();
                for(int i=0;i<method.GetParameters().Length;i++)
                {
                    string name=method.GetParameters()[i].Name;
                    bool allowed=section is PointMassSection?name is "nodeSetNames" or "referencePointNames":section is DistributedMassSection?name=="surfaceNames":name is "materialNames" or "partNames" or "elementSetNames";
                    if(!allowed)args[i]=null;
                }
            }
            method.Invoke(view,args);
        }
    }
    protected static void InitializeSelectionData(object item)
    {
        if(item is FeNodeSet nodes && nodes.CreationData==null && nodes.Labels!=null)nodes.CreationData=Ids(vtkSelectItem.Node,nodes.Labels);
        if(item is FeElementSet elements && elements.CreationData==null && elements.Labels!=null)elements.CreationData=Ids(vtkSelectItem.Element,elements.Labels);
        if(item is FeSurface surface && surface.CreationData==null && surface.FaceIds!=null)surface.CreationData=Ids(vtkSelectItem.Surface,surface.FaceIds);
    }
    static Selection Ids(vtkSelectItem kind,int[] ids)
    {
        var selection=new Selection {CurrentView=(int)ViewGeometryModelResults.Model,SelectItem=kind};
        selection.Add(new SelectionNodeIds(vtkSelectOperation.None,false,ids));
        return selection;
    }
    public virtual void SetSelection(int[] ids,Selection source=null,string prefix="")
    {
        var item=Item;
        vtkSelectItem kind=item is FeNodeSet?vtkSelectItem.Node:item is FeElementSet?vtkSelectItem.Element:item is FeSurface?vtkSelectItem.Surface:source?.SelectItem??throw new ArgumentException("A region needs an explicit selection kind.");
        if(source!=null && source.SelectItem!=kind)throw new CaeException("The picked selection has a different item type.");
        source=source?.DeepCopy(true,false)??Ids(kind,ids);
        if(item is FeNodeSet nodes) {nodes.Labels=ids;nodes.CreationData=source;}
        else if(item is FeElementSet elements) {elements.Labels=ids;elements.CreationData=source;}
        else if(item is FeSurface surface) {surface.FaceIds=ids;surface.CreationData=source;surface.CreatedFrom=FeSurfaceCreatedFrom.Selection;}
        else
        {
            Type type=item.GetType();
            var creation=type.GetProperty(prefix+"CreationData")??throw new CaeException("This definition has no "+prefix+" selection region.");
            creation.SetValue(item,source);
            type.GetProperty(prefix+"CreationIds").SetValue(item,ids);
            var region=type.GetProperty(prefix+"RegionType");
            if(region!=null)region.SetValue(item,RegionTypeEnum.Selection);
            else if(item is CoordinateSystem coordinate) _controller.UpdateModelCoordinateSystem(coordinate);
        }
        if(item is FeReferencePoint point)_controller.UpdateModelReferencePoint(point);
        Changed();
    }
    protected static void RestoreSelectionRegions(object item)
    {
        // Original OnPrepareForm presents owned internal regions as selections.
        foreach(string prefix in new[]{"","Master","Slave"})
        {
            Type type=item.GetType();
            var creation=type.GetProperty(prefix+"CreationData");
            var region=type.GetProperty(prefix+"RegionType");
            if(creation?.GetValue(item)!=null && region?.CanWrite==true)region.SetValue(item,RegionTypeEnum.Selection);
        }
    }
}
