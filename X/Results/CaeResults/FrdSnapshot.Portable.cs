// PrePoMax-X bounded inspection boundary; original FRD decoding and field math
// remain in the shared original partial. This is not FeResults preprocessing.
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using CaeMesh;

namespace CaeResults
{
    public sealed class FrdStaticField
    {
        public FieldData Data { get; }
        public Field Field { get; }
        internal FrdStaticField(FieldData data, Field field) { Data = data; Field = field; }
    }
    public sealed class FrdStaticSnapshot
    {
        public string SourceSha256 { get; }
        public string UnitSystemHeader { get; }
        public IReadOnlyDictionary<int, FeNode> Nodes { get; }
        public IReadOnlyDictionary<int, FeElement> Elements { get; }
        // Index i in every component belongs to NodeIdsInValueOrder[i].
        public IReadOnlyList<int> NodeIdsInValueOrder { get; }
        public IReadOnlyList<FrdStaticField> Fields { get; }
        internal FrdStaticSnapshot(string hash, string units, Dictionary<int, FeNode> nodes,
            Dictionary<int, FeElement> elements, int[] order, List<FrdStaticField> fields)
        {
            SourceSha256 = hash; UnitSystemHeader = units;
            Nodes = new ReadOnlyDictionary<int, FeNode>(nodes);
            Elements = new ReadOnlyDictionary<int, FeElement>(elements);
            NodeIdsInValueOrder = Array.AsReadOnly(order); Fields = fields.AsReadOnly();
        }
    }
    public static partial class FrdFileReader
    {
        private const long PortableMaximumBytes = 64 * 1024 * 1024;
        private static readonly object PortableReadLock = new object();

        static partial void ValidatePortableHeader(string line)
        {
            if (line.StartsWith("    2C", StringComparison.Ordinal) || line.StartsWith("    3C", StringComparison.Ordinal))
            {
                if (line.Length < 36 || !int.TryParse(line.Substring(6, 30), out int count) || count < 1 || count > 100000)
                    throw new InvalidDataException("Portable FRD mesh blocks require 1–100000 records.");
            }
            if (line.StartsWith("  100C", StringComparison.Ordinal))
            {
                if (line.Length < 36 || !int.TryParse(line.Substring(24, 12), out int count) || count < 1 || count > 100000)
                    throw new InvalidDataException("Portable FRD result blocks require 1–100000 records.");
            }
        }
        static partial void ValidatePortableComponents(int count)
        {
            if (count < 1 || count > 16) throw new InvalidDataException("Portable FRD supports 1–16 components per field.");
        }
        static partial void ValidatePortableAllocation(long count)
        {
            if (count < 0 || count > PortableMaximumBytes) throw new InvalidDataException("FRD binary allocation exceeds bounded input size.");
        }
        static partial void ValidatePortableTail(string[] lines)
        {
            var pending = lines.Where(l => !string.IsNullOrWhiteSpace(l)).ToArray();
            if (pending.Length != 1 || pending[0].Trim() != "9999")
                throw new InvalidDataException("Unclosed, truncated or trailing FRD data is not a complete result.");
        }
        public static FrdStaticSnapshot ReadStaticSnapshot(string fileName)
        {
            lock (PortableReadLock)
            {
                var culture = CultureInfo.CurrentCulture;
                try
                {
                    CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
                    if (fileName == null) throw new ArgumentNullException(nameof(fileName));
                    var info = new FileInfo(fileName);
                    if (!info.Exists) throw new FileNotFoundException("FRD file not found.", fileName);
                    if (info.Length == 0 || info.Length > PortableMaximumBytes) throw new InvalidDataException("FRD input must be nonempty and at most 64 MiB.");
                    if (fileName.ToUpperInvariant().Contains("RESULTSFORLASTITERATIONS.FRD"))
                        throw new NotSupportedException("Last-iteration results require full result preprocessing.");
                    byte[] bytes = File.ReadAllBytes(fileName);
                    string hash = Convert.ToHexStringLower(SHA256.HashData(bytes));
                    string tail = Encoding.ASCII.GetString(bytes, Math.Max(0, bytes.Length - 128), Math.Min(bytes.Length, 128));
                    if (!tail.TrimEnd().EndsWith("9999", StringComparison.Ordinal)) throw new InvalidDataException("A completed FRD terminal record is required.");
                    var sets = GetDataSets(fileName);
                    if (sets == null) throw new IOException("FRD file is unavailable.");
                    Dictionary<int, FeNode> nodes = null; Dictionary<int, int> lookup = null;
                    Dictionary<int, FeElement> elements = null;
                    var fields = new List<FrdStaticField>(); FieldData previous = null;
                    bool constantWidth = true; string unitHeader = null;
                    _bemaNodeIds = null;
                    foreach (var set in sets)
                    {
                        string id = set.Lines[0];
                        if (id.StartsWith("    1C", StringComparison.Ordinal))
                        {
                            if (nodes != null) throw new InvalidDataException("FRD heading must precede mesh.");
                            string space = GetModelSpace(set.Lines);
                            if (space != null && space != "3D" && space != "ThreeD") throw new NotSupportedException("Only raw 3D static fields are supported; no axisymmetric scaling is applied.");
                            unitHeader = set.Lines.FirstOrDefault(l => l.IndexOf("Unit system:", StringComparison.OrdinalIgnoreCase) >= 0);
                        }
                        else if (id.StartsWith("    2C", StringComparison.Ordinal))
                        {
                            if (nodes != null || elements != null || fields.Count > 0) throw new InvalidDataException("One ordered node block is required.");
                            if (set.IsBinary) nodes = GetNodesBinary(set, out lookup);
                            else { constantWidth = IsConstantWidth(set.Lines); nodes = GetNodes(set.Lines, constantWidth, out lookup); }
                            if (nodes.Count != int.Parse(id.Substring(6, 30)) || nodes.Any(n => n.Key <= 0 || !double.IsFinite(n.Value.X) || !double.IsFinite(n.Value.Y) || !double.IsFinite(n.Value.Z)))
                                throw new InvalidDataException("Incomplete or invalid FRD node block.");
                        }
                        else if (id.StartsWith("    3C", StringComparison.Ordinal))
                        {
                            if (nodes == null || elements != null || fields.Count > 0) throw new InvalidDataException("One element block after nodes is required.");
                            var empty = new HashSet<int>();
                            elements = set.IsBinary ? GetElementsBinary(set, empty, empty, empty, out _) : GetElements(set.Lines, empty, empty, empty, out _);
                            if (elements.Count != int.Parse(id.Substring(6, 30)) || elements.Any(e => e.Key <= 0 ||
                                (e.Value.GetType() != typeof(LinearHexaElement) && e.Value.GetType() != typeof(LinearTetraElement)) ||
                                e.Value.NodeIds.Any(n => !nodes.ContainsKey(n))))
                                throw new NotSupportedException("Only complete C3D8/C3D4 result meshes with valid node references are supported; quadratic tetrahedra remain gated.");
                        }
                        else if (id.StartsWith("    1PSTEP", StringComparison.Ordinal))
                        {
                            if (elements == null || fields.Count >= 64) throw new InvalidDataException("Fields require a complete mesh; at most 64 fields are supported.");
                            int line = 0; GetFieldHeaderData(set.Lines, ref line, previous, out var metadata, out int count);
                            if (metadata.StepType != StepTypeEnum.Static || count != nodes.Count || !float.IsFinite(metadata.Time))
                                throw new NotSupportedException("Only complete nodal fields in static steps are supported.");
                            ValidateOrder(set, line, count, lookup);
                            GetField(set, constantWidth, previous, lookup, out var data, out var field);
                            string[] required = field.Name switch
                            {
                                FOFieldNames.Disp => new[] { "U1", "U2", "U3" },
                                FOFieldNames.Forc => new[] { "F1", "F2", "F3" },
                                FOFieldNames.Stress => new[] { "S11", "S22", "S33", "S12", "S23", "S13" },
                                FOFieldNames.ToStrain => new[] { "E11", "E22", "E33", "E12", "E23", "E13" },
                                FOFieldNames.Error => new[] { "STR" },
                                _ => throw new NotSupportedException("Only displacement, force, stress, total-strain and stress-error fields are supported.")
                            };
                            if (!field.GetComponentNames().Where(n => n != FOComponentNames.All).ToHashSet().SetEquals(required))
                                throw new InvalidDataException("Unexpected component names for the field type.");
                            foreach (string component in field.GetComponentNames())
                                if (field.GetComponentValues(component).Any(v => !float.IsFinite(v))) throw new InvalidDataException("Nonfinite or malformed field value.");
                            if (!field.ContainsAllNecessaryComponents()) throw new InvalidDataException("Required field components are missing.");
                            if (fields.Any(f => f.Data.Name == data.Name && f.Data.StepId == data.StepId && f.Data.StepIncrementId == data.StepIncrementId))
                                throw new InvalidDataException("Duplicate field in one step/increment.");
                            field.ComputeInvariants();
                            if (field.GetComponentNames().Any(n => field.GetComponentValues(n).Any(v => !float.IsFinite(v))))
                                throw new InvalidDataException("Original derived field calculation is nonfinite.");
                            fields.Add(new FrdStaticField(data, field)); previous = new FieldData(data);
                        }
                        else throw new NotSupportedException("Unsupported FRD data block.");
                    }
                    if (nodes == null || elements == null || fields.Count == 0) throw new InvalidDataException("Complete mesh and at least one field are required.");
                    if (hash != Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(fileName)))) throw new IOException("FRD changed during inspection.");
                    return new FrdStaticSnapshot(hash, unitHeader, nodes, elements, lookup.OrderBy(p => p.Value).Select(p => p.Key).ToArray(), fields);
                }
                finally { CultureInfo.CurrentCulture = culture; _bemaNodeIds = null; }
            }
        }
        private static void ValidateOrder(FrdDataSet set, int line, int count, Dictionary<int, int> lookup)
        {
            int[] ids;
            if (set.IsBinary)
            {
                var components = set.Lines.Skip(line).ToArray(); ValidatePortableComponents(components.Length);
                int width = sizeof(int) + components.Count(IsResultsComponentStored) * GetBinaryValueSize(set.BinaryFormat);
                if (set.BinaryData.Length != (long)count * width) throw new InvalidDataException("Incomplete binary nodal values.");
                ids = Enumerable.Range(0, count).Select(i => BitConverter.ToInt32(set.BinaryData, i * width)).ToArray();
            }
            else
            {
                var values = set.Lines.Skip(line).Where(l => !l.StartsWith(" -5", StringComparison.Ordinal)).ToArray();
                ValidatePortableComponents(set.Lines.Length - line - values.Length);
                if (values.Length != count || values.Any(l => !l.StartsWith(" -1", StringComparison.Ordinal)))
                    throw new InvalidDataException("Complete single-record-per-node field values are required.");
                ids = values.Select(l => int.Parse(l.Substring(3, 10))).ToArray();
            }
            for (int i = 0; i < count; i++)
                if (!lookup.TryGetValue(ids[i], out int position) || position != i)
                    throw new NotSupportedException("Complete field records must follow node-block order; ambiguous original direct-index decoding is gated.");
        }
    }
}
