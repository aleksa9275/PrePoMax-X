using System.Runtime.Serialization;
using CaeGlobals;
using CaeMesh;
using CaeResults;

namespace PrePoMaxX.DataProbe;

internal static class TypeContracts
{
    internal static object Capture()
    {
        Type[] types = { typeof(Matrix), typeof(GeometryMetadata), typeof(GeometryMetadataEntity),
            typeof(GeometryMetadataProperty), typeof(IntegrationScale), typeof(IntegrationScaleType),
            typeof(FrdStreamReader) };
        return new
        {
            types = types.Select(type => new
            {
                name = type.FullName, identity = type.AssemblyQualifiedName, isPublic = type.IsPublic,
                serializable = type.IsDefined(typeof(SerializableAttribute), false)
            }).ToArray(),
            metadataImplementsOriginalInterfaces = typeof(ISerializable).IsAssignableFrom(typeof(GeometryMetadata)) &&
                typeof(IDeserializationCallback).IsAssignableFrom(typeof(GeometryMetadata)),
            assemblies = types.Select(type => type.Assembly).Distinct().Select(assembly => new
            {
                name = assembly.GetName().Name,
                references = assembly.GetReferencedAssemblies().Select(reference => reference.Name).Order().ToArray(),
                exportedTypes = assembly.GetExportedTypes().Select(type => type.FullName).Order().ToArray()
            }).ToArray()
        };
    }
}
