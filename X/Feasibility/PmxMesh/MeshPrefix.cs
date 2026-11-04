using CaeMesh;

internal static class MeshPrefix
{
    internal static (Dictionary<int, FeNode> Nodes, Dictionary<int, LinearHexaElement> Elements)
        Read(BinaryReader reader)
    {
        // Same node and element prefix as FeMesh.ReadFromBinaryReader. Validate
        // counts and connectivity before constructing the original types.
        var nodes = new Dictionary<int, FeNode>();
        int nodeCount = ReadCount(reader, 28);
        for (int i = 0; i < nodeCount; i++)
        {
            int id = reader.ReadInt32();
            double x = reader.ReadDouble();
            double y = reader.ReadDouble();
            double z = reader.ReadDouble();
            if (id < 1 || !double.IsFinite(x) || !double.IsFinite(y) || !double.IsFinite(z) ||
                !nodes.TryAdd(id, new FeNode(id, x, y, z)))
                throw new InvalidDataException("Invalid or duplicate node.");
        }

        var elements = new Dictionary<int, LinearHexaElement>();
        int elementCount = ReadCount(reader, 48);
        for (int i = 0; i < elementCount; i++)
        {
            int partId = reader.ReadInt32();
            int id = reader.ReadInt32();
            if (reader.ReadInt32() != (int)vtkCellType.VTK_HEXAHEDRON || reader.ReadInt32() != 8)
                throw new InvalidDataException("Only eight-node hexahedra are supported.");
            var connectivity = new int[8];
            for (int index = 0; index < connectivity.Length; index++)
                connectivity[index] = reader.ReadInt32();

            if (partId < 1 || id < 1 || connectivity.Distinct().Count() != connectivity.Length ||
                connectivity.Any(nodeId => !nodes.ContainsKey(nodeId)) ||
                !elements.TryAdd(id, new LinearHexaElement(id, connectivity) { PartId = partId }))
                throw new InvalidDataException("Invalid or duplicate element.");
        }
        return (nodes, elements);
    }

    internal static int ReadCount(BinaryReader reader, int bytesPerRecord)
    {
        int count = reader.ReadInt32();
        if (count < 1 || count > 250_000 ||
            count > (reader.BaseStream.Length - reader.BaseStream.Position) / bytesPerRecord)
            throw new InvalidDataException("Mesh count exceeds the probe limit or remaining input.");
        return count;
    }
}
