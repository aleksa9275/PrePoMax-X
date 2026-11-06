using System.Buffers.Binary;
using System.Formats.Nrbf;
using System.Text;

// A bounded wire-position index, not an object deserializer. The public NRBF
// decoder still validates the graph and identifies every editable owner.
// MS-NRBF record/class/member/array framing:
// https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-nrbf/5acd9dc4-1439-433a-8d53-eb2922a142d8
internal sealed class NrbfWire
{
    internal sealed record Slot(int Offset, int Length, int Kind, int Id);
    private sealed record Metadata(string[] Names, int[] Types, int[] PrimitiveTypes);
    private readonly BinaryReader reader;
    private readonly Dictionary<int, Metadata> metadata = new();
    private readonly Dictionary<int, Dictionary<string, Slot>> members = new();
    private readonly HashSet<int> ids = new();
    private readonly Dictionary<SerializationRecordId, int> publicIds = new();
    private int records, arraySlots;
    internal int MaximumId { get; private set; }

    internal NrbfWire(byte[] graph)
    {
        if (graph.Length is < 18 or > 16 * 1024 * 1024)
            throw new InvalidDataException("Wire graph byte limit exceeded.");
        reader = new BinaryReader(new MemoryStream(graph, false), new UTF8Encoding(false, true));
        if (reader.ReadByte() != 0) throw new InvalidDataException("Missing NRBF header.");
        reader.ReadInt32(); reader.ReadInt32();
        if (reader.ReadInt32() != 1 || reader.ReadInt32() != 0)
            throw new InvalidDataException("Unsupported NRBF wire version.");
        while (reader.BaseStream.Position < graph.Length - 1)
            Value(0, false);
        if (reader.ReadByte() != 11 || reader.BaseStream.Position != graph.Length)
            throw new InvalidDataException("Invalid wire MessageEnd.");
    }

    internal Slot StringMember(ClassRecord owner, string field)
    {
        int id = WireId(owner.Id);
        var target = owner.GetSerializationRecord(field) ?? throw new InvalidDataException("Missing string record.");
        if (!members.TryGetValue(id, out var fields) || !fields.TryGetValue(field, out var slot) ||
            slot.Kind is not (6 or 9) || slot.Id != WireId(target.Id))
            throw new InvalidDataException("Wire member does not match the decoded string owner.");
        return slot;
    }

    private int WireId(SerializationRecordId id)
    {
        if (publicIds.Count == 0)
        {
            // Record IDs are opaque in the public API. Match identities using a
            // standalone string record, as in the older exclusive-string probe.
            byte[] tiny = new byte[25];
            tiny[0] = 0; tiny[9] = 1; tiny[17] = 6; tiny[22] = 1; tiny[23] = 65; tiny[24] = 11;
            BinaryPrimitives.WriteInt32LittleEndian(tiny.AsSpan(5), -1);
            foreach (int wireId in ids.Where(value => value > 0))
            {
                BinaryPrimitives.WriteInt32LittleEndian(tiny.AsSpan(1), wireId);
                BinaryPrimitives.WriteInt32LittleEndian(tiny.AsSpan(18), wireId);
                using var input = new MemoryStream(tiny, false);
                publicIds.Add(NrbfDecoder.Decode(input).Id, wireId);
            }
        }
        return publicIds.TryGetValue(id, out int result) ? result :
            throw new InvalidDataException("Editable owner has no positive wire identity.");
    }

    private int Position => checked((int)reader.BaseStream.Position);
    private int Count(int limit)
    {
        int value = reader.ReadInt32();
        if (value < 0 || value > limit) throw new InvalidDataException("Wire collection limit exceeded.");
        return value;
    }
    private int ObjectId()
    {
        int id = reader.ReadInt32();
        if (id == 0 || !ids.Add(id)) throw new InvalidDataException("Duplicate/zero wire identity.");
        MaximumId = Math.Max(MaximumId, id);
        return id;
    }
    private string Text()
    {
        string text = reader.ReadString();
        if (text.Length > 16 * 1024 * 1024) throw new InvalidDataException("Wire string limit exceeded.");
        return text;
    }
    private void Skip(int count)
    {
        if (count < 0 || count > reader.BaseStream.Length - reader.BaseStream.Position)
            throw new InvalidDataException("Truncated wire primitive.");
        reader.BaseStream.Position += count;
    }
    private void Primitive(int type)
    {
        if (type == 3) { reader.ReadChar(); return; }
        if (type == 5) { Text(); return; }
        int size = type switch { 1 or 2 or 10 => 1, 7 or 14 => 2,
            8 or 11 or 15 => 4, 6 or 9 or 12 or 13 or 16 => 8, _ => 0 };
        if (size == 0) throw new InvalidDataException($"Unsupported primitive wire layout {type}.");
        Skip(size);
    }
    private int TypeInfo(int type)
    {
        switch (type)
        {
            case 0: case 7: return reader.ReadByte();
            case 3: Text(); break;
            case 4: Text(); reader.ReadInt32(); break;
            case 1: case 2: case 5: case 6: break;
            default: throw new InvalidDataException("Unsupported wire member type.");
        }
        return 0;
    }
    private void Class(int id, Metadata description, int depth)
    {
        var fields = new Dictionary<string, Slot>(StringComparer.Ordinal);
        members.Add(id, fields);
        for (int i = 0; i < description.Names.Length; i++)
        {
            int start = Position;
            Slot slot;
            if (description.Types[i] == 0)
            {
                Primitive(description.PrimitiveTypes[i]);
                slot = new Slot(start, Position - start, -1, 0);
            }
            else slot = Value(depth + 1, false).Slot;
            fields.Add(description.Names[i], slot);
        }
    }
    private void Array(int count, int type, int primitive, int depth)
    {
        arraySlots = checked(arraySlots + count);
        if (arraySlots > 1_000_000) throw new InvalidDataException("Wire array slot limit exceeded.");
        for (int i = 0; i < count;)
        {
            if (type == 0) { Primitive(primitive); i++; }
            else
            {
                int consumed = Value(depth + 1, true).Count;
                if (consumed < 1 || consumed > count - i) throw new InvalidDataException("Invalid wire null run.");
                i += consumed;
            }
        }
    }
    private (Slot Slot, int Count) Value(int depth, bool array)
    {
        if (depth > 128 || ++records > 100_000)
            throw new InvalidDataException("Wire depth/record limit exceeded.");
        int start = Position, kind = reader.ReadByte(), id = 0, consumed = 1;
        switch (kind)
        {
            case 12: // A library record is metadata, not a member value.
                reader.ReadInt32(); Text(); return Value(depth, array);
            case 1:
                id = ObjectId(); int source = reader.ReadInt32();
                if (!metadata.TryGetValue(source, out var existing)) throw new InvalidDataException("Unknown wire class metadata.");
                Class(id, existing, depth); break;
            case 4: case 5:
                id = ObjectId(); Text(); int count = Count(4096);
                string[] names = Enumerable.Range(0, count).Select(_ => Text()).ToArray();
                int[] types = Enumerable.Range(0, count).Select(_ => (int)reader.ReadByte()).ToArray();
                int[] primitives = types.Select(TypeInfo).ToArray();
                if (kind == 5) reader.ReadInt32();
                var description = new Metadata(names, types, primitives);
                metadata.Add(id, description); Class(id, description, depth); break;
            case 6: id = ObjectId(); Text(); break;
            case 7:
                id = ObjectId(); int shape = reader.ReadByte(), rank = Count(8);
                if (shape > 5 || rank < 1) throw new InvalidDataException("Unsupported wire array shape.");
                int length = 1;
                for (int i = 0; i < rank; i++) length = checked(length * Count(250_000));
                if (length > 250_000) throw new InvalidDataException("Wire array size limit exceeded.");
                if (shape >= 3) for (int i = 0; i < rank; i++) reader.ReadInt32();
                int type = reader.ReadByte(), primitive = TypeInfo(type);
                Array(length, type, primitive, depth); break;
            case 8: Primitive(reader.ReadByte()); break;
            case 9: id = reader.ReadInt32(); break;
            case 10: break;
            case 13: case 14:
                if (!array) throw new InvalidDataException("Null run outside wire array.");
                consumed = kind == 13 ? reader.ReadByte() : Count(250_000); break;
            case 15: case 16: case 17:
                id = ObjectId(); int size = Count(250_000);
                Array(size, kind == 15 ? 0 : 2, kind == 15 ? reader.ReadByte() : 0, depth); break;
            default: throw new InvalidDataException($"Unsupported wire record {kind}.");
        }
        return (new Slot(start, Position - start, kind, id), consumed);
    }
}
