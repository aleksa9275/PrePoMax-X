using CaeMesh;

// FeModel.WriteToBinaryWriter and FeMesh.WriteToBinaryWriter 3.0 layout.
// Engineering objects keep their original CaeMesh assembly ownership.
internal static class CadModel
{
    internal static object Read(string path)
    {
        using var stream = File.OpenRead(path);
        if (stream.Length > 128L * 1024 * 1024) throw new InvalidDataException("Model frame exceeds 128 MiB.");
        using var reader = new BinaryReader(stream);
        if (reader.ReadInt32() != 1) throw new InvalidDataException("Expected saved CAD geometry.");
        var geometry = ReadMesh(reader, true);
        string[] geometryNames = PmxBinary.ReadPartNames(reader);
        if (reader.ReadInt32() != 1) throw new InvalidDataException("Expected saved analysis mesh.");
        var mesh = ReadMesh(reader, false);
        string[] names = PmxBinary.ReadPartNames(reader);
        PmxBinary.End(reader);
        if (geometryNames.Length != 1 || names.Length != 1 || !names.SequenceEqual(geometryNames) ||
            geometry.Elements.Values.Select(e => e.PartId).Distinct().Count() != 1 ||
            mesh.Elements.Values.Select(e => e.PartId).Distinct().Count() != 1)
            throw new InvalidDataException("The CAD PMX boundary requires one matching geometry/mesh part.");
        return new {
            nodes = mesh.Nodes.Values.OrderBy(n => n.Id).Select(n => new {id=n.Id,coordinates=new[]{n.X,n.Y,n.Z}}),
            elements = mesh.Elements.Values.OrderBy(e => e.Id).Select(e => new {id=e.Id,partId=e.PartId,type="C3D4",connectivity=e.NodeIds}),
            partNames = names, meshAssembly = typeof(FeNode).Assembly.GetName().Name,
            geometry = new {partNames=geometryNames,nodes=geometry.Nodes.Count,elements=geometry.Elements.Count,
                partId=geometry.Elements.Values.First().PartId, nodeIds=geometry.Nodes.Keys.Order().ToArray(),
                elementIds=geometry.Elements.Keys.Order().ToArray()}
        };
    }

    private static (Dictionary<int,FeNode> Nodes, Dictionary<int,FeElement> Elements) ReadMesh(BinaryReader r, bool geometry)
    {
        int count = MeshPrefix.ReadCount(r,28);
        var nodes = new Dictionary<int,FeNode>();
        for (int i=0;i<count;i++)
        {
            int id=r.ReadInt32(); double x=r.ReadDouble(),y=r.ReadDouble(),z=r.ReadDouble();
            if (id<1 || !double.IsFinite(x)||!double.IsFinite(y)||!double.IsFinite(z)||!nodes.TryAdd(id,new FeNode(id,x,y,z)))
                throw new InvalidDataException("Invalid CAD model node.");
        }
        count = MeshPrefix.ReadCount(r,24);
        var elements = new Dictionary<int,FeElement>();
        for (int i=0;i<count;i++)
        {
            int part=r.ReadInt32(),id=r.ReadInt32(),vtk=r.ReadInt32(),length=r.ReadInt32();
            int expected = geometry ? vtk switch {3=>2,5=>3,_=>0} : vtk==10 ? 4 : 0;
            if (expected==0 || length!=expected) throw new NotSupportedException("CAD requires linear display edges/triangles and first-order C3D4 analysis elements; quadratic tetrahedra remain gated.");
            int[] labels = new int[length];
            for(int j=0;j<length;j++) labels[j]=r.ReadInt32();
            if(part<1 || id<1 || labels.Distinct().Count()!=length || labels.Any(n=>!nodes.ContainsKey(n)))
                throw new InvalidDataException("Invalid CAD model connectivity.");
            FeElement e = vtk switch {3=>new LinearBeamElement(id,labels),5=>new LinearTriangleElement(id,labels),_=>new LinearTetraElement(id,labels)};
            e.PartId=part;
            if(!elements.TryAdd(id,e))throw new InvalidDataException("Duplicate CAD model element.");
            if(e is LinearTetraElement tetra && (!double.IsFinite(tetra.GetVolume(nodes)) || tetra.GetVolume(nodes)<=0))
                throw new InvalidDataException("Original signed tetrahedral volume is not positive.");
        }
        if (!geometry && elements.Values.SelectMany(e=>e.NodeIds).Distinct().Count()!=nodes.Count)
            throw new InvalidDataException("Analysis mesh has unused nodes.");
        return(nodes,elements);
    }
}
