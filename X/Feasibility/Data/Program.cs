// PrePoMax-X feasibility assertions. All engineering implementations are source-linked unchanged.
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.Serialization;
using System.Text;
using System.Text.Json;
using CaeMesh;
using CaeResults;
using CaeGlobals;

namespace PrePoMaxX.DataProbe;

internal static class Program
{
    private static readonly List<object> Checks = new();
    private static readonly SortedDictionary<string, object> Observations = new();
    private static int failed;
    private static void Check(string name, Action action)
    {
        try { action(); Checks.Add(new { name, status = "passed" }); }
        catch (Exception e) { failed++; Checks.Add(new { name, status = "failed", error = e.GetBaseException().Message }); }
    }
    private static void Require(bool value) { if (!value) throw new Exception("Independent expected contract was not met."); }
    private static void Near(double actual, double expected) => Require(Math.Abs(actual - expected) <= 1e-12 * Math.Max(1, Math.Abs(expected)));
    private static void Throws<T>(Action action) where T : Exception
    {
        try { action(); } catch (Exception e) { if (e.GetBaseException() is T) return; throw; }
        throw new Exception("Expected " + typeof(T).Name);
    }
    private static GeometryMetadataEntity Entity(string kind, int id, string name, double[] values)
    {
        var entity = new GeometryMetadataEntity(kind, id);
        entity.Properties[name] = new GeometryMetadataProperty(values);
        return entity;
    }
    private static GeometryMetadata Metadata()
    {
        var data = new GeometryMetadata(2, "global", "mm");
        data.AddEntity(Entity("face", 41, "area", new double[] { 12.5 }));
        data.AddEntity(Entity("face", 7, "edge_ids", new double[] { 8, 13 }));
        var edge = Entity("edge", 8, "length", new double[] { 2.75 });
        edge.Properties["label"] = new GeometryMetadataProperty(new string[] { "é-edge", null, "" });
        data.AddEntity(edge);
        return data;
    }
    private static SerializationInfo Info(GeometryMetadata data)
    {
        // Framework metadata API only: no BinaryFormatter, file deserialization or type binder is invoked.
        var info = new SerializationInfo(typeof(GeometryMetadata), new FormatterConverter());
        data.GetObjectData(info, new StreamingContext());
        return info;
    }
    private sealed class ReconstructedMetadata : GeometryMetadata
    {
        public ReconstructedMetadata(SerializationInfo info) : base(info, new StreamingContext()) { }
    }
    private static GeometryMetadata Restore(byte[] block)
    {
        var info = new SerializationInfo(typeof(GeometryMetadata), new FormatterConverter());
        info.AddValue("_formatVersion", 2); info.AddValue("_coordinateSystem", "global");
        info.AddValue("_lengthUnit", "mm"); info.AddValue("_entityData", block);
        return new ReconstructedMetadata(info);
    }
    private static byte[] ExpectedSingleFaceBlock()
    {
        // Independently specified wire bytes: one kind/one entity/one numeric property/one IEEE double.
        // BinaryWriter uses little-endian integers/doubles and a length-prefixed UTF-8 string.
        return new byte[] { 1,0,0,0, 4,102,97,99,101, 1,0,0,0, 4,102,97,99,101,
                            41,0,0,0, 1,0,0,0, 4,97,114,101,97, 1, 1,0,0,0,
                            0,0,0,0,0,0,41,64 }; // 12.5
    }
    private sealed class FragmentedStream : MemoryStream
    {
        private readonly int chunk;
        public FragmentedStream(byte[] data, int chunk) : base(data) { this.chunk = chunk; }
        public override int Read(byte[] buffer, int offset, int count) => base.Read(buffer, offset, Math.Min(chunk, count));
    }
    private static FrdStreamReader Reader(byte[] bytes, int chunk = int.MaxValue) => new(new FragmentedStream(bytes, chunk));
    private static void Run()
    {
        Check("matrix_inverse_matches_independent_two_by_two_solution", () => {
            double[][] a={new double[]{4,7},new double[]{2,6}};var inv=Matrix.MatrixInverse(a);
            Near(inv[0][0],0.6);Near(inv[0][1],-0.7);Near(inv[1][0],-0.2);Near(inv[1][1],0.4);
            Require(a[0].SequenceEqual(new double[]{4,7}) && a[1].SequenceEqual(new double[]{2,6}));
            Observations["matrixInverse"]=inv;
        });
        Check("matrix_inverse_pivots_zero_leading_diagonal", () => {
            var inv=Matrix.MatrixInverse(new double[][]{new double[]{0,2},new double[]{1,3}});
            Near(inv[0][0],-1.5);Near(inv[0][1],1);Near(inv[1][0],0.5);Near(inv[1][1],0);
        });
        Check("matrix_rectangular_product_matches_independent_values", () => {
            var c=Matrix.MatrixProduct(new double[][]{new double[]{1,2,3},new double[]{4,5,6}},new double[][]{new double[]{7,8},new double[]{9,10},new double[]{11,12}});
            Require(c[0].SequenceEqual(new double[]{58,64}) && c[1].SequenceEqual(new double[]{139,154}));Observations["rectangularProduct"]=c;
        });
        Check("matrix_transpose_and_scalar_product_preserve_input", () => {
            double[][] a={new double[]{1,2,3},new double[]{4,5,6}};var t=Matrix.MatrixTranspose(a);var s=Matrix.ScalarProduct(a,-2);
            Require(t.Length==3 && t[2].SequenceEqual(new double[]{3,6}) && s[0].SequenceEqual(new double[]{-2,-4,-6}) && a[0][0]==1);
        });
        Check("matrix_nonconformable_product_is_rejected", () => Throws<Exception>(()=>Matrix.MatrixProduct(new double[][]{new double[]{1,2}},new double[][]{new double[]{3,4}})));
        Check("singular_matrix_raw_nonfinite_result_is_recorded", () => {
            var inverse=Matrix.MatrixInverse(new double[][]{new double[]{1,2},new double[]{2,4}});
            Require(inverse.SelectMany(row=>row).Any(value=>!double.IsFinite(value)));
            Observations["rawSingularInverse"]=inverse.Select(row=>row.Select(value=>value.ToString("R",System.Globalization.CultureInfo.InvariantCulture)).ToArray()).ToArray();
        });
        Check("metadata_preserves_nonsequential_ids_units_and_coordinate_system", () => {
            var m = Metadata(); Require(m.FormatVersion == 2 && m.LengthUnit == "mm" && m.CoordinateSystem == "global");
            Require(m.GetEntities("FACE").Select(e => e.Id).SequenceEqual(new[] { 7,41 }));
            Observations["metadata"] = new { version = m.FormatVersion, unit = m.LengthUnit, coordinates = m.CoordinateSystem,
                faceIds = m.GetEntities("face").Select(e => e.Id).ToArray(), edgeIds = m.GetEntities("edge").Select(e => e.Id).ToArray() };
        });
        Check("duplicate_entity_id_replaces_without_renumbering", () => {
            var m = Metadata(); m.AddEntity(Entity("face",41,"area",new double[]{99}));
            Require(m.GetEntities("face").Length == 2); Near(m.GetEntity("face",41).Properties["area"].NumericValues[0],99);
        });
        Check("numeric_and_text_constructors_copy_input_arrays", () => {
            double[] n = { 1,2 }; string[] s = { "a",null }; var np=new GeometryMetadataProperty(n);var sp=new GeometryMetadataProperty(s);
            n[0]=8;s[0]="b";Require(np.NumericValues[0]==1 && sp.TextValues[0]=="a" && sp.TextValues[1]==null);
        });
        Check("deep_copy_is_independent", () => {
            var m=Metadata();var c=m.DeepCopy();c.GetEntity("face",41).Properties["area"].NumericValues[0]=123;
            Require(m.GetEntity("face",41).Properties["area"].NumericValues[0]==12.5);
        });
        Check("fill_missing_preserves_existing_values_and_copies_new_values", () => {
            var target=new GeometryMetadata(2,"global","mm");target.AddEntity(Entity("face",41,"area",new double[]{99}));
            var source=Metadata();target.FillMissingFrom(source,true,true,false);Near(target.GetEntity("face",41).Properties["area"].NumericValues[0],99);
            target.GetEntity("edge",8).Properties["length"].NumericValues[0]=10;Near(source.GetEntity("edge",8).Properties["length"].NumericValues[0],2.75);
        });
        Check("canonical_measurements_require_explicit_geometry_access", () => {
            var e=Metadata().GetEntity("face",41);Throws<NotSupportedException>(() => e.TryGetNumbers("AREA",out _));
            Require(e.TryGetCanonicalNumbers("AREA",out var values));Near(values[0],12.5);
            Require(!e.TryGetCanonicalText("area",out _));
        });
        Check("mesh_metadata_omits_canonical_values_and_preserves_topology_ids", () => {
            var m=new GeometryMetadata(2,"global","mm");m.FillMissingFrom(Metadata(),true,true,true);
            Require(!m.GetEntity("face",41).Properties.ContainsKey("area"));
            Require(m.GetEntity("face",7).Properties["edge_ids"].NumericValues.SequenceEqual(new double[]{8,13}));
            Require(m.GetEntity("edge",8).Properties["label"].TextValues[1]==null);
        });
        Check("face_edge_import_flags_preserve_other_entity_kinds", () => {
            var source=Metadata();source.AddEntity(Entity("solid",1,"volume",new double[]{1}));source.AddEntity(Entity("vertex",100,"coor",new double[]{1,2,3}));
            var m=new GeometryMetadata(2,"global","mm");m.FillMissingFrom(source,false,false,false);
            Require(m.GetEntities("face").Length==0 && m.GetEntities("edge").Length==0 && m.GetEntities("solid").Length==0 && m.GetEntity("vertex",100)!=null);
        });
        Check("serialized_field_names_preserve_upstream_contract", () => {
            var info=Info(Metadata());var names=new List<string>();foreach(SerializationEntry e in info) names.Add(e.Name);
            Require(names.SequenceEqual(new[]{"_formatVersion","_coordinateSystem","_lengthUnit","_entityData"}));Observations["serializedFields"]=names;
        });
        Check("single_face_binary_block_matches_independent_wire_bytes", () => {
            var m=new GeometryMetadata(2,"global","mm");m.AddEntity(Entity("face",41,"area",new double[]{12.5}));
            var bytes=(byte[])Info(m).GetValue("_entityData",typeof(byte[]));Require(bytes.SequenceEqual(ExpectedSingleFaceBlock()));
            Observations["singleFaceBlockHex"]=Convert.ToHexString(bytes);
        });
        Check("metadata_block_preserves_numbers_unicode_null_and_empty_text", () => {
            var restored=Restore((byte[])Info(Metadata()).GetValue("_entityData",typeof(byte[])));
            Near(restored.GetEntity("face",41).Properties["area"].NumericValues[0],12.5);
            Require(restored.GetEntity("edge",8).Properties["label"].TextValues.SequenceEqual(new string[]{"é-edge",null,""}));
            Require(restored.GetEntities("face").Select(e=>e.Id).SequenceEqual(new[]{7,41}));
        });
        Check("truncated_metadata_block_is_rejected", () => Throws<EndOfStreamException>(() => Restore(ExpectedSingleFaceBlock()[..^1])));
        Check("unknown_serialized_field_is_rejected", () => {
            var info=Info(Metadata());info.AddValue("unexpected",0);Throws<NotSupportedException>(()=>new ReconstructedMetadata(info));
        });
        Check("default_and_none_scale_are_unity", () => { Require(default(IntegrationScale).IsUnity);Near(default(IntegrationScale).GetWeight(7),1);Near(IntegrationScale.None.GetWeight(0),1); });
        Check("thickness_scale_is_constant", () => { var s=IntegrationScale.FromThickness(0.125);Require(!s.IsUnity);Near(s.GetWeight(100),0.125);Near(s.GetWeight(0),0.125);Observations["thicknessWeight"]=s.GetWeight(100); });
        Check("axisymmetric_scale_is_full_circumference", () => { var s=IntegrationScale.FromAxisymmetric();Near(s.GetWeight(2),4*Math.PI);Near(s.GetWeight(0),0);Observations["axisymmetricAtRadius2"]=s.GetWeight(2); });
        Check("unknown_scale_enum_is_rejected", () => Throws<NotSupportedException>(()=>new IntegrationScale {Type=(IntegrationScaleType)999}.GetWeight(1)));
        Check("negative_scale_inputs_are_preserved_raw_observation", () => {
            Near(IntegrationScale.FromThickness(-2).GetWeight(1),-2);Near(IntegrationScale.FromAxisymmetric().GetWeight(-1),-2*Math.PI);
            Observations["rawNegativeScaleInputs"] = new { thickness=IntegrationScale.FromThickness(-2).GetWeight(1),axisymmetric=IntegrationScale.FromAxisymmetric().GetWeight(-1) };
        });
        Check("frd_reader_handles_crlf_empty_line_utf8_and_final_line", () => {
            var r=Reader(Encoding.UTF8.GetBytes("alpha\r\n\né-last"));Require(r.ReadLine()=="alpha" && r.ReadLine()=="" && r.ReadLine()=="é-last" && r.ReadLine()==null);
        });
        Check("frd_reader_handles_single_byte_partial_reads", () => {
            var r=Reader(Encoding.UTF8.GetBytes("é\r\nβ\n"),1);Require(r.ReadLine()=="é" && r.ReadLine()=="β" && r.ReadLine()==null);
        });
        Check("frd_reader_grows_past_one_megabyte_boundary", () => {
            var text=new string('x',(1<<20)+7);var r=Reader(Encoding.UTF8.GetBytes(text+"\r\nnext\n"));Require(r.ReadLine()==text && r.ReadLine()=="next" && r.ReadLine()==null);
        });
        Check("frd_reader_interleaves_text_binary_and_text_without_loss", () => {
            byte[] binary={0,255,10,13,42};var bytes=Encoding.UTF8.GetBytes("header\n").Concat(binary).Concat(Encoding.UTF8.GetBytes("tail\n")).ToArray();
            var r=Reader(bytes,3);Require(r.ReadLine()=="header" && r.ReadBytes(5).SequenceEqual(binary) && r.ReadLine()=="tail" && r.ReadLine()==null);
            Observations["mixedBinaryHex"]=Convert.ToHexString(binary);
        });
        Check("frd_reader_partial_binary_eof_returns_count_and_null", () => {
            var r=Reader(new byte[]{1,2,3},1);byte[] destination={99,99,99,99,99,99};Require(r.ReadBytes(destination,1,5)==3);
            Require(destination.SequenceEqual(new byte[]{99,1,2,3,99,99}));Require(r.ReadBytes(1)==null);
        });
        Check("frd_reader_zero_bytes_empty_stream_and_carriage_return", () => {
            var r=Reader(Array.Empty<byte>());Require(r.ReadBytes(0).Length==0 && r.ReadLine()==null);
            r=Reader(Encoding.UTF8.GetBytes("x\r"));Require(r.ReadLine()=="x" && r.ReadLine()==null);
        });
    }
    private static int Main(string[] args)
    {
        if (args.Length!=1 || args[0]!="--self-test") { Console.WriteLine("{\"success\":false,\"error\":\"Usage: DataProbe --self-test\"}");return 2; }
        Run();
        var result=new {schemaVersion=1,success=failed==0,runtime=new {os=RuntimeInformation.IsOSPlatform(OSPlatform.OSX)?"macOS":RuntimeInformation.IsOSPlatform(OSPlatform.Linux)?"Linux":"Windows",architecture=RuntimeInformation.ProcessArchitecture.ToString(),osArchitecture=RuntimeInformation.OSArchitecture.ToString(),framework=RuntimeInformation.FrameworkDescription},passed=Checks.Count-failed,failed,checks=Checks,observations=Observations,
            exploratoryTypeIdentity=typeof(GeometryMetadata).AssemblyQualifiedName,
            limitations="Six-file slice; no full reader, CAD, element integration, PMX/NRBF/Windows-oracle or whole-core equivalence. Probe assembly is not a persistent type owner."};
        Console.WriteLine(JsonSerializer.Serialize(result,new JsonSerializerOptions{WriteIndented=true}));return failed==0?0:1;
    }
}
