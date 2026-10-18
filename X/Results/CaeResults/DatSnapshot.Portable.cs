// PrePoMax-X bounded DAT inspection. Original DAT decoding and history entry
// operations remain in the shared original partials; full orchestration is legacy.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace CaeResults
{
    public sealed class DatStaticHistory
    {
        public string SetName { get; }
        public string BaseSetName { get; }
        public string FieldName { get; }
        public string ComponentName { get; }
        public int StepId { get; }
        public int Id { get; }
        public int? IntegrationPoint { get; }
        public HistoryResultEntries Entries { get; }
        public IReadOnlyList<int> IncrementIds { get; }
        internal List<int> Increments { get; } = new List<int>();
        internal DatStaticHistory(DatDataSet data, string component, int id, int? point, bool local)
        {
            SetName = data.SetName; BaseSetName = data.BaseSetName; FieldName = data.FieldName;
            ComponentName = component; StepId = data.StepId; Id = id; IntegrationPoint = point;
            Entries = new HistoryResultEntries(point.HasValue ? id + "_" + point.Value : id.ToString(CultureInfo.InvariantCulture), local);
            IncrementIds = Increments.AsReadOnly();
        }
    }
    public sealed class DatStaticSnapshot
    {
        public string SourceSha256 { get; }
        public int DataSetCount { get; }
        public IReadOnlyList<DatStaticHistory> Histories { get; }
        internal DatStaticSnapshot(string hash, int count, List<DatStaticHistory> histories)
        { SourceSha256 = hash; DataSetCount = count; Histories = histories.AsReadOnly(); }
    }
    public static partial class DatFileReader
    {
        private const int PortableDatMaxBytes = 8 * 1024 * 1024;
        private static readonly Dictionary<string, string> PortableDatHeaders = new Dictionary<string, string>
        {
            {"displacements", "(vx,vy,vz)"}, {"forces", "(fx,fy,fz)"},
            {"stresses", "(elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz)"},
            {"strains", "(elem, integ.pnt.,exx,eyy,ezz,exy,exz,eyz)"}
        };
        // DAT has no reliable completion trailer. This API inspects stored blocks;
        // a successful parse does not prove that a solver job finished.
        public static DatStaticSnapshot ReadStaticSnapshot(string fileName)
        {
            if (string.IsNullOrWhiteSpace(fileName)) throw new ArgumentException("A DAT path is required.");
            byte[] bytes;
            using (var file = File.OpenRead(fileName))
            {
                if (file.Length == 0 || file.Length > PortableDatMaxBytes) throw new InvalidDataException("DAT size must be 1 byte to 8 MiB.");
                bytes = new byte[(int)file.Length]; file.ReadExactly(bytes);
                if (file.ReadByte() != -1) throw new InvalidDataException("DAT changed during inspection.");
            }
            string hash = Convert.ToHexStringLower(SHA256.HashData(bytes));
            var culture = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
                string text = new UTF8Encoding(false, true).GetString(bytes);
                if (text.Length > 0 && text[0] == '\uFEFF') text = text.Substring(1);
                string[] lines = text.Replace("\r\n", "\n").Split('\n').Select(l => l.Trim()).ToArray();
                ValidatePortableDatLines(lines);
                var repaired = new Dictionary<string, string>();
                var blocks = SplitToDataSetLinesList(lines, repaired, out bool steady).ToArray();
                if (steady) throw new NotSupportedException("Steady-state DAT is outside this inspection boundary.");
                Repair(blocks);
                int step = -1, increment = -1, count = 0, scalarCount = 0;
                var histories = new Dictionary<(int step, string set, string field, string component, int id, int? point), DatStaticHistory>();
                var seenBlocks = new HashSet<(int step, int increment, string set, string field)>();
                foreach (string[] block in blocks)
                {
                    if (block[0].StartsWith(_stepKey, StringComparison.Ordinal))
                    { step = int.Parse(block[0].Substring(_stepKey.Length)); increment = -1; continue; }
                    if (block[0].StartsWith(_incrementKey, StringComparison.Ordinal))
                    { increment = int.Parse(block[0].Substring(_incrementKey.Length)); continue; }
                    DatDataSet data = GetDatDataSet(block, repaired, new Dictionary<string, string>());
                    data.StepId = step; data.IncrementId = increment;
                    if (step < 1 || increment < 1) throw new InvalidDataException("Missing DAT step/increment context.");
                    if (data.FieldName == HOFieldNames.Error || data.Values == null || data.Values.Length == 0 ||
                        !double.IsFinite(data.Time) || data.Time < 0 || string.IsNullOrEmpty(data.SetName))
                        throw new InvalidDataException("Invalid DAT dataset.");
                    if (++count > 256 || !seenBlocks.Add((step, increment, data.SetName, data.FieldName)))
                        throw new InvalidDataException("Too many or duplicate DAT datasets.");
                    bool tensor = data.FieldName == HOFieldNames.Stresses || data.FieldName == HOFieldNames.Strains;
                    string[] expected = tensor ? (data.FieldName == HOFieldNames.Stresses ?
                        new[] {"Id", "Int.Pnt.", "S11", "S22", "S33", "S12", "S13", "S23"} :
                        new[] {"Id", "Int.Pnt.", "E11", "E22", "E33", "E12", "E13", "E23"}) :
                        (data.FieldName == HOFieldNames.Displacements ? new[] {"Id", "U1", "U2", "U3"} : new[] {"Id", "RF1", "RF2", "RF3"});
                    if (!data.ComponentNames.SequenceEqual(expected) || data.Values.Length > 100000)
                        throw new InvalidDataException("Unsupported DAT component layout or size.");
                    var identities = new HashSet<(int id, int? point)>();
                    for (int row = 0; row < data.Values.Length; row++)
                    {
                        double[] values = data.Values[row];
                        if (values.Length != expected.Length || values.Any(v => !double.IsFinite(v))) throw new InvalidDataException("Malformed DAT row.");
                        int id = PortableDatId(values[0]); int? point = tensor ? PortableDatId(values[1]) : (int?)null;
                        if (!identities.Add((id, point))) throw new InvalidDataException("Duplicate DAT row identity.");
                        for (int component = tensor ? 2 : 1; component < values.Length; component++)
                        {
                            if (++scalarCount > 250000) throw new InvalidDataException("DAT sample limit exceeded.");
                            var key = (step, data.SetName, data.FieldName, expected[component], id, point);
                            if (!histories.TryGetValue(key, out DatStaticHistory history))
                            {
                                if (histories.Count >= 100000) throw new InvalidDataException("DAT history limit exceeded.");
                                history = new DatStaticHistory(data, expected[component], id, point, data.Locals[row]); histories.Add(key, history);
                            }
                            if (history.Entries.Local != data.Locals[row] ||
                                (history.Entries.Time.Count > 0 && history.Entries.Time.Last() >= data.Time))
                                throw new InvalidDataException("Mixed coordinate systems or non-increasing DAT history time.");
                            history.Entries.Add(data.Time, values[component]); history.Increments.Add(increment);
                        }
                    }
                }
                if (count == 0) throw new InvalidDataException("No supported DAT datasets.");
                using (var file = File.OpenRead(fileName))
                    if (file.Length != bytes.Length || Convert.ToHexStringLower(SHA256.HashData(file)) != hash)
                        throw new InvalidDataException("DAT changed during inspection.");
                return new DatStaticSnapshot(hash, count, histories.Values.ToList());
            }
            finally { CultureInfo.CurrentCulture = culture; }
        }
        private static int PortableDatId(double value)
        {
            if (value < 1 || value > int.MaxValue || value != Math.Truncate(value)) throw new InvalidDataException("DAT IDs must be positive integers.");
            return (int)value;
        }
        private static void ValidatePortableDatLines(string[] lines)
        {
            int step = -1, increment = -1, rows = 0; bool field = false;
            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i];
                if (line.Length > 4096 || line.Contains('\0')) throw new InvalidDataException("Invalid DAT line.");
                if (line.Length == 0) { if (field && rows > 0) { field = false; rows = 0; } continue; }
                if (line.StartsWith(_stepKey, StringComparison.Ordinal))
                {
                    if (field || !int.TryParse(line.Substring(_stepKey.Length), out int next) || next <= step || next < 1)
                        throw new InvalidDataException("Invalid DAT step order.");
                    if (i + 1 < lines.Length && lines[i + 1].Length != 0) throw new InvalidDataException("DAT metadata requires a separator line.");
                    step = next; increment = -1; continue;
                }
                if (line.StartsWith(_incrementKey, StringComparison.Ordinal))
                {
                    if (field || step < 1 || !int.TryParse(line.Substring(_incrementKey.Length), out int next) || next <= increment || next < 1)
                        throw new InvalidDataException("Invalid DAT increment order.");
                    if (i + 1 < lines.Length && lines[i + 1].Length != 0) throw new InvalidDataException("DAT metadata requires a separator line.");
                    increment = next; continue;
                }
                var header = PortableDatHeaders.FirstOrDefault(pair => line.StartsWith(pair.Key + " ", StringComparison.Ordinal));
                if (header.Key != null)
                {
                    string prefix = header.Key + " " + header.Value + " for set ";
                    if (field || step < 1 || increment < 1 || !line.StartsWith(prefix, StringComparison.Ordinal) ||
                        !Regex.IsMatch(line.Substring(prefix.Length), @"^[A-Za-z0-9_-]{1,79} and time\s+[+\-0-9.Ee]+$", RegexOptions.CultureInvariant, TimeSpan.FromSeconds(1)))
                        throw new InvalidDataException("Unsupported DAT header; use explicit step/increment and plain set names.");
                    if (line.Contains("_Ref_", StringComparison.OrdinalIgnoreCase) || line.Contains("_Rot_", StringComparison.OrdinalIgnoreCase))
                        throw new NotSupportedException("Reference-point histories require full result preprocessing.");
                    field = true; rows = 0; continue;
                }
                if (!field || !Regex.IsMatch(line, @"^[+\-0-9.Ee ]+( L)?$", RegexOptions.CultureInvariant, TimeSpan.FromSeconds(1)))
                    throw new NotSupportedException("Unsupported or unexpected DAT record.");
                rows++;
            }
            if (field && rows == 0) throw new InvalidDataException("Empty final DAT dataset.");
        }
    }
}
