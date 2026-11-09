using CaeGlobals;using CaeModel;using PrePoMax;using PrePoMax.Forms;
namespace PrePoMaxX.UI;
// Original .lib graph, units, equation restriction and Controller commands.
public sealed class MaterialLibrarySession(Controller controller)
{
    public MaterialLibraryItem Root {get;private set;}=new("Materials");
    public string FileName {get;private set;}
    readonly List<Material> model=controller.Model.Materials.Values.ToList();
    bool modelChanged;
    public Material[] ModelMaterials=>model.ToArray();
    public void New(string file){Root=new("Materials");FileName=Path.GetFullPath(file);Save();controller.AddMaterialLibraryFile(FileName);}
    public void Open(string file){Root=Tools.LoadDumpFromFile<MaterialLibraryItem>(Path.GetFullPath(file));FileName=Path.GetFullPath(file);controller.AddMaterialLibraryFile(FileName);}
    public void Use(string file,MaterialLibraryItem root){FileName=Path.GetFullPath(file);Root=root??throw new ArgumentNullException(nameof(root));}
    public void Save()=>Root.DumpToFile(FileName??throw new CaeException("Choose a library file first."));
    public void Unregister()=>controller.RemoveMaterialLibraryFile(FileName);
    public MaterialLibraryItem Category(MaterialLibraryItem parent,string name)
    {
        if(parent.Tag!=null)throw new CaeException("Select a library category.");
        ValidateName(parent,name,null);var item=new MaterialLibraryItem(name);parent.Items.Add(item);return item;
    }
    static void ValidateName(MaterialLibraryItem parent,string name,MaterialLibraryItem current){_=new Material(name);if(parent.Items.Any(i=>i!=current && i.Name==name))throw new CaeException("The category already contains the node named '"+name+"'.");}
    public void Rename(MaterialLibraryItem parent,MaterialLibraryItem item,string name){ValidateName(parent,name,item);item.Name=name;if(item.Tag!=null)item.Tag.Name=name;}
    public void Remove(MaterialLibraryItem parent,MaterialLibraryItem item)=>parent.Items.Remove(item);
    public void Move(MaterialLibraryItem parent,MaterialLibraryItem item,int delta){int index=parent.Items.IndexOf(item),target=index+delta;if(target<0||target>=parent.Items.Count)return;parent.Items.RemoveAt(index);parent.Items.Insert(target,item);}
    public void ToLibrary(MaterialLibraryItem category,string name)
    {
        if(category.Tag!=null)throw new CaeException("Please select a library category to which the material should be added.");
        var material=model.Single(m=>m.Name==name).DeepClone();string target=name;int count=1;while(category.Items.Any(m=>m.Name==target))target=name+"_Model-"+count++;
        material.Name=target;if(material.ContainsEquation())throw new CaeException("A material containing equations cannot be added to the library.");
        category.Items.Add(new MaterialLibraryItem(target){Tag=material});controller.Model.UnitSystem.SetConverterUnits();
    }
    public void ToModel(MaterialLibraryItem item)
    {
        if(item.Tag==null)throw new CaeException("Select a library material.");
        var material=item.Tag.DeepClone();string target=item.Name;int count=1;while(model.Any(m=>m.Name==target))target=item.Name+"_Library-"+count++;
        material.Name=target;model.Add(material);modelChanged=true;
    }
    public void RemoveModel(string name){model.RemoveAll(m=>m.Name==name);modelChanged=true;}
    public void MoveModel(int index,int delta){int target=index+delta;if(target<0||target>=model.Count)return;var m=model[index];model.RemoveAt(index);model.Insert(target,m);modelChanged=true;}
    public void Apply(){if(!modelChanged)return;var names=controller.GetMaterialNames();if(names.Length>0)controller.RemoveMaterialsCommand(names);foreach(var material in model)controller.AddMaterialCommand(material);modelChanged=false;}
    public PropertySheet Preview(MaterialLibraryItem item)=>new(item.Tag);
}
