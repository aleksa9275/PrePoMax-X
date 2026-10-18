// PrePoMax-X portable mesh exchange boundary. Original engineering types and
// algorithms remain owned by PrePoMax / Matej Borovinšek. See root LICENSE.
using System.Collections.Generic;
using CaeMesh;

namespace CaeModel
{
    // An in-memory reader result, not a persisted document or a replacement FeModel.
    public sealed class InpMeshData
    {
        public Dictionary<int, FeNode> Nodes { get; internal set; }
        public Dictionary<int, FeElement> Elements { get; internal set; }
        public List<InpElementSet> ElementBlocks { get; internal set; }
        public Dictionary<string, int[]> NodeSets { get; internal set; }
        public Dictionary<string, int[]> ElementSets { get; internal set; }
        public string[] Warnings { get; internal set; }
        public string[] OmittedKeywords { get; internal set; }
    }
}
