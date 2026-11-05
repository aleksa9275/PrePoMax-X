using System.Formats.Nrbf;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;

internal static partial class StaticGraph
{
    internal sealed record CadPart(string Name,int Id,string Brep,string BrepSha256,int[] Nodes,int[] Elements);

    internal static CadPart[] ReadCadGeometry(SerializationRecord root)
    {
        var model=Record(Controller(root).GetRawValue("_model"),"CaeModel.FeModel");
        var geometry=Record(model.GetRawValue("_geometry"),"CaeMesh.FeMesh");
        return Entries(geometry,"_parts").Select(pair=>{
            var part=Named(pair,"CaeMesh.GeometryPart");Active(part);
            string encoded=part.GetString("_cadFileData") ?? throw new InvalidDataException("Missing CAD BREP.");
            if(encoded.Length>24*1024*1024) throw new InvalidDataException("Compressed CAD data exceeds its limit.");
            byte[] bytes=Convert.FromBase64String(encoded);
            if(bytes.Length<5)throw new InvalidDataException("Truncated compressed CAD string.");
            int length=System.Buffers.Binary.BinaryPrimitives.ReadInt32LittleEndian(bytes);
            if(length<1 || length>16*1024*1024)throw new InvalidDataException("CAD string exceeds 16 MiB.");
            // Original StringCompressor framing: little-endian UTF8 byte length + GZip.
            using var input=new MemoryStream(bytes,4,bytes.Length-4,false);
            using var gzip=new GZipStream(input,CompressionMode.Decompress);
            byte[] text=new byte[length];gzip.ReadExactly(text);
            if(gzip.ReadByte()!=-1)throw new InvalidDataException("CAD decompressed length mismatch.");
            string brep=new UTF8Encoding(false,true).GetString(text);
            if(!brep.Contains("CASCADE Topology",StringComparison.Ordinal))throw new InvalidDataException("Expected original BREP CAD data.");
            return new CadPart(pair.Key,part.GetInt32("_partId"),brep,Convert.ToHexStringLower(SHA256.HashData(text)),
                Labels(part,"_nodeLabels"),Labels(part,"_labels"));
        }).ToArray();
    }

    private static void ValidateCadHistory(SerializationRecord root)
    {
        var history=Record(Controller(root).GetRawValue("_commands"),"PrePoMax.Commands.CommandsCollection");
        var commands=List(history.GetRawValue("_commands")).Select(v=>Record(v).TypeName.FullName).ToArray();
        string[] expected={"PrePoMax.Commands.CClear","PrePoMax.Commands.CSetNewModelProperties","PrePoMax.Commands.CImportFile"};
        if(!commands.SequenceEqual(expected) || history.GetInt32("_currPositionIndex")!=2)
            throw new InvalidDataException("Only the checked initial CAD import history is supported; history is preserved, not replayed.");
    }

    private static void ValidateCadGeometry(SerializationRecord root)
    {
        var parts=ReadCadGeometry(root);
        var model=Record(Controller(root).GetRawValue("_model"),"CaeModel.FeModel");
        var geometry=Record(model.GetRawValue("_geometry"),"CaeMesh.FeMesh");
        var mesh=Record(model.GetRawValue("_mesh"),"CaeMesh.FeMesh");
        var meshParts=Entries(mesh,"_parts").ToArray();
        if(parts.Length!=1 || meshParts.Length!=1 || parts[0].Name!=meshParts[0].Key ||
            parts[0].Id!=meshParts[0].Value.GetInt32("_partId"))
            throw new InvalidDataException("Expected one matching CAD/analysis part.");
        foreach(var part in new[]{Entries(geometry,"_parts").Single().Value,meshParts[0].Value})
        {
            if(part.GetRawValue("_geometryToMeshTransform")!=null)
                throw new InvalidDataException("CAD PMX transformations are outside this editing boundary.");
            var offset=(double[])BoundedArray(part.GetRawValue("_offset"),3).GetArray(typeof(double[]));
            if(offset.Length!=3 || offset.Any(v=>v!=0))
                throw new InvalidDataException("Exploded/transformed CAD PMX offsets are not supported.");
        }
        EmptyDictionaries(geometry,"_nodeSets","_elementSets","_surfaces","_referencePoints","_coordinateSystems");
        // Original geometry and mesh setup records remain opaque and byte-preserved.
        // The controlled editor changes neither their topology nor parameters.
    }
}
