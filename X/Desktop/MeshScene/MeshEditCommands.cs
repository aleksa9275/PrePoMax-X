using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using CaeMesh;
using CaeModel;
using FileInOut.Input;
using PrePoMaxX.MeshDeck;

// Job-owned transport; original FeMesh point transforms and element face ordering
// own geometry. Recipes are tool inputs, never PMX persistence.
internal static class MeshEditCommands
{
    internal sealed record Recipe(string Operation,string? NodeSet=null,double[]? Vector=null,double[]? Center=null,double[]? Axis=null,double? AngleDegrees=null,int StartNode=1,int StartElement=1,string? Formulation=null);
    internal static (InpMeshData Mesh,byte[] Bytes) Edit(string[] args)
    {
        CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
        var mesh=MeshFiles.Read(args[1]);
        if(mesh.OmittedKeywords.Length!=0 || mesh.Warnings.Length!=0)throw new InvalidDataException("Mesh editing requires standalone mesh data without omitted model keywords or formulation warnings.");
        byte[] recipeBytes=File.ReadAllBytes(args[2]);
        if(recipeBytes.Length>16384)throw new InvalidDataException("Mesh recipe exceeds 16 KiB.");
        using var document=JsonDocument.Parse(recipeBytes,new JsonDocumentOptions{MaxDepth=8});
        if(document.RootElement.EnumerateObject().Select(p=>p.Name).Distinct().Count()!=document.RootElement.EnumerateObject().Count())throw new InvalidDataException("Duplicate mesh recipe property.");
        var recipe=document.RootElement.Deserialize<Recipe>(new JsonSerializerOptions{PropertyNamingPolicy=JsonNamingPolicy.CamelCase,UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow,RespectRequiredConstructorParameters=true})??throw new InvalidDataException("Null mesh recipe.");
        double[] Vector(double[]? v,string role) {
            if(v==null || v.Length!=3 || v.Any(x=>!double.IsFinite(x)))throw new InvalidDataException("Three finite "+role+" coordinates required.");return v;
        }
        if(recipe.Operation is "translate" or "rotate" or "scale") {
            int[] ids=recipe.NodeSet==null?mesh.Nodes.Keys.ToArray():mesh.NodeSets.TryGetValue(recipe.NodeSet,out var members)?members:throw new InvalidDataException("Missing node set.");
            var points=ids.Select(id=>mesh.Nodes[id].Coor).ToArray();
            if(recipe.Operation=="translate") {
                if(recipe.Center!=null || recipe.Axis!=null || recipe.AngleDegrees.HasValue)throw new InvalidDataException("Translation uses a vector only.");
                FeMesh.TranslatePoints(points,Vector(recipe.Vector,"translation"));
            } else if(recipe.Operation=="rotate") {
                var axis=Vector(recipe.Axis,"axis");
                if(recipe.Vector!=null || (!double.IsFinite(axis.Sum(v=>v*v)) || axis.Sum(v=>v*v)<1e-30) || !recipe.AngleDegrees.HasValue || !double.IsFinite(recipe.AngleDegrees.Value))throw new InvalidDataException("Rotation requires a nonzero axis and finite degrees.");
                FeMesh.RotatePoints(points,Vector(recipe.Center,"center"),axis,recipe.AngleDegrees.Value*Math.PI/180);
            } else {
                var factors=Vector(recipe.Vector,"scale factors");
                if(factors.Any(v=>v<=0) || recipe.Axis!=null || recipe.AngleDegrees.HasValue)throw new InvalidDataException("Positive scale factors required.");
                FeMesh.ScalePoints(points,Vector(recipe.Center,"center"),factors);
            }
            for(int i=0;i<ids.Length;i++) {
                if(points[i].Any(v=>!double.IsFinite(v)))throw new InvalidDataException("Transformed coordinates must remain finite.");
                mesh.Nodes[ids[i]]=new FeNode(ids[i],points[i]);
            }
        } else if(recipe.Operation=="renumber") {
            if(recipe.NodeSet!=null || recipe.Vector!=null || recipe.Center!=null || recipe.Axis!=null || recipe.AngleDegrees.HasValue)throw new InvalidDataException("Renumbering applies to the complete mesh and its sets.");
            if(recipe.StartNode<1 || recipe.StartElement<1 || (long)recipe.StartNode+mesh.Nodes.Count>int.MaxValue || (long)recipe.StartElement+mesh.Elements.Count>int.MaxValue)throw new InvalidDataException("Positive bounded starting IDs required.");
            var nodes=mesh.Nodes.Keys.Order().Select((id,i)=>(id,next:recipe.StartNode+i)).ToDictionary(x=>x.id,x=>x.next);
            var elements=mesh.Elements.Keys.Order().Select((id,i)=>(id,next:recipe.StartElement+i)).ToDictionary(x=>x.id,x=>x.next);
            // Same ID-map orchestration as FeMesh.RenumberNodes/Elements; the
            // standalone graph has no surfaces/references outside these sets.
            var newNodes=mesh.Nodes.ToDictionary(n=>nodes[n.Key],n=>new FeNode(nodes[n.Key],n.Value.Coor));
            mesh.Nodes.Clear();foreach(var n in newNodes)mesh.Nodes.Add(n.Key,n.Value);
            foreach(var e in mesh.Elements.Values){e.NodeIds=e.NodeIds.Select(id=>nodes[id]).ToArray();e.Id=elements[e.Id];}
            var newElements=mesh.Elements.Values.ToDictionary(e=>e.Id);
            mesh.Elements.Clear();foreach(var e in newElements)mesh.Elements.Add(e.Key,e.Value);
            foreach(var b in mesh.ElementBlocks)b.ElementLabels=b.ElementLabels.Select(id=>elements[id]).ToHashSet();
            foreach(var k in mesh.NodeSets.Keys.ToArray())mesh.NodeSets[k]=mesh.NodeSets[k].Select(id=>nodes[id]).ToArray();
            foreach(var k in mesh.ElementSets.Keys.ToArray())mesh.ElementSets[k]=mesh.ElementSets[k].Select(id=>elements[id]).ToArray();
        } else if(recipe.Operation is "surface" or "edge") {
            if(recipe.NodeSet==null || !mesh.NodeSets.TryGetValue(recipe.NodeSet,out var labels))throw new InvalidDataException("Choose a source face/edge node set.");
            if(recipe.Vector!=null || recipe.Center!=null || recipe.Axis!=null || recipe.AngleDegrees.HasValue)throw new InvalidDataException("Boundary extraction has no coordinate transform.");
            var selected=labels.ToHashSet();var candidates=new List<(int Source,int Face,int[] Nodes)>();
            foreach(var e in mesh.Elements.Values.OrderBy(e=>e.Id)) {
                bool surface=recipe.Operation=="surface";
                if(surface && e is not FeElement3D || !surface && e is not FeElement2D)continue;
                for(int face=surface?1:3;face<=6;face++) {
                    int[] ids;try{ids=e.GetNodeIdsFromFaceName((FeFaceName)face);}catch(NotSupportedException){continue;}
                    candidates.Add((e.Id,face,ids));
                }
            }
            string Key(int[] ids)=>string.Join(",",ids.Order());
            var exterior=candidates.GroupBy(c=>Key(c.Nodes)).Where(g=>g.Count()==1).Select(g=>g.Single()).Where(c=>c.Nodes.All(selected.Contains)).ToArray();
            if(exterior.Length==0 || !selected.SetEquals(exterior.SelectMany(c=>c.Nodes)))throw new InvalidDataException("The selected set must exactly cover complete exterior faces/edges, including midsides.");
            var lines=new StringBuilder("*Node\n");
            foreach(var n in mesh.Nodes.Values.Where(n=>selected.Contains(n.Id)))lines.Append(FormattableString.Invariant($"{n.Id}, {n.X:G17}, {n.Y:G17}, {n.Z:G17}\n"));
            int index=0;
            foreach(var face in exterior) {
                string type=recipe.Operation=="edge" ? face.Nodes.Length==2?"T3D2":"T3D3" : face.Nodes.Length switch {3=>"S3",4=>"S4",6=>"S6",8=>"S8",_=>throw new NotSupportedException("Unsupported original boundary topology.")};
                if(recipe.Formulation!=null) {
                    // Surface/plane aliases share exact original topology.
                    string suffix=face.Nodes.Length.ToString();
                    bool compatible=recipe.Operation=="edge"?(face.Nodes.Length==2 ? new[]{"T3D2","T2D2","B31","B31R","B21"}:new[]{"T3D3","T2D3","B32","B32R"}).Contains(recipe.Formulation):
                        new[]{type,"M3D"+suffix,"CPS"+suffix,"CPE"+suffix,"CAX"+suffix}.SelectMany(StaticAnalysisDeckWriter.CompatibleSolidFormulations).Contains(recipe.Formulation);
                    if(!compatible)throw new InvalidDataException("Boundary formulation must match its exact topology.");type=recipe.Formulation;
                }
                lines.Append($"*Element,Type={type},Elset=EXTRACTED\n{++index}, ").AppendJoin(", ",face.Nodes).Append('\n');
            }
            foreach(var set in mesh.NodeSets) {
                int[] kept=set.Value.Where(selected.Contains).ToArray();if(kept.Length==0)continue;
                lines.Append($"*Nset,Nset={set.Key}\n");foreach(var row in kept.Chunk(8))lines.AppendJoin(", ",row).Append('\n');
            }
            mesh=InpFileReader.ReadMeshData(lines.ToString().Split('\n'));
        } else throw new InvalidDataException("Choose translate, rotate, scale, renumber, surface or edge.");
        if(recipe.Operation is not ("surface" or "edge") && recipe.Formulation!=null)throw new InvalidDataException("Formulation selection applies only to boundary extraction.");
        byte[] output=Encoding.UTF8.GetBytes(MeshDeckWriter.WriteMesh(mesh));
        if(output.Length>InpFileReader.MeshDataMaximumCharacters)throw new InvalidDataException("Edited mesh exceeds transport limit.");
        var checkedMesh=InpFileReader.ReadMeshData(Encoding.UTF8.GetString(output).Split('\n'));
        using(var stream=new FileStream(args[3],FileMode.CreateNew,FileAccess.Write,FileShare.None))stream.Write(output);
        return(checkedMesh,output);
    }
}
