using System.Reflection;
using System.Runtime.Serialization;

namespace PrePoMaxX.Persistence;

/// <summary>Only compiled, explicitly named application data types and a small
/// set of BCL value/collection types can be reconstructed. Payload names never
/// cause Assembly.Load, arbitrary activation, delegates or object replacement.</summary>
public sealed class NrbfTypePolicy
{
    readonly HashSet<Type> frameworkTypes = new();
    readonly Dictionary<string,Type> types = new(StringComparer.Ordinal);
    readonly Dictionary<string,Type> metadataTypes = new(StringComparer.Ordinal);
    readonly Dictionary<string,Assembly> assemblies = new(StringComparer.Ordinal);
    public NrbfTypePolicy(IEnumerable<Assembly> applicationAssemblies, IEnumerable<string> allowlist)
    {
        var app = applicationAssemblies.ToDictionary(a=>a.GetName().Name,StringComparer.Ordinal);
        foreach(string entry in allowlist.Where(l=>l.Length>0 && !l.StartsWith("#")))
        {
            int separator=entry.IndexOf('|');
            bool metadata=entry.StartsWith("@");
            string assembly=entry[(metadata?1:0)..separator], name=entry[(separator+1)..];
            Type type=app[assembly].GetType(name,throwOnError:true);
            if((!metadata && !type.IsSerializable) || typeof(Delegate).IsAssignableFrom(type))throw new SerializationException("Not a serializable data type: "+entry);
            (metadata?metadataTypes:types).Add(assembly+"|"+name,type); assemblies[assembly]=type.Assembly;
        }
        Type[] framework = {typeof(System.IO.Compression.CompressionLevel),typeof(object),typeof(Type),typeof(string),typeof(bool),typeof(byte),typeof(sbyte),typeof(short),typeof(ushort),typeof(int),typeof(uint),typeof(long),typeof(ulong),typeof(float),typeof(double),typeof(decimal),typeof(char),typeof(DateTime),typeof(TimeSpan),typeof(Guid),typeof(System.Drawing.Color),typeof(System.Drawing.Point),typeof(System.Drawing.PointF),typeof(System.Drawing.Size),typeof(System.Drawing.SizeF),typeof(System.Drawing.Rectangle),typeof(System.Drawing.RectangleF),typeof(List<>),typeof(Dictionary<,>),typeof(HashSet<>),typeof(KeyValuePair<,>),typeof(Queue<>),typeof(Stack<>),typeof(LinkedList<>),typeof(Tuple<>),typeof(Tuple<,>),typeof(Tuple<,,>),typeof(ValueTuple<,>),typeof(ValueTuple<,,>),typeof(Nullable<>),typeof(System.Collections.ArrayList),typeof(System.Collections.Hashtable)};
        foreach(Type type in framework) AddFramework(type);
        foreach(string name in new[]{"System.Collections.Generic.GenericEqualityComparer`1","System.Collections.Generic.ObjectEqualityComparer`1","System.Collections.Generic.EnumEqualityComparer`1","System.Collections.Generic.NullableEqualityComparer`1","System.Collections.Generic.GenericComparer`1","System.Collections.Generic.ObjectComparer`1"})
            AddFramework(typeof(object).Assembly.GetType(name,true));
        // Framework assembly identities used by net48 PMX payloads.
        foreach(string name in new[]{"mscorlib","System","System.Core","System.Private.CoreLib"})assemblies[name]=typeof(object).Assembly;
        assemblies["System.Drawing"]=typeof(System.Drawing.Color).Assembly;
        assemblies["System.Drawing.Primitives"]=typeof(System.Drawing.Color).Assembly;
        // Persisted nonvisual WinForms enum values retain their original identities.
        if(app.TryGetValue("PrePoMaxX.WinFormsCompat",out var forms))assemblies["System.Windows.Forms"]=forms;
    }
    void AddFramework(Type type)
    {
        frameworkTypes.Add(type);
        types[type.Assembly.GetName().Name+"|"+type.FullName]=type;
        assemblies[type.Assembly.GetName().Name]=type.Assembly;
    }
    public Type Resolve(string qualifiedName) => ResolveCore(qualifiedName,false);
    public Type ResolveMetadata(string qualifiedName) => ResolveCore(qualifiedName,true);
    Type ResolveCore(string qualifiedName,bool metadata)
    {
        if(qualifiedName.Length>16384)throw new SerializationException("Type name limit exceeded.");
        try
        {
            Type type=Type.GetType(qualifiedName,
                name=>assemblies.TryGetValue(name.Name,out var a)?a:throw new SerializationException("Assembly is not allowed: "+name.Name),
                (assembly,name,ignoreCase)=>Find(assembly,name,metadata),true,false);
            if(!metadata || !metadataTypes.ContainsValue(type))Require(type); return type;
        }
        catch(Exception e) when(e is not SerializationException) {throw new SerializationException("Type is not allowed: "+qualifiedName,e);}
    }
    Type Find(Assembly assembly,string name,bool metadata)
    {
        string renamed=CaeGlobals.RenamedTypeSerializationBinder.GetRenamedTypeName(name);
        if(renamed!=null)return metadata?ResolveMetadata(renamed):Resolve(renamed);
        string key=assembly?.GetName().Name+"|"+name;
        if(types.TryGetValue(key,out var type) || metadataTypes.TryGetValue(key,out type))return type;
        // net48 divides BCL data types differently from .NET; match only exact
        // allowlisted framework names, never an arbitrary supplied name.
        if(assembly==typeof(object).Assembly || assembly==typeof(System.Drawing.Color).Assembly)
            return frameworkTypes.SingleOrDefault(t=>t.FullName==name);
        return null;
    }
    public void RequireMetadata(Type type) {if(!metadataTypes.ContainsValue(type))Require(type);}
    public void Require(Type type)
    {
        if(type.IsArray) {if(type.GetArrayRank()>8)throw new SerializationException("Array rank limit exceeded.");RequireDeclaration(type.GetElementType());return;}
        if(type.IsConstructedGenericType) {Require(type.GetGenericTypeDefinition());foreach(Type argument in type.GenericTypeArguments)RequireDeclaration(argument);return;}
        if(!types.ContainsValue(type))throw new SerializationException("Type is not allowed: "+type.FullName);
    }
    void RequireDeclaration(Type type)
    {
        if(metadataTypes.ContainsValue(type))return;
        Require(type);
    }
    public static string AssemblyIdentity(Type type)
    {
        while(type.IsArray)type=type.GetElementType();
        if(type.IsConstructedGenericType)type=type.GetGenericTypeDefinition();
        if(type==typeof(HashSet<>))return "System.Core, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089";
        if(type==typeof(System.IO.Compression.CompressionLevel))return "System, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089";
        if(type.Assembly==typeof(object).Assembly)return "mscorlib, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089";
        if(type.Assembly==typeof(System.Drawing.Color).Assembly)return "System.Drawing, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a";
        if(type.Assembly.GetName().Name=="PrePoMaxX.WinFormsCompat")return "System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089";
        return type.Assembly.FullName;
    }
    public static bool IsSystemClass(Type type) => AssemblyIdentity(type).StartsWith("mscorlib,",StringComparison.Ordinal);
    public static string TypeName(Type type)
    {
        if(type.IsArray)return TypeName(type.GetElementType())+"["+new string(',',type.GetArrayRank()-1)+"]";
        if(!type.IsConstructedGenericType)return type.FullName;
        return type.GetGenericTypeDefinition().FullName+"[["+string.Join("],[",type.GenericTypeArguments.Select(t=>TypeName(t)+", "+AssemblyIdentity(t)))+"]]";
    }
}
