// PrePoMax-X portable reader boundary; parsing bodies are retained in
// InpFileReader.MeshParsing.cs from Matej Borovinšek's original implementation.
// Licensed under the root LICENSE.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using CaeGlobals;
using CaeMesh;
using CaeModel;

namespace FileInOut.Input
{
    static public partial class InpFileReader
    {
        private static readonly object _meshDataReadLock = new object();
        public const int MeshDataMaximumItems = 200000;
        public const int MeshDataMaximumCharacters = 16 * 1024 * 1024;

        // This entry point intentionally reads standalone mesh data, not materials,
        // BCs, steps, CAD or include files. Callers receive every omitted keyword.
        public static InpMeshData ReadMeshData(string[] lines)
        {
            if (lines == null) throw new ArgumentNullException("lines");
            if (lines.Length > MeshDataMaximumItems * 4 || lines.Any(line => line == null) ||
                lines.Sum(line => (long)line.Length + 1) > MeshDataMaximumCharacters)
                throw new CaeException("Mesh input exceeds the standalone reader limits or contains null lines.");
            lock (_meshDataReadLock)
            {
                var previousErrors = _errors;
                var previousWarnings = _warnings;
                var previousOutput = WriteDataToOutputStatic;
                var previousCulture = CultureInfo.CurrentCulture;
                var messages = new List<string>();
                try
                {
                    CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
                    _errors = new List<string>();
                    _warnings = new List<string>();
                    WriteDataToOutputStatic = messages.Add;
                    string[][] dataSets = GetDataSets(lines);
                    var nodes = new Dictionary<int, FeNode>();
                    var elements = new Dictionary<int, FeElement>();
                    var blocks = new List<InpElementSet>();
                    var nodeSets = new Dictionary<string, int[]>();
                    var elementSets = new Dictionary<string, int[]>();
                    var omitted = new List<string>();
                    foreach (string[] dataSet in dataSets)
                    {
                        string keyword = dataSet[0].Split(',')[0].Trim().ToUpperInvariant();
                        CheckMeshHeader(dataSet[0], keyword);
                        if (keyword == "*INCLUDE")
                            throw new CaeException("Standalone mesh input does not expand INCLUDE files; provide a flattened deck.");
                        if (keyword == "*NODE")
                        {
                            if (dataSet.Skip(1).Any(line =>
                            {
                                int count = line.Split(_splitter, StringSplitOptions.RemoveEmptyEntries).Length;
                                return count != 3 && count != 4;
                            })) throw new CaeException("Node records require ID, X, Y and optionally Z.");
                            string name;
                            HashSet<int> ids;
                            AddNodeCoordinates(dataSet, nodes, out name, out ids);
                            if (name != null) MergeMeshSet(nodeSets, name, ids);
                        }
                        else if (keyword == "*ELEMENT")
                        {
                            var block = new List<InpElementSet>();
                            AddElements(dataSet, ref elements, ref block);
                            if (block.Count != 1 || block[0].ElementLabels.Count == 0)
                                throw new CaeException("Element block is missing a valid type or connectivity.");
                            blocks.Add(block[0]);
                            if (block[0].Name != null) MergeMeshSet(elementSets, block[0].Name, block[0].ElementLabels);
                        }
                        else if (keyword != "*NSET" && keyword != "*ELSET") omitted.Add(dataSet[0]);
                        if (nodes.Count > MeshDataMaximumItems || elements.Count > MeshDataMaximumItems)
                            throw new CaeException("Mesh contains too many nodes or elements for this host.");
                    }
                    // As in the original model reader, sets are resolved after inline node/element sets exist.
                    foreach (string[] dataSet in dataSets)
                    {
                        string keyword = dataSet[0].Split(',')[0].Trim().ToUpperInvariant();
                        if (keyword != "*NSET" && keyword != "*ELSET") continue;
                        CheckMeshSetGeneration(dataSet);
                        string name;
                        int[] ids;
                        string kind = keyword.Substring(1);
                        var lookup = kind == "NSET" ? nodeSets : elementSets;
                        long expanded = 0;
                        foreach (string token in dataSet.Skip(1).SelectMany(line => line.Split(_splitter, StringSplitOptions.RemoveEmptyEntries)))
                        {
                            int[] referenced;
                            expanded += lookup.TryGetValue(token, out referenced) ? referenced.Length : 1;
                            if (expanded > MeshDataMaximumItems) throw new CaeException("Expanded set exceeds the host item limit.");
                        }
                        GetNodeOrElementSetData(kind, dataSet, (setKind, setName) =>
                        {
                            int[] labels;
                            var sets = setKind == "NSET" ? nodeSets : elementSets;
                            return sets.TryGetValue(setName, out labels) ? labels : null;
                        }, out name, out ids);
                        if (name == null || ids == null) throw new CaeException("Set definition could not be read.");
                        MergeMeshSet(kind == "NSET" ? nodeSets : elementSets, name, ids);
                    }
                    // AddError reports to both _errors and the callback. Warnings are valid inspect diagnostics.
                    var failures = _errors.Concat(messages.Where(message => !_warnings.Contains(message))).Distinct().ToArray();
                    if (failures.Length > 0) throw new CaeException(string.Join(Environment.NewLine, failures));
                    if (nodes.Count == 0 || elements.Count == 0) throw new CaeException("Mesh input must contain nodes and elements.");
                    foreach (var node in nodes.Values)
                        if (node.Id <= 0 || new[] { node.X, node.Y, node.Z }.Any(value => double.IsNaN(value) || double.IsInfinity(value)))
                            throw new CaeException("Mesh node IDs must be positive and coordinates finite.");
                    foreach (var element in elements.Values)
                        if (element.Id <= 0 || element.NodeIds.Any(id => !nodes.ContainsKey(id)))
                            throw new CaeException("Element IDs must be positive and connectivity must reference existing nodes.");
                    if (nodeSets.Values.Any(ids => ids.Any(id => !nodes.ContainsKey(id))) ||
                        elementSets.Values.Any(ids => ids.Any(id => !elements.ContainsKey(id))))
                        throw new CaeException("Mesh sets must reference existing node or element IDs.");
                    return new InpMeshData { Nodes = nodes, Elements = elements, ElementBlocks = blocks,
                        NodeSets = nodeSets, ElementSets = elementSets, Warnings = _warnings.ToArray(),
                        OmittedKeywords = omitted.Distinct().ToArray() };
                }
                finally
                {
                    _errors = previousErrors;
                    _warnings = previousWarnings;
                    WriteDataToOutputStatic = previousOutput;
                    CultureInfo.CurrentCulture = previousCulture;
                }
            }
        }

        private static void MergeMeshSet(Dictionary<string, int[]> sets, string name, IEnumerable<int> ids)
        {
            string error = NamedClass.CheckNameError(name, null);
            if (error != null) throw new CaeException(error);
            int[] previous;
            if (!sets.TryGetValue(name, out previous)) previous = new int[0];
            int[] labels = previous.Concat(ids).Distinct().OrderBy(id => id).ToArray();
            if (labels.Length > MeshDataMaximumItems) throw new CaeException("Mesh set exceeds the host item limit.");
            sets[name] = labels;
        }

        private static void CheckMeshHeader(string header, string keyword)
        {
            if (new[] { "*PART", "*ASSEMBLY", "*INSTANCE", "*SYSTEM", "*TRANSFORM" }.Contains(keyword))
                throw new CaeException("Scoped parts/assemblies and coordinate transforms require the full model reader.");
            string[] allowed = keyword == "*NODE" ? new[] { "NSET" } :
                               keyword == "*ELEMENT" ? new[] { "TYPE", "ELSET" } :
                               keyword == "*NSET" ? new[] { "NSET", "GENERATE" } :
                               keyword == "*ELSET" ? new[] { "ELSET", "GENERATE" } : null;
            if (allowed != null && header.Split(',').Skip(1).Any(token =>
                    !allowed.Contains(token.Split('=')[0].Trim().ToUpperInvariant())))
                throw new CaeException("Unsupported standalone mesh keyword parameter: " + header);
            if (allowed != null)
            {
                var seen = new HashSet<string>();
                foreach (string token in header.Split(',').Skip(1))
                {
                    string[] pair = token.Split('=');
                    string name = pair[0].Trim().ToUpperInvariant();
                    if (!seen.Add(name) || (name == "GENERATE" ? pair.Length != 1 : pair.Length != 2 || pair[1].Trim().Length == 0))
                        throw new CaeException("Invalid or duplicate standalone mesh parameter: " + header);
                }
            }
        }

        private static void CheckMeshSetGeneration(string[] lines)
        {
            if (!lines[0].Split(',').Any(token => token.Trim().Equals("GENERATE", StringComparison.OrdinalIgnoreCase))) return;
            long total = 0;
            foreach (string line in lines.Skip(1))
            {
                string[] fields = line.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);
                if (fields.Length < 2 || fields.Length > 3) throw new CaeException("Invalid GENERATE range.");
                int first = int.Parse(fields[0]);
                int last = int.Parse(fields[1]);
                int step = fields.Length == 3 ? int.Parse(fields[2]) : 1;
                if (first <= 0 || last < first || step <= 0 || (long)last + step > int.MaxValue)
                    throw new CaeException("GENERATE ranges require positive, increasing, bounded IDs and step.");
                total += ((long)last - first) / step + 1;
                if (total > MeshDataMaximumItems) throw new CaeException("Generated set exceeds the host item limit.");
            }
        }
    }
}
