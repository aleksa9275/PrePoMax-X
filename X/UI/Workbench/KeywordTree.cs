using System.Collections;
namespace PrePoMaxX.UI;
// Toolkit-neutral tree for original keyword-editor algorithms. Never persisted.
public sealed class KeywordTreeNode
{
    public string Text {get;set;}="";public string Name {get;set;}="";internal object Tag {get;set;}
    public KeywordTreeNode Parent {get;internal set;}public KeywordTreeNodes Nodes {get;}
    public int Index=>Parent?.Nodes.IndexOf(this)??-1;
    public bool Expanded {get;set;}
    public bool User=>Tag is KeywordNodeData data && data.Keyword is FileInOut.Output.Calculix.CalculixUserKeyword;
    public bool Title=>Tag is KeywordNodeData data && data.Keyword is FileInOut.Output.Calculix.CalTitle;
    public bool Modified=>Tag is KeywordNodeData data && data.KeywordOverride!=null;
    public string Data=>Tag is KeywordNodeData data?data.Data:"";
    public bool Active=>Tag is KeywordNodeData data && (data.Keyword is FileInOut.Output.Calculix.CalculixUserKeyword user?user.Active:data.KeywordOverride?.Disabled!=true);
    public KeywordTreeNode(){Nodes=new(this);}public void Expand()=>Expanded=true;
}
public sealed class KeywordTreeNodes(KeywordTreeNode parent) : IEnumerable<KeywordTreeNode>
{
    readonly List<KeywordTreeNode> nodes=[];
    public int Count=>nodes.Count;public KeywordTreeNode this[int index]=>nodes[index];
    public int Add(KeywordTreeNode node){node.Parent=parent;nodes.Add(node);return Count-1;}
    public KeywordTreeNode Add(string name){var node=new KeywordTreeNode{Text=name};Add(node);return node;}
    public void Insert(int index,KeywordTreeNode node){node.Parent=parent;nodes.Insert(Math.Min(index,Count),node);}
    public KeywordTreeNode Insert(int index,string text){var node=new KeywordTreeNode{Text=text};Insert(index,node);return node;}
    public void Remove(KeywordTreeNode node){nodes.Remove(node);node.Parent=null;}
    public void Clear(){foreach(var n in nodes)n.Parent=null;nodes.Clear();}
    public int IndexOf(KeywordTreeNode node)=>nodes.IndexOf(node);
    public IEnumerator<KeywordTreeNode> GetEnumerator()=>nodes.GetEnumerator();IEnumerator IEnumerable.GetEnumerator()=>GetEnumerator();
}
internal sealed class KeywordNodeData
{
 public FileInOut.Output.Calculix.CalculixKeyword Keyword;public string Data;public int NumOfLines;
 public int[] GeneratedIndices;public string OriginalSignature;public FileInOut.Output.Calculix.CalculixKeywordOverride KeywordOverride;
}
