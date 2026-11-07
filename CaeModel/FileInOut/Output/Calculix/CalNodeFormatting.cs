// Original CalNode 3D formatting shared with the bounded CAD PMX deck adapter.
// PrePoMax - Copyright (C) 2016-2026 Matej Borovinsek; see root LICENSE.
using System.Collections.Generic;
using System.Linq;
using System.Text;
using CaeMesh;
namespace FileInOut.Output.Calculix
{
    public static class CalNodeFormatting
    {
        internal static void Append3D(StringBuilder sb, FeNode node)
        {
            sb.AppendFormat("{0}, {1:E8}, {2:E8}, {3:E8}", node.Id, node.X, node.Y, node.Z).AppendLine();
        }
        public static string Write3D(IDictionary<int, FeNode> nodes)
        {
            var text = new StringBuilder("*Node\n");
            foreach (int id in nodes.Keys.OrderBy(i => i)) Append3D(text, nodes[id]);
            return text.ToString();
        }
        public static string Write2D(IDictionary<int, FeNode> nodes)
        {
            var text = new StringBuilder("*Node\n");
            foreach (int id in nodes.Keys.OrderBy(i => i))
            {
                var node = nodes[id];
                // Original CalNode.WriteNodes two-dimensional branch.
                text.AppendFormat("{0}, {1:E8}, {2:E8}", node.Id, node.X, node.Y).AppendLine();
            }
            return text.ToString();
        }
    }
}
