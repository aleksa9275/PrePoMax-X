using System.Buffers.Binary;
using System.Formats.Nrbf;
using System.Text;

internal sealed record EditString(string Role, int RecordId, int Offset, string Value)
{
    internal static EditString Find(byte[] graph, ClassRecord equation, string role)
    {
        if (equation.GetBoolean("_constant"))
            throw new InvalidDataException("Constant equation storage is unsupported.");
        var target = equation.GetSerializationRecord("_equation");
        if (target is not PrimitiveTypeRecord<string> text ||
            target.RecordType != SerializationRecordType.BinaryObjectString)
            throw new InvalidDataException("Expected a referenced NRBF string equation.");
        byte[] encoded = Encoding.UTF8.GetBytes(text.Value);
        if (encoded.Length is < 1 or > 127)
            throw new InvalidDataException("Equation is outside the probe's string length limit.");

        // The public decoder treats the record ID as opaque. Decode a tiny
        // standalone record for each possible wire ID and compare identities.
        byte[] candidate = new byte[17 + 6 + encoded.Length + 1];
        candidate[0] = 0; // SerializedStreamHeader
        BinaryPrimitives.WriteInt32LittleEndian(candidate.AsSpan(5), -1);
        candidate[9] = 1; // major version
        candidate[^1] = 11; // MessageEnd
        int offset = -1;
        int recordId = 0;
        ReadOnlySpan<byte> remaining = graph;
        int scanned = 0;
        int occurrences = 0;
        while (true)
        {
            int relative = remaining.IndexOf(encoded);
            if (relative < 0)
                break;
            int start = scanned + relative - 6;
            if (start >= 17 && graph[start] == 6 && graph[start + 5] == encoded.Length)
            {
                int id = BinaryPrimitives.ReadInt32LittleEndian(graph.AsSpan(start + 1, 4));
                if (++occurrences > 4096)
                    throw new InvalidDataException("Too many candidate equation records.");
                if (id > 0)
                {
                    BinaryPrimitives.WriteInt32LittleEndian(candidate.AsSpan(1), id);
                    graph.AsSpan(start, 6 + encoded.Length).CopyTo(candidate.AsSpan(17));
                    using var input = new MemoryStream(candidate, writable: false);
                    if (NrbfDecoder.Decode(input).Id.Equals(target.Id))
                    {
                        if (offset >= 0)
                            throw new InvalidDataException("Ambiguous equation record location.");
                        offset = start;
                        recordId = id;
                    }
                }
            }
            scanned += relative + 1;
            remaining = graph.AsSpan(scanned);
        }
        if (offset < 0)
            throw new InvalidDataException("Equation record has no matching wire location.");
        // The owning equation holds this string inline. An alias anywhere,
        // including in a primitive string array, needs a MemberReference.
        // A byte sequence inside other payload data also causes refusal.
        Span<byte> reference = stackalloc byte[5];
        reference[0] = (byte)SerializationRecordType.MemberReference;
        BinaryPrimitives.WriteInt32LittleEndian(reference[1..], recordId);
        if (graph.AsSpan().IndexOf(reference) >= 0)
            throw new InvalidDataException($"The {role} string may be shared with another graph slot.");
        return new EditString(role, recordId, offset, text.Value);
    }
}
