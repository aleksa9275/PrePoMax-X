using System.Reflection;
using System.Runtime.Serialization;
using System.Text;
using CaeGlobals;
using CaeModel;
using PrePoMax.LegacyImport;
using PrePoMaxX.Persistence;

// Persistence since 3.0.2: upstream's storage serializer (PmxObjectSerializer, [PmxType]/[PmxKey]) writes and reads
// projects, settings and clones; files of older versions (binary formatter) are read by upstream's legacy reader with
// every type bound by the allowlist (AllowlistBinder), never by the reader itself.
internal static class PersistenceChecks
{
    internal static string[] Run(NrbfTypePolicy policy)
    {
        var checks=new List<string>();
        var serializer=new PmxObjectSerializer();
        void Check(string name,bool value) {if(!value)throw new Exception(name);checks.Add(name);}
        T Copy<T>(T value) {byte[] bytes=serializer.SerializeToBytes(value);return (T)serializer.DeserializeFromBytes(bytes,0,bytes.Length);}
        object Legacy(byte[] value) {using var stream=new MemoryStream(value,false);return LegacyReader.Read(stream);}
        void Reject(string name,Action action)
        {
            try {action();}catch(Exception e) when(e is SerializationException || e.InnerException is SerializationException) {checks.Add(name);return;}
            throw new Exception("Refusal failed: "+name);
        }
        // The storage format (upstream 3.0.2)
        var cycle=new object[3];var material=new Material("Shared");cycle[0]=cycle;cycle[1]=material;cycle[2]=material;
        var cloned=Copy(cycle);
        Check("cycle identity",ReferenceEquals(cloned,cloned[0]));
        Check("shared object identity",ReferenceEquals(cloned[1],cloned[2]) && !ReferenceEquals(material,cloned[1]));
        var dictionary=new CaeGlobals.OrderedDictionary<string,Material>("Materials",StringComparer.OrdinalIgnoreCase);dictionary.Add("first",material);dictionary.Add("second",material);
        var copied=Copy(dictionary);
        Check("ordered dictionary and comparer",copied.Keys.SequenceEqual(new[]{"first","second"}) && copied.ContainsKey("FIRST"));
        Check("dictionary shared values",ReferenceEquals(copied["first"],copied["second"]));
        double[,] matrix={{double.NaN,-0.0},{double.PositiveInfinity,1.25}};var matrixCopy=Copy(matrix);
        Check("rectangular array shape",matrixCopy.GetLength(0)==2 && matrixCopy.GetLength(1)==2);
        Check("IEEE values and signed zero",double.IsNaN(matrixCopy[0,0]) && double.IsPositiveInfinity(matrixCopy[1,0]) && BitConverter.DoubleToInt64Bits(matrixCopy[0,1])==BitConverter.DoubleToInt64Bits(-0.0));
        Check("UTF-8 characters",Copy(new[]{'A','ž','\0'}).SequenceEqual(new[]{'A','ž','\0'}));
        var date=new DateTime(638000000000000000,DateTimeKind.Utc);Check("UTC DateTime value",Copy(new[]{date})[0].Ticks==date.Ticks);
        var settings=new Dictionary<string,PrePoMax.ISettings> {{"General",new PrePoMax.GeneralSettings()}};
        Check("settings interface declarations",Copy(settings)["General"] is PrePoMax.GeneralSettings);
        Check("material clone",material.DeepClone() is Material clone && !ReferenceEquals(clone,material) && clone.Name=="Shared");
        // Large original projects
        var strings=new object[2100000];for(int i=0;i<strings.Length;i++)strings[i]="n"+i;
        var stringsCopy=Copy(strings);
        Check("more than two million objects",stringsCopy.Length==strings.Length && (string)stringsCopy[^1]=="n2099999");
        var large=new int[33000000];large[^1]=7;
        var largeCopy=Copy(large);
        Check("more than 32 million array elements",largeCopy.Length==large.Length && largeCopy[^1]==7);
        large=null;largeCopy=null;strings=null;stringsCopy=null;GC.Collect();
        // B013: the FileInfo a distribution keeps of its file
        var distribution=new DistributionFromFile("Fields");var oldFile=typeof(DistributionFromFile).GetField("_oldFileInfo",BindingFlags.Instance|BindingFlags.NonPublic);
        string fieldFile=Path.Combine(Path.GetTempPath(),"field.txt");oldFile.SetValue(distribution,new FileInfo(fieldFile));
        Check("FileInfo of a distribution file",((FileInfo)oldFile.GetValue(Copy(distribution))).FullName==fieldFile);
        // Files of older versions: upstream's reader, every type through the allowlist
        Check("legacy reader restricted",LegacyReader.RestrictingBinder is AllowlistBinder);
        var legacyFile=(FileInfo)Legacy(Class("System.IO.FileInfo",null,("OriginalPath",fieldFile),("FullPath",fieldFile)));
        Check("legacy FileInfo (net48 OriginalPath, FullPath)",legacyFile.FullName==fieldFile);
        var legacyMaterial=(Material)Legacy(Class("CaeModel.Material",Assembly("CaeModel"),("_name","Steel")));
        Check("legacy original data type",legacyMaterial.Name=="Steel");
        Check("legacy removed application type read as null",Legacy(Class("CaeModel.TypeRemovedInAnOlderVersion",Assembly("CaeModel")))==null);
        Reject("unknown framework type",()=>Legacy(Class("System.Diagnostics.Process",Assembly("System"))));
        Reject("unknown assembly",()=>Legacy(Class("CaeGlobals.NamedClass","Untrusted.Assembly, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null")));
        Reject("spoofed comparer assembly",()=>Legacy(Class("System.OrdinalComparer","Untrusted.Assembly, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null")));
        Reject("application type outside the allowlist",()=>Legacy(Class("PrePoMax.Controller",Assembly("PrePoMax"))));
        Check("delegate payload never activated",Legacy(Class("System.DelegateSerializationHolder",null))==null);
        // The binder alone resolves: a name it does not bind is not looked up by the reader
        using(var stream=new MemoryStream(Class("System.Diagnostics.Process",Assembly("System")),false))
            Check("no reader fallback to Type.GetType",new LegacyObjectReader(new NullBinder(),true).Read(stream)==null);
        Check("original renamed type mapping",policy.Bind("CaeMesh, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null","CaeMesh.Meshing.ElementSizeTypeEnum")==typeof(CaeMesh.ElementSizeTypeEnum));
        Check("3.0.2 renamed type mapping",policy.Bind("CaeMesh, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null","CaeMesh.ExtrudeMesh")==typeof(CaeMesh.SweepMesh));
        Check("unsafe formatter remains disabled",!(AppContext.TryGetSwitch("System.Runtime.Serialization.EnableUnsafeBinaryFormatterSerialization",out bool enabled)&&enabled));
        return checks.ToArray();
    }
    sealed class NullBinder : SerializationBinder {public override Type BindToType(string assemblyName,string typeName)=>null;}
    static string Assembly(string name) => name+", Version=1.0.0.0, Culture=neutral, PublicKeyToken=null";
    // One NRBF class record (MS-NRBF 2.3.2.3/2.3.2.4) with string members, as the binary formatter writes it
    static byte[] Class(string name,string assembly,params (string Name,string Value)[] members)
    {
        using var output=new MemoryStream();using var writer=new BinaryWriter(output,Encoding.UTF8,true);
        writer.Write((byte)0);writer.Write(1);writer.Write(-1);writer.Write(1);writer.Write(0);
        if(assembly!=null) {writer.Write((byte)12);writer.Write(2);writer.Write(assembly);}
        writer.Write((byte)(assembly==null?4:5));writer.Write(1);writer.Write(name);writer.Write(members.Length);
        foreach(var member in members)writer.Write(member.Name);
        foreach(var member in members)writer.Write((byte)1);   // BinaryType String
        if(assembly!=null)writer.Write(2);
        int id=10;foreach(var member in members) {writer.Write((byte)6);writer.Write(id++);writer.Write(member.Value);}
        writer.Write((byte)11);writer.Flush();return output.ToArray();
    }
}
