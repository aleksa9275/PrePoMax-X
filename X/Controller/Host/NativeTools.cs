using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using System.Runtime.InteropServices;
namespace PrePoMax
{
    public static class NativeTools
    {
        public static void Configure(string manifest)
        {
            if(!Path.IsPathFullyQualified(manifest))throw new ArgumentException("Native tool manifest must be absolute.");
            using var json=JsonDocument.Parse(File.ReadAllText(manifest));
            var root=json.RootElement;
            if(root.GetProperty("schemaVersion").GetInt32()!=1)throw new InvalidDataException("Unknown native tool manifest.");
            var paths=new Dictionary<string,(string Path,string Hash)>();
            foreach(var entry in root.GetProperty("tools").EnumerateObject())
            {
                string path=entry.Value.GetProperty("path").GetString();
                string hash=entry.Value.GetProperty("sha256").GetString();
                if(!Path.IsPathFullyQualified(path) || !File.Exists(path) || hash!=Hash(path))throw new InvalidDataException("Native tool path/fingerprint is invalid: "+entry.Name);
                paths.Add(entry.Name,(path,hash));
            }
            if(paths.TryGetValue("lib3mf.dll",out var threeMf))
            {
                IntPtr library=NativeLibrary.Load(threeMf.Path);
                NativeLibrary.SetDllImportResolver(typeof(Lib3MF.Lib3MFWrapper).Assembly,
                    (name,assembly,searchPath)=>name=="lib3mf.dll"?library:IntPtr.Zero);
                Lib3MF.Lib3MFWrapper.GetLibraryVersion(out uint major,out uint minor,out uint micro);
                if(major!=2 || minor!=4 || micro!=1)throw new InvalidDataException("The original 3MF binding requires the explicit lib3mf 2.4.1 profile.");
            }
            RuntimePaths.ToolResolver=identity=>
            {
                if(!paths.TryGetValue(identity,out var tool))throw new FileNotFoundException("Native tool is not configured: "+identity);
                if(Hash(tool.Path)!=tool.Hash)throw new InvalidDataException("Native tool fingerprint changed: "+identity);
                return tool.Path;
            };
            EnablePlatformExecutables();
        }
        public static void EnablePlatformExecutables()
        {
            RuntimePaths.ExecutableValidator=path=>
            {
                if(!File.Exists(path))return false;
                if(OperatingSystem.IsWindows()) {string extension=Path.GetExtension(path);return extension==".exe" || extension==".bat" || extension==".cmd";}
                return (File.GetUnixFileMode(path)&(UnixFileMode.UserExecute|UnixFileMode.GroupExecute|UnixFileMode.OtherExecute))!=0;
            };
        }

        static string Hash(string path) => Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path)));
    }
}
