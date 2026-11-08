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
    public bool TemperatureDependent {get;}
    public string[] PropertyNames=>views.Select(v=>v.Name).ToArray();
    public MaterialEditSession(Controller controller,string name)
    {
        this.controller=controller;originalName=name;
        var material=controller.GetMaterial(name).DeepClone();
        Name=material.Name;Description=material.Description;initialDescription=material.Description;TemperatureDependent=material.TemperatureDependent;
        views=MaterialEditor.CreateViews(material).ToList();
    }
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
        bool apply=changed || Name!=originalName || (Description??"")!=(initialDescription??"");
        if(apply)controller.ReplaceMaterialCommand(originalName,material.DeepClone());
        committed=true;
        return apply;
    }
}
