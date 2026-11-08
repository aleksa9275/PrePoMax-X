using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;

namespace GmshCommon
{
    // A version number alone cannot distinguish stock Gmsh from PrePoMax's patched build.
    internal static class NativeProfile
    {
        internal const string Version = "4.13.0";
        private const string Revision = "4156db5d5647087b1575c3f4b8a65a891b81102b";
        private static readonly Lazy<IntPtr> Handle = new Lazy<IntPtr>(LoadCore);

        internal static IntPtr Load()
        {
            return Handle.Value;
        }

        private static IntPtr LoadCore()
        {
            string library = Environment.GetEnvironmentVariable("PREPOMAXX_GMSH_LIBRARY");
            if (!string.IsNullOrEmpty(library))
            {
                if (!Path.IsPathFullyQualified(library))
                    throw new DllNotFoundException("PREPOMAXX_GMSH_LIBRARY must be an absolute path.");
                return LoadVerified(library);
            }
            foreach (string name in new[] { "gmsh-4.13.dll", "libgmsh.4.13.0.dylib", "libgmsh.so.4.13.0" })
            {
                string candidate = Path.Combine(AppContext.BaseDirectory, name);
                if (File.Exists(candidate)) return LoadVerified(candidate);
            }
            throw new DllNotFoundException("The pinned PrePoMax Gmsh runtime is missing. Build X/Build/Gmsh " +
                "and set PREPOMAXX_GMSH_LIBRARY to its absolute library path (with adjacent gmsh-build.json).");
        }

        private static IntPtr LoadVerified(string library)
        {
            string manifest = Path.Combine(Path.GetDirectoryName(library), "gmsh-build.json");
            if (!File.Exists(library) || !File.Exists(manifest))
                throw new DllNotFoundException("Gmsh library and adjacent gmsh-build.json are required: " + library);
            using (JsonDocument document = JsonDocument.Parse(File.ReadAllText(manifest)))
            {
                JsonElement profile = document.RootElement;
                if (profile.GetProperty("schemaVersion").GetInt32() != 1 ||
                    profile.GetProperty("version").GetString() != Version ||
                    profile.GetProperty("revision").GetString() != Revision ||
                    profile.GetProperty("occtVersion").GetString() != "7.7.0")
                    throw new InvalidOperationException("Gmsh build profile does not match the pinned PrePoMax baseline.");
                using (FileStream stream = File.OpenRead(library))
                {
                    string actual = Convert.ToHexString(SHA256.HashData(stream));
                    if (!string.Equals(actual, profile.GetProperty("librarySha256").GetString(), StringComparison.OrdinalIgnoreCase))
                        throw new InvalidOperationException("Gmsh library fingerprint does not match gmsh-build.json.");
                }
            }
            return NativeLibrary.Load(library);
        }
    }
}
