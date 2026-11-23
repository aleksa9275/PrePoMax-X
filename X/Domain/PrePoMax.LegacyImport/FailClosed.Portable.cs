// PrePoMax-X: the legacy reader of the X build fails closed. Until a host installs the allowlist binder
// (X/Persistence AllowlistBinder, through OriginalPersistence.Install), a file written by the binary formatter can
// name no type at all; upstream's reader would otherwise resolve any type the file names.
using System;
using System.Runtime.CompilerServices;
using System.Runtime.Serialization;

namespace PrePoMax.LegacyImport
{
    internal static class FailClosed
    {
        [ModuleInitializer]
        internal static void Initialize()
        {
            if (LegacyReader.RestrictingBinder == null) LegacyReader.RestrictingBinder = new RefuseAll();
        }
        private sealed class RefuseAll : SerializationBinder
        {
            public override Type BindToType(string assemblyName, string typeName)
            {
                throw new SerializationException("No type allowlist is installed; the file cannot be read.");
            }
        }
    }
}
