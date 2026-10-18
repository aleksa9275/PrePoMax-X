// PrePoMax-X mesh-only boundary. Element formatting/conversion is delegated to
// Matej Borovinšek's original CalElement implementation. See root LICENSE.
using System;
using System.Globalization;
using System.Linq;
using System.Text;
using CaeGlobals;
using CaeMesh;

namespace CaeModel
{
    public static class MeshDeckWriter
    {
        // This is not CalculixFileWriter.GetModelKeywords: materials, loads, steps,
        // surfaces and other omitted model keywords are intentionally not written.
        public static string WriteMesh(InpMeshData mesh, ConvertPyramidsToEnum? pyramidConversion = null)
        {
            if (mesh == null) throw new ArgumentNullException("mesh");
            if (mesh.Warnings.Length != 0)
                throw new CaeException("Mesh export refuses formulation fallback warnings; use a supported input formulation.");
            bool pyramids = mesh.Elements.Values.Any(element => element is LinearPyramidElement || element is ParabolicPyramidElement);
            if (pyramids && !pyramidConversion.HasValue)
                throw new CaeException("Pyramid export requires an explicit conversion to collapsed wedges or hexahedrons.");
            if (pyramidConversion.HasValue && !Enum.IsDefined(typeof(ConvertPyramidsToEnum), pyramidConversion.Value))
                throw new ArgumentOutOfRangeException("pyramidConversion");
            var previousCulture = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
                var text = new StringBuilder("** PrePoMax-X mesh-only export; model definitions are omitted.\n*Node\n");
                // Roundtrip precision belongs to this transport boundary; engineering coordinates are unchanged.
                foreach (var node in mesh.Nodes.Values.OrderBy(node => node.Id))
                    text.AppendFormat(CultureInfo.InvariantCulture, "{0}, {1:G17}, {2:G17}, {3:G17}\n", node.Id, node.X, node.Y, node.Z);
                foreach (var block in mesh.ElementBlocks)
                {
                    string elementType = block.InpElementTypeNames.Single();
                    // All supported pyramid aliases enter the explicitly requested
                    // original conversion path, including the I/R input aliases.
                    if (mesh.Elements[block.ElementLabels.First()] is LinearPyramidElement) elementType = "C3D5";
                    else if (mesh.Elements[block.ElementLabels.First()] is ParabolicPyramidElement) elementType = "C3D13";
                    var keyword = new FileInOut.Output.Calculix.CalElement(elementType, block.Name,
                        block.ElementLabels.Select(id => mesh.Elements[id]).ToList(), pyramidConversion ?? ConvertPyramidsToEnum.Wedges);
                    text.Append(keyword.GetKeywordString()).Append(keyword.GetDataString());
                }
                foreach (var entry in mesh.NodeSets)
                {
                    text.Append("*Nset, Nset=").Append(entry.Key).AppendLine();
                    AppendLabels(text, entry.Value);
                }
                foreach (var entry in mesh.ElementSets)
                {
                    text.Append("*Elset, Elset=").Append(entry.Key).AppendLine();
                    AppendLabels(text, entry.Value);
                }
                return text.ToString();
            }
            finally { CultureInfo.CurrentCulture = previousCulture; }
        }

        private static void AppendLabels(StringBuilder text, int[] labels)
        {
            for (int i = 0; i < labels.Length; i += 8)
                text.AppendLine(string.Join(", ", labels.Skip(i).Take(8)));
        }
    }
}
