using CaeResults;
using static PmxBinary;

internal static class ResultFields
{
    private const int PmxVersion = 3_000_000;

    internal static object Compare(string frdPath, string meshFrame, string[] fieldFrames)
    {
        if (fieldFrames.Length is < 1 or > 64)
            throw new InvalidDataException("Expected 1–64 result fields.");
        var frd = FrdFileReader.ReadStaticSnapshot(frdPath);
        using var meshReader = Open(meshFrame);
        var (nodes, elements) = MeshPrefix.Read(meshReader);
        if (nodes.Count != frd.Nodes.Count || !nodes.All(entry =>
            frd.Nodes.TryGetValue(entry.Key, out var other) &&
            entry.Value.X == other.X && entry.Value.Y == other.Y && entry.Value.Z == other.Z) ||
            elements.Count != frd.Elements.Count || !elements.All(entry =>
            frd.Elements.TryGetValue(entry.Key, out var other) &&
            entry.Value.NodeIds.SequenceEqual(other.NodeIds)))
            throw new InvalidDataException("PMX result mesh differs from the FRD.");

        ReadPartNames(meshReader);
        if (meshReader.ReadInt32() != 1 || MeshPrefix.ReadCount(meshReader, 8) != nodes.Count)
            throw new InvalidDataException("Expected a complete result node lookup.");
        var nodeOrder = new int[nodes.Count];
        var assigned = new HashSet<int>();
        for (int index = 0; index < nodes.Count; index++)
        {
            int id = meshReader.ReadInt32();
            int slot = meshReader.ReadInt32();
            if (!nodes.ContainsKey(id) || !assigned.Add(id) || slot < 0 ||
                slot >= nodeOrder.Length || nodeOrder[slot] != 0)
                throw new InvalidDataException("Invalid result node lookup.");
            nodeOrder[slot] = id;
        }
        End(meshReader);

        var expectedFields = frd.Fields.ToDictionary(entry => entry.Data.GetHashKey());
        var frdIndex = frd.NodeIdsInValueOrder.Select((id, index) => (id, index))
            .ToDictionary(pair => pair.id, pair => pair.index);
        int components = 0;
        long values = 0;
        foreach (string frame in fieldFrames)
        {
            using var reader = Open(frame);
            PreflightField(reader, nodes.Count);
            reader.BaseStream.Position = 0;
            var data = FieldData.ReadFromBinaryReader(reader, PmxVersion);
            var field = Field.ReadFromBinaryReader(reader, PmxVersion);
            End(reader);
            if (!expectedFields.Remove(data.GetHashKey(), out var expected) ||
                data.Time != expected.Data.Time || data.StepType != expected.Data.StepType ||
                field.Name != expected.Field.Name)
                throw new InvalidDataException("Unexpected embedded field identity or step metadata.");

            var names = field.GetComponentNames();
            var rawNames = expected.Field.GetComponentNames()
                .Where(name => !expected.Field.IsComponentInvariant(name)).ToHashSet();
            if (!rawNames.SetEquals(names))
                throw new InvalidDataException("Embedded components differ from raw FRD components.");
            foreach (string name in names)
            {
                var actual = field.GetComponentValues(name);
                var source = expected.Field.GetComponentValues(name);
                for (int index = 0; index < actual.Length; index++)
                    if (actual[index] != source[frdIndex[nodeOrder[index]]])
                        throw new InvalidDataException($"Embedded field {field.Name}/{name} differs from FRD.");
                components++;
                values += actual.Length;
            }
        }
        if (expectedFields.Count != 0)
            throw new InvalidDataException("An FRD field was missing from the PMX.");
        return new { frdSha256 = frd.SourceSha256, nodeCount = nodes.Count,
            elementCount = elements.Count, fields = fieldFrames.Length, components, values };
    }

    private static void PreflightField(BinaryReader reader, int nodeCount)
    {
        // Validate lengths before the original reader allocates component arrays.
        Present(reader);
        SkipString(reader);
        OptionalString(reader);
        Skip(reader, 32); // increment, mode, diameter, method, step type, time, step and increment
        OptionalString(reader);
        Skip(reader, 4); // field-data flags
        Present(reader);
        SkipString(reader);
        Present(reader);
        int count = reader.ReadInt32();
        if (count is < 1 or > 16)
            throw new InvalidDataException("Invalid component count.");
        for (int index = 0; index < count; index++)
        {
            SkipString(reader);
            Skip(reader, 1); // invariant flag
            if (reader.ReadInt32() != nodeCount)
                throw new InvalidDataException("Field component length differs from the result mesh.");
            Skip(reader, nodeCount * 4L);
        }
        Skip(reader, 13); // data type, complex, data state, four flags
        End(reader);
    }

    private static void OptionalString(BinaryReader reader)
    {
        int present = reader.ReadInt32();
        if (present == 1)
            SkipString(reader);
        else if (present != 0)
            throw new InvalidDataException("Invalid optional string flag.");
    }

    private static void Present(BinaryReader reader)
    {
        if (reader.ReadInt32() != 1)
            throw new InvalidDataException("Missing expected field data.");
    }

}
