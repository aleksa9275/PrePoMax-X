using CaeMesh.ContactSearchNamespace;using CaeGlobals;using CaeMesh;using PrePoMax;using PrePoMax.Forms;
namespace PrePoMaxX.UI;
// Original ContactSearch and the original SearchContactPair property view own the work.
public sealed partial class ContactSearchSession(Controller controller)
{
    List<SearchContactPair> pairs=[];
    List<SearchContactPair> _selectedContactPairs=[];Controller _controller=>controller;
    public SearchContactPair[] Pairs=>pairs.ToArray();
    public string[] Interactions=>controller.GetSurfaceInteractionNames();
    public Task Search(double distance,double angle,string grouping,string type,string interaction,string method,bool adjust,GeometryFilterEnum filter)=>Task.Run(()=>{
        var search=new ContactSearch(controller.Model.Mesh,controller.Model.Geometry){GroupContactPairsBy=Enum.Parse<GroupContactPairsByEnum>(grouping)};
        var target=Enum.Parse<SearchContactPairType>(type);controller.SuppressExplodedView();
        try {pairs=search.FindContactPairs(distance,angle,filter,target==SearchContactPairType.Tie).Select(item=>{
            var pair=new SearchContactPair(item.Name,adjust,distance){Type=target,SurfaceInteractionName=interaction,ContactPairMethod=method,MasterSlaveItem=item};pair.PopulateDropDownLists(Interactions,["Node to surface","Surface to surface"]);return pair;}).ToList();}
        finally{controller.ResumeExplodedViews(false);}
    });
    public PropertySheet Properties(int index)=>new(pairs[index]);
    public void Remove(int index)=>pairs.RemoveAt(index);
    public void Swap(int index){pairs[index].MasterSlaveItem.SwapMasterSlave();pairs[index].Name=pairs[index].MasterSlaveItem.Name;}
    public void Highlight(int index){_selectedContactPairs=[pairs[index]];HighlightContactPairs();}
    public void Merge(int[] indices){_selectedContactPairs=indices.Select(i=>pairs[i]).ToList();MergeSelected();}
    // Original btnOK_Click (3.0.1): one OK adds every searched pair as one command.
    public void Apply()=>controller.AddSearchedContactPairsCommand(pairs);
}
