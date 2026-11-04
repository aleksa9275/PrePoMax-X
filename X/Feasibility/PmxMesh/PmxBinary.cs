using System.Text;

internal static class PmxBinary
{
    private const long MaxFrameBytes = 16 * 1024 * 1024;

    internal static BinaryReader Open(string path)
    {
        var stream = File.OpenRead(path);
        if (stream.Length <= MaxFrameBytes)
            return new BinaryReader(stream, new UTF8Encoding(false, true));
        stream.Dispose();
        throw new InvalidDataException("Result frame exceeds the probe limit.");
    }

    internal static string[] ReadPartNames(BinaryReader reader)
    {
        int count = MeshPrefix.ReadCount(reader, 5);
        var names = new string[count];
        for (int part = 0; part < count; part++)
        {
            names[part] = ReadName(reader);
            int present = reader.ReadInt32();
            if (present == -1)
                continue;
            if (present != 1)
                throw new InvalidDataException("Invalid part visualization flag.");

            // VisualizationData 3.0 layout. Skip without allocating the arrays.
            int[] widths = { -4, 4, -4, 8, 4, -4, -4, -4, -4, 8, 4, 4, 4, 4 };
            foreach (int width in widths)
            {
                if (width > 0)
                    SkipArray(reader, width);
                else
                {
                    int rows = ArrayCount(reader, 4);
                    for (int row = 0; row < rows; row++)
                        SkipArray(reader, -width);
                }
            }
        }
        if (names.Distinct(StringComparer.Ordinal).Count() != names.Length)
            throw new InvalidDataException("Duplicate part name.");
        return names;
    }

    private static int ArrayCount(BinaryReader reader, int width)
    {
        int count = reader.ReadInt32();
        if (count < -1 || count > (reader.BaseStream.Length - reader.BaseStream.Position) / width)
            throw new InvalidDataException("Invalid visualization array length.");
        return count;
    }

    private static void SkipArray(BinaryReader reader, int width) =>
        Skip(reader, Math.Max(0, ArrayCount(reader, width)) * (long)width);

    internal static void SkipString(BinaryReader reader)
    {
        Skip(reader, StringSize(reader));
    }

    private static string ReadName(BinaryReader reader)
    {
        int size = StringSize(reader);
        if (size == 0 || size > reader.BaseStream.Length - reader.BaseStream.Position)
            throw new InvalidDataException("Invalid part name length.");
        return new UTF8Encoding(false, true).GetString(reader.ReadBytes(size));
    }

    private static int StringSize(BinaryReader reader)
    {
        int size = reader.Read7BitEncodedInt();
        if (size is < 0 or > 4096)
            throw new InvalidDataException("PMX string exceeds the probe limit.");
        return size;
    }

    internal static void Skip(BinaryReader reader, long bytes)
    {
        if (bytes < 0 || bytes > reader.BaseStream.Length - reader.BaseStream.Position)
            throw new InvalidDataException("Truncated result frame.");
        reader.BaseStream.Position += bytes;
    }

    internal static void End(BinaryReader reader)
    {
        if (reader.BaseStream.Position != reader.BaseStream.Length)
            throw new InvalidDataException("Unexpected trailing result-frame bytes.");
    }
}
