using CaeMesh;

// Same binary prefix and original element factories as FeMesh.ReadFromBinaryReader.
// This reader never instantiates a serialized graph type.
internal static class FamilyMesh
{
    internal static object Read(string path)
    {
        using var stream=File.OpenRead(path);
        if(stream.Length>128L*1024*1024)throw new InvalidDataException("Model frame exceeds 128 MiB.");
        using var r=new BinaryReader(stream);
        int geometry=r.ReadInt32();
        if(geometry!=0 && (geometry!=1 || r.ReadInt32()!=0 || r.ReadInt32()!=0 || r.ReadInt32()!=0))throw new NotSupportedException("Family PMX exchange requires absent/empty CAD geometry.");
        if(r.ReadInt32()!=1)throw new InvalidDataException("Analysis mesh is absent.");
        var nodes=new Dictionary<int,FeNode>();int count=MeshPrefix.ReadCount(r,28);
        for(int i=0;i<count;i++) {
            int id=r.ReadInt32();double x=r.ReadDouble(),y=r.ReadDouble(),z=r.ReadDouble();
            if(id<1 || !double.IsFinite(x)||!double.IsFinite(y)||!double.IsFinite(z)||!nodes.TryAdd(id,new FeNode(id,x,y,z)))throw new InvalidDataException("Invalid or duplicate node.");
        }
        var elements=new Dictionary<int,FeElement>();count=MeshPrefix.ReadCount(r,24);
        for(int i=0;i<count;i++) {
            int part=r.ReadInt32(),id=r.ReadInt32(),vtk=r.ReadInt32(),length=r.ReadInt32();
            int expected=vtk switch {3=>2,21=>3,5=>3,9=>4,22=>6,23=>8,10=>4,14=>5,13=>6,12=>8,24=>10,27=>13,26=>15,25=>20,_=>0};
            if(expected==0 || length!=expected)throw new NotSupportedException("Unsupported original PMX element topology or node count.");
            var ids=new int[length];for(int j=0;j<length;j++)ids[j]=r.ReadInt32();
            if(part<1 || id<1 || ids.Distinct().Count()!=length || ids.Any(n=>!nodes.ContainsKey(n)))throw new InvalidDataException("Invalid part/element/connectivity.");
            FeElement e=vtk switch {3=>new LinearBeamElement(id,ids),21=>new ParabolicBeamElement(id,ids),5=>new LinearTriangleElement(id,ids),9=>new LinearQuadrilateralElement(id,ids),22=>new ParabolicTriangleElement(id,ids),23=>new ParabolicQuadrilateralElement(id,ids),10=>new LinearTetraElement(id,ids),14=>new LinearPyramidElement(id,ids),13=>new LinearWedgeElement(id,ids),12=>new LinearHexaElement(id,ids),24=>new ParabolicTetraElement(id,ids),27=>new ParabolicPyramidElement(id,ids),26=>new ParabolicWedgeElement(id,ids),25=>new ParabolicHexaElement(id,ids),_=>throw new NotSupportedException()};
            e.PartId=part;if(!elements.TryAdd(id,e))throw new InvalidDataException("Duplicate element.");
        }
        var names=PmxBinary.ReadPartNames(r);PmxBinary.End(r);
        return new {nodes=nodes.Values.Select(n=>new{id=n.Id,coordinates=n.Coor}),elements=elements.Values.Select(e=>new{id=e.Id,partId=e.PartId,vtkCellType=e.GetVtkCellType(),connectivity=e.NodeIds}),partNames=names,meshAssembly=typeof(FeNode).Assembly.GetName().Name};
    }
}
