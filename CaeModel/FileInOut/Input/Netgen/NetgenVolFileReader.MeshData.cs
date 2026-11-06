// PrePoMax-X bounded VOL transport. Original parsing and element permutations
// are shared with the Windows reader in NetgenVolFileReader.Parsing.cs.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using CaeMesh;
using CaeModel;

namespace FileInOut.Input
{
    public sealed class NetgenLinearSolidData
    {
        public int ElementOrder { get; internal set; }
        public Dictionary<int, FeNode> Nodes { get; internal set; }
        public Dictionary<int, FeElement> Elements { get; internal set; }
        public Dictionary<int, HashSet<int>> FaceNodeIds { get; internal set; }
        public Dictionary<int, HashSet<int>> EdgeNodeIds { get; internal set; }
    }

    public static partial class NetgenVolFileReader
    {
        public static InpMeshData CreateLinearSolidMesh(Dictionary<int, FeNode> nodes,
            Dictionary<int, FeElement> elements, List<InpElementSet> blocks,
            Dictionary<string, int[]> nodeSets, Dictionary<string, int[]> elementSets)
        {
            if (elements.Count == 0 || elements.Values.Any(e => !(e is LinearTetraElement)))
                throw new NotSupportedException("Only first-order tetrahedra may enter this native mesh transport.");
            return new InpMeshData { Nodes = nodes, Elements = elements, ElementBlocks = blocks,
                NodeSets = nodeSets, ElementSets = elementSets, Warnings = new string[0], OmittedKeywords = new string[0] };
        }

        public static NetgenLinearSolidData ReadLinearSolidData(string text)
        { return ReadSolidData(text, false); }

        // Transport never calls the gated quadratic measure/integration code.
        public static NetgenLinearSolidData ReadQuadraticSolidData(string text)
        { return ReadSolidData(text, true); }

        // Compatibility with the task 0084 preview API.
        public static NetgenLinearSolidData ReadQuadraticPreviewData(string text)
        { return ReadQuadraticSolidData(text); }

        private static NetgenLinearSolidData ReadSolidData(string text, bool quadratic)
        {
            if (string.IsNullOrWhiteSpace(text) || text.Length > 16 * 1024 * 1024)
                throw new InvalidDataException("VOL input must be nonempty and at most 16 MiB.");
            var dataSets = GetDataSets(text.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n'));
            var dimensions = dataSets.Where(s => s.Count > 0 && s[0] == "dimension").ToArray();
            if (dimensions.Length != 1 || dimensions[0].Count < 2 || dimensions[0][1] != "3")
                throw new InvalidDataException("A 3D VOL mesh is required.");
            var seen = new HashSet<string>();
            Dictionary<int, FeNode> nodes = null;
            var elements = new Dictionary<int, FeElement>();
            var surfaces = new Dictionary<int, HashSet<int>>();
            var edges = new Dictionary<int, HashSet<int>>();
            var vertices = new HashSet<int>();
            int next = 1;
            foreach (var set in dataSets)
            {
                if (set.Count == 0) continue;
                string kind = set[0];
                if (kind != "points" && kind != "volumeelements" && kind != "surfaceelementsuv" &&
                    kind != "surfaceelements" && kind != "edgesegmentsgi2") continue;
                if (!seen.Add(kind) || (kind == "surfaceelements" && seen.Contains("surfaceelementsuv")) ||
                    (kind == "surfaceelementsuv" && seen.Contains("surfaceelements")))
                    throw new InvalidDataException("Duplicate VOL mesh section.");
                if (set.Count < 2 || !int.TryParse(set[1], out int count) || count < 1 || count > 100000 ||
                    set.Count < count + 2 || (long)next + count > 300001)
                    throw new InvalidDataException("Incomplete or oversized VOL mesh section.");
                for (int i = 2; i < count + 2; i++)
                {
                    var row = set[i].Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (kind == "points" && row.Length != 3)
                        throw new InvalidDataException("VOL point needs three coordinates.");
                    if (kind == "volumeelements" && (row.Length != (quadratic ? 12 : 6) || row[1] != (quadratic ? "10" : "4")))
                        throw new NotSupportedException("Mesh order differs from the requested linear or quadratic profile.");
                    if ((kind == "surfaceelements" || kind == "surfaceelementsuv") &&
                        (row.Length < (quadratic ? 11 : 8) || row[4] != (quadratic ? "6" : "3")))
                        throw new NotSupportedException("Tetrahedral mesh order must match its CAD triangles.");
                    if (kind == "edgesegmentsgi2" && row.Length < 12)
                        throw new InvalidDataException("Incomplete VOL edge segment.");
                }
                string[] lines = set.ToArray();
                if (kind == "points") nodes = GetNodes(lines);
                else if (kind == "volumeelements") AddVolumeElements(lines, elements, ref next);
                else if (kind == "edgesegmentsgi2") AddLineElements(lines, elements, ref next, edges, vertices);
                else AddSurfaceElements(lines, elements, ref next, surfaces);
            }
            if (nodes == null || surfaces.Count == 0 || edges.Count == 0 || !seen.Contains("volumeelements") ||
                nodes.Values.Any(n => !Finite(n.X) || !Finite(n.Y) || !Finite(n.Z)) ||
                elements.Values.Any(e => e.NodeIds.Any(id => !nodes.ContainsKey(id)) ||
                    e.NodeIds.Distinct().Count() != e.NodeIds.Length) ||
                surfaces.Keys.Any(id => id < 1) || edges.Keys.Any(id => id < 1))
                throw new InvalidDataException("Incomplete or invalid native solid mesh.");
            var solid = elements.Where(e => quadratic ? e.Value is ParabolicTetraElement : e.Value is LinearTetraElement).ToDictionary(e => e.Key, e => e.Value);
            if (solid.Count == 0 || solid.Values.SelectMany(e => e.NodeIds).Distinct().Count() != nodes.Count ||
                solid.Values.Any(e => e.PartId < 1 || !Finite(CornerVolume(e, nodes)) ||
                    CornerVolume(e, nodes) <= 0))
                throw new InvalidDataException("Native tetrahedra require used nodes and positive original signed volumes.");
            if (quadratic)
            {
                var midsides = new Dictionary<string, int>();
                var inverse = new Dictionary<int, string>();
                var corners = new HashSet<int>(solid.Values.SelectMany(e => e.NodeIds.Take(4)));
                int[][] localEdges = { new[] {0,1}, new[] {1,2}, new[] {2,0}, new[] {0,3}, new[] {1,3}, new[] {2,3} };
                foreach (var e in solid.Values)
                    for (int i = 0; i < 6; i++)
                    {
                        string key = FaceKey(localEdges[i].Select(n => e.NodeIds[n]));
                        int mid = e.NodeIds[4+i];
                        if (corners.Contains(mid) || (midsides.TryGetValue(key, out int other) && other != mid) ||
                            (inverse.TryGetValue(mid, out string previous) && previous != key))
                            throw new InvalidDataException("Quadratic edges require one distinct shared midside node.");
                        midsides[key] = mid; inverse[mid] = key;
                    }
                foreach (var triangle in elements.Values.OfType<ParabolicTriangleElement>())
                    for (int i = 0; i < 3; i++)
                        if (!midsides.TryGetValue(FaceKey(new[] {triangle.NodeIds[i], triangle.NodeIds[(i+1)%3]}), out int mid) ||
                            mid != triangle.NodeIds[i+3])
                            throw new InvalidDataException("CAD triangle midsides do not match their tetrahedron edges.");
                foreach (var beam in elements.Values.OfType<LinearBeamElement>())
                {
                    if (!midsides.TryGetValue(FaceKey(beam.NodeIds), out int mid))
                        throw new InvalidDataException("CAD edge is not a quadratic tetrahedron edge.");
                    foreach (var edge in edges.Values)
                        if (edge.IsSupersetOf(beam.NodeIds)) edge.Add(mid);
                }
            }
            // Check the volume/surface incidence independently of the original parse.
            var faces = new Dictionary<string, int>();
            foreach (var e in solid.Values)
                foreach (int[] face in ((FeElement3D)e).GetAllVtkCells())
                {
                    string key = FaceKey(face);
                    faces[key] = faces.TryGetValue(key, out int n) ? n + 1 : 1;
                }
            var surfaceKeys = new HashSet<string>();
            foreach (var e in elements.Values.Where(e => quadratic ? e is ParabolicTriangleElement : e is LinearTriangleElement))
                if (!surfaceKeys.Add(FaceKey(e.NodeIds)))
                    throw new InvalidDataException("Repeated native surface triangle.");
            // Internal interfaces of conforming multi-solid compounds may be stored
            // as CAD surfaces too. They must still be actual tetrahedron faces.
            if (faces.Values.Any(n => n > 2) || surfaceKeys.Any(k => !faces.ContainsKey(k)) ||
                faces.Any(f => f.Value == 1 && !surfaceKeys.Contains(f.Key)))
                throw new InvalidDataException("Native volume boundary does not conform to its CAD surfaces.");
            return new NetgenLinearSolidData { ElementOrder = quadratic ? 2 : 1, Nodes = nodes, Elements = solid,
                FaceNodeIds = surfaces, EdgeNodeIds = edges };
        }

        public static InpMeshData CreateQuadraticSolidMesh(Dictionary<int, FeNode> nodes,
            Dictionary<int, FeElement> elements, List<InpElementSet> blocks,
            Dictionary<string, int[]> nodeSets, Dictionary<string, int[]> elementSets)
        {
            if (elements.Count == 0 || elements.Values.Any(e => !(e is ParabolicTetraElement)))
                throw new NotSupportedException("Quadratic transport requires C3D10 tetrahedra only.");
            return new InpMeshData { Nodes = nodes, Elements = elements, ElementBlocks = blocks,
                NodeSets = nodeSets, ElementSets = elementSets, Warnings = new string[0], OmittedKeywords = new string[0] };
        }

        private static double CornerVolume(FeElement e, Dictionary<int, FeNode> nodes)
        { return new LinearTetraElement(e.Id, e.NodeIds.Take(4).ToArray()).GetVolume(nodes); }

        private static string FaceKey(IEnumerable<int> ids) { return string.Join(",", ids.OrderBy(i => i)); }
        private static bool Finite(double v) { return !double.IsNaN(v) && !double.IsInfinity(v); }
    }
}
