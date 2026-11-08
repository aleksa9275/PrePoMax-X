using System.Runtime.Serialization;
using System.Text;
using CaeGlobals;
using CaeModel;
using PrePoMaxX.Persistence;

internal static class PersistenceChecks
{
    internal static string[] Run(NrbfTypePolicy policy)
    {
        var checks=new List<string>();var serializer=new RestrictedNrbfSerializer(policy);
        void Check(string name,bool value) {if(!value)throw new Exception(name);checks.Add(name);}
        byte[] Write(object value) {using var stream=new MemoryStream();serializer.Serialize(stream,value);return stream.ToArray();}
        object Read(byte[] value) {using var stream=new MemoryStream(value,false);return serializer.Deserialize(stream);}
        void Reject(string name,Action action)
        {
            try {action();}catch(SerializationException) {checks.Add(name);return;}
            throw new Exception("Refusal failed: "+name);
        }
        var cycle=new object[3];var material=new Material("Shared");cycle[0]=cycle;cycle[1]=material;cycle[2]=material;
        var cloned=(object[])Read(Write(cycle));
        Check("cycle identity",ReferenceEquals(cloned,cloned[0]));
        Check("shared object identity",ReferenceEquals(cloned[1],cloned[2]) && !ReferenceEquals(material,cloned[1]));
        var dictionary=new CaeGlobals.OrderedDictionary<string,Material>("Materials",StringComparer.OrdinalIgnoreCase);dictionary.Add("first",material);dictionary.Add("second",material);
        var copied=(CaeGlobals.OrderedDictionary<string,Material>)Read(Write(dictionary));
        Check("ordered dictionary and comparer",copied.Keys.SequenceEqual(new[]{"first","second"}) && copied.ContainsKey("FIRST"));
        Check("dictionary shared values",ReferenceEquals(copied["first"],copied["second"]));
        double[,] matrix={{double.NaN,-0.0},{double.PositiveInfinity,1.25}};var matrixCopy=(double[,])Read(Write(matrix));
        Check("rectangular array shape",matrixCopy.GetLength(0)==2 && matrixCopy.GetLength(1)==2);
        Check("IEEE values and signed zero",double.IsNaN(matrixCopy[0,0]) && double.IsPositiveInfinity(matrixCopy[1,0]) && BitConverter.DoubleToInt64Bits(matrixCopy[0,1])==BitConverter.DoubleToInt64Bits(-0.0));
        var chars=(char[])Read(Write(new[]{'A','ž','\0'}));Check("UTF-8 characters",chars.SequenceEqual(new[]{'A','ž','\0'}));
        var date=new DateTime(638000000000000000,DateTimeKind.Utc);Check("UTC DateTime value",((DateTime[])Read(Write(new[]{date})))[0].Ticks==date.Ticks);
        Check("converter Type metadata",(Type)Read(Write(typeof(StringDoubleConverter)))==typeof(StringDoubleConverter));
        var settings=new Dictionary<string,PrePoMax.ISettings> {{"General",new PrePoMax.GeneralSettings()}};
        var settingsCopy=(Dictionary<string,PrePoMax.ISettings>)Read(Write(settings));
        Check("settings interface declarations",settingsCopy["General"] is PrePoMax.GeneralSettings);
        Reject("unknown framework type",()=>Read(Class("System.Diagnostics.Process",null)));
        Reject("unknown assembly",()=>Read(Class("CaeGlobals.NamedClass","Untrusted.Assembly, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null")));
        Reject("delegate payload",()=>Read(Class("System.DelegateSerializationHolder",null)));
        Reject("delegate serialization",()=>Write((Action)(()=>{})));
        Reject("trailing bytes",()=>Read(Write(material).Concat(new byte[]{0}).ToArray()));
        byte[] meta=Write(typeof(string));Replace(meta,"System.String","System.Action");
        Reject("unknown Type metadata",()=>Read(meta));
        byte[] invalid=Write(material);Replace(invalid,"_description","_unexpectedX");Reject("unknown data member",()=>Read(invalid));
        Reject("spoofed comparer assembly",()=>Read(Class("System.OrdinalComparer","Untrusted.Assembly, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null")));
        Check("original renamed type mapping",policy.Resolve("CaeMesh.Meshing.ElementSizeTypeEnum, CaeMesh")==typeof(CaeMesh.ElementSizeTypeEnum));
        Check("unsafe formatter remains disabled",!(AppContext.TryGetSwitch("System.Runtime.Serialization.EnableUnsafeBinaryFormatterSerialization",out bool enabled)&&enabled));
        return checks.ToArray();
    }
    static byte[] Class(string name,string assembly)
    {
        using var output=new MemoryStream();using var writer=new BinaryWriter(output,Encoding.UTF8,true);
        writer.Write((byte)0);writer.Write(1);writer.Write(-1);writer.Write(1);writer.Write(0);
        if(assembly!=null) {writer.Write((byte)12);writer.Write(2);writer.Write(assembly);}
        writer.Write((byte)(assembly==null?4:5));writer.Write(1);writer.Write(name);writer.Write(0);if(assembly!=null)writer.Write(2);
        writer.Write((byte)11);writer.Flush();return output.ToArray();
    }
    static void Replace(byte[] data,string from,string to)
    {
        if(from.Length!=to.Length)throw new ArgumentException("Replacement must preserve wire length.");
        byte[] source=Encoding.UTF8.GetBytes(from),replacement=Encoding.UTF8.GetBytes(to);int index=data.AsSpan().IndexOf(source);
        if(index<0)throw new Exception("Wire field was not found.");replacement.CopyTo(data,index);
    }
}
