using System.Collections;
using CaeGlobals;
using CaeModel;
using PrePoMax;

namespace PrePoMaxX.UI;
public sealed class InteractionEditSession
{
    readonly Controller controller;
    readonly string originalName;
    readonly List<ViewSurfaceInteractionProperty> views=[];
    bool changed;
    public string Name {get;set;}
    public string Description {get;set;}="";
    public static string[] AvailableProperties=>["Surface Behavior","Friction","Gap Conductance"];
    public string[] PropertyNames=>views.Select(v=>v.Name).ToArray();
    public InteractionEditSession(Controller controller,string name)
    {
        this.controller=controller;originalName=name;
        var item=name==null?new SurfaceInteraction(controller.GetSurfaceInteractionNames().GetNextNumberedKey("Surface_Interaction")):controller.GetSurfaceInteraction(name).DeepClone();
        Name=item.Name;
        foreach(var property in item.Properties)views.Add(SurfaceInteractionEditor.CreateView(property));
    }
    public void AddProperty(int index)
    {
        var view=SurfaceInteractionEditor.CreateView(index switch {0=>new SurfaceBehavior(),1=>new Friction(),2=>new GapConductance(),_=>throw new ArgumentOutOfRangeException()});
        if(views.Any(v=>v.GetType()==view.GetType()))throw new CaeException("This interaction property already exists.");
        views.Add(view);changed=true;
    }
    public void RemoveProperty(int index) {views.RemoveAt(index);changed=true;}
    public void MoveProperty(int index,int offset)
    {
        int target=index+offset;if(target<0 || target>=views.Count)return;
        var view=views[index];views.RemoveAt(index);views.Insert(target,view);changed=true;
    }
    public PropertySheet Properties(int index)=>new(views[index],changed:()=>changed=true);
    public bool ShowProperties(int index)=>true;
    public bool ShowTable(int index)=>views[index] is ViewSurfaceBehavior sb?sb.PressureOverclosureType==PressureOverclosureEnum.Tabular:views[index] is ViewGapConductance;
    public CollectionSheet Table(int index)
    {
        var points=(IList)views[index].GetType().GetProperty("DataPoints")?.GetValue(views[index]);
        return points==null?null:new CollectionSheet(points,()=>changed=true);
    }
    public bool Commit()
    {
        UserControls.PropertyNameValidation.CheckName(originalName,Name,controller.GetSurfaceInteractionNames(),"surface interaction");
        var item=SurfaceInteractionEditor.Build(Name,views);
        if(originalName==null)controller.AddSurfaceInteractionCommand(item.DeepClone());
        else if(changed || originalName!=Name)controller.ReplaceSurfaceInteractionCommand(originalName,item.DeepClone());
        return changed || originalName!=Name;
    }
}
