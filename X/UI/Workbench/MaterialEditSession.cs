using System.Collections;
using CaeGlobals;
using CaeModel;
using PrePoMax;
using PrePoMax.PropertyViews;

namespace PrePoMaxX.UI;

// An isolated draft, as in FrmMaterial.Material. Cancel never touches the model.
public sealed class MaterialEditSession
{
    readonly Controller controller;
    readonly string originalName;
    readonly List<ViewMaterialProperty> views=[];
    bool committed;
    bool changed;
    readonly string initialDescription;
    public string Name {get;set;}
    public string Description {get;set;}
    bool temperatureDependent;
    public bool TemperatureDependent
    {
        get=>temperatureDependent;
        set {if(temperatureDependent==value)return;temperatureDependent=value;changed=true;foreach(var view in views.OfType<ViewThermalExpansion>())view.SetTemperatureDependence(value);}
    }
    public static string[] AvailableProperties=>MaterialEditor.PropertyTemplates().Select(p=>p.Key).ToArray();
    public string[] PropertyNames=>views.Select(v=>v.Name).ToArray();
    public MaterialEditSession(Controller controller,string name)
    {
        this.controller=controller;originalName=name;
        var material=name==null?new Material(controller.GetMaterialNames().GetNextNumberedKey("Material")):controller.GetMaterial(name).DeepClone();
        Name=material.Name;Description=material.Description;initialDescription=material.Description;TemperatureDependent=material.TemperatureDependent;
        views=MaterialEditor.CreateViews(material).ToList();
        changed=false;
    }
    public void AddProperty(int index)
    {
        MaterialProperty property=MaterialEditor.PropertyTemplates()[index].Value;
        bool elastic=property is Elastic || property is ElasticEngineeringConstants || property is ElasticLamina;
        if(views.Any(v=>v.Name==AvailableProperties[index]) || (elastic && views.Any(v=>v is ViewElastic || v is ViewElasticEngineeringConstants || v is ViewElasticLamina || v is ViewElasticWithDensity)))throw new CaeException("A material can contain only one property of the selected family.");
        var material=new Material(Name);material.TemperatureDependent=TemperatureDependent;material.AddProperty(property);
        views.AddRange(MaterialEditor.CreateViews(material));changed=true;
    }
    public void RemoveProperty(int index) {views.RemoveAt(index);changed=true;}
    public void MoveProperty(int index,int offset)
    {
        int target=index+offset;if(target<0 || target>=views.Count)return;
        var view=views[index];views.RemoveAt(index);views.Insert(target,view);changed=true;
    }
    public CollectionSheet Table(int index)=>Points(index)==null?null:new(Points(index),()=>changed=true,p=>TemperatureDependent || p.Name!="TemperatureEq");
    public PropertySheet Properties(int index)=>new(views[index],changed:()=>changed=true);
    IList Points(int index)=>(IList)views[index].GetType().GetProperty("DataPoints")?.GetValue(views[index]);
    public int RowCount(int index)=>Points(index)?.Count??0;
    public PropertySheet Row(int index,int row)=>new(Points(index)[row],p=>TemperatureDependent || p.Name!="TemperatureEq",()=>changed=true);
    public bool ShowProperties(int index)=>!TemperatureDependent || views[index] is ViewThermalExpansion || views[index] is ViewPlastic || views[index] is ViewSlipWear || views[index] is ViewElasticWithDensity;
    public bool ShowTable(int index)=>Points(index)!=null && (TemperatureDependent || views[index] is ViewPlastic);
    public bool Commit()
    {
        if(committed)throw new InvalidOperationException("This draft was already applied.");
        UserControls.PropertyNameValidation.CheckName(originalName,Name,controller.GetMaterialNames(),"material");
        var material=MaterialEditor.Build(Name,Description,TemperatureDependent,views);
        bool apply=originalName==null || changed || Name!=originalName || (Description??"")!=(initialDescription??"");
        if(originalName==null)controller.AddMaterialCommand(material.DeepClone());
        else if(apply)controller.ReplaceMaterialCommand(originalName,material.DeepClone());
        committed=true;
        return apply;
    }
}
