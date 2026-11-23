using System.Runtime.Serialization;

namespace PrePoMaxX.Persistence;

/// <summary>The binder the X hosts give upstream's legacy reader (PrePoMax.LegacyImport.LegacyReader.RestrictingBinder):
/// the reader then resolves no type itself, so a file written by the binary formatter can only name allowlisted types
/// (never unrestricted deserialization).</summary>
public sealed class AllowlistBinder : SerializationBinder
{
    readonly NrbfTypePolicy policy;
    public AllowlistBinder(NrbfTypePolicy policy) {this.policy=policy;}
    public override Type BindToType(string assemblyName,string typeName) => policy.Bind(assemblyName,typeName);
}
