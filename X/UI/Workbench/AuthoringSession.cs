using System.Reflection;
using CaeGlobals;
using CaeMesh;
using CaeModel;
using PrePoMax;
using PrePoMaxX.UI.OriginalForms;

namespace PrePoMaxX.UI;
public sealed class ModelTreeEntry
{
    public string Family {get;init;}
    public string Step {get;init;}
    public string Name {get;init;}
    public string Type {get;init;}
    public bool Group {get;init;}
    public string FolderId {get;init;}
    public ModelTreeEntry[] Children {get;init;}=[];
    // Original ModelTree node state (OriginalModelTree): displayed text, image key, colours, menu fields.
    public string Text {get;set;}
    public string Icon {get;set;}
    public bool Gray {get;set;}
    public bool Invalid {get;set;}
    public string[] Menu {get;set;}=[];
    public NamedClass Item {get;set;}
}
public sealed class AuthoringSession(Controller controller)
{
    public static string[] Families=>["Node sets","Element sets","Surfaces","Reference points","Coordinate systems","Materials","Sections","Constraints","Surface interactions","Contact pairs","Distributions","Amplitudes","Initial conditions","Steps"];
    public static string[] StepFamilies=>["Boundary conditions","Loads","Defined fields","History outputs","Field outputs"];
    public FormRule Edit(string family,string step=null,string name=null)=>FormRules.Create(family,controller,step,name);
    public MaterialEditSession Material(string name=null)=>new(controller,name);
    public InteractionEditSession Interaction(string name=null)=>new(controller,name);
    public ParameterEditSession Parameters()=>new(controller);
    public ControlsEditSession Controls(string step)=>new(controller,step);
    public ModelTreeEntry[] Tree
    {
        get
        {
            var rows=new List<ModelTreeEntry> {new(){Family="Model properties",Name=controller.Model.Name,Type="Model"},new(){Family="Parameters",Name="Parameters",Type="Parameters"}};
            rows.Add(new ModelTreeEntry {Family="Parts",Name="Parts",Group=true,Children=Children("Parts",null)});
            foreach(string family in Families)rows.Add(new ModelTreeEntry {Family=family,Name=family,Group=true,Children=Children(family,null)});
            return rows.ToArray();
        }
    }
    ModelTreeEntry Entry(string family,string step,NamedClass item)=>OriginalModelTree.Annotate(new() {Family=family,Step=step,Name=item.Name,Type=item.GetType().Name,
        Children=item is Step analysis?StepFamilies.Select(f=>new ModelTreeEntry {Family=f,Step=item.Name,Name=f,Group=true,Children=Children(f,item.Name)}).Append(new ModelTreeEntry {Family="Solution controls",Step=item.Name,Name="Solution controls",Type="Controls"}).ToArray():[]},item,OriginalModelTree.Model,controller);
    IEnumerable<NamedClass> Items(string family,string step)
    {
        var model=controller.Model;var mesh=model.Mesh;
        return family switch {
            "Parts"=>mesh?.Parts.Values??[],
            "Node sets"=>mesh?.NodeSets.Values.Where(i=>!i.Internal)??[],
            "Element sets"=>mesh?.ElementSets.Values.Where(i=>!i.Internal)??[],
            "Surfaces"=>mesh?.Surfaces.Values.Where(i=>!i.Internal)??[],
            "Reference points"=>mesh?.ReferencePoints.Values.Where(i=>!i.Internal)??[],
            "Coordinate systems"=>mesh?.CoordinateSystems.Values.Where(i=>!i.Internal)??[],
            "Materials"=>model.Materials.Values,
            "Sections"=>model.Sections.Values,
            "Constraints"=>model.Constraints.Values,
            "Surface interactions"=>model.SurfaceInteractions.Values,
            "Contact pairs"=>model.ContactPairs.Values,
            "Distributions"=>model.Distributions.Values,
            "Amplitudes"=>model.Amplitudes.Values,
            "Initial conditions"=>model.InitialConditions.Values,
            "Steps"=>controller.GetAllSteps(),
            "Boundary conditions"=>controller.GetStep(step).BoundaryConditions.Values,
            "Loads"=>controller.GetStep(step).Loads.Values,
            "Defined fields"=>controller.GetStep(step).DefinedFields.Values,
            "History outputs"=>controller.GetStep(step).HistoryOutputs.Values,
            "Field outputs"=>controller.GetStep(step).FieldOutputs.Values,
            _=>[]
        };
    }
    IOrderedDictionaryItemLayout<string> Layout(string family,string step)
    {
        object owner=StepFamilies.Contains(family)?controller.GetStep(step):new[]{"Parts","Node sets","Element sets","Surfaces","Reference points","Coordinate systems"}.Contains(family)?controller.Model.Mesh:controller.Model;
        string property=family switch {"Parts"=>"Parts","Reference points"=>"ReferencePoints","Coordinate systems"=>"CoordinateSystems","Defined fields"=>"DefinedFields",_=>plural.TryGetValue(family,out var value)?value:null};
        return property==null?null:owner?.GetType().GetProperty(property)?.GetValue(owner) as IOrderedDictionaryItemLayout<string>;
    }
    ModelTreeEntry[] Children(string family,string step)
    {
        var items=Items(family,step).ToDictionary(i=>i.Name,StringComparer.OrdinalIgnoreCase);
        var layout=Layout(family,step);
        if(layout==null)return items.Values.Select(i=>Entry(family,step,i)).ToArray();
        ModelTreeEntry[] Build(IEnumerable<OrderedDictionaryItemNode<string>> nodes)=>nodes.SelectMany(n=>n.IsGroup?new[]{new ModelTreeEntry {Family=family,Step=step,Name=n.Name,Group=true,FolderId=n.Id.ToString(),Children=Build(n.Children),Icon="Folder.ico"}}:items.TryGetValue(n.Key,out var item)?new[]{Entry(family,step,item)}:Array.Empty<ModelTreeEntry>()).ToArray();
        return Build(layout.GetItemLayoutSnapshot().Nodes);
    }
    Type CollectionType(string family,string step)
    {
        return family switch {"Parts"=>typeof(BasePart),"Node sets"=>typeof(FeNodeSet),"Element sets"=>typeof(FeElementSet),"Surfaces"=>typeof(FeSurface),"Reference points"=>typeof(FeReferencePoint),"Coordinate systems"=>typeof(CoordinateSystem),"Materials"=>typeof(Material),"Sections"=>typeof(Section),"Constraints"=>typeof(Constraint),"Surface interactions"=>typeof(SurfaceInteraction),"Contact pairs"=>typeof(ContactPair),"Distributions"=>typeof(Distribution),"Amplitudes"=>typeof(Amplitude),"Initial conditions"=>typeof(InitialCondition),"Boundary conditions"=>typeof(BoundaryCondition),"Loads"=>typeof(Load),"History outputs"=>typeof(HistoryOutput),"Field outputs"=>typeof(FieldOutput),"Defined fields"=>typeof(DefinedField),_=>throw new NotSupportedException("This collection cannot contain folders.")};
    }
    public bool CanOrganize(string family,string step)=>Layout(family,step)!=null;
    int ChildCount(string family,string step,string id,string[] excluded=null)
    {
        var roots=Layout(family,step).GetItemLayoutSnapshot().Nodes;
        IEnumerable<OrderedDictionaryItemNode<string>> Flatten(IEnumerable<OrderedDictionaryItemNode<string>> nodes)=>nodes.SelectMany(n=>new[]{n}.Concat(Flatten(n.Children)));
        var nodes=id==null?roots:Flatten(roots).Single(n=>n.Id==Guid.Parse(id)).Children;
        return nodes.Count(n=>!n.IsItem || excluded==null || !excluded.Contains(n.Key));
    }
    public void CreateFolder(string family,string step,string name,string[] items,string parentId=null)
    {
        var change=UserControls.OrderedDictionaryTreeLayoutChange.CreateGroup(UserControls.ViewType.Model,CollectionType(family,step),step,items,Guid.NewGuid(),parentId==null?null:Guid.Parse(parentId),ChildCount(family,step,parentId),name);
        controller.ChangeOrderedDictionaryItemLayoutCommand(change);
    }
    public void RenameFolder(string family,string step,string id,string name)=>controller.ChangeOrderedDictionaryItemLayoutCommand(UserControls.OrderedDictionaryTreeLayoutChange.RenameGroup(UserControls.ViewType.Model,CollectionType(family,step),step,Guid.Parse(id),name));
    public void RemoveFolder(string family,string step,string id)=>controller.ChangeOrderedDictionaryItemLayoutCommand(UserControls.OrderedDictionaryTreeLayoutChange.RemoveGroups(UserControls.ViewType.Model,CollectionType(family,step),step,[Guid.Parse(id)]));
    public void MoveToFolder(string family,string step,string[] names,string folderId)=>controller.ChangeOrderedDictionaryItemLayoutCommand(UserControls.OrderedDictionaryTreeLayoutChange.MoveItems(UserControls.ViewType.Model,CollectionType(family,step),step,names,folderId==null?null:Guid.Parse(folderId),ChildCount(family,step,folderId,names)));
    public void Move(string family,string step,string name,int offset)
    {
        if(family=="Steps") {int index=Array.IndexOf(controller.GetStepNames(),name);controller.MoveStepsCommand([name],Math.Max(0,index+offset));return;}
        var layout=Layout(family,step)??throw new NotSupportedException();
        (Guid? Parent,int Index) Find(IEnumerable<OrderedDictionaryItemNode<string>> nodes,Guid? parent)
        {
            int index=0;foreach(var node in nodes) {if(node.IsItem && node.Key==name)return(parent,index);if(node.IsGroup) {var found=Find(node.Children,node.Id);if(found.Index>=0)return found;}index++;}return(null,-1);
        }
        var position=Find(layout.GetItemLayoutSnapshot().Nodes,null);
        controller.ChangeOrderedDictionaryItemLayoutCommand(UserControls.OrderedDictionaryTreeLayoutChange.MoveItems(UserControls.ViewType.Model,CollectionType(family,step),step,[name],position.Parent,Math.Max(0,Math.Min(ChildCount(family,step,position.Parent?.ToString(),[name]),position.Index+offset))));
    }
    static readonly Dictionary<string,string> plural=new() {
        ["Node sets"]="NodeSets",["Element sets"]="ElementSets",["Surfaces"]="Surfaces",["Reference points"]="ModelReferencePoints",["Coordinate systems"]="ModelCoordinateSystems",
        ["Materials"]="Materials",["Sections"]="Sections",["Constraints"]="Constraints",["Surface interactions"]="SurfaceInteractions",["Contact pairs"]="ContactPairs",["Distributions"]="Distributions",["Amplitudes"]="Amplitudes",["Initial conditions"]="InitialConditions",["Steps"]="Steps",
        ["Boundary conditions"]="BoundaryConditions",["Loads"]="Loads",["Defined fields"]="DefinedFieldsForStep",["History outputs"]="HistoryOutputs",["Field outputs"]="FieldOutputs"
    };
    public void Remove(string family,string step,string[] names)=>Command("Remove",family,step,names);
    public void Duplicate(string family,string step,string[] names)=>Command("Duplicate",family,step,names);
    void Command(string action,string family,string step,string[] names)
    {
        if(names.Length==0)return;
        if(!plural.TryGetValue(family,out string suffix))throw new NotSupportedException("This tree item has no "+action+" command.");
        object[] args=StepFamilies.Contains(family)?[step,names]:[names];
        var method=typeof(Controller).GetMethods().SingleOrDefault(m=>m.Name==action+suffix+"Command" && m.GetParameters().Length==args.Length)??throw new NotSupportedException("Original command unavailable: "+action+suffix);
        try {method.Invoke(controller,args);}catch(TargetInvocationException error) {System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(error.InnerException??error).Throw();}
    }
    public void Activate(string family,string step,string[] names,bool active)
    {
        var items=Items(family,step).Where(i=>names.Contains(i.Name)).ToArray();
        controller.ActivateDeactivateMultipleCommand(items,active,items.Select(_=>step).ToArray());
    }
}
