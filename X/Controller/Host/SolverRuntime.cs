using System;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
namespace PrePoMax
{
    public static class SolverRuntime
    {
        // Select the build explicitly. This validates the retained source/build
        // profile, without choosing a backend or changing the model's solver.
        public static string Validate(string registry,string buildId,string directory)
        {
            using var json=JsonDocument.Parse(File.ReadAllText(registry));
            var root=json.RootElement;
            if(root.GetProperty("schemaVersion").GetInt32()!=1)throw new InvalidDataException("Unknown solver registry schema.");
            var builds=root.GetProperty("builds").EnumerateArray().Where(b=>b.GetProperty("id").GetString()==buildId).ToArray();
            if(builds.Length!=1)throw new InvalidDataException("An explicit solver build is required.");
            var build=builds[0];
            string os=OperatingSystem.IsWindows()?"Windows":OperatingSystem.IsMacOS()?"Darwin":"Linux";
            if(build.GetProperty("os").GetString()!=os || build.GetProperty("architecture").GetString()!=RuntimeInformation.ProcessArchitecture.ToString() || build.GetProperty("version").GetString()!="2.22")throw new InvalidDataException("Solver version or native target differs from the pinned baseline.");
            string executable=build.GetProperty("executable").GetString();
            bool found=false;
            foreach(var item in build.GetProperty("files").EnumerateObject())
            {
                if(Path.GetFileName(item.Name)!=item.Name || item.Name.Contains('\\'))throw new InvalidDataException("Invalid solver runtime basename.");
                Verify(Path.Combine(directory,item.Name),item.Value.GetString());found|=item.Name==executable;
            }
            if(!found)throw new InvalidDataException("Solver executable is not fingerprinted.");
            if(build.TryGetProperty("externalFiles",out var external))foreach(var item in external.EnumerateObject())
            {
                if(!Path.IsPathFullyQualified(item.Name))throw new InvalidDataException("External runtime path must be absolute.");
                Verify(item.Name,item.Value.GetString());
            }
            return Path.GetFullPath(Path.Combine(directory,executable));
        }
        static void Verify(string path,string expected)
        {
            if(!File.Exists(path) || Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(path)))!=expected)throw new InvalidDataException("Pinned solver/runtime file differs: "+path);
        }
    }
}
